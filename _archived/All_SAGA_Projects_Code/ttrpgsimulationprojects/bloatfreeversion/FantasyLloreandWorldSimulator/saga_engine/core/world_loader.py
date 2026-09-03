import json
import os
from typing import Dict, List, Optional, Tuple
from saga_engine.core.state import CampaignState

class WorldLoader:
    """
    Ingests the macro-world data (Master_World.json) and prepares the hex grid
    for real-time simulation and JIT content generation.
    """
    
    def __init__(self, world_path: str = "saga_engine/data/Master_World.json"):
        self.world_path = world_path
        self.hex_data: Dict[str, Dict] = {} # Keyed by "[q, r]" string
        self.grid_bounds: Dict[str, int] = {"min_q": 0, "max_q": 0, "min_r": 0, "max_r": 0}

    def load_world(self) -> bool:
        """Reads the large JSON file and indexes hexes for fast spatial lookup."""
        if not os.path.exists(self.world_path):
            print(f"[WORLD ERROR] Could not find world file at {self.world_path}")
            return False
            
        print(f"[WORLD] Loading macro-grid from {self.world_path}...")
        try:
            with open(self.world_path, "r") as f:
                raw_data = json.load(f)
                
            hexes = raw_data.get("hexes", [])
            for h in hexes:
                q, r = h.get("q", 0), h.get("r", 0)
                coord_key = f"[{q}, {r}]"
                self.hex_data[coord_key] = h
                
                # Track bounds for the GM View/Dashboard
                self.grid_bounds["min_q"] = min(self.grid_bounds["min_q"], q)
                self.grid_bounds["max_q"] = max(self.grid_bounds["max_q"], q)
                self.grid_bounds["min_r"] = min(self.grid_bounds["min_r"], r)
                self.grid_bounds["max_r"] = max(self.grid_bounds["max_r"], r)
                
            print(f"[WORLD] Successfully indexed {len(self.hex_data)} hex cells.")
            return True
        except Exception as e:
            print(f"[WORLD ERROR] Failed to parse world data: {e}")
            return False

    def get_hex(self, q: int, r: int) -> Optional[Dict]:
        """Returns the raw data of a specific hex."""
        return self.hex_data.get(f"[{q}, {r}]")

    def sync_to_state(self, state: CampaignState):
        """Injects relevant metadata into the persistent CampaignState."""
        state.world_tags["GRID_BOUNDS"] = [
            f"q:{self.grid_bounds['min_q']}..{self.grid_bounds['max_q']}",
            f"r:{self.grid_bounds['min_r']}..{self.grid_bounds['max_r']}"
        ]
        
        # Seed initial simulation values for AetherFlow
        # Biome Base Mapping
        biome_bases = {
            0: {"mana": 0.1, "moisture": 1.0}, 1: {"mana": 0.3, "moisture": 0.3},
            2: {"mana": 0.4, "moisture": 0.6}, 3: {"mana": 0.6, "moisture": 0.8},
            4: {"mana": 0.2, "moisture": 0.1}, 5: {"mana": 0.5, "moisture": 0.4},
            6: {"mana": 0.7, "moisture": 0.9}, 7: {"mana": 0.4, "moisture": 0.5},
            8: {"mana": 0.9, "moisture": 0.1}, 9: {"mana": 1.0, "moisture": 0.5},
            10: {"mana": 1.0, "moisture": 0.5}, 11: {"mana": 1.0, "moisture": 0.5},
            12: {"mana": 1.0, "moisture": 0.5}
        }
        
        for coord_key, data in self.hex_data.items():
            # coord_key is "[q, r]", we need "q,r" for dynamic_world map mapping
            q, r = data["q"], data["r"]
            stripped_key = f"{q},{r}"
            if stripped_key not in state.dynamic_world.hex_metadata:
                biome_id = data.get("biome_id", 0)
                base = biome_bases.get(biome_id, {"mana": 0.5, "moisture": 0.5})
                state.dynamic_world.hex_metadata[stripped_key] = {
                    "mana": base["mana"],
                    "moisture": base["moisture"],
                    "tension": 0.0
                }
        
    def get_neighbor_coords(self, q: int, r: int) -> List[Tuple[int, int]]:
        """Calculates Axial coordinate neighbors for pathfinding/simulation."""
        # Axial Hex Directions
        directions = [
            (1, 0), (1, -1), (0, -1),
            (-1, 0), (-1, 1), (0, 1)
        ]
        neighbors = []
        for dq, dr in directions:
            nq, nr = q + dq, r + dr
            if f"[{nq}, {nr}]" in self.hex_data:
                neighbors.append((nq, nr))
        return neighbors
