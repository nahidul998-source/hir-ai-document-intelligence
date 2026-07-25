import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, func, desc, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import User, Role, AuditLog
from app.infrastructure.database.models import (
    Tenant,
    ApiKey,
    FeatureFlag,
    ValidationRule,
    SystemConfig,
    BackupConfig
)


class AdminRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # User & Role Management
    async def get_users(self, skip: int = 0, limit: int = 50) -> List[User]:
        query = select(User).order_by(desc(User.created_at)).offset(skip).limit(limit)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def get_roles(self) -> List[Role]:
        query = select(Role)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def save_role(self, role: Role) -> Role:
        self.db.add(role)
        await self.db.flush()
        return role

    # Tenant Management
    async def save_tenant(self, tenant: Tenant) -> Tenant:
        self.db.add(tenant)
        await self.db.flush()
        return tenant

    async def get_tenants(self, skip: int = 0, limit: int = 50) -> List[Tenant]:
        query = select(Tenant).order_by(desc(Tenant.created_at)).offset(skip).limit(limit)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    # Feature Flags
    async def get_feature_flags(self) -> List[FeatureFlag]:
        query = select(FeatureFlag).order_by(FeatureFlag.key)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def save_feature_flag(self, flag: FeatureFlag) -> FeatureFlag:
        self.db.add(flag)
        await self.db.flush()
        return flag

    # Validation Rules
    async def get_validation_rules(self) -> List[ValidationRule]:
        query = select(ValidationRule).order_by(ValidationRule.field_name)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def save_validation_rule(self, rule: ValidationRule) -> ValidationRule:
        self.db.add(rule)
        await self.db.flush()
        return rule

    # System Configs
    async def get_system_configs(self) -> List[SystemConfig]:
        query = select(SystemConfig).order_by(SystemConfig.key)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def set_system_config(self, key: str, value: str, category: str = "general", description: Optional[str] = None) -> SystemConfig:
        query = select(SystemConfig).where(SystemConfig.key == key)
        res = await self.db.execute(query)
        cfg = res.scalar_one_or_none()
        if cfg:
            cfg.value = value
            if description:
                cfg.description = description
        else:
            cfg = SystemConfig(key=key, value=value, category=category, description=description)
            self.db.add(cfg)
        await self.db.flush()
        return cfg

    # API Keys
    async def save_api_key(self, api_key: ApiKey) -> ApiKey:
        self.db.add(api_key)
        await self.db.flush()
        return api_key

    async def get_api_keys(self, user_id: Optional[uuid.UUID] = None) -> List[ApiKey]:
        query = select(ApiKey)
        if user_id:
            query = query.where(ApiKey.user_id == user_id)
        query = query.order_by(desc(ApiKey.created_at))
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def revoke_api_key(self, key_id: uuid.UUID) -> bool:
        await self.db.execute(
            update(ApiKey).where(ApiKey.id == key_id).values(is_active=False)
        )
        return True

    # Backup Config
    async def get_backup_config(self) -> Optional[BackupConfig]:
        query = select(BackupConfig)
        res = await self.db.execute(query)
        return res.scalar_one_or_none()

    async def save_backup_config(self, config: BackupConfig) -> BackupConfig:
        self.db.add(config)
        await self.db.flush()
        return config
