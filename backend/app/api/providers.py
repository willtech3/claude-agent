
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.auth import oauth2_scheme

router = APIRouter()


class Provider(BaseModel):
    id: str
    name: str
    type: str
    status: str = "active"
    capabilities: list[str] = []


@router.get("/", response_model=list[Provider])
async def list_providers(token: str = Depends(oauth2_scheme)):
    # TODO: Implement actual provider listing
    return [
        {
            "id": "claude",
            "name": "Claude",
            "type": "ai",
            "status": "active",
            "capabilities": ["code", "analysis", "conversation"]
        },
        {
            "id": "openai",
            "name": "OpenAI",
            "type": "ai",
            "status": "active",
            "capabilities": ["code", "analysis", "conversation"]
        }
    ]


@router.get("/{provider_id}", response_model=Provider)
async def get_provider(provider_id: str, token: str = Depends(oauth2_scheme)):
    # TODO: Implement actual provider retrieval
    return {
        "id": provider_id,
        "name": "Claude",
        "type": "ai",
        "status": "active",
        "capabilities": ["code", "analysis", "conversation"]
    }
