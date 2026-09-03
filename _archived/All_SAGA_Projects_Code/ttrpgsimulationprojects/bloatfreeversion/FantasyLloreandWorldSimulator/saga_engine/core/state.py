from pydantic import BaseModel, Field
from typing import List, Dict, Optional

# 1. THE BIOLOGICAL CHASSIS (System Agnostic Base)
class VitalsState(BaseModel):
    """Real-time tracking of resource pools (Dynamic Keys)"""
    # Keyed by vital ID (e.g. 'hp', 'stamina')
    current: Dict[str, float] = {}
    maxima: Dict[str, float] = {}
    
    # Persistent anatomical state
    body_injuries: List[str] = []
    mind_injuries: List[str] = []

class WealthState(BaseModel):
    """Tracks the standard and volatile economy"""
    aetherium_coins: int = 0
    d_dust_grams: float = 0.0
    exchange_rate: float = 1.0

# 2. MICRO-SCALE MODELS (Regional Mapping)
class TileState(BaseModel):
    """Data for a single 1x1 regional tile."""
    type_id: int = 0
    height: float = 0.5
    mana: float = 0.0
    moisture: float = 0.0
    tags: List[str] = []

class RegionalState(BaseModel):
    """A 32x32 grid representing the micro-detail of a macro hex."""
    parent_hex_id: str # e.g. "0,0"
    # Row-major list of 1024 tiles (32 * 32)
    tiles: List[TileState] = []
    width: int = 32
    height: int = 32

# 2. THE CHRONOS STATE (Time Tracking)
class TimeState(BaseModel):
    """Maintains the simulation clock"""
    year: int = 1024
    month: int = 1
    day: int = 1
    hour: int = 8
    minute: int = 0
    season: str = "Deep Winter"
    
    def __str__(self):
        return f"Day {self.day}, {self.hour:02d}:{self.minute:02d} - {self.season}, Year {self.year}"

# 3. THE CAMPAIGN AGGREGATE
class PlayerCharacter(BaseModel):
    id: str
    name: str
    # System Agnostic Stats (Keyed by active ruleset)
    attributes: Dict[str, int] = {}
    vitals: VitalsState = Field(default_factory=VitalsState)
    wealth: WealthState
    location_hex: str = "[0, 0]" # Coordinate string for fast lookups

# 3. THE DYNAMIC WORLD (Simulation State)
class DynamicWorldState(BaseModel):
    """Tracks shifting variables like influence, weather, and resources"""
    # hex_id -> {factor_name: value}
    # e.g. "0,0" -> {"mana_flux": 0.8, "moisture": 0.4, "tension": 0}
    hex_metadata: Dict[str, Dict[str, float]] = {}
    
    # faction_id -> territory (list of hex_coord strings)
    faction_territories: Dict[int, List[str]] = {}
    
    # Global weather/environmental variables
    global_weather_stability: float = 1.0
    active_hazards: List[Dict] = []

# 4. THE CAMPAIGN AGGREGATE
class CampaignState(BaseModel):
    """The Ultimate Source of Truth for the S.A.G.A. Brain"""
    campaign_id: str
    chaos_level: int = 1
    chaos_tracker: int = 0
    
    time: TimeState = Field(default_factory=TimeState)
    active_player: Optional[PlayerCharacter] = None
    
    # Ruleset Hub
    active_ruleset_id: str = "shatterlands_rules"
    
    # Living World elements
    active_quests: List[Dict] = []
    world_tags: Dict[str, List[str]] = {}
    discovered_hexes: List[str] = []
    
    # Simulation Data
    dynamic_world: DynamicWorldState = Field(default_factory=DynamicWorldState)
    active_regional_state: Optional[RegionalState] = None
    
    # Engine Flags
    simulation_paused: bool = False
    ui_locked: bool = False
    current_hex_focus: Dict = {} # Data of the hex currently being inspected
