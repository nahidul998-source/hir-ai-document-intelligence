from pydantic import BaseModel
from typing import Optional, Any
from uuid import UUID
from datetime import datetime
from app.infrastructure.repositories.reviews import ReviewRepository
from app.infrastructure.database.models_phase3 import ReviewSession, ReviewField, FieldCorrection, ReviewHistory

class StartReviewCommand(BaseModel):
    document_id: UUID
    user_id: UUID

class SaveDraftFieldCommand(BaseModel):
    session_id: UUID
    field_name: str
    edited_value: Any
    user_id: UUID

class ApproveFieldCommand(BaseModel):
    session_id: UUID
    field_name: str
    user_id: UUID

class ApproveDocumentCommand(BaseModel):
    session_id: UUID
    user_id: UUID

class ReviewCommandHandler:
    def __init__(self, repo: ReviewRepository):
        self.repo = repo

    async def get_active_session(self, document_id: UUID):
        session = await self.repo.get_session_by_document(document_id)
        if not session:
            return None
        return {
            "session_id": str(session.id),
            "status": session.status,
        }

    async def handle_start_review(self, cmd: StartReviewCommand):
        # Prevent starting if already exists
        existing = await self.repo.get_session_by_document(cmd.document_id)
        if existing:
            return {"session_id": str(existing.id)}
            
        session = ReviewSession(
            document_id=cmd.document_id,
            extraction_id=cmd.document_id, # Mocking extraction link for now
            status="draft"
        )
        saved = await self.repo.save_session(session)
        return {"session_id": str(saved.id)}

    async def handle_save_draft(self, cmd: SaveDraftFieldCommand):
        field = await self.repo.get_field(cmd.session_id, cmd.field_name)
        if not field:
            raise ValueError("Field not found")

        # Create correction log
        correction = FieldCorrection(
            field_id=field.id,
            previous_value=field.edited_value or field.original_value,
            new_value=cmd.edited_value,
            reviewer_id=cmd.user_id
        )
        await self.repo.log_correction(correction)
        
        field.edited_value = cmd.edited_value
        await self.repo.save_field(field)
        return {"status": "draft_saved", "field": cmd.field_name}

    async def handle_approve_field(self, cmd: ApproveFieldCommand):
        field = await self.repo.get_field(cmd.session_id, cmd.field_name)
        field.validation_status = "valid"
        await self.repo.save_field(field)
        return {"status": "field_approved"}

    async def handle_approve_document(self, cmd: ApproveDocumentCommand):
        session = await self.repo.get_session_by_id(cmd.session_id)
        session.status = "approved"
        await self.repo.save_session(session)
        # Event dispatch handled externally
        return {"status": "document_approved"}
