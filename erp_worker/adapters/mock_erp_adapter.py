import logging
import asyncio
import uuid
from typing import Dict, Any, List

class MockERPAdapter:
    async def push_data(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy push method."""
        logging.info(f"MockERPAdapter: Pushing data for session {session_id} to ERP...")
        await asyncio.sleep(1)
        return {"erp_transaction_id": "ERP-987654321", "status": "success"}

    async def create_style(self, style_data: Dict[str, Any]) -> Dict[str, Any]:
        logging.info(f"MockERPAdapter: Creating Style {style_data.get('StyleID')}")
        await asyncio.sleep(0.5)
        return {
            "status": "success",
            "erp_style_id": f"ERP-STY-{str(uuid.uuid4())[:8].upper()}",
            "message": "Style successfully created in PLM."
        }

    async def create_bom(self, style_id: str, bom_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        logging.info(f"MockERPAdapter: Creating BOM for Style {style_id} with {len(bom_items)} items")
        await asyncio.sleep(1)
        return {
            "status": "success",
            "erp_bom_id": f"ERP-BOM-{str(uuid.uuid4())[:8].upper()}",
            "message": "BOM successfully created in PLM."
        }

    async def create_sales_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        po = order_data.get("PurchaseOrderNumber", "UNKNOWN")
        logging.info(f"MockERPAdapter: Creating Sales Order for PO {po}")
        await asyncio.sleep(1)
        return {
            "status": "success",
            "erp_order_id": f"ERP-SO-{str(uuid.uuid4())[:8].upper()}",
            "message": "Sales Order successfully created in ERP."
        }
