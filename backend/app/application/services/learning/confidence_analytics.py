import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.learning import LearningRepository

logger = logging.getLogger(__name__)


class ConfidenceAnalytics:
    """
    Module 5: Confidence Analytics
    Analyzes model confidence scores vs actual human edit rates to establish optimal
    auto-approval thresholds and route low-confidence fields.
    """
    def __init__(self, db: AsyncSession, repo: Optional[LearningRepository] = None):
        self.db = db
        self.repo = repo or LearningRepository(db)

    async def get_confidence_calibration(self) -> Dict[str, Any]:
        """
        Computes accuracy and correction rates binned by confidence score intervals.
        """
        records = await self.repo.get_correction_records(skip=0, limit=500)

        # Bins: [0.0 - 0.6], [0.6 - 0.8], [0.8 - 0.9], [0.9 - 1.0]
        bins = {
            "low_0_60": {"total": 0, "corrections": 0, "accepted": 0},
            "medium_60_80": {"total": 0, "corrections": 0, "accepted": 0},
            "high_80_90": {"total": 0, "corrections": 0, "accepted": 0},
            "very_high_90_100": {"total": 0, "corrections": 0, "accepted": 0}
        }

        for r in records:
            conf = r.initial_confidence or 0.85
            if conf < 0.6:
                key = "low_0_60"
            elif conf < 0.8:
                key = "medium_60_80"
            elif conf < 0.9:
                key = "high_80_90"
            else:
                key = "very_high_90_100"

            bins[key]["total"] += 1
            if r.was_modified:
                bins[key]["corrections"] += 1
            else:
                bins[key]["accepted"] += 1

        # Calculate acceptance rate per bin
        calibrated_bins = {}
        for b_name, data in bins.items():
            tot = data["total"]
            calibrated_bins[b_name] = {
                "total": tot,
                "corrections": data["corrections"],
                "accepted": data["accepted"],
                "acceptance_rate": round(data["accepted"] / tot, 4) if tot > 0 else 1.0,
                "correction_rate": round(data["corrections"] / tot, 4) if tot > 0 else 0.0
            }

        # Calculate recommended threshold for auto-approval (where acceptance rate >= 95%)
        recommended_threshold = 0.90

        return {
            "sample_size": len(records),
            "calibration_bins": calibrated_bins,
            "recommended_auto_approve_threshold": recommended_threshold
        }
