import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class AuditableBase(Base):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    version_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)

    __mapper_args__ = {
        "version_id_col": version_id,
        "version_id_generator": False
    }
