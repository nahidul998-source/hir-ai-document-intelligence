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
            
        # Get document to get its type
        from sqlalchemy.future import select
        from app.infrastructure.database.models import Document
        doc = None
        if hasattr(self.repo, "db") and self.repo.db:
            stmt = select(Document).where(Document.id == document_id)
            res = await self.repo.db.execute(stmt)
            doc = res.scalars().first()
        doc_type = getattr(doc, "document_type", "tech_pack") if doc else "tech_pack"
        
        fields = await self.repo.get_fields(session.id)
        
        fields_data = {}
        highlights = []
        for f in fields:
            fields_data[f.field_name] = f.edited_value or f.original_value
            if f.bounding_box and isinstance(f.bounding_box, list) and len(f.bounding_box) == 4:
                highlights.append({
                    "id": str(f.id),
                    "field_name": f.field_name,
                    "page": f.source_page or 1,
                    "x": f.bounding_box[0],
                    "y": f.bounding_box[1],
                    "width": f.bounding_box[2] - f.bounding_box[0],
                    "height": f.bounding_box[3] - f.bounding_box[1]
                })
        
        return {
            "session_id": str(session.id),
            "status": session.status,
            "document_type": doc_type,
            "fields": fields_data,
            "highlights": highlights
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
        
        # Get fields to construct payload
        fields = await self.repo.get_fields(cmd.session_id)
        approved_data = {
            f.field_name: f.edited_value or f.original_value 
            for f in fields
        }
        
        # Event dispatch via ERPPayloadBuilder
        from app.domain.services.erp.payload_builder import ERPPayloadBuilder
        
        # Get document type for builder
        from sqlalchemy.future import select
        from app.infrastructure.database.models import Document
        doc = None
        if hasattr(self.repo, "db") and self.repo.db:
            stmt = select(Document).where(Document.id == session.document_id)
            res = await self.repo.db.execute(stmt)
            doc = res.scalars().first()
        doc_type = getattr(doc, "document_type", "tech_pack") if doc else "tech_pack"
        
        erp_payload = ERPPayloadBuilder.build_payload(doc_type, approved_data)
        erp_payload["session_id"] = str(session.id)
        erp_payload["document_id"] = str(session.document_id)
        erp_payload["approved_by"] = str(cmd.user_id)
        
        from app.infrastructure.events.publisher import RabbitMQEventPublisher
        publisher = RabbitMQEventPublisher()
        await publisher.publish_event(
            routing_key="document.approved",
            payload=erp_payload
        )
        
        return {"status": "document_approved"}
