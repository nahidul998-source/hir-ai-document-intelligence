import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, ForeignKey, DateTime, Integer, Float, JSON, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import AuditableBase


class Tenant(AuditableBase):
    """
    Multi-tenant organization configuration and quota limits.
    """
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default="active", index=True)  # active | suspended | disabled
    max_users: Mapped[int] = mapped_column(Integer, default=50)
    storage_quota_gb: Mapped[float] = mapped_column(Float, default=100.0)
    settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)


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
