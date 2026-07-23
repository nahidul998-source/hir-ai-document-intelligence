import os
import pytest
from unittest.mock import patch, AsyncMock

from ai.worker.pipeline.document_processor import DocumentProcessor
from app.infrastructure.adapters.ai_provider_manager import AIProviderManager

@pytest.fixture
async def manager():
    m = AIProviderManager()
    try:
        await m.initialize()
    except Exception:
        pass
    return m

@pytest.fixture
def processor(manager):
    return DocumentProcessor(manager)

@pytest.mark.asyncio
async def test_full_pipeline_invoice(processor, manager):
    processor.classifier.classify = AsyncMock(return_value={"document_type": "generic"})
    processor.validation_pipeline.run = AsyncMock(return_value={
        "validated_data": {"invoice_number": "INV-100"},
        "master_data_metadata": {},
        "business_rule_errors": [],
        "is_valid": True
    })
    processor.orchestrator.generate_json = AsyncMock(return_value={
        "data": {"invoice_number": "INV-100"},
        "provider": "local_qwen"
    })
    
    result = await processor.process_document("invoice_2024.pdf", "Invoice INV-100 Total $500")
    
    assert result["classifier_result"] == "generic"
    assert result["extracted_data"] == {"invoice_number": "INV-100"}
    assert result["is_business_valid"] is True

@pytest.mark.asyncio
async def test_full_pipeline_fallback(processor, manager):
    processor.classifier.classify = AsyncMock(return_value={"document_type": "purchase_order"})
    processor.validation_pipeline.run = AsyncMock(return_value={
        "validated_data": {"po_number": "PO-999"},
        "master_data_metadata": {},
        "business_rule_errors": [],
        "is_valid": True
    })
    processor.orchestrator.generate_json = AsyncMock(return_value={
        "data": {"po_number": "PO-999"},
        "provider": "github"
    })
    
    result = await processor.process_document("PO_123.pdf", "Purchase Order PO-999")
    
    assert result["classifier_result"] == "purchase_order"
    assert result["extracted_data"] == {"po_number": "PO-999"}
    assert result["is_business_valid"] is True
