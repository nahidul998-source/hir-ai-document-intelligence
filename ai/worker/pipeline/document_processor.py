import os
import json
import logging
from typing import Dict, Any

from ai.worker.classifiers.document_classifier import DocumentClassifier, DocumentType
from ai.worker.prompt_registry.registry import PromptRegistry
from ai.worker.confidence.engine import ConfidenceEngine
from ai.worker.validators.json_validator import JSONValidator
from ai.worker.metrics.tracker import MetricsTracker

# The AI worker needs to import AIProviderManager from the backend. 
# PYTHONPATH must be set appropriately when running.
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend")))
from app.infrastructure.adapters.ai_provider_manager import AIProviderManager
from app.domain.services.validation.pipeline import ValidationPipeline

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, ai_provider_manager: AIProviderManager):
        self.classifier = DocumentClassifier()
        self.registry = PromptRegistry()
        self.confidence_engine = ConfidenceEngine()
        self.validator = JSONValidator()
        self.ai_provider = ai_provider_manager
        self.validation_pipeline = ValidationPipeline()
        
    async def process_document(self, filename: str, first_page_text: str = "") -> Dict[str, Any]:
        """
        Executes the Document Intelligence Pipeline.
        """
        metrics = MetricsTracker()
        metrics.start()
        
        # 1. Classification
        logger.info(f"Classifying document: {filename}")
        doc_type = self.classifier.classify(filename, first_page_text)
        
        # 2. Extract Text & Layout (Simulated for this phase without actual Docling/OCR models loaded)
        metrics.start_ocr()
        # Simulated extraction result
        simulated_text = first_page_text or "Simulated document content"
        metrics.end_ocr()
        
        # 3. Retrieve Prompt & Schema
        prompt_text = self.registry.get_prompt(doc_type)
        schema = self.registry.get_schema(doc_type)
        
        # 4. AI Provider Extraction
        system_prompt = "You are an expert Garment Merchandiser AI."
        full_prompt = f"{prompt_text}\n\nDocument Text:\n{simulated_text}"
        
        logger.info(f"Extracting JSON via AI Provider Manager for type {doc_type.value}")
        provider = await self.ai_provider.get_active_provider()
        metrics.start_llm(provider.name)
        
        try:
            extracted_json = await self.ai_provider.generate_json(
                prompt=full_prompt, 
                schema=schema, 
                system_prompt=system_prompt
            )
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            extracted_json = {}
            
        metrics.end_llm(tokens=len(full_prompt.split()))
        
        # 5. Validation (Schema)
        is_schema_valid, validation_msg = self.validator.validate_schema(extracted_json, schema)
        logger.info(f"JSON Validation: {is_schema_valid} - {validation_msg}")
        
        # 6. Enterprise Validation Engine (Master Data & Business Rules)
        enterprise_validation_result = await self.validation_pipeline.run(doc_type.value, extracted_json)
        
        # 7. Confidence Scoring
        confidence_metadata = self.confidence_engine.evaluate(
            extracted_data=enterprise_validation_result["validated_data"],
            ocr_data=None,
            provider=metrics.provider
        )
        
        # Gather Results
        return {
            "classifier_result": doc_type.value,
            "extracted_data": enterprise_validation_result["validated_data"],
            "confidence_metadata": confidence_metadata,
            "master_data_metadata": enterprise_validation_result["master_data_metadata"],
            "business_rule_errors": enterprise_validation_result["business_rule_errors"],
            "metrics": metrics.get_metrics(),
            "is_schema_valid": is_schema_valid,
            "is_business_valid": enterprise_validation_result["is_valid"],
            "validation_message": validation_msg
        }
