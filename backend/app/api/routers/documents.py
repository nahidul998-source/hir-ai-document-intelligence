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
        # Read uploaded file content
        content = await file.read()
        length = len(content)
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
