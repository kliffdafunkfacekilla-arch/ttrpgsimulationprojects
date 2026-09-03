import random
import math
from typing import Dict, List, Tuple, Optional

class RegionalGenerator:
    """
    The 'Zoom Lens' of the S.A.G.A. Brain.
    Turns a single Macro-Hex into a detailed 32x32 Local Grid.
    """
    
    def __init__(self, biome_manifest: Dict[int, str] = None):
        self.biome_manifest = biome_manifest or {
            0: "Ocean", 1: "Tundra", 2: "Grassland", 3: "Forest", 
            4: "Desert", 5: "Mountains", 6: "Swamp", 7: "Hills", 
            8: "Wasteland", 9: "Mass Zone", 10: "Ordo Zone", 
            11: "Motus Zone", 12: "Flux Zone"
        }

    def generate_local_context(self, macro_hex: Dict) -> Dict:
        """
        Creates a high-resolution local context based on macro-data.
        Macro-Hex keys: biome_id, height, faction_id, q, r
        """
        seed = f"{macro_hex['q']}_{macro_hex['r']}"
        random.seed(seed)
        
        biome_name = self.biome_manifest.get(macro_hex['biome_id'], "Unknown")
        base_height = macro_hex.get("height", 0.5)
        
        # 1. Generate 32x32 Micro-Map (Simplified as a grid of features)
        # We don't store 1024 tiles unless requested; we store "Area of Interest" (AOI)
        grid_size = 32
        points_of_interest = self._spawn_pois(biome_name, macro_hex)
        
        # 2. Distill the 'Vibe' (Environmental Factors)
        vibe = self._get_environmental_vibe(biome_name, base_height)
        
        return {
            "macro_coord": [macro_hex['q'], macro_hex['r']],
            "biome": biome_name,
            "local_grid_size": grid_size,
            "pois": points_of_interest,
            "environmental_vibe": vibe,
            "threat_rating": random.randint(1, 10),
            "generated_seed": seed
        }

    def _spawn_pois(self, biome: str, macro: Dict) -> List[Dict]:
        """Spawns 3-7 Points of Interest in the local grid."""
        count = random.randint(3, 7)
        pois = []
        
        # Biome-specific POI types
        themes = {
            "Ocean": ["Wreckage", "Coral Reef", "Abyssal Rift"],
            "Forest": ["Ancient Tree", "Hunter's Blind", "Fairy Circle"],
            "Mountains": ["Cavern Entrance", "Shrine", "Stone Bridge"],
            "Wasteland": ["Scrap Heap", "Crumbling Wall", "Toxic Vent"],
            "Grassland": ["Abandoned Farm", "Stone Obelisk", "Lone Well"]
        }
        
        options = themes.get(biome, ["Generic Landmark"])
        
        for _ in range(count):
            x = random.randint(0, 31)
            y = random.randint(0, 31)
            pois.append({
                "type": random.choice(options),
                "coord": [x, y],
                "discovered": False,
                "dynamic_status": "Stable"
            })
            
        # Add Faction Presence if faction_id > 0
        if macro.get("faction_id", 0) > 0:
            pois.append({
                "type": "Faction Outpost",
                "coord": [random.randint(5, 25), random.randint(5, 25)],
                "faction_id": macro["faction_id"],
                "discovered": True
            })
            
        return pois

    def _get_environmental_vibe(self, biome: str, height: float) -> Dict:
        """Calculates environmental friction (Visibility, Difficulty, Resources)."""
        vibe = {
            "visibility": "Clear",
            "traversability": "Easy",
            "resource_density": "Sparse"
        }
        
        if height > 0.7:
            vibe["traversability"] = "Challenging"
        if biome == "Forest" or biome == "Ocean":
            vibe["visibility"] = "Obscured"
        if biome == "Forest" or biome == "Grassland":
            vibe["resource_density"] = "Abundant"
            
        return vibe
