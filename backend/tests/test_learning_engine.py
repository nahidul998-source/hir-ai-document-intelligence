import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from app.main import app
from app.core.config import settings
from app.infrastructure.database.models import User
from app.infrastructure.database.models import (
    LearningCorrectionRecord,
    LearningDataset,
    LearningDatasetItem,
    PromptOptimizationRecord
)

# Mock user fixture
mock_user = User(
    id=uuid4(),
    email="learning_admin@example.com",
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
async def test_list_correction_records_endpoint(override_auth):
    """Verify listing learning correction records."""
    mock_db = AsyncMock()

    # Mock DB query results
    rec = LearningCorrectionRecord(
        id=uuid4(),
        document_id=uuid4(),
        session_id=uuid4(),
        field_id=uuid4(),
        reviewer_id=mock_user.id,
        field_name="total_amount",
        original_extracted_value="$1000",
        corrected_value="$1200",
        was_modified=True,
        initial_confidence=0.88,
        created_at=datetime.now(timezone.utc)
    )

    mock_exec_res = MagicMock()
    mock_exec_res.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[rec])))
    mock_exec_res.scalar = MagicMock(return_value=1)
    mock_db.execute = AsyncMock(return_value=mock_exec_res)

    from app.database.session import get_db
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get(f"{settings.API_V1_STR}/learning/corrections?skip=0&limit=10")

    app.dependency_overrides.pop(get_db, None)

    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "records" in data
    assert data["total"] == 1
    assert data["records"][0]["field_name"] == "total_amount"


@pytest.mark.asyncio
async def test_confidence_analytics_endpoint(override_auth):
    """Verify confidence analytics endpoint returns calibration bins."""
    mock_db = AsyncMock()
    mock_exec_res = MagicMock()
    mock_exec_res.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    mock_db.execute = AsyncMock(return_value=mock_exec_res)

    from app.database.session import get_db
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get(f"{settings.API_V1_STR}/learning/analytics/confidence")

    app.dependency_overrides.pop(get_db, None)

    assert res.status_code == 200
    data = res.json()
    assert "calibration_bins" in data
    assert "recommended_auto_approve_threshold" in data


@pytest.mark.asyncio
async def test_quality_report_endpoint(override_auth):
    """Verify extraction quality report endpoint."""
    mock_db = AsyncMock()
    mock_exec_res = MagicMock()
    mock_exec_res.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    mock_db.execute = AsyncMock(return_value=mock_exec_res)

    from app.database.session import get_db
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get(f"{settings.API_V1_STR}/learning/reports/quality")

    app.dependency_overrides.pop(get_db, None)

    assert res.status_code == 200
    data = res.json()
    assert "overall_accuracy" in data
    assert "dataset_readiness" in data
