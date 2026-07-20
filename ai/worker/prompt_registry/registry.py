import yaml
from pathlib import Path
from typing import Dict, Any
from ai.worker.classifiers.document_classifier import DocumentType

class PromptRegistry:
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(__file__).parent / templates_dir
        self.templates: Dict[str, Dict[str, Any]] = {}
        self.load_templates()

    def load_templates(self):
        if not self.templates_dir.exists():
            self.templates_dir.mkdir(parents=True, exist_ok=True)
            return
            
        for template_file in self.templates_dir.glob("*.yaml"):
            with open(template_file, "r") as f:
                content = yaml.safe_load(f)
                self.templates[template_file.stem] = content

    def get_prompt(self, doc_type: DocumentType) -> str:
        template = self.templates.get(doc_type.value)
        if not template:
            # Fallback to generic
            template = self.templates.get(DocumentType.GENERIC.value)
            
        if not template:
            return "Extract all available information into a structured JSON format."
            
        return template.get("prompt_text", "")
        
    def get_schema(self, doc_type: DocumentType) -> dict:
        template = self.templates.get(doc_type.value)
        if not template:
            template = self.templates.get(DocumentType.GENERIC.value)
            
        if not template:
            return {}
            
        return template.get("output_schema", {})

    def get_metadata(self, doc_type: DocumentType) -> dict:
        template = self.templates.get(doc_type.value)
        if not template:
            template = self.templates.get(DocumentType.GENERIC.value)
        if not template:
            return {}
        return {
            "version": template.get("version", "1.0.0"),
            "author": template.get("author", "System"),
            "approval_status": template.get("approval_status", "approved"),
            "supported_document_types": template.get("supported_document_types", [doc_type.value]),
            "compatible_model_families": template.get("compatible_model_families", []),
            "created_date": template.get("created_date", "2026-07-20"),
            "modified_date": template.get("modified_date", "2026-07-20")
        }

    def get_version(self, doc_type: DocumentType) -> str:
        return self.get_metadata(doc_type).get("version", "1.0.0")
