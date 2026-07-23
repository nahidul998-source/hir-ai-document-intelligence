from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from uuid import UUID

class ExtractionPayload(BaseModel):
    document_type: str = Field(..., description="Classified document type")
    extracted_data: Dict[str, Any] = Field(..., description="The validated JSON extraction result")
    confidence_metadata: Dict[str, Any] = Field(..., description="Confidence scores and bounding boxes")
