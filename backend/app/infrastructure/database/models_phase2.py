import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, ForeignKey, DateTime, Integer, Float, JSON, Boolean, Text
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

class DocumentPage(AuditableBase):
    __tablename__ = "document_pages"
    
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[Optional[float]] = mapped_column(Float)
    height: Mapped[Optional[float]] = mapped_column(Float)
    text_content: Mapped[Optional[str]] = mapped_column(Text)
    ocr_confidence: Mapped[Optional[float]] = mapped_column(Float)
    
class DocumentTable(AuditableBase):
    __tablename__ = "document_tables"
    
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    table_index: Mapped[int] = mapped_column(Integer, nullable=False)
    table_data: Mapped[dict] = mapped_column(JSON, default=dict)
    
class DocumentLayoutBlock(AuditableBase):
    __tablename__ = "document_layout_blocks"
    
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    block_type: Mapped[str] = mapped_column(String(50), nullable=False) # title, paragraph, image
    bbox: Mapped[dict] = mapped_column(JSON, default=dict)
    text_content: Mapped[Optional[str]] = mapped_column(Text)
