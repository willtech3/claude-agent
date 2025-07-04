import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from agent.worker import AgentWorker
from agent.config import config


@pytest.fixture
def mock_session_manager():
    return Mock()


@pytest.fixture
def mock_claude_wrapper():
    return Mock()


@pytest.fixture
def mock_sqs_handler():
    handler = Mock()
    handler.receive_messages = AsyncMock()
    handler.process_message = AsyncMock()
    return handler


@pytest.fixture
def worker(mock_session_manager, mock_claude_wrapper, mock_sqs_handler):
    with patch('agent.worker.SessionManager', return_value=mock_session_manager):
        with patch('agent.worker.ClaudeCodeWrapper', return_value=mock_claude_wrapper):
            with patch('agent.worker.SQSTaskHandler', return_value=mock_sqs_handler):
                return AgentWorker()


class TestAgentWorker:
    def test_init(self, worker):
        assert worker.running is False
        assert worker.redis_client is None
        assert worker.session_manager is not None
        assert worker.claude_wrapper is not None
        assert worker.sqs_handler is not None
        
    @pytest.mark.asyncio
    async def test_start_stop(self, worker):
        # Mock init_connections to avoid real connections
        worker._init_connections = AsyncMock()
        
        # Mock process_messages to stop after one iteration
        async def mock_process():
            if worker.running:
                worker.running = False
                
        worker._process_messages = AsyncMock(side_effect=mock_process)
        
        # Start worker
        await worker.start()
        
        # Verify initialization was called
        worker._init_connections.assert_called_once()
        worker._process_messages.assert_called()
        
    @pytest.mark.asyncio
    async def test_stop(self, worker):
        # Mock Redis client
        mock_redis = AsyncMock()
        worker.redis_client = mock_redis
        
        await worker.stop()
        
        assert worker.running is False
        mock_redis.close.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_init_connections_with_redis(self, worker):
        # Mock Redis connection
        mock_redis = AsyncMock()
        
        with patch('agent.worker.config') as mock_config:
            mock_config.redis_url = "redis://localhost:6379"
            
            with patch('agent.worker.aioredis.from_url', return_value=mock_redis) as mock_from_url:
                await worker._init_connections()
                
                mock_from_url.assert_called_once_with("redis://localhost:6379")
                assert worker.redis_client == mock_redis
                
    @pytest.mark.asyncio
    async def test_init_connections_redis_failure(self, worker):
        with patch('agent.worker.config') as mock_config:
            mock_config.redis_url = "redis://localhost:6379"
            
            with patch('agent.worker.aioredis.from_url', side_effect=Exception("Connection failed")):
                # Should not raise exception
                await worker._init_connections()
                
                assert worker.redis_client is None
                
    @pytest.mark.asyncio
    async def test_process_messages_no_messages(self, worker):
        # Mock no messages
        worker.sqs_handler.receive_messages.return_value = []
        
        await worker._process_messages()
        
        worker.sqs_handler.receive_messages.assert_called_once()
        worker.sqs_handler.process_message.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_process_messages_with_messages(self, worker):
        # Mock messages
        messages = [
            {"MessageId": "msg-1"},
            {"MessageId": "msg-2"},
            {"MessageId": "msg-3"}
        ]
        worker.sqs_handler.receive_messages.return_value = messages
        
        await worker._process_messages()
        
        # Should process all messages
        assert worker.sqs_handler.process_message.call_count == 3
        
    @pytest.mark.asyncio
    async def test_process_messages_concurrent_limit(self, worker):
        # Mock many messages (more than limit of 5)
        messages = [{"MessageId": f"msg-{i}"} for i in range(10)]
        worker.sqs_handler.receive_messages.return_value = messages
        
        # Track concurrent executions
        concurrent_count = 0
        max_concurrent = 0
        
        async def mock_process(msg):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.01)  # Simulate processing
            concurrent_count -= 1
            
        worker.sqs_handler.process_message.side_effect = mock_process
        
        await worker._process_messages()
        
        # Should only process 5 messages concurrently
        assert worker.sqs_handler.process_message.call_count == 5
        assert max_concurrent <= 5
        
    @pytest.mark.asyncio
    async def test_process_messages_error_handling(self, worker):
        # Mock messages with one failing
        messages = [{"MessageId": "msg-1"}, {"MessageId": "msg-2"}]
        worker.sqs_handler.receive_messages.return_value = messages
        
        # First call raises exception, second succeeds
        worker.sqs_handler.process_message.side_effect = [
            Exception("Process failed"),
            None
        ]
        
        # Should not raise exception
        await worker._process_messages()
        
        # Both messages should be attempted
        assert worker.sqs_handler.process_message.call_count == 2
        
    @pytest.mark.asyncio
    async def test_start_with_process_error(self, worker):
        # Mock init_connections
        worker._init_connections = AsyncMock()
        
        # Mock process_messages to raise error then stop
        call_count = 0
        
        async def mock_process():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Process error")
            worker.running = False
            
        worker._process_messages = AsyncMock(side_effect=mock_process)
        
        # Should handle error and continue
        await worker.start()
        
        # Should have called process_messages twice (error + stop)
        assert worker._process_messages.call_count == 2