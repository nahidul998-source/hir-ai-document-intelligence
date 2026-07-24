import uuid
from typing import BinaryIO, List, Optional
from app.domain.interfaces import IStorageAdapter
from app.infrastructure.database.models import Document, DocumentVersion, AuditLog
from app.infrastructure.repositories.documents import DocumentRepository
from app.infrastructure.repositories.audit_logs import AuditLogRepository
from app.infrastructure.events.publisher import RabbitMQEventPublisher
from app.core.config import settings


class DocumentService:
    def __init__(
        self,
        document_repo: DocumentRepository,
        audit_repo: AuditLogRepository,
        storage_adapter: IStorageAdapter,
        event_publisher: RabbitMQEventPublisher
    ):
        self.document_repo = document_repo
        self.audit_repo = audit_repo
        self.storage_adapter = storage_adapter
        self.event_publisher = event_publisher

    async def upload_document(
        self,
        project_id: uuid.UUID,
        filename: str,
        file_type: str,
        data: BinaryIO,
        length: int,
        uploader_id: uuid.UUID
    ) -> Document:
        # 1. Generate unique file key and upload to MinIO
        file_uuid = uuid.uuid4()
        extension = filename.split(".")[-1] if "." in filename else "bin"
        minio_key = f"projects/{project_id}/documents/{file_uuid}.{extension}"

        # Sync read binary data stream
        await self.storage_adapter.upload_file(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=minio_key,
            data=data,
            length=length,
            content_type=file_type
        )

        # 2. Persist Document record
        document = Document(
            id=file_uuid,
            project_id=project_id,
            filename=filename,
            file_type=file_type,
            minio_key=minio_key,
            current_version=1,
            status="pending",
            uploader_id=uploader_id
        )
        await self.document_repo.add(document)

        # 3. Create DocumentVersion record
        version = DocumentVersion(
            document_id=document.id,
            version_number=1,
            minio_key=minio_key,
            created_by=uploader_id
        )
        await self.document_repo.add_version(version)

        # 4. Audit Log entry
        audit = AuditLog(
            user_id=uploader_id,
            action="UPLOAD_DOCUMENT",
            details={"document_id": str(document.id), "filename": filename, "project_id": str(project_id)}
        )
        await self.audit_repo.add(audit)

        # 5. Dispatch document.uploaded event to RabbitMQ
        await self.event_publisher.publish_event(
            routing_key="document.uploaded",
            payload={
                "document_id": str(document.id),
                "project_id": str(project_id),
                "filename": filename,
                "minio_key": minio_key,
                "version": 1
            }
        )

        return document

    async def get_document(self, document_id: uuid.UUID) -> Optional[Document]:
        return await self.document_repo.get(document_id)

    async def list_documents(self, project_id: uuid.UUID) -> List[Document]:
        return await self.document_repo.get_by_project(project_id)

    async def delete_document(self, document_id: uuid.UUID) -> None:
        document = await self.document_repo.get(document_id)
        if not document:
            return

        # Delete from Minio
        try:
            await self.storage_adapter.client.remove_object(
                settings.MINIO_BUCKET_NAME,
                document.minio_key
            )
        except Exception:
            pass # Ignore if already deleted or missing
            
        await self.document_repo.delete(document_id)

    async def process_document(self, document_id: uuid.UUID, ai_provider: Optional[str] = None) -> Document:
        document = await self.document_repo.get(document_id)
        if not document:
            raise ValueError("Document not found")

        # Update status to processing
        document.status = "processing"
        await self.document_repo.update(document)

        # Republish event
        payload = {
            "document_id": str(document.id),
            "project_id": str(document.project_id),
            "filename": document.filename,
            "minio_key": document.minio_key,
            "version": document.current_version
        }
        if ai_provider:
            payload["ai_provider"] = ai_provider

        await self.event_publisher.publish_event(
            routing_key="document.uploaded",
            payload=payload
        )
        return document

