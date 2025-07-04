import json
import uuid

import aioboto3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings

router = APIRouter()


class TaskRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="The prompt for the task")


class TaskResponse(BaseModel):
    task_id: str
    status: str


@router.post("/", response_model=TaskResponse)
async def create_task(request: TaskRequest) -> TaskResponse:
    """Create a new task and send it to SQS queue."""
    # Generate task ID
    task_id = str(uuid.uuid4())

    # Prepare SQS message
    message = {"task_id": task_id, "prompt": request.prompt}

    try:
        # Create SQS client
        session = aioboto3.Session()
        async with session.client(
            "sqs", region_name=settings.AWS_REGION, endpoint_url=settings.AWS_ENDPOINT_URL
        ) as sqs:
            # Send message to SQS
            await sqs.send_message(
                QueueUrl=settings.TASK_QUEUE_URL, MessageBody=json.dumps(message)
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {e!s}") from e

    return TaskResponse(task_id=task_id, status="queued")
