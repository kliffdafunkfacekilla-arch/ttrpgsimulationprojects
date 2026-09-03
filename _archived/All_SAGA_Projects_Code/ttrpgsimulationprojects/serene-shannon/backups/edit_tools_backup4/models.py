# python_fmg/core/models.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import json

@dataclass
class Paragon:
    id: Optional[int] = None
    name: str = ""
    archetype: str = "Commander"  # e.g. Commander, Merchant, Mage
    level: int = 1
    stats_json: str = "{}"
    traits_json: str = "[]"
    motivation: str = ""

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
    paragons: List[Paragon] = field(default_factory=list)

@dataclass
class Religion:
    id: int
    name: str
    type: str = "Polytheism" # e.g. Monotheism, Polytheism, Animism
    color: str = "#8E44AD"
    center_q: int = 0
    center_r: int = 0

@dataclass
class Culture:
    id: int
    name: str
    language_base: str = "Common"
    color: str = "#E67E22"
    center_q: int = 0
    center_r: int = 0
    expansionism: float = 1.0

@dataclass
class Province:
    id: int
    name: str
    faction_id: int = 1
    color: str = "#1ABC9C"

@dataclass
class Marker:
    id: int
    type: str = "Ruins" # e.g. Ruins, Dungeon, Cave, Portal
    description: str = ""
    global_q: int = 0
    global_r: int = 0

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
    
    # Relationships to other structures
    religion_id: int = 0 # 0 represents None
    culture_id: int = 0
    province_id: int = 0
    
    # Emergent state (e.g. settlements)
    settlement: Optional[Settlement] = None

@dataclass
class Faction:
    id: int
    name: str
    treasury: float = 1000.0
    technology_level: int = 1
    special_rule: Optional[str] = None
    coa_json: str = "{}" # Armoria-style shield division and charges
    relations: Dict[int, Tuple[str, int]] = field(default_factory=dict) # target_faction_id -> (status, trust_level)

@dataclass
class WorldEntity:
    id: Optional[int] = None
    type: str = "Regiment"  # e.g. Regiment, Cult Monster, Null Zealots, Hurricane
    global_hex_id: int = 1
    global_q: int = 0
    global_r: int = 0
    radius: int = 1
    duration: int = 50
    intensity: float = 1.0
    alignment: Optional[str] = None
    micro_q: int = 0
    micro_r: int = 0

@dataclass
class TradeRoute:
    id: Optional[int] = None
    faction_id: int = 1
    settlement_a_id: int = 1
    settlement_b_id: int = 1
    bandwidth: int = 10
    route_type: str = "Land"

@dataclass
class MapState:
    hexes: Dict[Tuple[int, int], GlobalHex] = field(default_factory=dict)
    factions: Dict[int, Faction] = field(default_factory=dict)
    entities: List[WorldEntity] = field(default_factory=list)
    routes: List[TradeRoute] = field(default_factory=list)
    religions: Dict[int, Religion] = field(default_factory=dict)
    cultures: Dict[int, Culture] = field(default_factory=dict)
    provinces: Dict[int, Province] = field(default_factory=dict)
    markers: List[Marker] = field(default_factory=list)
    
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
