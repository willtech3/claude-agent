import asyncio
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SQSHandler:
    """Handle SQS message polling and processing."""
    
    def __init__(self, sqs_client, queue_url: str, claude_wrapper):
        self.sqs_client = sqs_client
        self.queue_url = queue_url
        self.claude_wrapper = claude_wrapper
        self.running = False
        
    async def start(self):
        """Start polling SQS for messages."""
        self.running = True
        logger.info(f"Starting SQS polling on {self.queue_url}")
        
        while self.running:
            try:
                await self._poll_messages()
            except Exception as e:
                logger.error(f"Error polling SQS: {e}", exc_info=True)
                await asyncio.sleep(5)  # Back off on error
                
    async def stop(self):
        """Stop polling."""
        self.running = False
        
    async def _poll_messages(self):
        """Poll SQS for messages and process them."""
        # Receive messages
        response = self.sqs_client.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20,  # Long polling
            VisibilityTimeout=300  # 5 minutes to process
        )
        
        messages = response.get("Messages", [])
        
        for message in messages:
            try:
                # Parse message body
                body = json.loads(message["Body"])
                
                # Process the task
                await self.claude_wrapper.handle_task(body)
                
                # Delete message on success
                self.sqs_client.delete_message(
                    QueueUrl=self.queue_url,
                    ReceiptHandle=message["ReceiptHandle"]
                )
                
                logger.info(f"Successfully processed message {message['MessageId']}")
                
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                # Message will become visible again after VisibilityTimeout