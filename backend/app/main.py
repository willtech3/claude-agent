import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum

from app.api import auth, git_providers, projects, providers, tasks, websocket
from app.core.config import settings
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup
    await init_db()
    yield
    # Shutdown


app = FastAPI(title="Claude Agent API", version="0.1.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
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
app.include_router(websocket.router, tags=["websocket"])


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/")
async def root():
    return {"message": "Claude Agent API", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "healthy", "environment": os.getenv("ENVIRONMENT", "development")}


# Lambda handler
lambda_handler = Mangum(app)
