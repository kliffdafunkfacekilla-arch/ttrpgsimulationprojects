# python_fmg/core/models.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import json

@dataclass
class Trait:
    name: str
    type: str  # Combat, Magic, Diplomatic, Economic, Chaos, etc.
    effect: str

@dataclass
class Paragon:
    id: Optional[int] = None
    name: str = ""
    archetype: str = "Commander"
    level: int = 1
    stats_json: str = "{}"
    traits_json: str = "[]"
    motivation: str = ""
    faction_id: int = 1
    color: str = "#1ABC9C"
    
    @property
    def stats(self) -> Dict[str, int]:
        try:
            parsed = json.loads(self.stats_json)
            # Ensure all 12 keys exist, fill defaults if missing
            defaults = {
                "Might": 10, "Endurance": 10, "Finesse": 10, "Reflex": 10,
                "Vitality": 10, "Fortitude": 10, "Knowledge": 10, "Logic": 10,
                "Awareness": 10, "Intuition": 10, "Charm": 10, "Willpower": 10
            }
            for k, v in defaults.items():
                if k not in parsed:
                    parsed[k] = v
            return parsed
        except Exception:
            return {
                "Might": 10, "Endurance": 10, "Finesse": 10, "Reflex": 10,
                "Vitality": 10, "Fortitude": 10, "Knowledge": 10, "Logic": 10,
                "Awareness": 10, "Intuition": 10, "Charm": 10, "Willpower": 10
            }
            
    @stats.setter
    def stats(self, val: Dict[str, int]):
        self.stats_json = json.dumps(val)

    @property
    def traits(self) -> List[str]:
        try:
            return json.loads(self.traits_json)
        except Exception:
            return []
            
    @traits.setter
    def traits(self, val: List[str]):
        self.traits_json = json.dumps(val)

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
    inventory_json: str = "{}"  # Reused for buildings / properties
    hidden_cultists: int = 0
    magic_loadout: str = "[]"
    paragons: List[Paragon] = field(default_factory=list)
    linked_paragon_id: Optional[int] = None  # Reused from magic_loadout or custom field

@dataclass
class Religion:
    # Reused as ChaosPath
    id: int
    name: str
    type: str = "Chaos Path"
    color: str = "#8E44AD"
    center_q: int = 0
    center_r: int = 0
    is_prison: bool = False

@dataclass
class Culture:
    # Reused as FringeGroup (Cartels/Pirates/Smugglers)
    id: int
    name: str
    language_base: str = "Cartel"  # Fringe group type
    color: str = "#E67E22"
    center_q: int = 0
    center_r: int = 0
    expansionism: float = 1.0

@dataclass
class Province:
    # Reused as Paragon Area of Influence
    id: int
    name: str
    faction_id: int = 1
    color: str = "#1ABC9C"
    paragon_id: Optional[int] = None

@dataclass
class Marker:
    id: int
    type: str = "Ruins"
    description: str = ""
    global_q: int = 0
    global_r: int = 0
    resource_type: str = "None"
    resource_value: float = 0.0
    icon: str = "*"
    global_hex_id: Optional[int] = None

@dataclass
class GlobalHex:
    id: int
    q: int
    r: int
    biome: int = 4
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
    
    religion_id: int = 0
    culture_id: int = 0
    province_id: int = 0
    
    settlement: Optional[Settlement] = None

    @property
    def current_direction(self) -> str:
        if not self.micro_data_json:
            return ""
        try:
            d = json.loads(self.micro_data_json)
            return d.get("current_direction", "")
        except:
            return ""
            
    @current_direction.setter
    def current_direction(self, val: str):
        try:
            d = json.loads(self.micro_data_json) if self.micro_data_json else {}
        except:
            d = {}
        d["current_direction"] = val
        self.micro_data_json = json.dumps(d)
        
@dataclass
class Faction:
    id: int
    name: str
    treasury: float = 1000.0
    technology_level: int = 1
    special_rule: Optional[str] = None
    coa_json: str = "{}"
    relations: Dict[int, Tuple[str, int]] = field(default_factory=dict)
    
    # Custom simulation parameters
    species_population_json: str = "{}"  # Species name -> percentage
    sparkborn_attunement_json: str = "[]"  # List of attuned power types
    aggression_level: float = 5.0
    trade_level: float = 5.0
    faction_trait: str = ""

    @property
    def species_population(self) -> Dict[str, float]:
        try:
            return json.loads(self.species_population_json)
        except Exception:
            return {"Human": 1.0}

    @species_population.setter
    def species_population(self, val: Dict[str, float]):
        self.species_population_json = json.dumps(val)

    @property
    def sparkborn_attunement(self) -> List[str]:
        try:
            return json.loads(self.sparkborn_attunement_json)
        except Exception:
            return []

    @sparkborn_attunement.setter
    def sparkborn_attunement(self, val: List[str]):
        self.sparkborn_attunement_json = json.dumps(val)

@dataclass
class WorldEntity:
    id: Optional[int] = None
    type: str = "Merchant"  # Reused as moving unit types
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
    
    # Custom simulation databases
    trait_pool: List[Trait] = field(default_factory=list)
    
    # Calendar configurations
    calendar_week_names: List[str] = field(default_factory=lambda: ["Sol", "Luna", "Aether", "Terra", "Ignis", "Aqua", "Zephyr"])
    calendar_months: List[Dict] = field(default_factory=lambda: [
        {"name": "Dawn", "weeks": 4},
        {"name": "Zenith", "weeks": 4},
        {"name": "Twilight", "weeks": 4},
        {"name": "Nadir", "weeks": 4}
    ])
    calendar_seasons: List[Dict] = field(default_factory=lambda: [
        {"name": "Spring", "months": ["Dawn"], "temp_adjust": 0.0, "precip": 50.0},
        {"name": "Summer", "months": ["Zenith"], "temp_adjust": 5.0, "precip": 20.0},
        {"name": "Autumn", "months": ["Twilight"], "temp_adjust": -2.0, "precip": 60.0},
        {"name": "Winter", "months": ["Nadir"], "temp_adjust": -8.0, "precip": 40.0}
    ])

    # Economy settings
    building_costs: Dict[str, Dict[str, int]] = field(default_factory=lambda: {
        "Farm": {"Gold": 100, "Wood": 50},
        "Mine": {"Gold": 200, "Stone": 100},
        "Barracks": {"Gold": 300, "Stone": 150, "Iron": 50}
    })
    refined_goods: List[Dict] = field(default_factory=lambda: [
        {"name": "Steel Ingots", "cost": 50, "effect": "Unlocks military tier 2"},
        {"name": "Planks", "cost": 20, "effect": "Reduces building costs by 10%"}
    ])
    luxury_goods: List[Dict] = field(default_factory=lambda: [
        {"name": "Silk Robes", "cost": 150, "effect": "Increases noble happiness"},
        {"name": "Spices", "cost": 80, "effect": "Increases settlement wealth growth"}
    ])
    base_resources: List[Dict] = field(default_factory=lambda: [
        {"name": "Wood", "value": 5, "source_biomes": [1, 2, 4]},
        {"name": "Stone", "value": 8, "source_biomes": [6, 13]},
        {"name": "Iron Ore", "value": 15, "source_biomes": [6]}
    ])

    # World Configurator parameters
    temperature_equator: float = 30.0
    temperature_pole: float = -15.0
    temperature_offset: float = 0.0
    precipitation_multiplier: float = 1.0
    wind_direction_angle: float = 90.0  # Wind angle in degrees (e.g. 90=East, 270=West, etc.)

    def serialize_to_azgaar_json(self) -> str:
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
