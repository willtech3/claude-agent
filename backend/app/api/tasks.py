from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.auth import oauth2_scheme

router = APIRouter()


class Task(BaseModel):
    id: str
    project_id: str
    title: str
    description: str | None = None
    status: str = "pending"
    priority: str = "medium"


@router.get("/", response_model=List[Task])
async def list_tasks(project_id: str, token: str = Depends(oauth2_scheme)):
    # TODO: Implement actual task listing
    return [
        {
            "id": "task-1",
            "project_id": project_id,
            "title": "Sample Task",
            "description": "A sample task",
            "status": "pending",
            "priority": "medium"
        }
    ]


@router.post("/", response_model=Task)
async def create_task(task: Task, token: str = Depends(oauth2_scheme)):
    # TODO: Implement actual task creation
    return task


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str, token: str = Depends(oauth2_scheme)):
    # TODO: Implement actual task retrieval
    return {
        "id": task_id,
        "project_id": "proj-1",
        "title": "Sample Task",
        "description": "A sample task",
        "status": "pending",
        "priority": "medium"
    }