from typing import Dict, Any
import json

class ERPPayloadBuilder:
    """
    Transforms review-approved data into structured ERP payloads.
    In a real system, this could load specific mappings per buyer or style.
    """
    @staticmethod
    def build_payload(document_type: str, approved_data: Dict[str, Any]) -> Dict[str, Any]:
        # Generic fallback schema
        payload = {
            "erp_module": "Unknown",
            "transaction_type": "CREATE",
            "data": approved_data
        }
        
        if document_type == "tech_pack":
            payload["erp_module"] = "ProductLifecycleManagement"
            payload["transaction_type"] = "CREATE_STYLE"
            
            # Map fields safely
            payload["data"] = {
                "StyleID": approved_data.get("style_number", "UNKNOWN"),
                "Season": approved_data.get("season", ""),
                "Brand": approved_data.get("brand", ""),
                "BillOfMaterials": approved_data.get("bom", []),
                "Measurements": approved_data.get("measurements", {})
            }
            
        elif document_type == "buyer_order":
            payload["erp_module"] = "SalesOrderManagement"
            payload["transaction_type"] = "CREATE_SALES_ORDER"
            
            payload["data"] = {
                "PurchaseOrderNumber": approved_data.get("po_number", ""),
                "BuyerID": approved_data.get("buyer", ""),
                "TotalQuantity": approved_data.get("total_quantity", 0),
                "OrderItems": approved_data.get("items", [])
            }
            
        return payload
