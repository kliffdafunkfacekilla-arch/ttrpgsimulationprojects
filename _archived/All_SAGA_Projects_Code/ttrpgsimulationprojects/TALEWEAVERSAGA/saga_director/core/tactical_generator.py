import random
from typing import Dict, List, Optional, Any
from .encounter_schemas import CombatEncounter, Combatant, SpatialData

class TacticalGenerator:
    _world_manager = None

    @classmethod
    def set_world_manager(cls, wm):
        cls._world_manager = wm

    @staticmethod
    def apply_deltas(grid: List[List[Any]], deltas: List[Dict]):
        if not deltas:
            return
        for d in deltas:
            x = d.get("x")
            y = d.get("y")
            val = d.get("new_value")
            if x is not None and y is not None and 0 <= y < len(grid) and 0 <= x < len(grid[0]):
                grid[y][x] = val

    @staticmethod
    def generate_region_map(biome: str, hex_id: int, deltas: List[Dict] = None):
        """Tier 2: 20x20 Regional Strategic Grid."""
        width, height = 20, 20
        grid = [[0 for _ in range(width)] for _ in range(height)]
        grid[10][10] = 1 # Central POI
        
        TacticalGenerator.apply_deltas(grid, [d for d in (deltas or []) if d["layer"] == 2])

        return {
            "hex_id": hex_id,
            "biome": biome,
            "grid": grid,
            "width": width,
            "height": height
        }

    @staticmethod
    def generate_local_grid(biome: str, hex_id: int, rx: int, ry: int, deltas: List[Dict] = None):
        """Tier 3: 100x100 Local Exploration Grid."""
        width, height = 100, 100
        grid = [["G" for _ in range(width)] for _ in range(height)]
        
        TacticalGenerator.apply_deltas(grid, [d for d in (deltas or []) if d["layer"] == 3])

        return {
            "hex_id": hex_id,
            "rx": rx,
            "ry": ry,
            "biome": biome,
            "grid": grid,
            "width": width,
            "height": height
        }

    @staticmethod
    def generate_ambient_encounter(
        biome: str, 
        hex_id: int, 
        lx: int, 
        ly: int, 
        current_hour: float = 12.0, 
        densities: Dict = None,
        external_npcs: List = None,
        player_sprite: Dict = None,
        deltas: List[Dict] = None
    ):
        """Tier 4: 100x100 Player/Tactical Grid with building interiors and NPCs."""
        width, height = 100, 100
        grid = [["EMPTY" for _ in range(width)] for _ in range(height)]
        
        for y in range(40, 60):
            for x in range(40, 60):
                if x == 40 or x == 59 or y == 40 or y == 59:
                    grid[y][x] = "WALL"
                else:
                    grid[y][x] = "FLOOR"

        rng = random.Random(hex_id + lx + ly)
        for _ in range(200):
            rx = rng.randint(0, 99)
            ry = rng.randint(0, 99)
            if grid[ry][rx] == "EMPTY":
                grid[ry][rx] = "GRASS" if rng.random() > 0.2 else "DEBRIS"

        TacticalGenerator.apply_deltas(grid, [d for d in (deltas or []) if d["layer"] in [4, 5]])

        return {
            "encounter_id": f"TAC_{hex_id}_{lx}_{ly}",
            "biome": biome,
            "grid": grid,
            "gridWidth": width,
            "gridHeight": height,
            "tokens": external_npcs or [],
            "data": {
                "category": "COMBAT",
                "title": f"{biome} Tactical Zone",
                "narrative_prompt": f"You have entered a tactical zone in the {biome}.",
                "enemies": []
            }
        }
