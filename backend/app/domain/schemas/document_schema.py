from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class UIFieldSchema(BaseModel):
    ui_widget: str = Field(..., description="The UI component to render (e.g., text, select, date, table)")
    label: str
    placeholder: Optional[str] = None
    required: bool = False
    options: Optional[List[Dict[str, str]]] = None # For select fields
    width: Optional[str] = "full" # half, full, etc.

class ValidationSchema(BaseModel):
    master_data_type: Optional[str] = None # e.g. "Buyer", "Color", "Style"
    regex: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    custom_rule: Optional[str] = None

class ERPMappingSchema(BaseModel):
    target_table: str
    target_field: str
    transformation: Optional[str] = None # e.g. "uppercase", "to_date"

class FieldSchemaDefinition(BaseModel):
    name: str
    type: str # string, number, boolean, array, object
    ui: UIFieldSchema
    validation: Optional[ValidationSchema] = None
    erp_mapping: Optional[ERPMappingSchema] = None
    description: Optional[str] = None
    items: Optional[Any] = None # For arrays of primitive types or object (table rows)
    properties: Optional[List[Any]] = None # For objects (nested fields or table columns)

class DocumentModuleSchema(BaseModel):
    module_id: str
    title: str
    fields: List[FieldSchemaDefinition]

class DocumentTypeSchema(BaseModel):
    document_type: str
    name: str
    description: str
    modules: List[DocumentModuleSchema]
