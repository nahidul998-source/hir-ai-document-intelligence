import sys
import os
import uuid
import json
import logging
from typing import Dict, Any, Optional

from ai.worker.classifiers.document_classifier import DocumentClassifier, DocumentType
from ai.worker.prompt_registry.registry import PromptRegistry
from ai.worker.confidence.engine import ConfidenceEngine
from ai.worker.validators.json_validator import JSONValidator
from ai.worker.metrics.tracker import MetricsTracker

# The AI worker needs to import AIProviderManager from the backend. 
# PYTHONPATH must be set appropriately when running.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend")))
from app.infrastructure.adapters.ai_provider_manager import AIProviderManager
from app.application.services.ai.orchestrator import AIOrchestrator
from app.domain.services.validation.pipeline import ValidationPipeline

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, ai_provider_manager: AIProviderManager):
        self.classifier = DocumentClassifier()
        self.registry = PromptRegistry()
        self.confidence_engine = ConfidenceEngine()
        self.validator = JSONValidator()
        self.ai_provider = ai_provider_manager
        self.orchestrator = AIOrchestrator(ai_provider_manager)
        self.validation_pipeline = ValidationPipeline()
        
    async def process_document(
        self, 
        filename: str, 
        first_page_text: str = "", 
        trace_id: Optional[str] = None, 
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the Document Intelligence Pipeline.
        """
        metrics = MetricsTracker()
        metrics.start()
        
        request_id = str(uuid.uuid4())
        trace_id = trace_id or str(uuid.uuid4())
        correlation_id = correlation_id or str(uuid.uuid4())
        
        # 1. Classification
        logger.info(f"Classifying document: {filename} (Trace: {trace_id})")
        doc_type = self.classifier.classify(filename, first_page_text)
        
        # 2. Extract Text & Layout (Simulated for this phase without actual Docling/OCR models loaded)
        metrics.start_ocr()
        simulated_text = first_page_text or "Simulated document content"
        metrics.end_ocr()
        
        # 3. Retrieve Prompt & Schema & Metadata
        prompt_text = self.registry.get_prompt(doc_type)
        schema = self.registry.get_schema(doc_type)
        prompt_meta = self.registry.get_metadata(doc_type)
        prompt_version = prompt_meta.get("version", "1.0.0")
        
        # 4. AI Provider Extraction via Orchestrator
        system_prompt = "You are an expert Garment Merchandiser AI."
        full_prompt = f"{prompt_text}\n\nDocument Text:\n{simulated_text}"
        
        logger.info(f"Extracting JSON via AI Orchestrator for type {doc_type.value} (Trace: {trace_id})")
        
        provider_name = "unknown"
        model_name = "unknown"
        fallback_count = 0
        latency_ms = 0
        extracted_json = {}
        
        try:
            orch_res = await self.orchestrator.generate_json(
                prompt=full_prompt,
                schema=schema,
                document_type=doc_type.value,
                system_prompt=system_prompt,
                trace_id=trace_id,
                correlation_id=correlation_id
            )
            extracted_json = orch_res["data"]
            provider_name = orch_res["provider"]
            model_name = orch_res["model"]
            fallback_count = orch_res["fallback_count"]
            latency_ms = orch_res["latency_ms"]
        except Exception as e:
            logger.error(f"Extraction failed via AI Orchestrator: {str(e)} (Trace: {trace_id})")
            extracted_json = {}
            
        metrics.start_llm(provider_name)
        # Update metrics duration with the orchestrator latency
        metrics.llm_duration = int(latency_ms)
        metrics.end_llm(tokens=len(full_prompt.split()))
        
        # 5. Validation (Schema)
        is_schema_valid, validation_msg = self.validator.validate_schema(extracted_json, schema)
        
        # 6. Pydantic Static Validation
        is_pydantic_valid = False
        pydantic_msg = "Skipped"
        if is_schema_valid and extracted_json:
            is_pydantic_valid, pydantic_msg = self.validator.validate_pydantic(extracted_json, doc_type.value)
        
        logger.info(
            f"JSON Validation | Schema: {is_schema_valid} ({validation_msg}) | "
            f"Pydantic: {is_pydantic_valid} ({pydantic_msg}) (Trace: {trace_id})"
        )
        
        # 7. Enterprise Validation Engine (Master Data & Business Rules)
        enterprise_validation_result = await self.validation_pipeline.run(doc_type.value, extracted_json)
        
        # 8. Confidence Scoring
        confidence_metadata = self.confidence_engine.evaluate(
            extracted_data=enterprise_validation_result["validated_data"],
            ocr_data=None,
            provider=metrics.provider
        )
        
        # Extended structured logging requirement
        log_payload = {
            "request_id": request_id,
            "trace_id": trace_id,
            "correlation_id": correlation_id,
            "provider": provider_name,
            "model": model_name,
            "document_type": doc_type.value,
            "prompt_version": prompt_version,
            "retry_count": self.ai_provider.metrics.get(provider_name, {}).get("retry_count", 0) if provider_name != "unknown" else 0,
            "fallback_status": "triggered" if fallback_count > 0 else "none",
            "fallback_count": fallback_count,
            "latency": latency_ms,
            "validation_result": "SUCCESS" if (is_schema_valid and is_pydantic_valid and enterprise_validation_result["is_valid"]) else "FAILED",
            "schema_valid": is_schema_valid,
            "pydantic_valid": is_pydantic_valid,
            "business_valid": enterprise_validation_result["is_valid"]
        }
        logger.info(f"AI_REQUEST_METRICS: {json.dumps(log_payload)}")
        
        # Gather Results
        return {
            "classifier_result": doc_type.value,
            "extracted_data": enterprise_validation_result["validated_data"],
            "confidence_metadata": confidence_metadata,
            "master_data_metadata": enterprise_validation_result["master_data_metadata"],
            "business_rule_errors": enterprise_validation_result["business_rule_errors"],
            "metrics": metrics.get_metrics(),
            "is_schema_valid": is_schema_valid,
            "is_pydantic_valid": is_pydantic_valid,
            "is_business_valid": enterprise_validation_result["is_valid"],
            "validation_message": f"Schema: {validation_msg}. Pydantic: {pydantic_msg}"
        }
