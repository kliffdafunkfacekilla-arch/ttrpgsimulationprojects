"""
Core data models for SAGA Unified.
These strict Pydantic models represent the player character, inventory, and items.
Using Pydantic ensures data integrity before passing state to the LLM or saving to disk.
"""
from pydantic import BaseModel, Field, model_validator
from typing import Dict, List, Optional, Any

class TerrainTile(BaseModel):
    """
    Represents a single tactical node on the VTT battle map.
    Provides strict typing for pathfinding, line of sight, and environmental physics.
    """
    x: int
    y: int
    tile_type: str = "floor"
    tags: List[str] = Field(default_factory=list)

class Item(BaseModel):
    """
    Represents an equippable or consumable item in the game world.
    """
    name: str
    item_type: str
    gear_category: str = "generic"
    stat_type: str
    scaling_stat_primary: str = ""
    scaling_stat_secondary: str = ""
    modifier: int = 0
    loadout_cost: int = 0
    armor_mod: int = 0
    quantity: int = 1
    consumable_effect: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

class Inventory(BaseModel):
    """
    Manages the player's physical and mental equipment slots, as well as their bag of loose items.
    Enhanced version from SAGA_Voice with better slot management.
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

    @property
    def physical_armor_mod(self) -> int:
        """Sums the armor_mod of all equipped physical armor."""
        return sum(item.armor_mod for slot, item in self.slots.items() if slot in self.physical_slots and item)

    @property
    def mental_armor_mod(self) -> int:
        """Sums the armor_mod of all equipped mental wards (rings, amulets)."""
        return sum(item.armor_mod for slot, item in self.slots.items() if slot in self.mental_slots and item)

    def equip_item(self, slot: str, item: Item) -> bool:
        """Equip an item to a specific slot."""
        if slot in self.slots:
            # Unequip current item if present
            if self.slots[slot]:
                self.bag.append(self.slots[slot])
            self.slots[slot] = item
            return True
        return False

    def unequip_item(self, slot: str) -> Optional[Item]:
        """Unequip an item from a specific slot."""
        if slot in self.slots and self.slots[slot]:
            item = self.slots[slot]
            self.slots[slot] = None
            self.bag.append(item)
            return item
        return None

class CharacterSheet(BaseModel):
    """
    The definitive source of truth for a player character's state.
    Includes base stats, derived pools (HP, Stamina, Focus), and inventory.
    Enhanced with features from SAGA_Voice character sheet.
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
    tags: List[str] = Field(default_factory=list)
    unspent_stat_points: int = 0
    unspent_skill_points: int = 0
    
    # Trauma & Conditions
    trauma_tokens: int = 0
    is_stabilized: bool = True
    has_disadvantage: bool = False
    adrenaline_shock: bool = False
    bleed_stacks: int = 0
    chaos_ticks: int = 0
    injury_tallies: List[str] = Field(default_factory=list)
    
    # Action Economy (The 3-Beat Pulse)
    active_move_beats: int = 1
    active_stamina_beats: int = 1
    active_focus_beats: int = 1
    
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

    # --- Tactical Sub-Stats ---
    @property
    def perception_substat(self) -> int:
        return (2 * (self.stats.get("awareness", 0) + self.stats.get("logic", 0)) + self.stats.get("vitality", 0)) // 3

    @property
    def movement_substat(self) -> int:
        return (2 * (self.stats.get("reflexes", 0) + self.stats.get("might", 0)) + self.stats.get("intuition", 0)) // 3

    @property
    def balance_substat(self) -> int:
        return (2 * (self.stats.get("endurance", 0) + self.stats.get("fortitude", 0)) + self.stats.get("willpower", 0)) // 3

    @property
    def stealth_substat(self) -> int:
        return (2 * (self.stats.get("knowledge", 0) + self.stats.get("charm", 0)) + self.stats.get("finesse", 0)) // 3

    def take_damage(self, amount: int, is_physical: bool = True):
        if amount <= 0:
            return
            
        if is_physical:
            self.current_hp -= amount
            if self.current_hp <= 0:
                self.current_hp = 0
                if self.is_zero_state and (self.bleed_stacks > 0 or "drain" in self.tags):
                    if "dead" not in self.tags: self.tags.append("dead")
                self.is_zero_state = True
        else:
            self.current_composure -= amount
            if self.current_composure <= 0:
                self.current_composure = 0
                if self.is_zero_state and (self.chaos_ticks > 0 or "drain" in self.tags):
                    if "dead" not in self.tags: self.tags.append("dead")
                self.is_zero_state = True

    def desperate_rally(self):
        """Consume a beat to force an incapacitated character to burn remaining reserves."""
        if self.is_zero_state and (self.active_move_beats > 0 or self.active_stamina_beats > 0 or self.active_focus_beats > 0):
            # Consume 1 beat of any type
            if self.active_move_beats > 0:
                self.active_move_beats -= 1
            elif self.active_stamina_beats > 0:
                self.active_stamina_beats -= 1
            elif self.active_focus_beats > 0:
                self.active_focus_beats -= 1
                
            # Restore 1 capacity point
            if self.current_hp <= 0:
                self.current_hp = 1
            if self.current_composure <= 0:
                self.current_composure = 1
            self.is_zero_state = False

    def consume_anomaly_cost(self, move_beats: int, focus_beats: int, stamina_beats: int, focus_cost: int, stamina_cost: int) -> bool:
        """Attempts to consume costs for an anomaly. Returns True if successful, False if insufficient."""
        if (self.active_move_beats < move_beats or 
            self.active_focus_beats < focus_beats or 
            self.active_stamina_beats < stamina_beats or
            self.active_focus < focus_cost or 
            self.active_stamina < stamina_cost):
            return False
            
        self.active_move_beats -= move_beats
        self.active_focus_beats -= focus_beats
        self.active_stamina_beats -= stamina_beats
        self.active_focus -= focus_cost
        self.active_stamina -= stamina_cost
        return True
        
    def permanently_reduce_max_stamina(self, amount: int):
        """Used by the Channeling Chaos Friction effect."""
        self.max_stamina -= amount
        if self.max_stamina < 0:
            self.max_stamina = 0
        if self.active_stamina > self.max_stamina:
            self.active_stamina = self.max_stamina

    # --- Enhanced features from SAGA_Voice ---
    def regenerate_beats(self):
        """Regenerate action beats based on loadout tax (SAGA_Voice enhancement)."""
        tax = self.inventory.get_physical_tax() + self.inventory.get_mental_tax()
        regen_rate = 1 if tax > (self.max_stamina / 2) else 2
        
        self.active_move_beats = min(self.active_move_beats + regen_rate, 3)
        self.active_stamina_beats = min(self.active_stamina_beats + regen_rate, 3)
        self.active_focus_beats = min(self.active_focus_beats + regen_rate, 3)

    def is_encumbered(self) -> bool:
        """Check if character is encumbered by gear (SAGA_Voice enhancement)."""
        tax = self.inventory.get_physical_tax() + self.inventory.get_mental_tax()
        return tax > (self.max_stamina / 2)