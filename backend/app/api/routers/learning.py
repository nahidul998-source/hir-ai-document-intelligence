import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.api.deps import get_current_user
from app.infrastructure.database.models import User

from app.infrastructure.repositories.learning import LearningRepository
from app.application.services.learning.correction_collector import CorrectionCollector
from app.application.services.learning.dataset_builder import DatasetBuilder
from app.application.services.learning.prompt_optimizer import PromptOptimizer
from app.application.services.learning.feedback_engine import AIFeedbackEngine
from app.application.services.learning.confidence_analytics import ConfidenceAnalytics
from app.application.services.learning.reviewer_analytics import ReviewerAnalytics
from app.application.services.learning.quality_reports import ExtractionQualityReports

router = APIRouter(prefix="/learning", tags=["Continuous Learning Engine"])


@router.get("/corrections", tags=["Continuous Learning Engine"])
async def list_correction_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    document_type: Optional[str] = None,
    field_name: Optional[str] = None,
    was_modified: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists captured human review learning correction records."""
    repo = LearningRepository(db)
    records = await repo.get_correction_records(
        skip=skip,
        limit=limit,
        document_type=document_type,
        field_name=field_name,
        was_modified=was_modified
    )
    total = await repo.count_correction_records(
        document_type=document_type,
        field_name=field_name,
        was_modified=was_modified
    )

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "records": [
            {
                "id": str(r.id),
                "document_id": str(r.document_id),
                "session_id": str(r.session_id),
                "field_name": r.field_name,
                "original_extracted_value": r.original_extracted_value,
                "corrected_value": r.corrected_value,
                "was_modified": r.was_modified,
                "initial_confidence": r.initial_confidence,
                "source_page": r.source_page,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in records
        ]
    }


@router.post("/sessions/{session_id}/collect", tags=["Continuous Learning Engine"])
async def collect_session_corrections(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Triggers CorrectionCollector to store approved learning data for a review session."""
    collector = CorrectionCollector(db)
    records = await collector.collect_from_approved_session(session_id, current_user.id)
    return {
        "status": "success",
        "collected_count": len(records),
        "session_id": str(session_id)
    }


@router.post("/datasets", tags=["Continuous Learning Engine"])
async def create_learning_dataset(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Builds a new fine-tuning or few-shot exemplar dataset."""
    builder = DatasetBuilder(db)
    dataset = await builder.build_dataset(
        name=payload.get("name", "Learning Dataset"),
        description=payload.get("description", ""),
        dataset_type=payload.get("dataset_type", "fine_tuning_jsonl"),
        document_type=payload.get("document_type"),
        target_field=payload.get("target_field"),
        min_confidence_threshold=float(payload.get("min_confidence_threshold", 0.0)),
        only_modified=bool(payload.get("only_modified", False))
    )
    return {
        "id": str(dataset.id),
        "name": dataset.name,
        "sample_count": dataset.sample_count,
        "status": dataset.status
    }


@router.get("/datasets", tags=["Continuous Learning Engine"])
async def list_datasets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists generated learning datasets."""
    repo = LearningRepository(db)
    datasets = await repo.get_datasets(skip=skip, limit=limit)
    return [
        {
            "id": str(d.id),
            "name": d.name,
            "description": d.description,
            "dataset_type": d.dataset_type,
            "sample_count": d.sample_count,
            "status": d.status,
            "created_at": d.created_at.isoformat() if d.created_at else None
        }
        for d in datasets
    ]


@router.get("/datasets/{dataset_id}/export", tags=["Continuous Learning Engine"])
async def export_dataset(
    dataset_id: uuid.UUID,
    format: str = Query("jsonl", regex="^(jsonl|json|csv)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Exports dataset content formatted as JSONL, JSON, or CSV."""
    builder = DatasetBuilder(db)
    try:
        content = await builder.export_dataset_content(dataset_id, format)
        media_type = "application/x-ndjson" if format == "jsonl" else ("text/csv" if format == "csv" else "application/json")
        return PlainTextResponse(content, media_type=media_type)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/prompts/exemplars", tags=["Continuous Learning Engine"])
async def get_few_shot_exemplars(
    field_name: Optional[str] = None,
    max_samples: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Gets top dynamic few-shot prompt exemplars."""
    optimizer = PromptOptimizer(db)
    return await optimizer.generate_few_shot_exemplars(field_name=field_name, max_samples=max_samples)


@router.post("/prompts/optimize", tags=["Continuous Learning Engine"])
async def create_prompt_optimization(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Registers a new prompt version and triggers evaluation."""
    optimizer = PromptOptimizer(db)
    record = await optimizer.create_prompt_version(
        prompt_name=payload.get("prompt_name", "purchase_order_extraction"),
        version=payload.get("version", "v1.1"),
        template_content=payload.get("template_content", "System prompt..."),
        few_shot_exemplars=payload.get("few_shot_exemplars", []),
        is_active=bool(payload.get("is_active", True)),
        notes=payload.get("notes")
    )
    eval_res = await optimizer.evaluate_prompt_accuracy(record.prompt_name, record.version)
    return {
        "id": str(record.id),
        "prompt_name": record.prompt_name,
        "version": record.version,
        "eval_result": eval_res
    }


@router.get("/analytics/feedback", tags=["Continuous Learning Engine"])
async def get_feedback_analytics(
    field_name: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Gets AI Feedback Engine metrics."""
    engine = AIFeedbackEngine(db)
    target_field = field_name or "total_amount"
    return await engine.compute_field_feedback(target_field)


@router.get("/analytics/confidence", tags=["Continuous Learning Engine"])
async def get_confidence_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Gets Confidence Analytics calibration data."""
    analytics = ConfidenceAnalytics(db)
    return await analytics.get_confidence_calibration()


@router.get("/analytics/reviewers", tags=["Continuous Learning Engine"])
async def get_reviewer_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Gets Reviewer Analytics productivity metrics."""
    analytics = ReviewerAnalytics(db)
    return await analytics.get_reviewer_productivity()


@router.get("/reports/quality", tags=["Continuous Learning Engine"])
async def get_extraction_quality_report(
    document_type: Optional[str] = None,
    buyer_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates Extraction Quality Report."""
    reports = ExtractionQualityReports(db)
    return await reports.generate_quality_report(document_type=document_type, buyer_code=buyer_code)
