import difflib
from typing import List, Tuple, Dict, Any, Optional

class FuzzyMatcher:
    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold

    def normalize(self, text: str) -> str:
        """Standardize text for comparison."""
        if not text:
            return ""
        return text.strip().lower()

    def match(self, target: str, candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Attempts to match `target` against a list of candidate dictionaries.
        Each candidate dict must have a 'name' and optional 'aliases' (List[str]).
        
        Returns the best matched candidate dict with added match metadata, or None.
        """
        if not target or not candidates:
            return None
            
        norm_target = self.normalize(target)
        best_match = None
        highest_score = 0.0
        
        for candidate in candidates:
            # Check exact name match
            norm_name = self.normalize(candidate.get("name", ""))
            if norm_target == norm_name:
                return {**candidate, "match_score": 1.0, "validation_method": "exact"}
            
            # Check exact alias match
            aliases = candidate.get("aliases", [])
            for alias in aliases:
                if norm_target == self.normalize(alias):
                    return {**candidate, "match_score": 1.0, "validation_method": "alias_exact"}
            
            # Fuzzy match name
            score = difflib.SequenceMatcher(None, norm_target, norm_name).ratio()
            if score > highest_score:
                highest_score = score
                best_match = {**candidate, "match_score": score, "validation_method": "fuzzy_name"}
            
            # Fuzzy match aliases
            for alias in aliases:
                alias_score = difflib.SequenceMatcher(None, norm_target, self.normalize(alias)).ratio()
                if alias_score > highest_score:
                    highest_score = alias_score
                    best_match = {**candidate, "match_score": alias_score, "validation_method": "fuzzy_alias"}
                    
        if highest_score >= self.threshold and best_match:
            return best_match
            
        return None
