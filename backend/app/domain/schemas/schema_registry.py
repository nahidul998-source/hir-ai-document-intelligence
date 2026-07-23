import json
import os
from pathlib import Path
from typing import Dict, Optional
from app.domain.schemas.document_schema import DocumentTypeSchema

class DocumentSchemaRegistry:
    def __init__(self, schemas_dir: str = None):
        if schemas_dir is None:
            # Default to backend/app/domain/schemas/definitions
            self.schemas_dir = Path(__file__).parent / "definitions"
        else:
            self.schemas_dir = Path(schemas_dir)
            
        self.schemas: Dict[str, DocumentTypeSchema] = {}
        self.load_schemas()

    def load_schemas(self):
        if not self.schemas_dir.exists():
            self.schemas_dir.mkdir(parents=True, exist_ok=True)
            return

        for schema_file in self.schemas_dir.glob("*.json"):
            try:
                with open(schema_file, "r") as f:
                    data = json.load(f)
                    schema = DocumentTypeSchema(**data)
                    self.schemas[schema.document_type] = schema
            except Exception as e:
                print(f"Failed to load schema from {schema_file}: {e}")

    def get_schema(self, document_type: str) -> Optional[DocumentTypeSchema]:
        return self.schemas.get(document_type)

    def get_all_schemas(self) -> Dict[str, DocumentTypeSchema]:
        return self.schemas

# Singleton instance
schema_registry = DocumentSchemaRegistry()
