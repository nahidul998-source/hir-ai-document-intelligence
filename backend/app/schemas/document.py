import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    filename: str
    file_type: str
    minio_key: str
    current_version: int
    status: str
    confidence_score: Optional[float] = None
    uploader_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
