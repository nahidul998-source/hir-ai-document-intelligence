from typing import Dict, Any, List

class GarmentKnowledgeEngine:
    """
    Applies deep merchandising logic to validate and derive garment parameters.
    """
    
    @staticmethod
    def evaluate(document_type: str, extracted_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        insights = []
        
        if document_type == "tech_pack":
            insights.extend(GarmentKnowledgeEngine._evaluate_tech_pack(extracted_data))
        elif document_type == "buyer_order" or document_type == "order_sheet":
            insights.extend(GarmentKnowledgeEngine._evaluate_buyer_order(extracted_data))
            
        return insights
        
    @staticmethod
    def _evaluate_tech_pack(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        insights = []
        
        # 1. BOM Completeness Check
        bom = data.get("bom", [])
        if not isinstance(bom, list):
            bom = []
            
        has_fabric = any("fabric" in str(item.get("item_type", "")).lower() for item in bom)
        has_thread = any("thread" in str(item.get("item_type", "")).lower() for item in bom)
        has_label = any("label" in str(item.get("item_type", "")).lower() for item in bom)
        
        if not has_fabric:
            insights.append({"field": "bom", "severity": "high", "message": "BOM is missing Main Fabric."})
        if not has_thread:
            insights.append({"field": "bom", "severity": "medium", "message": "BOM is missing Sewing Thread."})
        if not has_label:
            insights.append({"field": "bom", "severity": "medium", "message": "BOM is missing Main Label."})
            
        # 2. Fabric GSM Validation
        for idx, item in enumerate(bom):
            item_desc = str(item.get("description", "")).lower()
            gsm_str = str(item.get("gsm", "")).replace("gsm", "").strip()
            
            if gsm_str.isdigit():
                gsm = int(gsm_str)
                if "jersey" in item_desc and (gsm < 120 or gsm > 250):
                    insights.append({"field": f"bom[{idx}].gsm", "severity": "high", "message": f"GSM {gsm} is outside standard range (120-250) for Single Jersey."})
                if "denim" in item_desc and gsm < 200:
                    insights.append({"field": f"bom[{idx}].gsm", "severity": "high", "message": f"GSM {gsm} is unusually low for Denim (expected > 200)."})
                    
        # 3. Fabric Consumption Derivation (Marker Yield)
        for idx, item in enumerate(bom):
            cutable_width = item.get("cutable_width")
            marker_length = item.get("marker_length")
            consumption = item.get("consumption")
            
            # If consumption is missing but we have width and length (in meters)
            if not consumption and cutable_width and marker_length:
                try:
                    w = float(cutable_width)
                    l = float(marker_length)
                    # Rough square meter calculation
                    derived_cons = (w * l) / 10000 if w > 100 else (w * l)
                    insights.append({"field": f"bom[{idx}].consumption", "severity": "info", "message": f"Derived Consumption: ~{derived_cons:.2f} based on Yield."})
                except Exception:
                    pass
                    
        return insights
        
    @staticmethod
    def _evaluate_buyer_order(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        insights = []
        
        # 1. Size Ratio validation
        items = data.get("items", [])
        if not isinstance(items, list):
            items = []
            
        for idx, item in enumerate(items):
            total_qty = item.get("quantity", 0)
            breakdown = item.get("size_breakdown", {})
            
            if isinstance(breakdown, dict) and breakdown:
                sum_sizes = sum(int(v) for v in breakdown.values() if str(v).isdigit())
                if sum_sizes > 0 and sum_sizes != int(total_qty):
                    insights.append({
                        "field": f"items[{idx}].size_breakdown",
                        "severity": "high",
                        "message": f"Size ratio sum ({sum_sizes}) does not match line total quantity ({total_qty})."
                    })
                    
        return insights
