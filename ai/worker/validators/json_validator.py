import json
from jsonschema import validate, ValidationError
from typing import Tuple, Dict, Any

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
