import pytest
from ai.worker.classifiers.document_classifier import DocumentClassifier, DocumentType
from ai.worker.prompt_registry.registry import PromptRegistry

@pytest.mark.asyncio
async def test_classifier():
    classifier = DocumentClassifier()
    # Test Tech Pack classification
    res = await classifier.classify("spring_2024_style_details.pdf", "technical package for new season")
    assert res["document_type"] == DocumentType.TECH_PACK.value
    
    # Test Order Sheet
    res = await classifier.classify("PO_12345.pdf", "sales order qty 500")
    assert res["document_type"] in [DocumentType.ORDER_SHEET.value, DocumentType.TECH_PACK.value]

def test_registry():
    registry = PromptRegistry()
    prompt = registry.get_prompt(DocumentType.TECH_PACK)
    assert "tech pack" in prompt.lower()
    
    schema = registry.get_schema(DocumentType.TECH_PACK)
    assert schema["type"] == "object"
    assert "style_number" in schema["properties"]
