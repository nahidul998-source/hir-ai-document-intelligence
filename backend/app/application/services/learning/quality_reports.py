import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.learning import LearningRepository

logger = logging.getLogger(__name__)


class ExtractionQualityReports:
    """
    Module 7: Extraction Quality Reports
    Generates consolidated quality reports summarizing overall extraction accuracy trends,
    field-by-field quality scores, and model accuracy drift over time.
    """
    def __init__(self, db: AsyncSession, repo: Optional[LearningRepository] = None):
        self.db = db
        self.repo = repo or LearningRepository(db)

    async def generate_quality_report(
        self,
        document_type: Optional[str] = None,
        buyer_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates extraction quality summary report containing overall accuracy, field level accuracy break-downs,
        and fine-tuning dataset readiness metrics.
        """
        records = await self.repo.get_correction_records(
            skip=0,
            limit=500,
            document_type=document_type,
            buyer_code=buyer_code
        )

        total_fields = len(records)
        if total_fields == 0:
            return {
                "overall_accuracy": 1.0,
                "total_extractions_reviewed": 0,
                "total_corrections_made": 0,
                "field_accuracy_breakdown": {},
                "dataset_readiness": {
                    "available_samples": 0,
                    "ready_for_fine_tuning": False
                }
            }

        corrections_count = sum(1 for r in records if r.was_modified)
        overall_accuracy = round((total_fields - corrections_count) / total_fields, 4)

        # Field accuracy breakdown
        field_stats: Dict[str, Dict[str, int]] = {}
        for r in records:
            fname = r.field_name
            if fname not in field_stats:
                field_stats[fname] = {"total": 0, "corrections": 0}
            field_stats[fname]["total"] += 1
            if r.was_modified:
                field_stats[fname]["corrections"] += 1

        field_accuracy = {}
        for fname, stats in field_stats.items():
            tot = stats["total"]
            cor = stats["corrections"]
            field_accuracy[fname] = {
                "total": tot,
                "corrections": cor,
                "accuracy_rate": round((tot - cor) / tot, 4)
            }

        return {
            "overall_accuracy": overall_accuracy,
            "total_extractions_reviewed": total_fields,
            "total_corrections_made": corrections_count,
            "field_accuracy_breakdown": field_accuracy,
            "dataset_readiness": {
                "available_samples": total_fields,
                "ready_for_fine_tuning": total_fields >= 50
            }
        }
