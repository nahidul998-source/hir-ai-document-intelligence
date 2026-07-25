import json
from pydantic import BaseModel
from typing import Optional, Any
from uuid import UUID
from datetime import datetime

from app.infrastructure.repositories.reviews import ReviewRepository
from app.infrastructure.database.models import ReviewSession, ReviewField, FieldCorrection, ReviewHistory
from app.infrastructure.events.publisher import RabbitMQEventPublisher
from app.domain.services.erp.payload_builder import ERPPayloadBuilder

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
    def __init__(self, repo: ReviewRepository, publisher: RabbitMQEventPublisher):
        self.repo = repo
        self.publisher = publisher

    def _parse_field_value(self, val_to_use: Any) -> Any:
        if isinstance(val_to_use, str):
            try:
                return json.loads(val_to_use)
            except json.JSONDecodeError:
                pass
        return val_to_use

    async def get_active_session(self, document_id: UUID):
        session = await self.repo.get_session_by_document(document_id)
        if not session:
            return None
            
        doc_type = await self.repo.get_document_type(document_id)
        fields = await self.repo.get_fields(session.id)
        
        fields_data = {}
        highlights = []
        for f in fields:
            val_to_use = f.edited_value if f.edited_value is not None else f.original_value
            fields_data[f.field_name] = self._parse_field_value(val_to_use)
            
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
        existing = await self.repo.get_session_by_document(cmd.document_id)
        if existing:
            return {"session_id": str(existing.id)}
            
        extraction_id = await self.repo.get_latest_extraction_id(cmd.document_id)
        if not extraction_id:
            raise ValueError("Cannot start review session: Document extraction has not completed yet.")

        session = ReviewSession(
            document_id=cmd.document_id,
            extraction_id=extraction_id,
            status="draft"
        )
        saved = await self.repo.save_session(session)
        return {"session_id": str(saved.id)}

    async def handle_save_draft(self, cmd: SaveDraftFieldCommand):
        field = await self.repo.get_field(cmd.session_id, cmd.field_name)
        if not field:
            raise ValueError("Field not found")

        if cmd.edited_value is None:
            str_value = None
        elif isinstance(cmd.edited_value, (dict, list)):
            str_value = json.dumps(cmd.edited_value)
        else:
            str_value = str(cmd.edited_value)

        correction = FieldCorrection(
            field_id=field.id,
            previous_value=field.edited_value or field.original_value,
            new_value=str_value,
            reviewer_id=cmd.user_id
        )
        await self.repo.log_correction(correction)
        
        field.edited_value = str_value
        await self.repo.save_field(field)
        return {"status": "draft_saved", "field": cmd.field_name}

    async def handle_approve_field(self, cmd: ApproveFieldCommand):
        field = await self.repo.get_field(cmd.session_id, cmd.field_name)
        if not field:
            raise ValueError("Field not found")
        field.validation_status = "valid"
        await self.repo.save_field(field)
        return {"status": "field_approved"}

    async def handle_approve_document(self, cmd: ApproveDocumentCommand):
        session = await self.repo.get_session_by_id(cmd.session_id)
        if not session:
            raise ValueError("Session not found")
        session.status = "approved"
        await self.repo.save_session(session)
        
        fields = await self.repo.get_fields(cmd.session_id)
        approved_data = {}
        for f in fields:
            val_to_use = f.edited_value if f.edited_value is not None else f.original_value
            approved_data[f.field_name] = self._parse_field_value(val_to_use)
        
        doc_type = await self.repo.get_document_type(session.document_id)
        
        erp_payload = ERPPayloadBuilder.build_payload(doc_type, approved_data)
        erp_payload["session_id"] = str(session.id)
        erp_payload["document_id"] = str(session.document_id)
        erp_payload["approved_by"] = str(cmd.user_id)
        
        await self.publisher.publish_event(
            routing_key="document.approved",
            payload=erp_payload
        )
        
        return {"status": "document_approved"}
