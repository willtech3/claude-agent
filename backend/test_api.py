#!/usr/bin/env python3
"""Test script for the minimal API implementation."""

import asyncio
import json
import httpx
import websockets


async def test_create_task():
    """Test creating a task via the API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/tasks/",
            json={"prompt": "Create a hello world Python script"}
        )
        print(f"Create task response: {response.status_code}")
        print(f"Response body: {response.json()}")
        return response.json()["task_id"]


async def test_websocket(task_id: str):
    """Test WebSocket connection for a task."""
    uri = f"ws://localhost:8000/ws/{task_id}"
    print(f"Connecting to WebSocket: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("WebSocket connected, waiting for messages...")
            
            # Listen for a few messages
            for _ in range(5):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    print(f"Received: {data}")
                    
                    if data.get("type") == "complete":
                        break
                except asyncio.TimeoutError:
                    print("No message received in 5 seconds")
                    break
                    
    except Exception as e:
        print(f"WebSocket error: {e}")


async def main():
    """Run the tests."""
    print("Testing minimal API implementation...")
    
    # Test task creation
    task_id = await test_create_task()
    
    # Test WebSocket
    await test_websocket(task_id)


if __name__ == "__main__":
    asyncio.run(main())