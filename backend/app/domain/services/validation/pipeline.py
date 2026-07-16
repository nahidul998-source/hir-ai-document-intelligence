import logging
from typing import Dict, Any
from .master_data_validator import MasterDataValidator
from .business_rules import BusinessRulesValidator

logger = logging.getLogger(__name__)

class ValidationPipeline:
    """
    Orchestrates the Enterprise Validation Engine:
    1. Schema Validation (assumed done via LLM strict JSON prior to this)
    2. Master Data Validation (Fuzzy Matching against ERP Cache)
    3. Business Rules Validation (Garment logic)
    """
    def __init__(self):
        self.mdv = MasterDataValidator()
        self.brv = BusinessRulesValidator()
        
    async def run(self, document_type: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the pipeline and enriches the data with validation metadata.
        """
        logger.info(f"Starting Validation Pipeline for {document_type}")
        
        enriched_data = extracted_data.copy()
        validation_metadata = {}
        
        # Step 1: Master Data Validation
        for key, value in extracted_data.items():
            if isinstance(value, str):
                md_result = await self.mdv.validate_field(key, value)
                if md_result.get("status") != "skipped":
                    validation_metadata[key] = md_result
                    
            elif isinstance(value, list):
                # E.g. array of order lines
                for idx, item in enumerate(value):
                    if isinstance(item, dict):
                        for sub_key, sub_value in item.items():
                            if isinstance(sub_value, str):
                                md_result = await self.mdv.validate_field(sub_key, sub_value)
                                if md_result.get("status") != "skipped":
                                    validation_metadata[f"{key}[{idx}].{sub_key}"] = md_result

        # Step 2: Business Rules Validation
        br_errors = self.brv.validate(document_type, extracted_data)
        
        # Final Output Payload
        return {
            "validated_data": enriched_data,
            "master_data_metadata": validation_metadata,
            "business_rule_errors": br_errors,
            "is_valid": len(br_errors) == 0 and all(m.get("status") == "valid" for m in validation_metadata.values())
        }
