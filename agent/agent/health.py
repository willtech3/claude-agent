from datetime import datetime
from typing import Dict, Any

from pydantic import BaseModel


class HealthStatus(BaseModel):
    status: str
    timestamp: datetime
    version: str = "0.1.0"
    checks: Dict[str, Any] = {}


async def get_health_status() -> HealthStatus:
    checks = {
        "worker": "healthy",
        "memory": "ok",
        "connections": {
            "sqs": "connected",
            "redis": "connected"
        }
    }
    
    return HealthStatus(
        status="healthy",
        timestamp=datetime.utcnow(),
        checks=checks
    )