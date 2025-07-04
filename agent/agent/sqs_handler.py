import asyncio
import json
import os
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
import structlog

from agent.claude_code import ClaudeCodeWrapper
from agent.event_parser import EventType
from agent.config import config

logger = structlog.get_logger()


class SQSTaskHandler:
    def __init__(self, claude_wrapper: ClaudeCodeWrapper):
        self.claude_wrapper = claude_wrapper
        self.queue_url = config.sqs_queue_url or ""
        self.result_queue_url = config.sqs_result_queue_url or ""
        self.s3_bucket = config.s3_bucket_name
        
        # Initialize AWS clients
        self.sqs = self._create_sqs_client(config.aws_endpoint_url)
        self.s3 = self._create_s3_client(config.aws_endpoint_url)
        
    def _create_sqs_client(self, endpoint_url: Optional[str]):
        if endpoint_url:
            # LocalStack or custom endpoint
            return boto3.client(
                'sqs',
                endpoint_url=endpoint_url,
                region_name=config.aws_region,
                aws_access_key_id=config.aws_access_key_id or "test",
                aws_secret_access_key=config.aws_secret_access_key or "test"
            )
        else:
            # Real AWS
            return boto3.client('sqs')
            
    def _create_s3_client(self, endpoint_url: Optional[str]):
        if endpoint_url:
            # LocalStack or custom endpoint
            return boto3.client(
                's3',
                endpoint_url=endpoint_url,
                region_name=config.aws_region,
                aws_access_key_id=config.aws_access_key_id or "test",
                aws_secret_access_key=config.aws_secret_access_key or "test"
            )
        else:
            # Real AWS
            return boto3.client('s3')
            
    async def receive_messages(self, max_messages: int = 1, wait_time_seconds: int = 20) -> list:
        if not self.queue_url:
            logger.warning("No SQS queue URL configured")
            return []
            
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.sqs.receive_message(
                    QueueUrl=self.queue_url,
                    MaxNumberOfMessages=max_messages,
                    WaitTimeSeconds=wait_time_seconds,
                    MessageAttributeNames=['All']
                )
            )
            return response.get('Messages', [])
        except ClientError as e:
            logger.error("Failed to receive SQS messages", error=str(e))
            return []
            
    async def process_message(self, message: Dict[str, Any]):
        receipt_handle = message.get('ReceiptHandle')
        retry_count = int(message.get('Attributes', {}).get('ApproximateReceiveCount', '0'))
        max_retries = config.max_task_retries
        
        task_id = 'unknown'
        
        try:
            # Parse task from message body
            task = json.loads(message['Body'])
            task_id = task.get('id', 'unknown')
            
            logger.info("Processing task", task_id=task_id, retry_count=retry_count)
            
            # Check if we've exceeded retry limit
            if retry_count > max_retries:
                logger.error("Task exceeded retry limit", task_id=task_id, retry_count=retry_count)
                await self._send_status_update(task_id, "FAILED", {
                    "error": f"Task failed after {retry_count} attempts",
                    "message": "Task exceeded retry limit"
                })
                # Delete message to prevent further retries
                await self._delete_message(receipt_handle)
                return
            
            # Send initial status update
            await self._send_status_update(task_id, "PROCESSING", {
                "message": f"Task processing started (attempt {retry_count + 1})"
            })
            
            # Process task with Claude
            events = []
            error_occurred = False
            
            async for event in self.claude_wrapper.execute_task(task):
                events.append(event)
                
                # Send progress updates for significant events
                if event["type"] in [EventType.PROGRESS, EventType.TOOL_USE]:
                    await self._send_status_update(task_id, "PROCESSING", {
                        "progress": event
                    })
                elif event["type"] == EventType.ERROR:
                    error_occurred = True
                    
            # Check if task completed successfully
            completion_event = next(
                (e for e in events if e["type"] == EventType.COMPLETION),
                None
            )
            
            if completion_event and not error_occurred:
                # Save artifacts to S3
                artifact_url = await self._save_artifacts(task_id, events)
                
                # Send completion status
                await self._send_status_update(task_id, "COMPLETED", {
                    "artifact_url": artifact_url,
                    "summary": completion_event.get("summary", {}),
                    "message": "Task completed successfully"
                })
                
                # Delete message from queue
                await self._delete_message(receipt_handle)
            else:
                # Task failed
                error_event = next(
                    (e for e in events if e["type"] == EventType.ERROR),
                    None
                )
                
                error_msg = error_event.get("error", "Unknown error") if error_event else "Task did not complete"
                
                # Check if error is retryable
                retryable_errors = [
                    "rate limit",
                    "timeout",
                    "connection",
                    "network",
                    "temporary"
                ]
                
                is_retryable = any(err in error_msg.lower() for err in retryable_errors)
                
                if is_retryable and retry_count < max_retries:
                    # Don't delete message - let it retry
                    logger.warning("Retryable error occurred", task_id=task_id, error=error_msg)
                    await self._send_status_update(task_id, "RETRYING", {
                        "error": error_msg,
                        "retry_count": retry_count + 1,
                        "message": f"Task will be retried (attempt {retry_count + 2})"
                    })
                else:
                    # Non-retryable error or exceeded retries
                    await self._send_status_update(task_id, "FAILED", {
                        "error": error_msg,
                        "message": "Task failed permanently"
                    })
                    # Delete message to prevent further retries
                    await self._delete_message(receipt_handle)
                    
        except json.JSONDecodeError as e:
            logger.error("Invalid message format", error=str(e))
            # Delete malformed message
            await self._delete_message(receipt_handle)
            
        except Exception as e:
            logger.error("Failed to process message", task_id=task_id, error=str(e))
            
            # Try to update task status
            try:
                await self._send_status_update(task_id, "FAILED", {
                    "error": str(e),
                    "message": "Task processing failed"
                })
            except:
                pass
                
            # Check if we should retry
            if retry_count < max_retries:
                # Don't delete message - let it retry
                logger.info("Message will be retried", task_id=task_id, retry_count=retry_count)
            else:
                # Delete message after max retries
                await self._delete_message(receipt_handle)
            
    async def _delete_message(self, receipt_handle: str):
        if not self.queue_url or not receipt_handle:
            return
            
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.sqs.delete_message(
                    QueueUrl=self.queue_url,
                    ReceiptHandle=receipt_handle
                )
            )
        except ClientError as e:
            logger.error("Failed to delete message", error=str(e))
            
    async def _send_status_update(self, task_id: str, status: str, data: Dict[str, Any]):
        if not self.result_queue_url:
            logger.debug("No result queue configured, skipping status update")
            return
            
        message = {
            "task_id": task_id,
            "status": status,
            "timestamp": self._get_timestamp(),
            **data
        }
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.sqs.send_message(
                    QueueUrl=self.result_queue_url,
                    MessageBody=json.dumps(message),
                    MessageAttributes={
                        'task_id': {
                            'StringValue': task_id,
                            'DataType': 'String'
                        },
                        'status': {
                            'StringValue': status,
                            'DataType': 'String'
                        }
                    }
                )
            )
        except ClientError as e:
            logger.error("Failed to send status update", error=str(e))
            
    async def _save_artifacts(self, task_id: str, events: list) -> str:
        # Create artifact data
        artifact = {
            "task_id": task_id,
            "timestamp": self._get_timestamp(),
            "events": events,
            "summary": self._create_summary(events)
        }
        
        # Upload to S3
        key = f"tasks/{task_id}/result.json"
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.s3.put_object(
                    Bucket=self.s3_bucket,
                    Key=key,
                    Body=json.dumps(artifact, indent=2),
                    ContentType='application/json'
                )
            )
            
            # Return S3 URL
            if config.aws_endpoint_url:
                # LocalStack URL
                return f"{config.aws_endpoint_url}/{self.s3_bucket}/{key}"
            else:
                # Real S3 URL
                return f"https://{self.s3_bucket}.s3.amazonaws.com/{key}"
                
        except ClientError as e:
            logger.error("Failed to save artifacts", error=str(e))
            return ""
            
    def _create_summary(self, events: list) -> Dict[str, Any]:
        summary = {
            "total_events": len(events),
            "tools_used": [],
            "files_changed": [],
            "errors": []
        }
        
        for event in events:
            if event["type"] == EventType.TOOL_USE and event.get("status") == "completed":
                tool = event.get("tool", "")
                if tool not in summary["tools_used"]:
                    summary["tools_used"].append(tool)
                    
            elif event["type"] == EventType.COMPLETION:
                summary["files_changed"] = event.get("summary", {}).get("changes", [])
                
            elif event["type"] == EventType.ERROR:
                summary["errors"].append(event.get("error", "Unknown error"))
                
        return summary
        
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"