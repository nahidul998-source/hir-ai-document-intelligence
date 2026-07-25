from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import Optional, List
from app.infrastructure.database.models import ReviewSession, ReviewField, FieldCorrection

class ReviewRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_session_by_document(self, document_id: UUID) -> Optional[ReviewSession]:
        stmt = select(ReviewSession).where(ReviewSession.document_id == document_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
        
    async def get_session_by_id(self, session_id: UUID) -> Optional[ReviewSession]:
        stmt = select(ReviewSession).where(ReviewSession.id == session_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def save_session(self, session: ReviewSession) -> ReviewSession:
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session
        
    async def get_fields(self, session_id: UUID) -> List[ReviewField]:
        stmt = select(ReviewField).where(ReviewField.session_id == session_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
        
    async def get_field(self, session_id: UUID, field_name: str) -> Optional[ReviewField]:
        stmt = select(ReviewField).where(
            ReviewField.session_id == session_id,
            ReviewField.field_name == field_name
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def save_field(self, field: ReviewField) -> ReviewField:
        self.db.add(field)
        await self.db.commit()
        await self.db.refresh(field)
        return field

    async def log_correction(self, correction: FieldCorrection) -> FieldCorrection:
        self.db.add(correction)
        await self.db.commit()
        return correction

    async def get_document_type(self, document_id: UUID) -> str:
        from app.infrastructure.database.models import Document
        stmt = select(Document).where(Document.id == document_id)
        res = await self.db.execute(stmt)
        doc = res.scalars().first()
        return getattr(doc, "document_type", "tech_pack") if doc and getattr(doc, "document_type", None) else "tech_pack"

    async def get_latest_extraction_id(self, document_id: UUID) -> Optional[UUID]:
        from app.infrastructure.database.models import DocumentExtraction
        stmt = select(DocumentExtraction).where(
            DocumentExtraction.document_id == document_id
        ).order_by(DocumentExtraction.created_at.desc())
        res = await self.db.execute(stmt)
        extraction = res.scalars().first()
        return getattr(extraction, "id", None) if extraction else None
