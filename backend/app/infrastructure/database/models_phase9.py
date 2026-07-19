import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, ForeignKey, DateTime, Integer, Float, JSON, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import AuditableBase


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
