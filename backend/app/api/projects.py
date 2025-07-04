from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.auth import oauth2_scheme

router = APIRouter()


class Project(BaseModel):
    id: str
    name: str
    description: str | None = None
    provider: str
    status: str = "active"


@router.get("/", response_model=List[Project])
async def list_projects(token: str = Depends(oauth2_scheme)):
    # TODO: Implement actual project listing
    return [
        {
            "id": "proj-1",
            "name": "Sample Project",
            "description": "A sample project",
            "provider": "claude",
            "status": "active"
        }
    ]


@router.post("/", response_model=Project)
async def create_project(project: Project, token: str = Depends(oauth2_scheme)):
    # TODO: Implement actual project creation
    return project


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str, token: str = Depends(oauth2_scheme)):
    # TODO: Implement actual project retrieval
    return {
        "id": project_id,
        "name": "Sample Project",
        "description": "A sample project",
        "provider": "claude",
        "status": "active"
    }