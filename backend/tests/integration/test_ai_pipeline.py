import os
import pytest
from unittest.mock import patch, AsyncMock

from ai.worker.pipeline.document_processor import DocumentProcessor
from app.infrastructure.adapters.ai_provider_manager import AIProviderManager

@pytest.fixture
def manager():
    test_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(test_dir, "../../../configs/ai.yaml")
    return AIProviderManager(config_path)

@pytest.fixture
def processor(manager):
    return DocumentProcessor(manager)

@pytest.mark.asyncio
async def test_full_pipeline_invoice(processor, manager):
    # Mock ValidationPipeline to return valid result
    processor.validation_pipeline.run = AsyncMock(return_value={
        "validated_data": {"invoice_number": "INV-100"},
        "master_data_metadata": {},
        "business_rule_errors": [],
        "is_valid": True
    })
    
    # Mock provider generation
    with patch("app.infrastructure.adapters.providers.openai_provider.LocalOpenAIProvider.generate_json", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = {"invoice_number": "INV-100"}
        
        # Also mock health check so we use local provider
        with patch("app.infrastructure.adapters.providers.openai_provider.LocalOpenAIProvider.is_healthy", new_callable=AsyncMock) as mock_health:
            mock_health.return_value = True
            
            result = await processor.process_document("invoice_2024.pdf", "Invoice INV-100 Total $500")
            
            assert result["classifier_result"] == "generic"
            assert result["extracted_data"] == {"invoice_number": "INV-100"}
            assert result["is_business_valid"] is True
            assert result["metrics"]["provider_name"] == "local_qwen"

@pytest.mark.asyncio
async def test_full_pipeline_fallback(processor, manager):
    processor.validation_pipeline.run = AsyncMock(return_value={
        "validated_data": {"po_number": "PO-999"},
        "master_data_metadata": {},
        "business_rule_errors": [],
        "is_valid": True
    })
    
    # Local provider is unhealthy, github provider is healthy
    async def mock_health(self):
        return self.name == "github"
        
    async def mock_generate(self, *args, **kwargs):
        if self.name == "github":
            return {"po_number": "PO-999"}
        raise RuntimeError("Failed")

    with patch("app.infrastructure.adapters.providers.openai_provider.LocalOpenAIProvider.is_healthy", side_effect=mock_health, autospec=True):
        with patch("app.infrastructure.adapters.providers.openai_provider.LocalOpenAIProvider.generate_json", side_effect=mock_generate, autospec=True):
            
            result = await processor.process_document("PO_123.pdf", "Purchase Order PO-999")
            
            assert result["classifier_result"] == "purchase_order"
            assert result["extracted_data"] == {"po_number": "PO-999"}
            assert result["is_business_valid"] is True
            assert result["metrics"]["provider_name"] == "github"
