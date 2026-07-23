import json
import logging
import httpx
import os

class WebhookERPAdapter:
    """
    Adapter to post approved review sessions to a webhook endpoint representing an ERP system.
    """
    def __init__(self):
        self.erp_url = os.environ.get("ERP_WEBHOOK_URL", "http://localhost:8080/erp-webhook")
        
    async def push_approved_data(self, session_id: str, payload: dict) -> dict:
        """
        Pushes approved document data to an ERP webhook.
        """
        logging.info(f"WebhookERPAdapter: Pushing data for session {session_id} to ERP at {self.erp_url}...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.erp_url,
                    json=payload
                )
                
                # We don't raise_for_status here as we might just want to log failure if the endpoint isn't up
                # but in production we'd want to handle retries via RabbitMQ DLQ.
                if response.status_code >= 400:
                    logging.warning(f"WebhookERPAdapter: ERP responded with {response.status_code}: {response.text}")
                    return {"status": "failed", "reason": f"HTTP {response.status_code}"}
                    
                logging.info(f"WebhookERPAdapter: Successfully pushed session {session_id}")
                return {"status": "success", "erp_response": response.text}
                
        except Exception as e:
            logging.error(f"WebhookERPAdapter: Failed to push to ERP webhook: {e}")
            return {"status": "failed", "reason": str(e)}

    async def create_style(self, data: dict) -> dict:
        logging.info(f"WebhookERPAdapter: Creating Style")
        return await self.push_approved_data("CREATE_STYLE", data)
        
    async def create_bom(self, style_id: str, bom_items: list) -> dict:
        logging.info(f"WebhookERPAdapter: Creating BOM for style {style_id}")
        return await self.push_approved_data("CREATE_BOM", {"style_id": style_id, "items": bom_items})
        
    async def create_sales_order(self, data: dict) -> dict:
        logging.info(f"WebhookERPAdapter: Creating Sales Order")
        return await self.push_approved_data("CREATE_SALES_ORDER", data)
        
    async def push_data(self, session_id: str, payload: dict) -> dict:
        logging.info(f"WebhookERPAdapter: Pushing legacy data for session {session_id}")
        return await self.push_approved_data(session_id, payload)

    def transform_to_erp_format(self, raw_data: dict) -> dict:
        """
        Transforms internal data format to ERP-specific format.
        """
        logging.info("WebhookERPAdapter: Transforming payload to ERP format.")
        # Minimal transformation - just pass through for now
        return {
            "source": "hir_ai_pipeline",
            "data": raw_data
        }
