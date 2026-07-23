import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from app.api.deps import get_document_service, get_current_user
from app.application.services.document_service import DocumentService
from app.infrastructure.database.models import User
from app.schemas.document import DocumentResponse

router = APIRouter()


@router.post("/upload/{project_id}", response_model=DocumentResponse)
async def upload_document(
    project_id: uuid.UUID,
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service),
    current_user: User = Depends(get_current_user)
):
    try:
        # Security Phase 9: Enhanced File Validation
        ALLOWED_MIMES = [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "image/png",
            "image/jpeg"
        ]
        
        # Read uploaded file content
        content = await file.read()
        length = len(content)
        
        if length > 25 * 1024 * 1024:  # 25MB max
            raise HTTPException(status_code=413, detail="File too large")
            
        import magic
        mime = magic.from_buffer(content, mime=True)
        if mime not in ALLOWED_MIMES:
            raise HTTPException(status_code=415, detail=f"Unsupported file type: {mime}")
            
        from io import BytesIO
        file_stream = BytesIO(content)

        document = await document_service.upload_document(
            project_id=project_id,
            filename=file.filename,
            file_type=file.content_type or "application/octet-stream",
            data=file_stream,
            length=length,
            uploader_id=current_user.id
        )
        return document
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/{project_id}", response_model=List[DocumentResponse])
async def list_documents(
    project_id: uuid.UUID,
    document_service: DocumentService = Depends(get_document_service),
    current_user: User = Depends(get_current_user)
):
    documents = await document_service.list_documents(project_id)
    return documents


@router.get("/download/{document_id}")
async def download_document(
    document_id: uuid.UUID,
    document_service: DocumentService = Depends(get_document_service),
    current_user: User = Depends(get_current_user)
):
    document = await document_service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        from app.core.config import settings
        from fastapi.responses import StreamingResponse
        file_stream = await document_service.storage_adapter.download_file(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=document.minio_key
        )
        return StreamingResponse(
            file_stream,
            media_type=document.file_type or "application/pdf",
            headers={"Content-Disposition": f"inline; filename={document.filename}"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        )

from app.schemas.extraction_payload import ExtractionPayload
from app.infrastructure.database.models_phase2 import DocumentExtraction
from app.infrastructure.database.models_phase3 import ReviewSession, ReviewField
from app.database.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

@router.post("/{document_id}/extraction")
async def save_extraction(
    document_id: uuid.UUID,
    payload: ExtractionPayload,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Get document version
        from app.infrastructure.database.models import DocumentVersion, Document
        stmt = select(DocumentVersion).where(DocumentVersion.document_id == document_id).order_by(DocumentVersion.version_number.desc())
        result = await db.execute(stmt)
        version = result.scalars().first()
        if not version:
            raise HTTPException(status_code=404, detail="Document version not found")
        
        # Save extraction
        extraction = DocumentExtraction(
            document_id=document_id,
            document_version_id=version.id,
            extracted_data=payload.extracted_data,
            prompt_version="1.0"
        )
        db.add(extraction)
        await db.flush()
        
        # Update document status
        doc_stmt = select(Document).where(Document.id == document_id)
        doc_res = await db.execute(doc_stmt)
        doc = doc_res.scalars().first()
        if doc:
            doc.status = "review_pending"
            doc.document_type = payload.document_type
            
        # Create review session
        session = ReviewSession(
            document_id=document_id,
            extraction_id=extraction.id,
            status="draft"
        )
        db.add(session)
        await db.flush()
        
        # Create review fields
        for field_name, field_value in payload.extracted_data.items():
            str_value = str(field_value) if field_value is not None else None
            metadata = payload.confidence_metadata.get(field_name, {})
            review_field = ReviewField(
                session_id=session.id,
                field_name=field_name,
                original_value=str_value,
                edited_value=str_value,
                confidence=metadata.get("confidence_score"),
                source_page=metadata.get("source_page"),
                bounding_box=metadata.get("bounding_box"),
                provider=metadata.get("provider"),
                validation_status="pending"
            )
            db.add(review_field)
            
        await db.commit()
        return {"status": "success", "extraction_id": str(extraction.id), "session_id": str(session.id)}
    except Exception as e:
        await db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save extraction: {str(e)}"
        )
