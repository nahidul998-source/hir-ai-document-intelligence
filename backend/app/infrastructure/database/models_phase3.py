import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, ForeignKey, DateTime, Integer, Float, JSON, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import AuditableBase

class ReviewSession(AuditableBase):
    __tablename__ = "review_sessions"

    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    extraction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_extractions.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft") 
    
    fields = relationship("ReviewField", back_populates="session", cascade="all, delete-orphan", foreign_keys="ReviewField.session_id")
    history = relationship("ReviewHistory", back_populates="session", cascade="all, delete-orphan", foreign_keys="ReviewHistory.session_id")
    comments = relationship("ReviewComment", back_populates="session", cascade="all, delete-orphan", foreign_keys="ReviewComment.session_id")
    approvals = relationship("Approval", back_populates="session", cascade="all, delete-orphan", foreign_keys="Approval.session_id")

class ReviewField(AuditableBase):
    __tablename__ = "review_fields"

    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("review_sessions.id"), nullable=False)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    original_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    edited_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bounding_box: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    validation_status: Mapped[str] = mapped_column(String(50), default="pending") 
    reviewer_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    session = relationship("ReviewSession", back_populates="fields", foreign_keys=[session_id])
    corrections = relationship("FieldCorrection", back_populates="field", cascade="all, delete-orphan", foreign_keys="FieldCorrection.field_id")

class FieldCorrection(AuditableBase):
    """Immutable log of field modifications"""
    __tablename__ = "field_corrections"

    field_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("review_fields.id"), nullable=False)
    previous_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    field = relationship("ReviewField", back_populates="corrections", foreign_keys=[field_id])

class ReviewComment(AuditableBase):
    __tablename__ = "review_comments"

    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("review_sessions.id"), nullable=False)
    field_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) 
    comment_text: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    session = relationship("ReviewSession", back_populates="comments", foreign_keys=[session_id])

class Approval(AuditableBase):
    """Tracks explicit field or document approvals"""
    __tablename__ = "approvals"

    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("review_sessions.id"), nullable=False)
    field_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reviewer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    session = relationship("ReviewSession", back_populates="approvals", foreign_keys=[session_id])

class ReviewHistory(AuditableBase):
    """Audit log specifically for review transitions"""
    __tablename__ = "review_history"

    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("review_sessions.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False) 
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    session = relationship("ReviewSession", back_populates="history", foreign_keys=[session_id])

class ERPTransaction(AuditableBase):
    """Tracks ERP integration status"""
    __tablename__ = "erp_transactions"

    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("review_sessions.id"), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(50), default="queued") 
    payload: Mapped[dict] = mapped_column(JSON, default=dict) 
    response_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
