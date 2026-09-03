import random
from typing import Dict, List, Optional
from saga_engine.core.state import CampaignState

class EntityForger:
    """
    The 'Blacksmith' and 'Recruiter' of the S.A.G.A. Brain.
    Generates NPCs and Items using the active system-agnostic ruleset.
    """
    
    def __init__(self, state: CampaignState, ruleset: Dict = None):
        self.state = state
        self.ruleset = ruleset or {}

    def forge_npc(self, archetype_id: str, threat_level: int = 1) -> Dict:
        """
        Builds a complete NPC character sheet using the ruleset's stats.
        """
        # 1. Get stats from ruleset (e.g., Might, Finesse, etc.)
        stat_keys = self.ruleset.get("primary_stats", ["Attribute1", "Attribute2"])
        stats = {}
        for key in stat_keys:
            # Base 10 + random offset scaled by threat
            stats[key] = 10 + random.randint(-2, 2) + (threat_level // 2)
            
        # 2. Derive Vitals using ruleset formulas if applicable
        hp_formula = self.ruleset.get("vitals_formulas", {}).get("hp", "Attribute1 + 20")
        # Simplified parser: just uses the first stat for now in this demo
        hp = stats.get(stat_keys[0], 10) + 20 + (threat_level * 5)
        
        npc = {
            "id": f"NPC_{random.randint(100, 999)}",
            "archetype": archetype_id,
            "threat_level": threat_level,
            "stats": stats,
            "vitals": {"hp": hp, "max_hp": hp},
            "inventory": self._generate_npc_loot(threat_level),
            "status": "Active"
        }
        return npc

    def forge_item(self, category_id: str, quality_level: int = 1) -> Dict:
        """
        Generates a procedural item based on the ruleset's categories.
        """
        item_names = {
            "WEAPON": ["Jagged Blade", "Heavy Maul", "Polished Spear"],
            "ARMOR": ["Leather Wraps", "Scrap Plate", "Reinforced Tunic"],
            "UTILITY": ["Flare", "Scrapper's Kit", "Stim-Injector"]
        }
        
        base_name = random.choice(item_names.get(category_id, ["Odd Relic"]))
        
        # Pull traits from ruleset if available
        traits = self.ruleset.get("item_traits", {}).get(category_id, ["Standard"])
        active_trait = random.choice(traits)
        
        item = {
            "id": f"ITM_{random.randint(1000, 9999)}",
            "name": f"{active_trait} {base_name}",
            "category": category_id,
            "quality": quality_level,
            "stats": {
                "power": quality_level * 2,
                "weight": random.uniform(0.5, 5.0)
            },
            "tags": [active_trait, category_id]
        }
        return item

    def _generate_npc_loot(self, threat: int) -> List[Dict]:
        """Generates random loot for NPCs."""
        loot = []
        if random.random() > 0.5:
            loot.append(self.forge_item("UTILITY", 1))
        return loot
