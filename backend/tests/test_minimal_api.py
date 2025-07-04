"""Tests for minimal API implementation."""

import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_create_task_endpoint_exists(client):
    """Test that the create task endpoint exists."""
    response = client.post("/api/tasks/", json={"prompt": "Test prompt"})
    # We expect either 200 or 500 (if SQS is not available)
    assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_create_task_with_mock_sqs():
    """Test task creation with mocked SQS."""
    from app.api.tasks import create_task, TaskRequest
    
    with patch("app.api.tasks.aioboto3.Session") as mock_session:
        # Mock the SQS client
        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock(return_value={"MessageId": "test-message-id"})
        
        # Configure the mock session
        mock_session.return_value.client.return_value.__aenter__.return_value = mock_sqs
        
        # Test the function
        request = TaskRequest(prompt="Test prompt")
        response = await create_task(request)
        
        assert response.status_code == "queued"
        assert len(response.task_id) == 36  # UUID length
        
        # Verify SQS was called
        mock_sqs.send_message.assert_called_once()


def test_websocket_endpoint_exists(client):
    """Test that the WebSocket endpoint exists."""
    # WebSocket endpoints can't be tested with regular TestClient
    # Just verify the route is registered
    routes = [route.path for route in app.routes]
    assert "/ws/{task_id}" in routes


def test_health_endpoint(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"