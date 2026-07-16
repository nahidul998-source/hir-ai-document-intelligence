from typing import List
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.models import Document, DocumentVersion
from app.infrastructure.repositories.base import SQLAlchemyRepository


class DocumentRepository(SQLAlchemyRepository[Document]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Document)

    async def get_by_project(self, project_id: uuid.UUID) -> List[Document]:
        query = select(Document).where(Document.project_id == project_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def add_version(self, version: DocumentVersion) -> DocumentVersion:
        self.session.add(version)
        await self.session.flush()
        return version

    async def get_versions(self, document_id: uuid.UUID) -> List[DocumentVersion]:
        query = select(DocumentVersion).where(DocumentVersion.document_id == document_id).order_by(DocumentVersion.version_number.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())
