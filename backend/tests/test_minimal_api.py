"""Tests for minimal API implementation."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocket

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_sqs():
    """Mock SQS client."""
    with patch("app.api.tasks.aioboto3.Session") as mock_session:
        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock(return_value={"MessageId": "test-message-id"})
        mock_session.return_value.client.return_value.__aenter__.return_value = mock_sqs
        yield mock_sqs


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch("app.api.websocket.redis.from_url") as mock_redis_factory:
        mock_redis = AsyncMock()
        mock_pubsub = AsyncMock()
        mock_redis.pubsub.return_value = mock_pubsub
        mock_redis_factory.return_value = mock_redis
        yield mock_redis, mock_pubsub


def test_create_task_success(client, mock_sqs):
    """Test successful task creation."""
    response = client.post("/api/tasks/", json={"prompt": "Test prompt"})

    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "queued"
    assert len(data["task_id"]) == 36  # UUID length

    # Verify SQS was called with correct parameters
    mock_sqs.send_message.assert_called_once()
    call_args = mock_sqs.send_message.call_args[1]
    assert "QueueUrl" in call_args
    assert "MessageBody" in call_args

    # Verify message format
    message = json.loads(call_args["MessageBody"])
    assert message["prompt"] == "Test prompt"
    assert "task_id" in message


def test_create_task_invalid_request(client):
    """Test task creation with invalid request."""
    response = client.post("/api/tasks/", json={"invalid": "field"})
    assert response.status_code == 422  # Validation error


def test_create_task_empty_prompt(client):
    """Test task creation with empty prompt."""
    response = client.post("/api/tasks/", json={"prompt": ""})
    assert response.status_code == 422  # Validation should fail


@pytest.mark.asyncio
async def test_create_task_sqs_failure():
    """Test task creation when SQS fails."""
    from app.api.tasks import TaskRequest, create_task

    with patch("app.api.tasks.aioboto3.Session") as mock_session:
        # Mock SQS to raise an exception
        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock(side_effect=Exception("SQS Error"))
        mock_session.return_value.client.return_value.__aenter__.return_value = mock_sqs

        request = TaskRequest(prompt="Test prompt")

        with pytest.raises(Exception) as exc_info:
            await create_task(request)

        assert "Failed to queue task" in str(exc_info.value)


def test_websocket_endpoint_exists(client):
    """Test that the WebSocket endpoint exists."""
    routes = [route.path for route in app.routes]
    assert "/ws/{task_id}" in routes


@pytest.mark.asyncio
async def test_websocket_streaming():
    """Test WebSocket message streaming."""
    from app.api.websocket import websocket_endpoint

    # Create mock WebSocket
    mock_websocket = AsyncMock(spec=WebSocket)
    mock_websocket.accept = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    mock_websocket.close = AsyncMock()

    with patch("app.api.websocket.redis.from_url") as mock_redis_factory:
        # Setup Redis mock
        mock_redis = AsyncMock()
        mock_pubsub = AsyncMock()

        # Mock message stream
        test_messages = [
            {"type": "subscribe"},  # Subscription confirmation
            {
                "type": "message",
                "data": json.dumps({"type": "output", "content": "Starting task..."}),
            },
            {
                "type": "message",
                "data": json.dumps({"type": "output", "content": "Task completed"}),
            },
            {"type": "message", "data": json.dumps({"type": "complete", "status": "success"})},
        ]

        async def mock_listen():
            for msg in test_messages:
                yield msg

        mock_pubsub.listen = mock_listen
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock()
        mock_pubsub.close = AsyncMock()

        mock_redis.pubsub = MagicMock(return_value=mock_pubsub)
        mock_redis.close = AsyncMock()
        mock_redis_factory.return_value = mock_redis

        # Test the websocket endpoint
        task_id = str(uuid.uuid4())
        await websocket_endpoint(mock_websocket, task_id)

        # Verify WebSocket interactions
        mock_websocket.accept.assert_called_once()
        assert mock_websocket.send_json.call_count == 3  # Three message sends

        # Verify message contents
        calls = mock_websocket.send_json.call_args_list
        assert calls[0][0][0]["content"] == "Starting task..."
        assert calls[1][0][0]["content"] == "Task completed"
        assert calls[2][0][0]["type"] == "complete"

        # Verify cleanup
        mock_websocket.close.assert_called_once()
        mock_redis.close.assert_called_once()


def test_health_endpoint(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_exception_handlers(client):
    """Test exception handlers."""
    # Test general exception handler by causing an SQS error
    with patch("app.api.tasks.aioboto3.Session") as mock_session:
        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock(side_effect=Exception("Test error"))
        mock_session.return_value.client.return_value.__aenter__.return_value = mock_sqs

        response = client.post("/api/tasks/", json={"prompt": "Test"})
        assert response.status_code == 500
        assert "Failed to queue task" in response.json()["detail"]
