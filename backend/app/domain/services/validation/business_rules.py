from typing import Dict, Any, List

class BusinessRulesValidator:
    """
    Validates garment-specific business rules dynamically based on document type.
    """
    
    def validate(self, document_type: str, extracted_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Executes business rules against the entire extracted payload.
        Returns a list of validation errors/warnings.
        """
        errors = []
        
        # 1. TechPack Rules
        if document_type == "tech_pack":
            if "fabrics" not in extracted_data or not extracted_data["fabrics"]:
                errors.append({
                    "field": "fabrics",
                    "severity": "high",
                    "message": "Tech Packs must contain at least one fabric definition."
                })
            
            # Measurement tolerance check
            if "measurements" in extracted_data:
                for idx, m in enumerate(extracted_data["measurements"]):
                    if "value" in m and "tolerance" in m:
                        if m["tolerance"] and float(m["tolerance"]) > (float(m["value"]) * 0.1):
                            errors.append({
                                "field": f"measurements[{idx}].tolerance",
                                "severity": "medium",
                                "message": f"Tolerance ({m['tolerance']}) is suspiciously large for value ({m['value']})."
                            })
                
        # 2. Order Sheet Rules
        if document_type == "order_sheet":
            if "order_lines" in extracted_data:
                total_qty = extracted_data.get("total_quantity", 0)
                calculated_qty = sum(line.get("quantity", 0) for line in extracted_data["order_lines"] if isinstance(line, dict))
                
                if total_qty and float(total_qty) != float(calculated_qty):
                    errors.append({
                        "field": "total_quantity",
                        "severity": "high",
                        "message": f"Total quantity ({total_qty}) does not match sum of order lines ({calculated_qty})."
                    })
                    
        # 3. Universal Incoterms Logic
        incoterm = extracted_data.get("incoterm", "").upper()
        if incoterm in ["FOB", "CIF", "CFR"] and not extracted_data.get("port_of_loading"):
            errors.append({
                "field": "port_of_loading",
                "severity": "medium",
                "message": f"Incoterm {incoterm} requires a Port of Loading."
            })
            
        return errors
