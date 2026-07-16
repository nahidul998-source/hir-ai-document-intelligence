from typing import Generic, TypeVar, Type, List, Optional, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import DeclarativeBase

T = TypeVar('T', bound=Any)


class IRepository(Generic[T]):
    """Abstract interface for all repositories enforcing DDD/SOLID boundaries."""

    async def get(self, id: uuid.UUID) -> Optional[T]:
        raise NotImplementedError

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        raise NotImplementedError

    async def add(self, entity: T) -> T:
        raise NotImplementedError

    async def update(self, entity: T) -> T:
        raise NotImplementedError

    async def delete(self, id: uuid.UUID) -> None:
        raise NotImplementedError


class SQLAlchemyRepository(IRepository[T], Generic[T]):
    """Concrete repository implementing SQLAlchemy 2 Async operations."""

    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model

    async def get(self, id: uuid.UUID) -> Optional[T]:
        query = select(self.model).where(self.model.id == id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        query = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def add(self, entity: T) -> T:
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def update(self, entity: T) -> T:
        # Entity is modified in-place, we merge it to session state
        merged = await self.session.merge(entity)
        await self.session.flush()
        return merged

    async def delete(self, id: uuid.UUID) -> None:
        query = delete(self.model).where(self.model.id == id)
        await self.session.execute(query)
        await self.session.flush()
