import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.database.models import User, Role
from app.infrastructure.database.models_phase8 import Tenant
from app.infrastructure.repositories.admin import AdminRepository

logger = logging.getLogger(__name__)


class UserTenantService:
    """
    Handles User lifecycle management, Role definitions, and Multi-tenant quota enforcement.
    """
    def __init__(self, db: AsyncSession, repo: Optional[AdminRepository] = None):
        self.db = db
        self.repo = repo or AdminRepository(db)

    async def list_users(self, skip: int = 0, limit: int = 50) -> List[User]:
        return await self.repo.get_users(skip=skip, limit=limit)

    async def create_tenant(
        self,
        name: str,
        code: str,
        max_users: int = 50,
        storage_quota_gb: float = 100.0,
        settings: Optional[Dict[str, Any]] = None
    ) -> Tenant:
        tenant = Tenant(
            name=name,
            code=code,
            status="active",
            max_users=max_users,
            storage_quota_gb=storage_quota_gb,
            settings=settings or {}
        )
        saved = await self.repo.save_tenant(tenant)
        await self.db.commit()
        logger.info(f"Created tenant '{name}' with code '{code}'.")
        return saved

    async def list_tenants(self, skip: int = 0, limit: int = 50) -> List[Tenant]:
        return await self.repo.get_tenants(skip=skip, limit=limit)

    async def create_role(self, name: str, permissions: Dict[str, bool]) -> Role:
        role = Role(name=name, permissions=permissions)
        saved = await self.repo.save_role(role)
        await self.db.commit()
        logger.info(f"Created role '{name}'.")
        return saved

    async def list_roles(self) -> List[Role]:
        return await self.repo.get_roles()
