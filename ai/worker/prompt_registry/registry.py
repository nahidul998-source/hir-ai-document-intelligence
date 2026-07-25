import sys
import os
from typing import Dict, Any
from ai.worker.classifiers.document_classifier import DocumentType

# Make sure backend is in path to import SchemaRegistry
from app.domain.schemas.schema_registry import schema_registry

class PromptRegistry:
    def __init__(self):
        pass

    def get_prompt(self, doc_type: DocumentType) -> str:
        """
        Dynamically builds the extraction prompt based on the JSON schema definition.
        """
        schema_def = schema_registry.get_schema(doc_type.value)
        if not schema_def:
            return "Extract all available information into a structured JSON format."
            
        prompt = f"Extract all data for a {schema_def.name} document.\n\nDescription: {schema_def.description}\n\nRequired modules:\n"
        
        for module in schema_def.modules:
            prompt += f"- {module.title}:\n"
            for field in module.fields:
                desc = f": {field.description}" if field.description else ""
                prompt += f"  * {field.name} ({field.type}){desc}\n"
                
        prompt += "\nEnsure the extracted JSON strictly matches the provided schema structure. Leave missing fields as null."
        return prompt
        
    def get_schema(self, doc_type: DocumentType) -> dict:
        """
        Dynamically constructs the JSON schema from the registry.
        """
        schema_def = schema_registry.get_schema(doc_type.value)
        if not schema_def:
            return {}
            
        properties = {}
        for module in schema_def.modules:
            for field in module.fields:
                if field.type == "array" and hasattr(field, "items") and field.items:
                    items_def = field.items
                    if isinstance(items_def, dict) and "properties" in items_def:
                        item_props = {prop["name"]: {"type": prop.get("type", "string")} for prop in items_def["properties"]}
                        properties[field.name] = {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": item_props
                            }
                        }
                    else:
                        properties[field.name] = {"type": "array", "items": {"type": "string"}}
                else:
                    properties[field.name] = {"type": field.type}
                    
        return {"type": "object", "properties": properties}

    def get_metadata(self, doc_type: DocumentType) -> dict:
        schema_def = schema_registry.get_schema(doc_type.value)
        if not schema_def:
            return {"version": "1.0.0"}
            
        return {
            "version": getattr(schema_def, "version", "1.0.0"),
            "author": "SchemaRegistry",
            "approval_status": "approved",
            "supported_document_types": [doc_type.value],
            "compatible_model_families": ["gpt-4", "claude-3"],
            "created_date": getattr(schema_def, "effective_date", None),
            "modified_date": getattr(schema_def, "effective_date", None)
        }

    def get_version(self, doc_type: DocumentType) -> str:
        return self.get_metadata(doc_type).get("version", "1.0.0")
