import pytest
from httpx import AsyncClient
from agent.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health endpoint returns healthy status"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "services" in data
        assert data["services"]["redis"]["status"] in ["healthy", "unhealthy"]
        assert data["services"]["sqs"]["status"] in ["healthy", "unhealthy"]


@pytest.mark.asyncio
async def test_metrics_endpoint():
    """Test metrics endpoint returns prometheus metrics"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/metrics")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"
        content = response.text
        # Check for standard prometheus metrics
        assert "# HELP" in content
        assert "# TYPE" in content