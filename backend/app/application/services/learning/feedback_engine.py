import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models_phase7 import AIFeedbackMetric
from app.infrastructure.repositories.learning import LearningRepository

logger = logging.getLogger(__name__)


class AIFeedbackEngine:
    """
    Module 4: AI Feedback Engine
    Evaluates discrepancy patterns between model extractions and human corrections,
    categorizing error root causes and computing field-level accuracy feedback.
    """
    def __init__(self, db: AsyncSession, repo: Optional[LearningRepository] = None):
        self.db = db
        self.repo = repo or LearningRepository(db)

    async def compute_field_feedback(self, field_name: str) -> Dict[str, Any]:
        """
        Calculates field error distribution, accuracy metrics, and error root causes.
        """
        records = await self.repo.get_correction_records(skip=0, limit=200, field_name=field_name)
        total = len(records)

        if total == 0:
            return {
                "field_name": field_name,
                "total_extractions": 0,
                "total_corrections": 0,
                "accuracy_rate": 1.0,
                "error_pattern_distribution": {}
            }

        corrections = [r for r in records if r.was_modified]
        total_corrections = len(corrections)
        accuracy = round((total - total_corrections) / total, 4)

        # Categorize error patterns
        patterns: Dict[str, int] = {
            "format_mismatch": 0,
            "ocr_misread": 0,
            "missing_field": 0,
            "incorrect_mapping": 0
        }

        for c in corrections:
            orig = (c.original_extracted_value or "").strip()
            corr = (c.corrected_value or "").strip()

            if not orig and corr:
                patterns["missing_field"] += 1
            elif orig.replace("-", "").replace("/", "") == corr.replace("-", "").replace("/", ""):
                patterns["format_mismatch"] += 1
            elif len(orig) == len(corr) and orig != corr:
                patterns["ocr_misread"] += 1
            else:
                patterns["incorrect_mapping"] += 1

        # Store metric
        metric = AIFeedbackMetric(
            time_bucket=datetime.utcnow(),
            field_name=field_name,
            total_extractions=total,
            total_corrections=total_corrections,
            accuracy_rate=accuracy,
            avg_confidence=round(sum(r.initial_confidence or 0.8 for r in records) / total, 2),
            error_pattern_distribution=patterns
        )
        await self.repo.save_feedback_metric(metric)
        await self.db.commit()

        return {
            "field_name": field_name,
            "total_extractions": total,
            "total_corrections": total_corrections,
            "accuracy_rate": accuracy,
            "error_pattern_distribution": patterns
        }
