import uuid
from typing import Optional, Dict, List, Any
from sqlalchemy import String, Integer, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base_model import AuditableBase

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
