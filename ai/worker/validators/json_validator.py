import json
from jsonschema import validate, ValidationError
from typing import Tuple, Dict, Any, Optional
from pydantic import ValidationError as PydanticValidationError

# Try importing backend extraction schemas. Support import fallback.
try:
    from app.schemas.extraction import InvoiceSchema, OrderSheetSchema, TechPackSchema
except ImportError:
    # Worker standalone fallback
    InvoiceSchema, OrderSheetSchema, TechPackSchema = None, None, None

class JSONValidator:
    @staticmethod
    def validate_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, str]:
        if not schema:
            return True, "No schema provided, skipped validation."
            
        try:
            validate(instance=data, schema=schema)
            return True, "Valid"
        except ValidationError as e:
            return False, str(e)

    @staticmethod
    def validate_pydantic(data: Dict[str, Any], document_type: str) -> Tuple[bool, str]:
        """Perform static Pydantic model validation based on document type."""
        mapping = {
            "invoice": InvoiceSchema,
            "order_sheet": OrderSheetSchema,
            "purchase_order": OrderSheetSchema,
            "tech_pack": TechPackSchema
        }
        
        model_cls = mapping.get(document_type)
        if not model_cls:
            return True, f"No static Pydantic model defined for type: {document_type}"
            
        try:
            model_cls(**data)
            return True, "Pydantic validation passed."
        except PydanticValidationError as e:
            return False, str(e)
