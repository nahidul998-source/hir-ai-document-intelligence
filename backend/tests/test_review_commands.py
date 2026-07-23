import pytest
from uuid import uuid4
from app.application.commands.review_commands import (
    ReviewCommandHandler, SaveDraftFieldCommand, ApproveDocumentCommand
)
from app.infrastructure.database.models_phase3 import ReviewSession, ReviewField

class MockReviewRepository:
    def __init__(self):
        self.sessions = {}
        self.fields = {}
        self.corrections = []

    async def get_session_by_document(self, document_id):
        return self.sessions.get(document_id)

    async def get_session_by_id(self, session_id):
        for s in self.sessions.values():
            if s.id == session_id:
                return s
        return None

    async def save_session(self, session):
        if not hasattr(session, "id") or session.id is None:
            session.id = uuid4()
        self.sessions[session.document_id] = session
        return session

    async def get_fields(self, session_id):
        return [f for (s_id, f_name), f in self.fields.items() if s_id == session_id]

    async def get_field(self, session_id, field_name):
        return self.fields.get((session_id, field_name))

    async def save_field(self, field):
        if not hasattr(field, "id") or field.id is None:
            field.id = uuid4()
        self.fields[(field.session_id, field.field_name)] = field
        return field

    async def log_correction(self, correction):
        self.corrections.append(correction)
        return correction

@pytest.mark.asyncio
async def test_save_draft_field():
    repo = MockReviewRepository()
    session_id = uuid4()
    field = ReviewField(
        session_id=session_id,
        field_name="style_number",
        original_value="FW24-001",
        edited_value=None,
        confidence=0.9
    )
    await repo.save_field(field)

    handler = ReviewCommandHandler(repo)
    cmd = SaveDraftFieldCommand(
        session_id=session_id,
        field_name="style_number",
        edited_value="FW24-002",
        user_id=uuid4()
    )
    result = await handler.handle_save_draft(cmd)
    
    assert result["status"] == "draft_saved"
    assert result["field"] == "style_number"
    assert field.edited_value == "FW24-002"

@pytest.mark.asyncio
async def test_approve_document():
    repo = MockReviewRepository()
    session = ReviewSession(
        document_id=uuid4(),
        extraction_id=uuid4(),
        status="draft"
    )
    await repo.save_session(session)

    handler = ReviewCommandHandler(repo)
    cmd = ApproveDocumentCommand(
        session_id=session.id,
        user_id=uuid4()
    )
    result = await handler.handle_approve_document(cmd)
    
    assert result["status"] == "document_approved"
    assert session.status == "approved"

