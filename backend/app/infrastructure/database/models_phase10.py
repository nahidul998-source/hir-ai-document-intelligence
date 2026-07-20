import uuid
from typing import List, Optional
from sqlalchemy import String, ForeignKey, Integer, Float, JSON, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector  # Assuming pgvector is installed

from .base_model import AuditableBase

class KnowledgeBase(AuditableBase):
    __tablename__ = "knowledge_bases"

    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Multi-tenant isolation
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    visibility: Mapped[str] = mapped_column(String(50), default="private")
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    chunks: Mapped[List["KnowledgeChunk"]] = relationship("KnowledgeChunk", back_populates="knowledge_base", cascade="all, delete-orphan")


class KnowledgeChunk(AuditableBase):
    __tablename__ = "knowledge_chunks"

    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("knowledge_bases.id"), nullable=False)
    
    # Multi-tenant isolation
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Vector Embedding
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536))
    
    # Text Data
    text_content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Metadata
    chunk_id: Mapped[str] = mapped_column(String(255), index=True, unique=True, nullable=False)
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("documents.id"), nullable=True)
    document_version: Mapped[int] = mapped_column(Integer, default=1)
    page_number: Mapped[Optional[int]] = mapped_column(Integer)
    section_title: Mapped[Optional[str]] = mapped_column(String(255))
    heading_path: Mapped[Optional[str]] = mapped_column(Text)
    buyer: Mapped[Optional[str]] = mapped_column(String(100))
    ocr_confidence: Mapped[Optional[float]] = mapped_column(Float)
    
    # Bounding Box [x1, y1, x2, y2]
    bbox: Mapped[Optional[dict]] = mapped_column(JSON) 

    knowledge_base: Mapped["KnowledgeBase"] = relationship("KnowledgeBase", back_populates="chunks")
