import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, ForeignKey, DateTime, Integer, Float, JSON, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import AuditableBase, Base


class Role(AuditableBase):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    permissions: Mapped[dict] = mapped_column(JSON, default=dict)

    users: Mapped[List["User"]] = relationship("User", back_populates="role", foreign_keys="User.role_id")


class User(AuditableBase):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id"), nullable=False)

    role: Mapped["Role"] = relationship("Role", back_populates="users", foreign_keys=[role_id])
    projects: Mapped[List["Project"]] = relationship("Project", back_populates="owner", foreign_keys="Project.owner_id")
    uploaded_documents: Mapped[List["Document"]] = relationship("Document", back_populates="uploader", foreign_keys="Document.uploader_id")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="user", foreign_keys="AuditLog.user_id")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="reviewer", foreign_keys="Review.reviewer_id")


class Project(AuditableBase):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    owner: Mapped["User"] = relationship("User", back_populates="projects", foreign_keys=[owner_id])
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="project", cascade="all, delete-orphan", foreign_keys="Document.project_id")


class Document(AuditableBase):
    __tablename__ = "documents"

    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50))
    minio_key: Mapped[str] = mapped_column(String(500), nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(50), default="pending") 
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    uploader_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    project: Mapped["Project"] = relationship("Project", back_populates="documents", foreign_keys=[project_id])
    uploader: Mapped["User"] = relationship("User", back_populates="uploaded_documents", foreign_keys=[uploader_id])
    versions: Mapped[List["DocumentVersion"]] = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan", foreign_keys="DocumentVersion.document_id")
    jobs: Mapped[List["Job"]] = relationship("Job", back_populates="document", cascade="all, delete-orphan", foreign_keys="Job.document_id")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="document", cascade="all, delete-orphan", foreign_keys="Review.document_id")


class DocumentVersion(AuditableBase):
    __tablename__ = "document_versions"

    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    minio_key: Mapped[str] = mapped_column(String(500), nullable=False)

    document: Mapped["Document"] = relationship("Document", back_populates="versions", foreign_keys=[document_id])


class Job(AuditableBase):
    __tablename__ = "jobs"

    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False) 
    status: Mapped[str] = mapped_column(String(50), default="queued") 
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="jobs", foreign_keys=[document_id])


class Event(AuditableBase):
    __tablename__ = "events"

    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(50), default="pending") 


class Review(AuditableBase):
    __tablename__ = "reviews"

    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False)
    reviewer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    comments: Mapped[Optional[str]] = mapped_column(Text)
    modifications: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    document: Mapped["Document"] = relationship("Document", back_populates="reviews", foreign_keys=[document_id])
    reviewer: Mapped["User"] = relationship("User", back_populates="reviews", foreign_keys=[reviewer_id])


class AuditLog(AuditableBase):
    __tablename__ = "audit_logs"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs", foreign_keys=[user_id])
