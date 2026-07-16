import pytest
from uuid import uuid4
from app.application.commands.review_commands import (
    ReviewCommandHandler, SaveDraftFieldCommand, ApproveDocumentCommand
)

@pytest.mark.asyncio
async def test_save_draft_field():
    handler = ReviewCommandHandler()
    cmd = SaveDraftFieldCommand(
        session_id=uuid4(),
        field_name="style_number",
        edited_value="FW24-002",
        user_id=uuid4()
    )
    result = await handler.handle_save_draft(cmd)
    
    assert result["status"] == "draft_saved"
    assert result["field"] == "style_number"

@pytest.mark.asyncio
async def test_approve_document():
    handler = ReviewCommandHandler()
    cmd = ApproveDocumentCommand(
        session_id=uuid4(),
        user_id=uuid4()
    )
    result = await handler.handle_approve_document(cmd)
    
    assert result["status"] == "document_approved"
