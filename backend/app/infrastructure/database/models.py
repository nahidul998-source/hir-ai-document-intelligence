import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import String, ForeignKey, DateTime, Integer, Float, JSON, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

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
    document_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
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
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys="DocumentVersion.created_by")


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
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    document: Mapped["Document"] = relationship("Document", back_populates="reviews", foreign_keys=[document_id])
    reviewer: Mapped["User"] = relationship("User", back_populates="reviews", foreign_keys=[reviewer_id])


class AuditLog(AuditableBase):
    __tablename__ = "audit_logs"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs", foreign_keys=[user_id])


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

class AIProviderConfig(AuditableBase):
    """
    Database-backed configuration for AI Providers.
    """
    __tablename__ = "ai_provider_configs"

    key: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    api_url: Mapped[str] = mapped_column(String(500), nullable=False)
    api_key: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    connect_timeout: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    read_timeout: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    retry_timeout: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    priority_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    capabilities: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class AIProviderRoutingRule(AuditableBase):
    """
    Rules dictating which providers should handle specific document types.
    """
    __tablename__ = "ai_provider_routing_rules"

    document_type: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    provider_keys: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)


class MasterBuyer(AuditableBase):
    __tablename__ = "md_buyers"
    
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    erp_reference_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    aliases: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)

class MasterSupplier(AuditableBase):
    __tablename__ = "md_suppliers"
    
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    erp_reference_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    aliases: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)

class MasterBrand(AuditableBase):
    __tablename__ = "md_brands"
    
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    erp_reference_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    buyer_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("md_buyers.id"))
    aliases: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)

class MasterFabric(AuditableBase):
    __tablename__ = "md_fabrics"
    
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    erp_reference_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    composition: Mapped[Optional[str]] = mapped_column(String(255))
    aliases: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)

class MasterColor(AuditableBase):
    __tablename__ = "md_colors"
    
    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    hex_code: Mapped[Optional[str]] = mapped_column(String(20))
    erp_reference_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    aliases: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)

class MasterSize(AuditableBase):
    __tablename__ = "md_sizes"
    
    name: Mapped[str] = mapped_column(String(50), index=True, nullable=False) # e.g., 'XL', '32', 'OS'
    erp_reference_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    aliases: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)

class MasterUOM(AuditableBase):
    __tablename__ = "md_uoms"
    
    name: Mapped[str] = mapped_column(String(50), index=True, nullable=False) # e.g., 'pcs', 'kg', 'meters'
    erp_reference_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    aliases: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)


class KnowledgeBase(AuditableBase):
    __tablename__ = "knowledge_bases"

    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Multi-tenant isolation is inherited from AuditableBase
    visibility: Mapped[str] = mapped_column(String(50), default="private")
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    chunks: Mapped[List["KnowledgeChunk"]] = relationship("KnowledgeChunk", back_populates="knowledge_base", cascade="all, delete-orphan")


class KnowledgeChunk(AuditableBase):
    __tablename__ = "knowledge_chunks"

    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("knowledge_bases.id"), nullable=False)
    
    # Multi-tenant isolation is inherited from AuditableBase
    
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


class Tenant(Base):
    """
    Multi-tenant organization configuration and quota limits.
    """
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    version_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default="active", index=True)  # active | suspended | disabled
    max_users: Mapped[int] = mapped_column(Integer, default=50)
    storage_quota_gb: Mapped[float] = mapped_column(Float, default=100.0)
    settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)

    __mapper_args__ = {
        "version_id_col": version_id,
        "version_id_generator": False
    }


class ApiKey(AuditableBase):
    """
    External system integration API access keys.
    """
    __tablename__ = "api_keys"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    hashed_secret: Mapped[str] = mapped_column(String(255), nullable=False)
    scopes: Mapped[List[str]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)


class FeatureFlag(AuditableBase):
    """
    Dynamic feature toggle configuration.
    """
    __tablename__ = "feature_flags"

    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    target_tenants: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    rules: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)


class ValidationRule(AuditableBase):
    """
    Custom field extraction validation constraints.
    """
    __tablename__ = "validation_rules"

    field_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)  # regex | range | required | math_balance
    constraint_value: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str] = mapped_column(String(255), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class SystemConfig(AuditableBase):
    """
    Global platform configuration settings.
    """
    __tablename__ = "system_configs"

    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="general", index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_encrypted: Mapped[bool] = mapped_column(Boolean, default=False)


class BackupConfig(AuditableBase):
    """
    Database and file storage backup schedule configuration and metadata.
    """
    __tablename__ = "backup_configs"

    schedule_cron: Mapped[str] = mapped_column(String(50), default="0 2 * * *")
    destination_bucket: Mapped[str] = mapped_column(String(150), default="hir-backups")
    retention_days: Mapped[int] = mapped_column(Integer, default=30)
    is_automated: Mapped[bool] = mapped_column(Boolean, default=True)
    last_backup_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)


class AnalyticsSnapshot(AuditableBase):
    """
    Stores historical telemetry metric snapshots for high-speed BI trend reporting.
    """
    __tablename__ = "analytics_snapshots"

    metric_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    dimension: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    time_bucket: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    value_number: Mapped[float] = mapped_column(Float, default=0.0)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)


class SLAPolicy(AuditableBase):
    """
    SLA targets and processing time threshold policies per document type.
    """
    __tablename__ = "sla_policies"

    document_type: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    max_processing_time_seconds: Mapped[int] = mapped_column(Integer, default=300)
    target_compliance_pct: Mapped[float] = mapped_column(Float, default=95.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

