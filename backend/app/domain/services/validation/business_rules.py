from typing import Dict, Any, List

class BusinessRulesValidator:
    """
    Validates garment-specific business rules.
    """
    
    def validate(self, document_type: str, extracted_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Executes business rules against the entire extracted payload.
        Returns a list of validation errors/warnings.
        """
        errors = []
        
        # 1. Required fields by Document Type
        if document_type == "TechPack":
            if "fabrics" not in extracted_data or not extracted_data["fabrics"]:
                errors.append({
                    "field": "fabrics",
                    "severity": "high",
                    "message": "Tech Packs must contain at least one fabric definition."
                })
                
        # 2. Logic Validation (e.g. Quantity Math)
        if "order_lines" in extracted_data:
            total_qty = extracted_data.get("total_quantity", 0)
            calculated_qty = sum(line.get("quantity", 0) for line in extracted_data["order_lines"])
            
            if total_qty != calculated_qty:
                errors.append({
                    "field": "total_quantity",
                    "severity": "high",
                    "message": f"Total quantity ({total_qty}) does not match sum of order lines ({calculated_qty})."
                })
                
        # 3. Currency / Incoterms Logic
        incoterm = extracted_data.get("incoterm", "").upper()
        if incoterm in ["FOB", "CIF"] and "port_of_loading" not in extracted_data:
            errors.append({
                "field": "port_of_loading",
                "severity": "medium",
                "message": f"Incoterm {incoterm} requires a Port of Loading."
            })
            
        return errors
