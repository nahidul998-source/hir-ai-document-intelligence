import logging
import asyncio
from typing import Dict, Any

class MockERPAdapter:
    async def push_data(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mocks pushing approved data to an ERP.
        Simulates network latency and potential failures.
        """
        logging.info(f"MockERPAdapter: Pushing data for session {session_id} to ERP...")
        await asyncio.sleep(1) # Simulate network delay
        
        # Simulate success response
        return {
            "erp_transaction_id": "ERP-987654321",
            "status": "success",
            "message": "Data successfully ingested into Merchandising Module",
            "record_count": len(payload.get("fields", []))
        }
