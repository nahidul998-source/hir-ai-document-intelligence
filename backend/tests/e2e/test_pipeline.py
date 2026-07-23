import pytest
import asyncio
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_end_to_end_pipeline():
    async with AsyncClient(app=app, base_url="http://test") as ac:
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
