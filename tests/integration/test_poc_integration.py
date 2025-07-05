"""Integration tests for Claude Agent POC."""
import pytest
import requests
import json
import time
import os
from typing import Dict, Any
import websocket
import threading
import queue


BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
WS_URL = os.getenv("WS_URL", "ws://localhost:8000")


class WebSocketClient:
    """Simple WebSocket client for testing."""
    
    def __init__(self, url: str):
        self.url = url
        self.messages = queue.Queue()
        self.ws = None
        self.thread = None
        
    def connect(self, task_id: str):
        """Connect to WebSocket for a specific task."""
        def on_message(ws, message):
            self.messages.put(json.loads(message))
            
        def on_error(ws, error):
            print(f"WebSocket error: {error}")
            
        def run():
            self.ws = websocket.WebSocketApp(
                f"{self.url}/ws/{task_id}",
                on_message=on_message,
                on_error=on_error
            )
            self.ws.run_forever()
            
        self.thread = threading.Thread(target=run)
        self.thread.daemon = True
        self.thread.start()
        time.sleep(1)  # Give it time to connect
        
    def get_messages(self, timeout: int = 30) -> list:
        """Get all messages received within timeout."""
        messages = []
        end_time = time.time() + timeout
        
        while time.time() < end_time:
            try:
                msg = self.messages.get(timeout=1)
                messages.append(msg)
                if msg.get("type") == "complete":
                    break
            except queue.Empty:
                continue
                
        return messages
        
    def close(self):
        """Close WebSocket connection."""
        if self.ws:
            self.ws.close()


@pytest.fixture
def api_client():
    """Create an API client for tests."""
    session = requests.Session()
    # Add any auth headers if needed
    return session


def wait_for_api(max_attempts: int = 10):
    """Wait for API to be available."""
    for i in range(max_attempts):
        try:
            response = requests.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(2)
    return False


@pytest.fixture(scope="session", autouse=True)
def ensure_services_running():
    """Ensure all services are running before tests."""
    if not wait_for_api():
        pytest.skip("API service is not running. Run './scripts/start-poc.sh' first.")


class TestBasicIntegration:
    """Basic integration tests."""
    
    def test_health_endpoint(self, api_client):
        """Test health endpoint is accessible."""
        response = api_client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        
    def test_create_simple_task(self, api_client):
        """Test creating a simple hello world task."""
        # Create task
        task_data = {
            "prompt": "Create a Python hello world script",
            "context": {}
        }
        
        response = api_client.post(f"{BASE_URL}/api/tasks", json=task_data)
        assert response.status_code in [200, 201]
        
        task = response.json()
        assert "id" in task
        assert task["status"] in ["pending", "queued"]
        
        # Connect to WebSocket for real-time updates
        ws_client = WebSocketClient(WS_URL)
        ws_client.connect(task["id"])
        
        # Wait for task completion
        messages = ws_client.get_messages(timeout=60)
        ws_client.close()
        
        # Verify we got output
        assert len(messages) > 0
        
        # Check for completion
        complete_msgs = [m for m in messages if m.get("type") == "complete"]
        assert len(complete_msgs) > 0
        
        # Verify workspace has the file
        workspace_path = f"workspaces/{task['id']}"
        if os.path.exists(workspace_path):
            files = os.listdir(workspace_path)
            python_files = [f for f in files if f.endswith(".py")]
            assert len(python_files) > 0
            
    def test_multi_file_task(self, api_client):
        """Test creating a task that generates multiple files."""
        task_data = {
            "prompt": "Create a Flask API with two endpoints: /hello and /status",
            "context": {}
        }
        
        response = api_client.post(f"{BASE_URL}/api/tasks", json=task_data)
        assert response.status_code in [200, 201]
        
        task = response.json()
        task_id = task["id"]
        
        # Connect to WebSocket
        ws_client = WebSocketClient(WS_URL)
        ws_client.connect(task_id)
        
        # Wait for completion
        messages = ws_client.get_messages(timeout=90)
        ws_client.close()
        
        # Verify completion
        complete_msgs = [m for m in messages if m.get("type") == "complete"]
        assert len(complete_msgs) > 0
        
        # Check workspace for multiple files
        workspace_path = f"workspaces/{task_id}"
        if os.path.exists(workspace_path):
            files = os.listdir(workspace_path)
            # Should have at least app.py and requirements.txt
            assert any("app" in f and f.endswith(".py") for f in files)
            assert any("requirements" in f for f in files)
            
    def test_error_handling(self, api_client):
        """Test error handling for invalid input."""
        # Test empty prompt
        response = api_client.post(f"{BASE_URL}/api/tasks", json={"prompt": ""})
        assert response.status_code == 422  # Validation error
        
        # Test missing prompt
        response = api_client.post(f"{BASE_URL}/api/tasks", json={})
        assert response.status_code == 422
        
    def test_task_status_endpoint(self, api_client):
        """Test task status endpoint."""
        # Create a task
        task_data = {"prompt": "Write a simple function", "context": {}}
        response = api_client.post(f"{BASE_URL}/api/tasks", json=task_data)
        task = response.json()
        task_id = task["id"]
        
        # Check status endpoint
        response = api_client.get(f"{BASE_URL}/api/tasks/{task_id}")
        assert response.status_code == 200
        
        status_data = response.json()
        assert status_data["id"] == task_id
        assert "status" in status_data
        assert "created_at" in status_data


class TestLongRunningTasks:
    """Tests for long-running tasks."""
    
    def test_streaming_updates(self, api_client):
        """Test that updates stream properly for long tasks."""
        task_data = {
            "prompt": "Create a complete TODO application with React, including components, state management, and styling",
            "context": {}
        }
        
        response = api_client.post(f"{BASE_URL}/api/tasks", json=task_data)
        task = response.json()
        
        ws_client = WebSocketClient(WS_URL)
        ws_client.connect(task["id"])
        
        # Collect messages for up to 2 minutes
        messages = ws_client.get_messages(timeout=120)
        ws_client.close()
        
        # Should have multiple output messages
        output_msgs = [m for m in messages if m.get("type") == "output"]
        assert len(output_msgs) > 5  # Should stream multiple updates
        
        # Verify no timeout occurred
        error_msgs = [m for m in messages if m.get("type") == "error"]
        timeout_errors = [m for m in error_msgs if "timeout" in str(m).lower()]
        assert len(timeout_errors) == 0


class TestConcurrentTasks:
    """Test handling of concurrent tasks."""
    
    def test_queue_multiple_tasks(self, api_client):
        """Test that multiple tasks are queued properly."""
        task_ids = []
        
        # Submit 3 tasks rapidly
        for i in range(3):
            task_data = {
                "prompt": f"Create a Python script that prints 'Task {i}'",
                "context": {}
            }
            response = api_client.post(f"{BASE_URL}/api/tasks", json=task_data)
            assert response.status_code in [200, 201]
            task_ids.append(response.json()["id"])
            
        # Check that all tasks are created
        for task_id in task_ids:
            response = api_client.get(f"{BASE_URL}/api/tasks/{task_id}")
            assert response.status_code == 200
            
        # Wait a bit for processing
        time.sleep(5)
        
        # At least one should be processing or completed
        statuses = []
        for task_id in task_ids:
            response = api_client.get(f"{BASE_URL}/api/tasks/{task_id}")
            statuses.append(response.json()["status"])
            
        # Should have different statuses showing queue behavior
        assert not all(status == "pending" for status in statuses)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])