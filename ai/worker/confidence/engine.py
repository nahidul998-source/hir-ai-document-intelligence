import re
from typing import Dict, Any
from difflib import SequenceMatcher

class ConfidenceEngine:
    """
    Evaluates confidence of extracted fields dynamically by comparing against raw OCR payload.
    """
    
    def __init__(self):
        pass

    def _calculate_fuzzy_score(self, extracted_str: str, ocr_text: str) -> float:
        """
        Calculates a confidence score by checking if the extracted string exists in the OCR text.
        Returns 1.0 for exact matches, and a fuzzy score for partial matches.
        """
        extracted_str = str(extracted_str).lower().strip()
        ocr_text = ocr_text.lower()
        
        # Exact match check
        if extracted_str in ocr_text:
            return 1.0
            
        # If it's a number, it must be exact. If not found, hallucination risk.
        if extracted_str.replace('.', '', 1).isdigit():
            return 0.4
            
        # Fuzzy match logic for text
        best_score = 0.0
        words = extracted_str.split()
        if not words:
            return 0.0
            
        # Check token presence
        found_tokens = sum(1 for w in words if w in ocr_text)
        token_ratio = found_tokens / len(words)
        
        # Compute SequenceMatcher ratio against a sliding window (expensive, so we just use token ratio)
        return round(0.5 + (token_ratio * 0.4), 2) # Base 0.5 + up to 0.4 based on token presence

    def evaluate(self, extracted_data: dict, ocr_text: str = "", provider: str = "unknown", layout_blocks: list = None) -> Dict[str, Any]:
        """
        Creates confidence metadata for each field in the extracted data.
        Maps the field to the source bounding box if found in layout_blocks.
        """
        metadata = {}
        layout_blocks = layout_blocks or []
        
        def _find_bbox(value_str: str) -> tuple:
            if not value_str or not layout_blocks:
                return [0, 0, 0, 0], 1
            value_str = value_str.lower()
            best_block = None
            for b in layout_blocks:
                b_text = str(b.get("text", "")).lower()
                if value_str in b_text or (len(value_str)>3 and value_str in b_text):
                    return b.get("bbox", [0, 0, 0, 0]), b.get("page", 1)
            return [0, 0, 0, 0], 1
        
        # Flatten extracted data for processing
        def _flatten_and_evaluate(data: Any, prefix: str = ""):
            if isinstance(data, dict):
                for k, v in data.items():
                    _flatten_and_evaluate(v, f"{prefix}{k}.")
            elif isinstance(data, list):
                for idx, v in enumerate(data):
                    _flatten_and_evaluate(v, f"{prefix}[{idx}].")
            else:
                key = prefix.rstrip('.')
                if data:
                    str_val = str(data)
                    score = self._calculate_fuzzy_score(str_val, ocr_text)
                    bbox, page = _find_bbox(str_val)
                    metadata[key] = {
                        "value": data,
                        "confidence_score": score,
                        "source_page": page,
                        "bounding_box": bbox,
                        "provider": provider,
                        "validation_status": "valid" if score > 0.6 else "review_required"
                    }
                else:
                    metadata[key] = {
                        "value": data,
                        "confidence_score": 0.0,
                        "source_page": 1,
                        "bounding_box": [0,0,0,0],
                        "provider": provider,
                        "validation_status": "missing"
                    }
                    
        _flatten_and_evaluate(extracted_data)
        return metadata
