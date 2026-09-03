import random
from typing import List, Dict, Optional
from saga_engine.core.state import RegionalState, TileState

class RegionalGenerator:
    """
    JIT Procedural Generator for 32x32 regional maps.
    Derives micro-detail from macro-hex biome and atmospheric data.
    """
    
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed

    def generate_region(self, q: int, r: int, macro_data: Dict, dynamic_meta: Dict) -> RegionalState:
        """
        Creates a deterministic 32x32 regional map.
        Deterministic: Same coordinates + same seed = same map.
        """
        # Create a stable seed for this specific hex
        coord_seed = hash(f"{q},{r},{self.seed}")
        random.seed(coord_seed)
        
        parent_id = f"{q},{r}"
        biome_id = macro_data.get("biome_id", 0)
        base_height = macro_data.get("height", 0.5)
        mana = dynamic_meta.get("mana", 0.5)
        moisture = dynamic_meta.get("moisture", 0.5)
        
        region = RegionalState(parent_hex_id=parent_id)
        
        # Biome to Tile Type Mapping
        # 0: Water, 1: Sand/Dirt, 2: Grass, 3: Trees, 4: Rock/Mountain, 5: Swamp/Mud
        biome_rules = {
            0: [0, 0, 0, 0, 0], # Ocean: Purely water
            1: [1, 1, 1, 4, 1], # Tundra: Dirt/Rock
            2: [2, 2, 2, 3, 0], # Grassland: Grass/Trees/Water
            3: [3, 3, 2, 3, 0], # Forest: Heavy trees
            4: [1, 1, 1, 4, 1], # Desert: Sand
            5: [4, 4, 4, 1, 4], # Mountains: Rock
            6: [5, 5, 0, 5, 3]  # Swamp: Mud/Water/Trees
        }
        
        weights = biome_rules.get(biome_id, [1, 1, 1, 1, 1])
        
        for _ in range(32 * 32):
            t_type = random.choice(weights)
            # Add some noise to height, mana, moisture based on macro base
            t_height = max(0.0, min(1.0, base_height + (random.random() - 0.5) * 0.2))
            t_mana = max(0.0, min(1.0, mana + (random.random() - 0.5) * 0.1))
            t_moisture = max(0.0, min(1.0, moisture + (random.random() - 0.5) * 0.1))
            
            tile = TileState(
                type_id=t_type,
                height=t_height,
                mana=t_mana,
                moisture=t_moisture
            )
            region.tiles.append(tile)
            
        return region
