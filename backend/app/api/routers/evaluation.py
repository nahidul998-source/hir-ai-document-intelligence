from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.api.deps import get_db, get_current_user
from app.infrastructure.database.models import User, Document
from app.infrastructure.database.models_phase3 import ReviewField

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])

@router.get("/metrics")
async def get_evaluation_metrics(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns AI vs Human agreement metrics, hallucination proxy (rejections),
    and average review time.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Analyze ReviewFields to determine agreement
    query = select(ReviewField.status, func.count(ReviewField.id)).where(
        ReviewField.created_at >= cutoff
    ).group_by(ReviewField.status)
    
    res = await db.execute(query)
    field_counts = {row[0]: row[1] for row in res.all()}
    
    total_fields = sum(field_counts.values())
    approved_count = field_counts.get("approved", 0)
    edited_count = field_counts.get("edited", 0)
    rejected_count = field_counts.get("rejected", 0)
    
    ai_human_agreement = (approved_count / total_fields) * 100 if total_fields > 0 else 0
    hallucination_rate = (rejected_count / total_fields) * 100 if total_fields > 0 else 0
    correction_rate = (edited_count / total_fields) * 100 if total_fields > 0 else 0
    
    # Average Review Time (Time from document created to approved)
    # Simple proxy: if document is approved, updated_at - created_at
    doc_query = select(
        func.avg(func.extract('epoch', Document.updated_at - Document.created_at))
    ).where(Document.status == 'approved', Document.created_at >= cutoff)
    
    doc_res = await db.execute(doc_query)
    avg_review_seconds = doc_res.scalar() or 0
    
    return {
        "timeframe_days": days,
        "total_fields_reviewed": total_fields,
        "ai_human_agreement_percent": round(ai_human_agreement, 2),
        "hallucination_rate_percent": round(hallucination_rate, 2),
        "correction_rate_percent": round(correction_rate, 2),
        "average_review_time_seconds": round(avg_review_seconds, 2)
    }
