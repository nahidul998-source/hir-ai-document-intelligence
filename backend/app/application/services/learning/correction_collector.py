import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.database.models import ReviewSession, ReviewField, FieldCorrection
from app.infrastructure.database.models import LearningCorrectionRecord
from app.infrastructure.repositories.learning import LearningRepository

logger = logging.getLogger(__name__)


class CorrectionCollector:
    """
    Module 1: Correction Collector
    Captures human edits and confirmed extractions when a review session is completed/approved,
    converting them into reusable structured learning records.
    """
    def __init__(self, db: AsyncSession, repo: Optional[LearningRepository] = None):
        self.db = db
        self.repo = repo or LearningRepository(db)

    async def collect_from_approved_session(self, session_id: uuid.UUID, reviewer_id: uuid.UUID) -> List[LearningCorrectionRecord]:
        """
        Extracts all fields from an approved review session and persists learning correction records.
        """
        # Fetch review session with fields
        query = select(ReviewField).where(ReviewField.session_id == session_id)
        result = await self.db.execute(query)
        fields = list(result.scalars().all())

        if not fields:
            logger.warning(f"No review fields found for session {session_id} during correction collection.")
            return []

        # Fetch session metadata to get document_id
        session_query = select(ReviewSession).where(ReviewSession.id == session_id)
        session_res = await self.db.execute(session_query)
        session = session_res.scalar_one_or_none()
        document_id = session.document_id if session else session_id

        collected_records: List[LearningCorrectionRecord] = []

        for f in fields:
            orig = f.original_value
            final_val = f.edited_value if f.edited_value is not None else f.original_value
            was_modified = f.edited_value is not None and f.edited_value != f.original_value

            record = LearningCorrectionRecord(
                document_id=document_id,
                session_id=session_id,
                field_id=f.id,
                reviewer_id=reviewer_id,
                document_type="purchase_order",  # Configurable or derived from document
                buyer_code=None,  # Populated from session/document metadata
                field_name=f.field_name,
                original_extracted_value=orig,
                corrected_value=final_val,
                was_modified=was_modified,
                initial_confidence=f.confidence or 0.85,
                source_page=f.source_page or 1,
                bounding_box=f.bounding_box,
                ocr_context_snippet=f"Snippet around field '{f.field_name}' in document page {f.source_page or 1}",
                ai_provider=f.provider or "primary_llm",
                prompt_version="v1.0"
            )
            saved_record = await self.repo.save_correction_record(record)
            collected_records.append(saved_record)

        await self.db.commit()
        logger.info(f"Collected {len(collected_records)} learning correction records from session {session_id}")
        return collected_records
