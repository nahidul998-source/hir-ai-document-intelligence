import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.main import app
from app.core.config import settings
from app.infrastructure.database.models import User, Role
from app.infrastructure.database.models_phase8 import FeatureFlag, Tenant, SystemConfig

admin_role = Role(
    id=uuid4(),
    name="Admin",
    permissions=["admin:read", "admin:write"]
)

# Mock admin user fixture
mock_admin_user = User(
    id=uuid4(),
    email="superadmin@example.com",
    is_active=True,
    role_id=admin_role.id,
    role=admin_role
)


@pytest.fixture
def override_admin_auth():
    from app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_list_admin_users(override_admin_auth):
    """Verify admin user listing endpoint."""
    mock_db = AsyncMock()
    mock_exec_res = MagicMock()
    mock_exec_res.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_admin_user])))
    mock_db.execute = AsyncMock(return_value=mock_exec_res)

    from app.database.session import get_db
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get(f"{settings.API_V1_STR}/admin/users")

    app.dependency_overrides.pop(get_db, None)

    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["email"] == "superadmin@example.com"


@pytest.mark.asyncio
async def test_feature_flags_endpoint(override_admin_auth):
    """Verify feature flags management endpoint."""
    mock_db = AsyncMock()
    flag = FeatureFlag(id=uuid4(), key="enable_rag_context", is_enabled=True, description="RAG search feature")

    mock_exec_res = MagicMock()
    mock_exec_res.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[flag])))
    mock_db.execute = AsyncMock(return_value=mock_exec_res)

    from app.database.session import get_db
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get(f"{settings.API_V1_STR}/admin/feature-flags")

    app.dependency_overrides.pop(get_db, None)

    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["key"] == "enable_rag_context"
    assert data[0]["is_enabled"] == True


@pytest.mark.asyncio
async def test_create_tenant_endpoint(override_admin_auth):
    """Verify tenant creation endpoint."""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()
    mock_db.commit = AsyncMock()

    from app.database.session import get_db
    app.dependency_overrides[get_db] = lambda: mock_db

    payload = {
        "name": "Acme Garment Factory",
        "code": "ACME_001",
        "max_users": 100,
        "storage_quota_gb": 500.0
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(f"{settings.API_V1_STR}/admin/tenants", json=payload)

    app.dependency_overrides.pop(get_db, None)

    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Acme Garment Factory"
    assert data["code"] == "ACME_001"
