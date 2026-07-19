import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.main import app
from app.core.config import settings
from app.infrastructure.database.models import User, Role

admin_role = Role(
    id=uuid4(),
    name="Admin",
    permissions=["review:read", "review:write"]
)

mock_admin_user = User(
    id=uuid4(),
    email="bi_admin@example.com",
    is_active=True,
    role_id=admin_role.id,
    role=admin_role
)


@pytest.fixture
def override_auth():
    from app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_executive_overview_endpoint(override_auth):
    """Verify BI executive overview KPI endpoint."""
    mock_db = AsyncMock()
    mock_exec_res = MagicMock()
    mock_exec_res.all = MagicMock(return_value=[("completed", 50), ("review_pending", 10)])
    mock_exec_res.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    mock_exec_res.scalar = MagicMock(return_value=0.95)
    mock_db.execute = AsyncMock(return_value=mock_exec_res)

    from app.database.session import get_db
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get(f"{settings.API_V1_STR}/analytics/overview")

    app.dependency_overrides.pop(get_db, None)

    assert res.status_code == 200
    data = res.json()
    assert "total_documents" in data
    assert "ai_accuracy_pct" in data
    assert "erp_success_rate_pct" in data


@pytest.mark.asyncio
async def test_token_usage_endpoint(override_auth):
    """Verify AI provider token and cost breakdown endpoint."""
    mock_db = AsyncMock()
    from app.database.session import get_db
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get(f"{settings.API_V1_STR}/analytics/token-usage")

    app.dependency_overrides.pop(get_db, None)

    assert res.status_code == 200
    data = res.json()
    assert "total_tokens" in data
    assert "total_cost_usd" in data
    assert len(data["providers"]) >= 1


@pytest.mark.asyncio
async def test_export_endpoint(override_auth):
    """Verify CSV and Excel report exports."""
    mock_db = AsyncMock()
    mock_exec_res = MagicMock()
    mock_exec_res.all = MagicMock(return_value=[])
    mock_exec_res.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    mock_exec_res.scalar = MagicMock(return_value=0.95)
    mock_db.execute = AsyncMock(return_value=mock_exec_res)

    from app.database.session import get_db
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res_csv = await ac.get(f"{settings.API_V1_STR}/analytics/export?format=csv")
        res_excel = await ac.get(f"{settings.API_V1_STR}/analytics/export?format=excel")

    app.dependency_overrides.pop(get_db, None)

    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    assert "Metric,Value" in res_csv.text

    assert res_excel.status_code == 200
    assert "vnd.ms-excel" in res_excel.headers["content-type"]
