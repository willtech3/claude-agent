import json

import redis.asyncio as redis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import settings

router = APIRouter()

# Store active WebSocket connections
active_connections: dict[str, WebSocket] = {}


@router.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for streaming task results."""
    await websocket.accept()
    active_connections[task_id] = websocket

    # Create Redis client
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = redis_client.pubsub()

    try:
        # Subscribe to task channel
        await pubsub.subscribe(f"task:{task_id}")

        # Listen for messages
        async for message in pubsub.listen():
            if message["type"] == "message":
                # Parse and send message to client
                try:
                    data = json.loads(message["data"])
                    await websocket.send_json(data)

                    # Check if task is complete
                    if data.get("type") == "complete":
                        break
                except json.JSONDecodeError:
                    # Send raw message if not JSON
                    await websocket.send_json({"type": "output", "content": message["data"]})

    except WebSocketDisconnect:
        # Client disconnected
        pass
    except Exception as e:
        # Send error message
        await websocket.send_json({"type": "error", "content": str(e)})
    finally:
        # Cleanup
        active_connections.pop(task_id, None)
        await pubsub.unsubscribe(f"task:{task_id}")
        await pubsub.close()
        await redis_client.close()
        await websocket.close()
