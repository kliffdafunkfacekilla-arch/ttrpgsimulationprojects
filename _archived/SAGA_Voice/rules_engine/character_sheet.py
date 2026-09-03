from rules_engine.inventory import Inventory, Item

class CharacterSheet:
    """
    Core data structure for the BRUTAL engine.
    Now supports all 12 core stats and derives pools automatically.
    """
    def __init__(self, name: str, stats: dict = None, origin: str = "Unknown"):
        self.name = name
        self.biological_origin = origin
        
        # 12 Core Stats
        self.stats = {
            "endurance": 5, "fortitude": 5, "vitality": 5,
            "willpower": 5, "logic": 5, "charm": 5,
            "might": 5, "reflexes": 5, "finesse": 5,
            "knowledge": 5, "awareness": 5, "intuition": 5
        }
        
        if stats:
            for k, v in stats.items():
                if k in self.stats:
                    self.stats[k] = min(v, 8) # Hard Biological Ceiling at creation
                    
        self.inventory = Inventory()
        
        self.level = 1
        self.xp = 0
        self.skills = []
        self.unspent_stat_points = 0
        self.unspent_skill_points = 0
        
        self.trauma_tokens = 0
        self.is_stabilized = True
        self.has_disadvantage = False
        
        # Chapter 5 Trauma Pipeline properties
        self.injury_tallies = []
        self.active_bleed = False
        self.active_trauma = False
        self.is_zero_state = False
        self.looted = False
        
        # Clash/Combat Mechanics
        self.has_active_defended = False
        self.has_advantage = False
        
        # Functional State
        self.tags = set()
        self.modifiers = {}
        
        self._derive_pools()
        self._init_battery()
        
    def _derive_pools(self):
        # SET 1: CAPACITIES & THRESHOLDS
        # Health [2 Body, 1 Mind]
        self.max_hp = self.stats["vitality"] + self.stats["endurance"] + self.stats["willpower"]
        self.current_hp = getattr(self, 'current_hp', self.max_hp)
        
        # Stamina (Pool) [2 Body, 1 Mind]
        self.max_stamina = self.stats["might"] + self.stats["finesse"] + self.stats["intuition"]
        
        # Focus (Pool) [1 Body, 2 Mind]
        self.max_focus = self.stats["logic"] + self.stats["charm"] + self.stats["reflexes"]
        
        # Composure [1 Body, 2 Mind]
        self.max_composure = self.stats["knowledge"] + self.stats["awareness"] + self.stats["fortitude"]
        self.current_composure = getattr(self, 'current_composure', self.max_composure)
        
    def _init_battery(self):
        # Active Battery: All combatants initialize with 10 tokens
        self.active_stamina = 10
        self.active_focus = 10
        self.is_zero_state = False
        self.beats = {"move": 1, "stamina": 1, "focus": 1}
        
    def start_turn(self):
        """Regenerate beats and pools based on Loadout Tax."""
        self.beats = {"move": 1, "stamina": 1, "focus": 1}
        self.has_active_defended = False
        
        tax = self.inventory.get_physical_tax() + self.inventory.get_mental_tax()
        regen_rate = 1 if tax > (self.max_stamina / 2) else 2
        
        # Cap regen at 75% max
        stamina_cap = int(self.max_stamina * 0.75)
        focus_cap = int(self.max_focus * 0.75)
        
        if self.active_stamina < stamina_cap:
            self.active_stamina = min(self.active_stamina + regen_rate, stamina_cap)
            
        if self.active_focus < focus_cap:
            self.active_focus = min(self.active_focus + regen_rate, focus_cap)

    def get_reserve_pool(self) -> int:
        """Reserve pool is capacity minus gear tax."""
        tax = self.inventory.get_physical_tax() + self.inventory.get_mental_tax()
        return self.max_stamina - tax - self.trauma_tokens
        
    def get_stat(self, stat_name: str) -> int:
        if self.is_zero_state:
            return 0 # All stats collapse, resulting in flat DC 10
            
        base = self.stats.get(stat_name.lower(), 0)
        # Apply gear modifiers
        gear_mod = self.inventory.get_total_modifier(stat_name)
        return base + gear_mod
        
    def get_derived_stat(self, stat_name: str) -> int:
        stat_name = stat_name.lower()
        # SET 2: COMBAT, SENSES & DEFENSE
        if stat_name in ["physical defense", "phys_def"]:
            return self.get_stat("might") + self.get_stat("fortitude") + self.get_stat("logic")
        elif stat_name in ["speed", "initiative"]:
            return self.get_stat("reflexes") + self.get_stat("endurance") + self.get_stat("willpower")
        elif stat_name in ["perception"]:
            return self.get_stat("finesse") + self.get_stat("knowledge") + self.get_stat("awareness")
        elif stat_name in ["mental defense", "ment_def"]:
            return self.get_stat("vitality") + self.get_stat("charm") + self.get_stat("intuition")
        return 0
        
    def is_physically_encumbered(self) -> bool:
        """Returns True if physical gear tax exceeds 50% of Stamina Capacity."""
        return self.inventory.get_physical_tax() > (self.max_stamina / 2)
        
    def is_mentally_encumbered(self) -> bool:
        """Returns True if mental gear tax exceeds 50% of Focus Capacity."""
        return self.inventory.get_mental_tax() > (self.max_focus / 2)
        
    def reset_turn_states(self):
        self.has_active_defended = False
        self.has_advantage = False

    def take_damage(self, amount: int, is_composure: bool = False):
        if is_composure:
            self.current_composure -= amount
            if self.current_composure <= 0:
                self.is_zero_state = True
        else:
            self.current_hp -= amount
            if self.current_hp <= 0:
                self.is_zero_state = True
        
    def apply_action_cost(self, cost: dict):
        self.active_stamina -= cost.get("stamina", 0)
        self.active_focus -= cost.get("focus", 0)

    def consume(self, item: Item):
        """Applies a consumable item's effect and decrements quantity."""
        if not item.consumable_effect:
            return False
            
        is_healing = False
        if "heal" in item.consumable_effect:
            self.current_hp = min(self.max_hp, self.current_hp + item.consumable_effect["heal"])
            is_healing = True
        if "stamina" in item.consumable_effect:
            self.active_stamina = min(self.max_stamina, self.active_stamina + item.consumable_effect["stamina"])
        if "focus" in item.consumable_effect:
            self.active_focus = min(self.max_focus, self.active_focus + item.consumable_effect["focus"])
            
        if is_healing and self.is_zero_state and self.current_hp > 0:
            self.is_zero_state = False
            self.active_stamina = 0
            self.active_focus = 0
            
        item.quantity -= 1
        return True
        
    def add_xp(self, amount: int):
        self.xp += amount
        # Simple threshold for leveling up: 100 * current level
        if self.xp >= self.level * 100:
            self.xp -= self.level * 100
            self.level_up()
            
    def level_up(self):
        """Increases level, grants a skill point, and grants a stat point every other level."""
        self.level += 1
        self.unspent_skill_points += 1
        
        if self.level % 2 == 0:
            self.unspent_stat_points += 1
            
    def spend_stat_point(self, stat_name: str):
        if self.unspent_stat_points > 0:
            key = stat_name.lower()
            if key in self.stats:
                self.stats[key] += 1
                self.unspent_stat_points -= 1
                self._derive_pools() # Recalculate max HP/Capacities
                return True
        return False
        
    def unlock_skill(self, skill_name: str):
        if self.unspent_skill_points > 0 and skill_name not in self.skills:
            self.skills.append(skill_name)
            self.unspent_skill_points -= 1
            return True
        return False

    def to_dict(self):
        return {
            "name": self.name,
            "biological_origin": self.biological_origin,
            "base_stats": self.stats,
            "current_hp": self.current_hp,
            "current_composure": self.current_composure,
            "active_stamina": self.active_stamina,
            "active_focus": self.active_focus,
            "level": self.level,
            "xp": self.xp,
            "skills": self.skills,
            "unspent_stat_points": self.unspent_stat_points,
            "unspent_skill_points": self.unspent_skill_points,
            "trauma_tokens": self.trauma_tokens,
            "is_stabilized": self.is_stabilized,
            "has_disadvantage": self.has_disadvantage,
            "inventory": self.inventory.to_dict()
        }
        
    @classmethod
    def from_dict(cls, data):
        sheet = cls(data["name"], data["base_stats"], data.get("biological_origin", "Unknown"))
        sheet.current_hp = data["current_hp"]
        sheet.current_composure = data["current_composure"]
        sheet.active_stamina = data["active_stamina"]
        sheet.active_focus = data["active_focus"]
        sheet.level = data.get("level", 1)
        sheet.xp = data.get("xp", 0)
        sheet.skills = data.get("skills", [])
        sheet.unspent_stat_points = data.get("unspent_stat_points", 0)
        sheet.unspent_skill_points = data.get("unspent_skill_points", 0)
        sheet.trauma_tokens = data["trauma_tokens"]
        sheet.is_stabilized = data["is_stabilized"]
        sheet.has_disadvantage = data["has_disadvantage"]
        
        # Load Inventory
        if "inventory" in data:
            inv_data = data["inventory"]
            sheet.inventory.gold = inv_data.get("gold", 0)
            for slot_key, item_data in inv_data.get("slots", {}).items():
                if item_data:
                    item = Item(item_data["name"], item_data["item_type"], item_data["stat_type"], 
                                item_data["modifier"], item_data["loadout_cost"], item_data.get("quantity", 1),
                                item_data.get("consumable_effect", {}), item_data.get("tags", []))
                    sheet.inventory.equip(item, target_slot=slot_key)
                    
        return sheet
