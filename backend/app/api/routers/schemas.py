from fastapi import APIRouter, HTTPException
from typing import Dict, List
from app.domain.schemas.schema_registry import schema_registry
from app.domain.schemas.document_schema import DocumentTypeSchema

router = APIRouter(tags=["Schemas"])

@router.get("/documents", response_model=Dict[str, DocumentTypeSchema])
async def get_all_document_schemas():
    """Retrieve all document schemas available in the registry."""
    return schema_registry.get_all_schemas()

@router.get("/documents/{document_type}", response_model=DocumentTypeSchema)
async def get_document_schema(document_type: str):
    """Retrieve the schema for a specific document type."""
    schema = schema_registry.get_schema(document_type)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    return schema
