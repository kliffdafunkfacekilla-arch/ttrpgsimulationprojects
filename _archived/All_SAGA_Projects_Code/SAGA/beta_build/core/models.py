"""
Core data models for the S.A.G.A Engine Beta.
These strict Pydantic models represent the player character, inventory, and items.
Using Pydantic ensures data integrity before passing state to the LLM or saving to disk.
"""
from pydantic import BaseModel, Field, model_validator
from typing import Dict, List, Optional, Any

class Item(BaseModel):
    """
    Represents an equippable or consumable item in the game world.
    """
    name: str
    item_type: str
    stat_type: str
    modifier: int = 0
    loadout_cost: int = 0
    armor_mod: int = 0
    quantity: int = 1
    consumable_effect: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

class Inventory(BaseModel):
    """
    Manages the player's physical and mental equipment slots, as well as their bag of loose items.
    """
    gold: int = 0
    slots: Dict[str, Optional[Item]] = {
        "head": None, "eyewear": None, "necklace": None, "brooch": None,
        "body": None, "overcoat": None, "legs": None, "feet": None,
        "hand": None, "weapon": None, "backup_weapon": None,
        "ring_1": None, "ring_2": None
    }
    bag: List[Item] = Field(default_factory=list)

    @property
    def physical_slots(self) -> set:
        return {"body", "legs", "feet", "hand", "weapon", "backup_weapon", "overcoat"}
        
    @property
    def mental_slots(self) -> set:
        return {"head", "eyewear", "necklace", "brooch", "ring_1", "ring_2"}

    def get_physical_tax(self) -> int:
        return sum(item.loadout_cost for slot, item in self.slots.items() if slot in self.physical_slots and item)

    def get_mental_tax(self) -> int:
        return sum(item.loadout_cost for slot, item in self.slots.items() if slot in self.mental_slots and item)

class CharacterSheet(BaseModel):
    """
    The definitive source of truth for a player character's state.
    Includes base stats, derived pools (HP, Stamina, Focus), and inventory.
    """
    name: str
    biological_origin: str = "Unknown"
    
    # Base Stats
    stats: Dict[str, int] = Field(default_factory=lambda: {
        "endurance": 5, "fortitude": 5, "vitality": 5,
        "willpower": 5, "logic": 5, "charm": 5,
        "might": 5, "reflexes": 5, "finesse": 5,
        "knowledge": 5, "awareness": 5, "intuition": 5
    })
    
    inventory: Inventory = Field(default_factory=Inventory)
    
    level: int = 1
    xp: int = 0
    skills: List[str] = Field(default_factory=list)
    unspent_stat_points: int = 0
    unspent_skill_points: int = 0
    
    trauma_tokens: int = 0
    is_stabilized: bool = True
    has_disadvantage: bool = False
    
    # Derived pools
    max_hp: int = 15
    current_hp: int = 15
    max_composure: int = 15
    current_composure: int = 15
    max_stamina: int = 15
    max_focus: int = 15
    
    active_stamina: int = 10
    active_focus: int = 10
    is_zero_state: bool = False

    @model_validator(mode='after')
    def derive_pools(self) -> 'CharacterSheet':
        # Derive pools based on base stats
        self.max_hp = self.stats.get("endurance", 0) + self.stats.get("fortitude", 0) + self.stats.get("vitality", 0)
        self.max_composure = self.stats.get("willpower", 0) + self.stats.get("logic", 0) + self.stats.get("charm", 0)
        self.max_stamina = self.stats.get("might", 0) + self.stats.get("reflexes", 0) + self.stats.get("finesse", 0)
        self.max_focus = self.stats.get("knowledge", 0) + self.stats.get("awareness", 0) + self.stats.get("intuition", 0)
        
        # Ensure current values don't exceed max during recalculation
        self.current_hp = min(self.current_hp, self.max_hp)
        self.current_composure = min(self.current_composure, self.max_composure)
        self.active_stamina = min(self.active_stamina, self.max_stamina)
        self.active_focus = min(self.active_focus, self.max_focus)
        
        return self
