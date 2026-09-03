# python_fmg/core/models.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import json

@dataclass
class Settlement:
    id: Optional[int] = None
    faction_id: int = 1
    faction_name: str = "Neutral"
    name: str = ""
    settlement_level: int = 1
    population: int = 50
    wealth: float = 100.0
    security_points: float = 10.0
    inventory_json: str = "{}"
    hidden_cultists: int = 0
    magic_loadout: str = "[]"

@dataclass
class GlobalHex:
    id: int
    q: int
    r: int
    biome: int = 4  # Default to plains (4)
    elevation: int = 5
    p1: int = 0      # Chaos
    p2: int = 0      # Temp
    p3: int = 0      # Moisture
    res: int = 0     # Resource rating
    wind_direction: str = "W"
    river_volume: int = 0
    is_lake: bool = False
    chaos_domain: Optional[str] = None
    flow_target_id: Optional[int] = None
    micro_data_json: Optional[str] = None
    
    # Emergent state (e.g. settlements)
    settlement: Optional[Settlement] = None

@dataclass
class Faction:
    id: int
    name: str
    treasury: float = 1000.0
    technology_level: int = 1
    special_rule: Optional[str] = None

@dataclass
class MapState:
    hexes: Dict[Tuple[int, int], GlobalHex] = field(default_factory=dict)
    factions: Dict[int, Faction] = field(default_factory=dict)
    
    def serialize_to_azgaar_json(self) -> str:
        """Serializes the state to a JSON structure similar to Azgaar exports."""
        cells = []
        for (q, r), hx in sorted(self.hexes.items(), key=lambda item: item[1].id):
            cells.append({
                "id": hx.id,
                "q": hx.q,
                "r": hx.r,
                "height": hx.elevation,
                "biome": hx.biome,
                "temp": hx.p2,
                "moist": hx.p3,
                "burg": hx.settlement.name if hx.settlement else None
            })
        return json.dumps({"cells": cells}, indent=2)
