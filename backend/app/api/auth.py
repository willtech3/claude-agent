from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    username: str
    email: str
    full_name: str | None = None


@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # TODO: Implement actual authentication
    return {
        "access_token": "fake-jwt-token",
        "token_type": "bearer"
    }


@router.get("/me", response_model=User)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # TODO: Implement actual user retrieval
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User"
    }