import uuid
from typing import Optional, List
from sqlalchemy import String, JSON, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base_model import AuditableBase

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
