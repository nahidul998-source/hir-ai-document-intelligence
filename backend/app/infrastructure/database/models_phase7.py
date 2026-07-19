import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, ForeignKey, DateTime, Integer, Float, JSON, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import AuditableBase


class LearningCorrectionRecord(AuditableBase):
    """
    Stores an approved human edit or confirmed extraction value along with context
    to serve as reusable training/exemplar data for prompt optimization and fine-tuning.
    """
    __tablename__ = "learning_correction_records"

    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("review_sessions.id"), nullable=False, index=True)
    field_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("review_fields.id"), nullable=False, index=True)
    reviewer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    document_type: Mapped[str] = mapped_column(String(100), default="purchase_order", index=True)
    buyer_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    original_extracted_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    corrected_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    was_modified: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    initial_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bounding_box: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    ocr_context_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    ai_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(50), default="v1.0")

    dataset_items = relationship("LearningDatasetItem", back_populates="correction_record", cascade="all, delete-orphan")


class LearningDataset(AuditableBase):
    """
    Standardized dataset compiled from selected learning correction records.
    Can be exported as OpenAI/Anthropic/LLaMA JSONL fine-tuning files or Few-Shot prompt exemplars.
    """
    __tablename__ = "learning_datasets"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dataset_type: Mapped[str] = mapped_column(String(50), default="fine_tuning_jsonl", index=True)  # fine_tuning_jsonl | few_shot_prompt
    document_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    target_field: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    min_confidence_threshold: Mapped[float] = mapped_column(Float, default=0.0)

    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="ready")  # building | ready | archived
    export_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)

    items = relationship("LearningDatasetItem", back_populates="dataset", cascade="all, delete-orphan")


class LearningDatasetItem(AuditableBase):
    """
    Individual formatted input/output sample in a LearningDataset.
    """
    __tablename__ = "learning_dataset_items"

    dataset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learning_datasets.id"), nullable=False, index=True)
    correction_record_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learning_correction_records.id"), nullable=False, index=True)

    input_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    target_output: Mapped[str] = mapped_column(Text, nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, default=1.0)

    dataset = relationship("LearningDataset", back_populates="items")
    correction_record = relationship("LearningCorrectionRecord", back_populates="dataset_items")


class PromptOptimizationRecord(AuditableBase):
    """
    Tracks iterations of system prompts, benchmark accuracy against learning datasets,
    and automatic dynamic exemplar selection settings.
    """
    __tablename__ = "prompt_optimization_records"

    prompt_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    template_content: Mapped[str] = mapped_column(Text, nullable=False)
    few_shot_exemplars: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list)

    eval_accuracy_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    eval_sample_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class AIFeedbackMetric(AuditableBase):
    """
    Stores aggregated evaluation feedback metrics, error categories, and confidence calibrations.
    """
    __tablename__ = "ai_feedback_metrics"

    time_bucket: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    total_extractions: Mapped[int] = mapped_column(Integer, default=0)
    total_corrections: Mapped[int] = mapped_column(Integer, default=0)

    accuracy_rate: Mapped[float] = mapped_column(Float, default=1.0)
    avg_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    error_pattern_distribution: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
