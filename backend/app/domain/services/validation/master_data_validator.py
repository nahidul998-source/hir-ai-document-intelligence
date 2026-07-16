import logging
from typing import Dict, Any, List
from .fuzzy_matcher import FuzzyMatcher

logger = logging.getLogger(__name__)

class MasterDataValidator:
    """
    Validates extracted values against local Master Data Cache.
    """
    def __init__(self, threshold: float = 0.85):
        self.matcher = FuzzyMatcher(threshold=threshold)
        
    async def get_cached_master_data(self, entity_type: str) -> List[Dict[str, Any]]:
        """
        Simulates fetching cached ERP data from Redis/Local DB.
        """
        # Mock data (this would actually query the md_* tables)
        if entity_type == "supplier":
            return [
                {"erp_id": "SUP-101", "name": "FastSew Ltd", "aliases": ["Fast Sew", "FastSew"]},
                {"erp_id": "SUP-102", "name": "Prime Textiles", "aliases": ["Prime", "PrimeTex"]}
            ]
        elif entity_type == "uom":
            return [
                {"erp_id": "UOM-PCS", "name": "Pieces", "aliases": ["pcs", "pieces", "pc"]},
                {"erp_id": "UOM-KGS", "name": "Kilograms", "aliases": ["kg", "kgs", "kilo"]}
            ]
        return []

    async def validate_field(self, field_name: str, extracted_value: Any) -> Dict[str, Any]:
        """
        Validates a single field. If valid, attaches validation metadata.
        """
        if not extracted_value or not isinstance(extracted_value, str):
            return {"status": "skipped", "reason": "non_string_value"}
            
        # Map field names to master data entity types (Configurable in real app)
        entity_map = {
            "supplier_name": "supplier",
            "factory": "supplier",
            "uom": "uom",
            "unit": "uom"
        }
        
        entity_type = entity_map.get(field_name.lower())
        if not entity_type:
            return {"status": "skipped", "reason": "no_master_data_mapping"}
            
        candidates = await self.get_cached_master_data(entity_type)
        match_result = self.matcher.match(extracted_value, candidates)
        
        if match_result:
            return {
                "status": "valid",
                "master_record_id": match_result["erp_id"],
                "matched_value": match_result["name"],
                "normalized_value": self.matcher.normalize(extracted_value),
                "match_score": match_result["match_score"],
                "validation_method": match_result["validation_method"]
            }
            
        return {
            "status": "invalid",
            "reason": "no_match_found",
            "normalized_value": self.matcher.normalize(extracted_value)
        }
