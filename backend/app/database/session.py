from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from sqlalchemy import event
from sqlalchemy.orm import Session, with_loader_criteria
from app.core.context import tenant_context
from app.infrastructure.database.base_model import AuditableBase

@event.listens_for(Session, "do_orm_execute")
def _add_tenant_filter(execute_state):
    """
    Globally intercepts ORM executions and injects a WHERE tenant_id = ? clause
    for any model inheriting from AuditableBase.
    """
    tenant_id = tenant_context.get()
    
    # If there's a tenant in context, apply the filter
    if tenant_id and not execute_state.is_column_load and not execute_state.is_relationship_load:
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                AuditableBase,
                lambda cls: cls.tenant_id == tenant_id,
                include_aliases=True
            )
        )

# Create async engine with connection pooling config suitable for enterprise scale
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection helper for FastAPI routes or services."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
