import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, ForeignKey, DateTime, Integer, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import AuditableBase
from .models import Document, DocumentVersion

class DocumentExtraction(AuditableBase):
    __tablename__ = "document_extractions"

    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False)
    document_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_versions.id"), nullable=False)
    extracted_data: Mapped[dict] = mapped_column(JSON, default=dict)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    
    document = relationship("Document", foreign_keys=[document_id])
    document_version = relationship("DocumentVersion", foreign_keys=[document_version_id])
    metrics = relationship("ExtractionMetric", back_populates="extraction", cascade="all, delete-orphan", foreign_keys="ExtractionMetric.extraction_id")

class ExtractionMetric(AuditableBase):
    __tablename__ = "extraction_metrics"

    extraction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_extractions.id"), nullable=False)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    
    extraction = relationship("DocumentExtraction", back_populates="metrics", foreign_keys=[extraction_id])
