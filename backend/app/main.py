import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.api import auth, projects, tasks, providers, git_providers
from app.core.config import settings
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup
    await init_db()
    yield
    # Shutdown


app = FastAPI(
    title="Claude Agent API",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(providers.router, prefix="/api/providers", tags=["providers"])
app.include_router(git_providers.router, prefix="/api/git-providers", tags=["git-providers"])


@app.get("/")
async def root():
    return {"message": "Claude Agent API", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development")
    }


# Lambda handler
lambda_handler = Mangum(app)