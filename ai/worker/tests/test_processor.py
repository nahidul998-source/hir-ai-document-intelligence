import pytest
from ai.worker.classifiers.document_classifier import DocumentClassifier, DocumentType
from ai.worker.prompt_registry.registry import PromptRegistry

def test_classifier():
    classifier = DocumentClassifier()
    # Test Tech Pack classification
    doc_type = classifier.classify("spring_2024_style_details.pdf", "technical package for new season")
    assert doc_type == DocumentType.TECH_PACK
    
    # Test Order Sheet
    doc_type = classifier.classify("PO_12345.pdf", "sales order qty 500")
    assert doc_type == DocumentType.ORDER_SHEET

def test_registry():
    registry = PromptRegistry()
    prompt = registry.get_prompt(DocumentType.TECH_PACK)
    assert "tech pack" in prompt.lower()
    
    schema = registry.get_schema(DocumentType.TECH_PACK)
    assert schema["type"] == "object"
    assert "style_number" in schema["properties"]
