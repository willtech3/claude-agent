import json
import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "postgresql://claude:claude_dev_password@localhost:5432/claude_agent"
    REDIS_URL: str = "redis://localhost:6379"
    AWS_ENDPOINT_URL: str | None = None
    JWT_SECRET_KEY: str = "dev-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        origins_str = os.getenv("ALLOWED_ORIGINS", '["http://localhost:3000"]')
        try:
            return json.loads(origins_str)
        except json.JSONDecodeError:
            return ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()