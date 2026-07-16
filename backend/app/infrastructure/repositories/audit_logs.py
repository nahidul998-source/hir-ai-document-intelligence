from typing import List
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.models import AuditLog
from app.infrastructure.repositories.base import SQLAlchemyRepository


class AuditLogRepository(SQLAlchemyRepository[AuditLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, AuditLog)

    async def get_by_user(self, user_id: uuid.UUID) -> List[AuditLog]:
        query = select(AuditLog).where(AuditLog.user_id == user_id).order_by(AuditLog.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())
