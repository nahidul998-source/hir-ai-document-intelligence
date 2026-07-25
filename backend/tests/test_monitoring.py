import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from app.main import app
from app.core.config import settings
from app.infrastructure.database.models import User, AuditLog, Job

# Define a mock current user
mock_user = User(
    id=uuid4(),
    email="admin@example.com",
    is_active=True,
    role_id=uuid4()
)


@pytest.fixture
def override_auth():
    from app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_metrics_endpoint_unauthenticated():
    """Verify metrics endpoint works without auth for scraper scraping."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"{settings.API_V1_STR}/monitoring/metrics")
    assert response.status_code == 200
    assert "hir_http_requests_total" in response.text


@pytest.mark.asyncio
@patch("app.api.routers.monitoring.aioredis.from_url")
@patch("app.api.routers.monitoring.aio_pika.connect")
@patch("app.api.routers.monitoring.asyncio.to_thread")
async def test_health_endpoint(
    mock_to_thread, 
    mock_pika_connect, 
    mock_redis_from_url, 
    override_auth
):
    """Verify health endpoint executes database, redis, rabbitmq and minio connections."""
    # Mock Redis client
    mock_redis = MagicMock()
    mock_redis.ping = AsyncMock()
    mock_redis.get = AsyncMock(return_value=datetime.now(timezone.utc).replace(tzinfo=None).isoformat().encode("utf-8"))
    mock_redis.close = AsyncMock()
    mock_redis_from_url.return_value = mock_redis
    
    # Mock RabbitMQ connection
    mock_conn = MagicMock()
    mock_conn.close = AsyncMock()
    mock_pika_connect.return_value = mock_conn

    # Mock MinIO thread task
    mock_to_thread.return_value = True

    # Mock DB session
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock()
    
    from app.database.session import get_db
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"{settings.API_V1_STR}/monitoring/health")
        
    app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "postgresql" in data["services"]
    assert "redis" in data["services"]
    assert "rabbitmq" in data["services"]
    assert "minio" in data["services"]
    assert "ai_providers" in data["services"]
    assert "workers" in data["services"]


@pytest.mark.asyncio
async def test_audit_logs_endpoint(override_auth):
    """Verify audit logs endpoint returns paginated structured list."""
    # Mock DB session
    mock_db = AsyncMock()
    
    # Mock execute returning empty logs
    mock_execute_result = MagicMock()
    mock_execute_result.scalar = MagicMock(return_value=0)
    mock_execute_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    mock_db.execute = AsyncMock(return_value=mock_execute_result)

    from app.database.session import get_db
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"{settings.API_V1_STR}/monitoring/audit-logs?skip=0&limit=5")
        
    app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "logs" in data
    assert len(data["logs"]) == 0


@pytest.mark.asyncio
async def test_jobs_endpoint(override_auth):
    """Verify jobs monitoring statistics endpoint."""
    mock_db = AsyncMock()
    
    mock_execute_result = MagicMock()
    mock_execute_result.all = MagicMock(return_value=[("completed", 5), ("failed", 1)])
    mock_execute_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    mock_db.execute = AsyncMock(return_value=mock_execute_result)

    from app.database.session import get_db
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"{settings.API_V1_STR}/monitoring/jobs?limit=5")
        
    app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "recent_jobs" in data
    assert data["summary"]["completed"] == 5
    assert data["summary"]["failed"] == 1
    assert data["summary"]["queued"] == 0
