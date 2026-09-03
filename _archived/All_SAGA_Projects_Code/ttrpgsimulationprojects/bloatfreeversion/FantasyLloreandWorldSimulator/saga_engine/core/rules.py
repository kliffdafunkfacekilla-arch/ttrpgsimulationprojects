import json
import os
import re
from typing import Dict, List, Optional, Any

class RulesetManager:
    """
    The Agnostic Engine for RPG mechanics.
    Loads JSON schemas to define attributes, vitals, and resolution formulas.
    """
    
    def __init__(self, ruleset_path: str):
        self.ruleset_path = ruleset_path
        self.data: Dict[str, Any] = {}
        self.attributes: List[Dict] = []
        self.vitals: List[Dict] = []
        self.resolutions: Dict[str, str] = {}
        
    def load(self) -> bool:
        """Parses the ruleset JSON and indexes components."""
        if not os.path.exists(self.ruleset_path):
            print(f"[RULES ERROR] Ruleset not found: {self.ruleset_path}")
            return False
            
        try:
            with open(self.ruleset_path, "r") as f:
                self.data = json.load(f)
                
            self.attributes = self.data.get("attributes", [])
            self.vitals = self.data.get("vitals", [])
            self.resolutions = self.data.get("resolutions", {})
            
            print(f"[RULES] Switched to system: {self.data.get('system_name', 'Unknown')}")
            return True
        except Exception as e:
            print(f"[RULES ERROR] Failed to load ruleset: {e}")
            return False

    def calculate_vital(self, vital_id: str, stats: Dict[str, int]) -> int:
        """Evaluates a vital formula using the provided stats."""
        vital = next((v for v in self.vitals if v["id"] == vital_id), None)
        if not vital:
            return 0
            
        formula = vital.get("formula", "0")
        
        # Simple evaluation logic (replaces stat names with values)
        # Note: In a production environment, we would use a safer parser.
        # For S.A.G.A. Brain, we'll use a regex replacement and literal_eval or similar.
        processed_formula = formula
        for attr_id, value in stats.items():
            # Replace whole words only to avoid partial matches (e.g., 'str' in 'strength')
            processed_formula = re.sub(rf'\b{attr_id}\b', str(value), processed_formula)
            
        # Add support for 'mod' logic if needed
        # e.g. str_mod = (str - 10) // 2
        for attr_id, value in stats.items():
            mod_val = (value - 10) // 2
            processed_formula = re.sub(rf'\b{attr_id}_mod\b', str(mod_val), processed_formula)

        try:
            # We use a safe eval-like approach for basic math
            # Only allow arithmetic characters
            if not re.match(r'^[0-9+\-*/().\s]+$', processed_formula):
                return 0
            return int(eval(processed_formula))
        except:
            return 0

    def get_attribute_names(self) -> Dict[str, str]:
        """Returns a mapping of ID -> Human Name for UI labels."""
        return {a["id"]: a["name"] for a in self.attributes}

    def get_default_stats(self) -> Dict[str, int]:
        """Returns a base stat block (all zeros or defined defaults)."""
        return {a["id"]: 0 for a in self.attributes}
