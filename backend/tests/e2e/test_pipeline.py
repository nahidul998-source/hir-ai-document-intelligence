import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from app.api.deps import get_current_user, get_document_service
from app.infrastructure.database.models import User

from app.schemas.document import DocumentResponse

mock_user = User(id=uuid4(), email="test@example.com", is_active=True)

test_doc_id = uuid4()
test_proj_id = uuid4()

mock_doc = DocumentResponse(
    id=test_doc_id,
    project_id=test_proj_id,
    filename="tech_pack.pdf",
    file_type="application/pdf",
    minio_key="test_key",
    current_version=1,
    status="uploaded",
    confidence_score=0.95,
    uploader_id=mock_user.id,
    created_at=datetime.now(),
    updated_at=datetime.now()
)

mock_doc_service = MagicMock()
mock_doc_service.upload_document = AsyncMock(return_value=mock_doc)

from app.database.session import get_db
from app.infrastructure.database.models import DocumentVersion
from app.infrastructure.database.models import ReviewSession, ReviewField

mock_version = MagicMock(id=uuid4(), document_id=test_doc_id, version_number=1, minio_key="test_key")

db_sessions = {}
db_fields = {}

async def mock_get_db():
    mock_session = AsyncMock()
    
    def fake_add(obj):
        if not getattr(obj, "id", None):
            setattr(obj, "id", uuid4())
        if isinstance(obj, ReviewSession):
            db_sessions[obj.document_id] = obj
            db_sessions[obj.id] = obj
        elif isinstance(obj, ReviewField):
            db_fields[(obj.session_id, obj.field_name)] = obj

    def fake_execute(stmt):
        mock_res = MagicMock()
        stmt_str = str(stmt).lower()
        if "document_versions" in stmt_str:
            mock_res.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_version)))
        elif "review_sessions" in stmt_str:
            sessions = [v for v in db_sessions.values() if isinstance(v, ReviewSession)]
            mock_res.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=sessions[0] if sessions else None)))
        elif "review_fields" in stmt_str:
            fields = [v for v in db_fields.values() if isinstance(v, ReviewField)]
            mock_res.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=fields), first=MagicMock(return_value=fields[0] if fields else None)))
        else:
            mock_res.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=None), all=MagicMock(return_value=[])))
        return mock_res

    mock_session.add = fake_add
    mock_session.execute = AsyncMock(side_effect=fake_execute)
    yield mock_session

@pytest.fixture(autouse=True)
def override_deps():
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_document_service] = lambda: mock_doc_service
    app.dependency_overrides[get_db] = mock_get_db
    yield
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_document_service, None)
    app.dependency_overrides.pop(get_db, None)

@pytest.mark.asyncio
async def test_end_to_end_pipeline():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Upload Document
        upload_resp = await ac.post(
            "/api/v1/documents/upload/123e4567-e89b-12d3-a456-426614174000",
            files={"file": ("tech_pack.pdf", b"%PDF-1.4 mock pdf data", "application/pdf")}
        )
        assert upload_resp.status_code in (200, 201)
        doc_id = upload_resp.json()["id"]

        # 2. Simulate Worker Extraction Result
        ext_resp = await ac.post(
            f"/api/v1/documents/{doc_id}/extraction",
            json={
                "document_type": "tech_pack",
                "extracted_data": {"style_number": "ST-123", "season": "SS24"},
                "confidence_metadata": {
                    "style_number": {"confidence_score": 0.95, "source_page": 1, "bounding_box": [10, 10, 50, 20]},
                    "season": {"confidence_score": 0.88, "source_page": 1, "bounding_box": [10, 30, 50, 40]}
                }
            }
        )
        assert ext_resp.status_code == 200
        session_id = ext_resp.json()["session_id"]

        # 3. Fetch Review Session
        rev_resp = await ac.get(f"/api/v1/documents/{doc_id}/review")
        assert rev_resp.status_code == 200
        session_data = rev_resp.json()
        assert session_data["status"] == "draft"
        assert "style_number" in session_data["fields"]
        assert len(session_data["highlights"]) == 2

        # 4. Modify Draft Field
        patch_resp = await ac.patch(
            f"/api/v1/documents/{doc_id}/review/fields/style_number",
            json={"session_id": session_id, "edited_value": "ST-123-MOD"}
        )
        assert patch_resp.status_code == 200

        # 5. Approve Document (Triggers ERP Payload Builder)
        appr_resp = await ac.post(
            f"/api/v1/documents/{doc_id}/review/approve",
            json={"session_id": session_id}
        )
        assert appr_resp.status_code == 200
        assert appr_resp.json()["status"] == "document_approved"
