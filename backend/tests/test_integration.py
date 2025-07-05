"""Integration tests for the minimal API implementation."""

import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.mark.asyncio
async def test_full_task_flow_integration():
    """Test complete flow: API → SQS → WebSocket streaming."""
    # This test simulates the full task flow with mocked AWS services

    task_id = None
    sqs_message = None

    # Mock SQS to capture the message
    with patch("app.api.tasks.aioboto3.Session") as mock_sqs_session:
        mock_sqs = AsyncMock()

        async def capture_message(**kwargs):
            nonlocal sqs_message
            sqs_message = json.loads(kwargs["MessageBody"])
            return {"MessageId": "test-message-id"}

        mock_sqs.send_message = capture_message
        mock_sqs_session.return_value.client.return_value.__aenter__.return_value = mock_sqs

        # Create a task via API
        client = TestClient(app)
        response = client.post("/api/tasks/", json={"prompt": "Create a hello world function"})

        assert response.status_code == 200
        task_data = response.json()
        task_id = task_data["task_id"]
        assert task_data["status"] == "queued"

    # Verify SQS message format
    assert sqs_message is not None
    assert sqs_message["task_id"] == task_id
    assert sqs_message["prompt"] == "Create a hello world function"

    # Simulate agent processing and WebSocket streaming
    with patch("app.api.websocket.redis.from_url") as mock_redis_factory:
        mock_redis = AsyncMock()
        mock_pubsub = AsyncMock()

        # Simulate messages that would come from the agent
        agent_messages = [
            {"type": "subscribe"},
            {
                "type": "message",
                "data": json.dumps(
                    {"type": "output", "content": "Creating hello world function..."}
                ),
            },
            {
                "type": "message",
                "data": json.dumps(
                    {"type": "code", "content": "def hello_world():\n    print('Hello, World!')"}
                ),
            },
            {
                "type": "message",
                "data": json.dumps(
                    {"type": "complete", "status": "success", "artifacts": ["hello.py"]}
                ),
            },
        ]

        async def mock_listen():
            for msg in agent_messages:
                yield msg

        mock_pubsub.listen = mock_listen
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock()
        mock_pubsub.close = AsyncMock()
        mock_redis.pubsub.return_value = mock_pubsub
        mock_redis.close = AsyncMock()
        mock_redis_factory.return_value = mock_redis

        # Test WebSocket connection
        with client.websocket_connect(f"/ws/{task_id}") as websocket:
            # Receive output message
            message1 = websocket.receive_json()
            assert message1["type"] == "output"
            assert "Creating hello world" in message1["content"]

            # Receive code message
            message2 = websocket.receive_json()
            assert message2["type"] == "code"
            assert "def hello_world" in message2["content"]

            # Receive completion message
            message3 = websocket.receive_json()
            assert message3["type"] == "complete"
            assert message3["status"] == "success"
            assert "hello.py" in message3["artifacts"]


@pytest.mark.asyncio
async def test_concurrent_tasks():
    """Test handling multiple concurrent tasks."""
    task_ids = []

    with patch("app.api.tasks.aioboto3.Session") as mock_sqs_session:
        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock(return_value={"MessageId": "test-id"})
        mock_sqs_session.return_value.client.return_value.__aenter__.return_value = mock_sqs

        client = TestClient(app)

        # Create multiple tasks concurrently
        for i in range(5):
            prompt = f"Task {i}"
            response = client.post("/api/tasks/", json={"prompt": prompt})
            assert response.status_code == 200
            task_ids.append(response.json()["task_id"])

        # Verify all tasks were queued
        assert len(task_ids) == 5
        assert len(set(task_ids)) == 5  # All unique IDs

        # Verify SQS was called 5 times
        assert mock_sqs.send_message.call_count == 5


def test_error_propagation():
    """Test that errors are properly propagated through the system."""
    client = TestClient(app)

    # Test with SQS failure
    with patch("app.api.tasks.aioboto3.Session") as mock_sqs_session:
        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock(side_effect=Exception("AWS Service Error"))
        mock_sqs_session.return_value.client.return_value.__aenter__.return_value = mock_sqs

        response = client.post("/api/tasks/", json={"prompt": "Test"})
        assert response.status_code == 500
        assert "Failed to queue task" in response.json()["detail"]


def test_websocket_error_handling():
    """Test WebSocket error handling and cleanup."""
    client = TestClient(app)
    task_id = str(uuid.uuid4())

    with patch("app.api.websocket.redis.from_url") as mock_redis_factory:
        mock_redis = AsyncMock()
        mock_pubsub = AsyncMock()

        # Simulate Redis connection error
        mock_pubsub.subscribe = AsyncMock(side_effect=Exception("Redis connection failed"))
        mock_redis.pubsub.return_value = mock_pubsub
        mock_redis_factory.return_value = mock_redis

        # WebSocket should handle the error gracefully
        with pytest.raises(Exception), client.websocket_connect(f"/ws/{task_id}"):
            # Should receive error message
            pass
