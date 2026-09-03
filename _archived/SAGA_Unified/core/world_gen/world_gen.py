import csv
import logging
import random
from typing import Dict, Any

from core.models.character_sheet import TerrainTile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WorldGen")

class WorldGenerator:
    """
    Parses Okasha CSV data and generates local tactical matrices for the SAGA engine.
    """
    def __init__(self, burgs_csv_path: str = r"C:\Users\krazy\Desktop\Okasha\Okasha Burgs 2026-06-26-06-56.csv"):
        self.burgs = {}
        self._load_burgs(burgs_csv_path)

    def _load_burgs(self, path: str):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    burg_name = row.get("Burg", "").lower()
                    if burg_name:
                        self.burgs[burg_name] = row
            logger.info(f"Loaded {len(self.burgs)} burgs from Okasha data.")
        except Exception as e:
            logger.error(f"Failed to load burgs CSV: {e}")

    def generate_local_map(self, location_name: str, width: int = 40, height: int = 40, is_ambush: bool = False, dynamic_entities: list = None) -> Dict[str, Any]:
        """
        Generates a 2D grid matrix for the given location name.
        """
        loc_lower = location_name.lower()
        burg_data = self.burgs.get(loc_lower)

        # Decide biome/style based on data
        biome = "grass"
        if is_ambush:
            biome = "wilderness_ambush"
        elif burg_data:
            biome = "town"
            # We could read elevation, temperature, etc. here for more precision

        # Generate a rich Terrain Node grid
        grid = []
        for y in range(height):
            row = []
            for x in range(width):
                if x == 0 or x == width - 1 or y == 0 or y == height - 1:
                    row.append(TerrainTile(
                        x=x, y=y, tile_type="wall", 
                        tags=["cover", "heavy", "stone", "blocks_los"]
                    ).model_dump())
                else:
                    r = random.random()
                    if r < 0.05:
                        row.append(TerrainTile(
                            x=x, y=y, tile_type="obstacle", 
                            tags=["cover", "stone"]
                        ).model_dump())
                    elif r < 0.07:
                        row.append(TerrainTile(
                            x=x, y=y, tile_type="water", 
                            tags=["water", "difficult_terrain", "conductive"]
                        ).model_dump())
                    elif r < 0.08:
                        row.append(TerrainTile(
                            x=x, y=y, tile_type="chest", 
                            tags=["interactable", "loot", "closed"]
                        ).model_dump())
                    else:
                        row.append(TerrainTile(
                            x=x, y=y, tile_type="floor", 
                            tags=["floor"]
                        ).model_dump())
            grid.append(row)

        # Inject dynamic entities if provided by the AI Director
        entities = []
        if dynamic_entities:
            for ent in dynamic_entities:
                # Ensure they have valid spawn coordinates
                ent_x = ent.get("x", random.randint(5, width - 5))
                ent_y = ent.get("y", random.randint(5, height - 5))
                
                # Assign a unique ID if none exists
                uuid = ent.get("uuid", f"ent_{random.randint(10000, 99999)}")
                
                entities.append({
                    "uuid": uuid,
                    "x": ent_x,
                    "y": ent_y,
                    "sprite": ent.get("sprite", "hostile" if "hostile" in ent.get("tags", []) else "vendor"),
                    "name": ent.get("name", "Unknown Entity"),
                    "personality": ent.get("personality", "neutral"),
                    "tags": ent.get("tags", [])
                })
        else:
            # Fallback random generation
            if is_ambush:
                for _ in range(random.randint(2, 4)):
                    entities.append({
                        "uuid": f"enemy_{random.randint(1000, 9999)}",
                        "x": random.randint(5, width - 5),
                        "y": random.randint(5, height - 5),
                        "sprite": "hostile",
                        "name": "Bandit",
                        "personality": "hostile",
                        "tags": ["humanoid", "hostile", "bandit"]
                    })
            elif biome == "town":
                entities.append({
                    "uuid": f"npc_{random.randint(1000, 9999)}",
                    "x": width // 2 + 2,
                    "y": height // 2,
                    "sprite": "vendor",
                    "name": "Local Merchant",
                    "personality": "vendor",
                    "tags": ["humanoid", "civilian", "merchant"]
                })

        map_name = f"Wilderness Ambush near {location_name}" if is_ambush else (location_name if burg_data else f"Wilderness near {location_name}")

        return {
            "name": map_name,
            "biome": biome,
            "width": width,
            "height": height,
            "grid": grid,
            "entities": entities,
            "is_ambush": is_ambush
        }

if __name__ == "__main__":
    wg = WorldGenerator()
    test_map = wg.generate_local_map("Aloa")
    print(f"Generated Map: {test_map['name']} (Biome: {test_map['biome']})")
    print(f"Grid Size: {test_map['width']}x{test_map['height']}")
    print(f"Entities: {len(test_map['entities'])}")
