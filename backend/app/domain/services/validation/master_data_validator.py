import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

# Note: In production we'd use pg_trgm, but we'll use a basic ILIKE search here for compatibility without requiring postgres extension setup.
from app.infrastructure.database.models import MasterBuyer, MasterSupplier, MasterFabric, MasterUOM

logger = logging.getLogger(__name__)

class MasterDataValidator:
    """
    Validates extracted values against Postgres Master Data tables.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_cached_master_data(self, entity_type: str, query: str) -> List[Dict[str, Any]]:
        """
        Fetches master data directly from PostgreSQL.
        """
        model_map = {
            "supplier": MasterSupplier,
            "buyer": MasterBuyer,
            "fabric": MasterFabric,
            "uom": MasterUOM
        }
        
        model_class = model_map.get(entity_type)
        if not model_class:
            return []
            
        stmt = select(model_class).where(
            or_(
                model_class.name.ilike(f"%{query}%"),
                model_class.erp_reference_id.ilike(f"%{query}%")
            )
        ).limit(5)
        
        result = await self.db.execute(stmt)
        records = result.scalars().all()
        
        return [
            {
                "erp_id": rec.erp_reference_id,
                "name": rec.name,
                "aliases": rec.aliases or []
            }
            for rec in records
        ]

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
            "unit": "uom",
            "buyer": "buyer",
            "fabric": "fabric"
        }
        
        entity_type = entity_map.get(field_name.lower())
        if not entity_type:
            return {"status": "skipped", "reason": "no_master_data_mapping"}
            
        candidates = await self.get_cached_master_data(entity_type, extracted_value)
        
        if candidates:
            best_match = candidates[0]
            return {
                "status": "valid",
                "master_record_id": best_match["erp_id"],
                "matched_value": best_match["name"],
                "normalized_value": extracted_value,
                "match_score": 1.0, # Basic ILIKE matching
                "validation_method": "postgres_ilike"
            }
            
        return {
            "status": "invalid",
            "reason": "no_match_found",
            "normalized_value": extracted_value
        }
