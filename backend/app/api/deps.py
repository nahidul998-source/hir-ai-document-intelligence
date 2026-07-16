import uuid
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.infrastructure.repositories.users import UserRepository
from app.infrastructure.repositories.projects import ProjectRepository
from app.infrastructure.repositories.documents import DocumentRepository
from app.infrastructure.repositories.audit_logs import AuditLogRepository
from app.infrastructure.adapters.storage.minio_adapter import MinIOStorageAdapter
from app.infrastructure.events.publisher import RabbitMQEventPublisher
from app.application.services.user_service import UserService
from app.application.services.project_service import ProjectService
from app.application.services.document_service import DocumentService
from app.infrastructure.database.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Singletons/Shared Instances for infrastructure adapters
_storage_adapter = MinIOStorageAdapter()
_event_publisher = RabbitMQEventPublisher()


async def get_storage_adapter() -> MinIOStorageAdapter:
    return _storage_adapter


async def get_event_publisher() -> RabbitMQEventPublisher:
    return _event_publisher


# Repositories
async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


async def get_project_repository(db: AsyncSession = Depends(get_db)) -> ProjectRepository:
    return ProjectRepository(db)


async def get_document_repository(db: AsyncSession = Depends(get_db)) -> DocumentRepository:
    return DocumentRepository(db)


async def get_audit_repository(db: AsyncSession = Depends(get_db)) -> AuditLogRepository:
    return AuditLogRepository(db)


# Services
async def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(repo)


async def get_project_service(repo: ProjectRepository = Depends(get_project_repository)) -> ProjectService:
    return ProjectService(repo)


async def get_document_service(
    repo: DocumentRepository = Depends(get_document_repository),
    audit: AuditLogRepository = Depends(get_audit_repository),
    storage: MinIOStorageAdapter = Depends(get_storage_adapter),
    publisher: RabbitMQEventPublisher = Depends(get_event_publisher)
) -> DocumentService:
    return DocumentService(repo, audit, storage, publisher)


# Current User Extraction (Authentication Dependency)
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(get_user_service)
) -> User:
    user_id = user_service.verify_access_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user
