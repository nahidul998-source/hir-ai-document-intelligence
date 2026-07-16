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
