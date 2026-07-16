from typing import List
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.models import Project
from app.infrastructure.repositories.base import SQLAlchemyRepository


class ProjectRepository(SQLAlchemyRepository[Project]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Project)

    async def get_by_owner(self, owner_id: uuid.UUID) -> List[Project]:
        query = select(Project).where(Project.owner_id == owner_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
