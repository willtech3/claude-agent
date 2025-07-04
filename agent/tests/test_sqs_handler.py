import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from botocore.exceptions import ClientError

from agent.sqs_handler import SQSTaskHandler
from agent.claude_code import ClaudeCodeWrapper
from agent.event_parser import EventType
from agent.config import config


@pytest.fixture
def mock_claude_wrapper():
    return Mock(spec=ClaudeCodeWrapper)


@pytest.fixture
def sqs_handler(mock_claude_wrapper):
    with patch('boto3.client') as mock_boto_client:
        # Mock SQS and S3 clients
        mock_sqs = Mock()
        mock_s3 = Mock()
        mock_boto_client.side_effect = lambda service, **kwargs: mock_sqs if service == 'sqs' else mock_s3
        
        handler = SQSTaskHandler(mock_claude_wrapper)
        handler.sqs = mock_sqs
        handler.s3 = mock_s3
        handler.queue_url = "http://test-queue"
        handler.result_queue_url = "http://test-result-queue"
        handler.s3_bucket = "test-bucket"
        
        return handler


class TestSQSTaskHandler:
    @pytest.mark.asyncio
    async def test_receive_messages_success(self, sqs_handler):
        # Mock SQS response
        mock_messages = [
            {
                'MessageId': 'msg-1',
                'ReceiptHandle': 'handle-1',
                'Body': '{"id": "task-1", "prompt": "test"}',
                'Attributes': {'ApproximateReceiveCount': '1'}
            }
        ]
        sqs_handler.sqs.receive_message.return_value = {'Messages': mock_messages}
        
        messages = await sqs_handler.receive_messages()
        
        assert len(messages) == 1
        assert messages[0]['MessageId'] == 'msg-1'
        sqs_handler.sqs.receive_message.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_receive_messages_no_queue_url(self):
        # Test with no queue URL configured
        handler = SQSTaskHandler(Mock())
        handler.queue_url = ""
        
        messages = await handler.receive_messages()
        assert messages == []
        
    @pytest.mark.asyncio
    async def test_receive_messages_client_error(self, sqs_handler):
        # Mock client error
        sqs_handler.sqs.receive_message.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied'}}, 'ReceiveMessage'
        )
        
        messages = await sqs_handler.receive_messages()
        assert messages == []
        
    @pytest.mark.asyncio
    async def test_process_message_success(self, sqs_handler, mock_claude_wrapper):
        # Set up claude wrapper to return success events
        async def mock_execute_task(task):
            yield {"type": EventType.PROGRESS, "status": "working"}
            yield {"type": EventType.COMPLETION, "status": "completed", "summary": {}}
            
        mock_claude_wrapper.execute_task = AsyncMock(side_effect=mock_execute_task)
        
        message = {
            'ReceiptHandle': 'handle-1',
            'Body': '{"id": "task-1", "prompt": "test", "repository_url": "https://github.com/test/repo"}',
            'Attributes': {'ApproximateReceiveCount': '1'}
        }
        
        await sqs_handler.process_message(message)
        
        # Verify task was processed
        mock_claude_wrapper.execute_task.assert_called_once()
        
        # Verify status updates were sent
        assert sqs_handler.sqs.send_message.call_count >= 2  # At least start and completion
        
        # Verify message was deleted
        sqs_handler.sqs.delete_message.assert_called_once_with(
            QueueUrl=sqs_handler.queue_url,
            ReceiptHandle='handle-1'
        )
        
        # Verify artifacts were saved
        sqs_handler.s3.put_object.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_process_message_task_failure(self, sqs_handler, mock_claude_wrapper):
        # Set up claude wrapper to return error
        async def mock_execute_task(task):
            yield {"type": EventType.ERROR, "error": "Task failed"}
            
        mock_claude_wrapper.execute_task = AsyncMock(side_effect=mock_execute_task)
        
        message = {
            'ReceiptHandle': 'handle-1',
            'Body': '{"id": "task-1", "prompt": "test"}',
            'Attributes': {'ApproximateReceiveCount': '1'}
        }
        
        await sqs_handler.process_message(message)
        
        # Verify failure status was sent
        status_calls = sqs_handler.sqs.send_message.call_args_list
        assert any("FAILED" in str(call) for call in status_calls)
        
        # Message should be deleted for non-retryable error
        sqs_handler.sqs.delete_message.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_process_message_retryable_error(self, sqs_handler, mock_claude_wrapper):
        # Set up claude wrapper to return retryable error
        async def mock_execute_task(task):
            yield {"type": EventType.ERROR, "error": "Rate limit exceeded"}
            
        mock_claude_wrapper.execute_task = AsyncMock(side_effect=mock_execute_task)
        
        message = {
            'ReceiptHandle': 'handle-1',
            'Body': '{"id": "task-1", "prompt": "test"}',
            'Attributes': {'ApproximateReceiveCount': '1'}
        }
        
        await sqs_handler.process_message(message)
        
        # Verify retry status was sent
        status_calls = sqs_handler.sqs.send_message.call_args_list
        assert any("RETRYING" in str(call) for call in status_calls)
        
        # Message should NOT be deleted for retryable error
        sqs_handler.sqs.delete_message.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_process_message_max_retries_exceeded(self, sqs_handler, mock_claude_wrapper):
        message = {
            'ReceiptHandle': 'handle-1',
            'Body': '{"id": "task-1", "prompt": "test"}',
            'Attributes': {'ApproximateReceiveCount': '5'}  # Exceeds default max of 3
        }
        
        await sqs_handler.process_message(message)
        
        # Task should not be executed
        mock_claude_wrapper.execute_task.assert_not_called()
        
        # Failed status should be sent
        status_calls = sqs_handler.sqs.send_message.call_args_list
        assert any("FAILED" in str(call) and "exceeded retry limit" in str(call) for call in status_calls)
        
        # Message should be deleted
        sqs_handler.sqs.delete_message.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_process_message_invalid_json(self, sqs_handler):
        message = {
            'ReceiptHandle': 'handle-1',
            'Body': 'invalid json',
            'Attributes': {}
        }
        
        await sqs_handler.process_message(message)
        
        # Message should be deleted for invalid format
        sqs_handler.sqs.delete_message.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_delete_message_error_handling(self, sqs_handler):
        # Mock delete failure
        sqs_handler.sqs.delete_message.side_effect = ClientError(
            {'Error': {'Code': 'MessageNotFound'}}, 'DeleteMessage'
        )
        
        # Should not raise exception
        await sqs_handler._delete_message("handle-1")
        
    @pytest.mark.asyncio
    async def test_send_status_update(self, sqs_handler):
        await sqs_handler._send_status_update("task-1", "PROCESSING", {"message": "Working"})
        
        sqs_handler.sqs.send_message.assert_called_once()
        call_args = sqs_handler.sqs.send_message.call_args[1]
        
        assert call_args['QueueUrl'] == sqs_handler.result_queue_url
        
        body = json.loads(call_args['MessageBody'])
        assert body['task_id'] == 'task-1'
        assert body['status'] == 'PROCESSING'
        assert body['message'] == 'Working'
        assert 'timestamp' in body
        
    @pytest.mark.asyncio
    async def test_save_artifacts_success(self, sqs_handler):
        events = [
            {"type": EventType.TOOL_USE, "tool": "Write", "status": "completed"},
            {"type": EventType.COMPLETION, "summary": {"changes": ["file1.py"]}}
        ]
        
        url = await sqs_handler._save_artifacts("task-1", events)
        
        sqs_handler.s3.put_object.assert_called_once()
        call_args = sqs_handler.s3.put_object.call_args[1]
        
        assert call_args['Bucket'] == 'test-bucket'
        assert call_args['Key'] == 'tasks/task-1/result.json'
        assert call_args['ContentType'] == 'application/json'
        
        # Verify artifact content
        body = json.loads(call_args['Body'])
        assert body['task_id'] == 'task-1'
        assert body['events'] == events
        assert 'summary' in body
        
        # Check returned URL
        assert url.endswith('/test-bucket/tasks/task-1/result.json')
        
    @pytest.mark.asyncio
    async def test_save_artifacts_s3_error(self, sqs_handler):
        # Mock S3 error
        sqs_handler.s3.put_object.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied'}}, 'PutObject'
        )
        
        events = []
        url = await sqs_handler._save_artifacts("task-1", events)
        
        # Should return empty string on error
        assert url == ""
        
    def test_create_summary(self, sqs_handler):
        events = [
            {"type": EventType.TOOL_USE, "tool": "Write", "status": "completed"},
            {"type": EventType.TOOL_USE, "tool": "Edit", "status": "completed"},
            {"type": EventType.TOOL_USE, "tool": "Write", "status": "completed"},
            {"type": EventType.ERROR, "error": "Something went wrong"},
            {"type": EventType.COMPLETION, "summary": {"changes": ["file1.py", "file2.py"]}}
        ]
        
        summary = sqs_handler._create_summary(events)
        
        assert summary['total_events'] == 5
        assert summary['tools_used'] == ['Write', 'Edit']
        assert summary['files_changed'] == ['file1.py', 'file2.py']
        assert summary['errors'] == ['Something went wrong']