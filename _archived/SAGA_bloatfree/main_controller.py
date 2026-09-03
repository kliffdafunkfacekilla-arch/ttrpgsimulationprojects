import sys
import json
import random

# ==============================================================================
# CRITICAL WINDOWS FIX: 
# llama_cpp must be initialized BEFORE PyQt6 is imported, otherwise it causes
# a memory access violation (0x00000000) during backend initialization.
# ==============================================================================
from ai_dm.director import AIDirector
print("Pre-initializing AI Director to prevent PyQt6 conflict...")
GLOBAL_AI = AIDirector()

from PyQt6.QtWidgets import QApplication
from frontend.app import SagaDesktopApp
# Clean Modules
from world_manager.simulation import WorldSimulator
from world_manager.map_generator import ClusterManager
from rules_engine.clash_calculator import ClashCalculator
from rules_engine.character_sheet import CharacterSheet
from rules_engine.inventory import Item
from world_manager.npc_ai import NPCAI
from story_manager.quest_weaver import QuestWeaver, GruntPack

class SimpleAI:
    def parse_intent(self, intent_raw: str) -> dict:
        parts = intent_raw.split()
        target = parts[0] if parts else ""
        return {"target": target}

    def generate_llm_prompt(self, mechanical_result: str, context: str) -> str:
        return f"Mechanics: {mechanical_result}\nContext:{context}"

class SimpleLore:
    def get_context_for_location(self, target: str) -> str:
        return f"No lore available for {target}."

class SagaMessageBus:
    def __init__(self):
        self.subscribers = {}
    def subscribe(self, event_type, callback):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
    def publish(self, event_type, payload=None):
        print(f"EVENT DISPATCHED - Type: {event_type}, Payload: {payload}")
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                callback(payload)

class SagaController:
    def __init__(self):
        self.bus = SagaMessageBus()
        self.ai = GLOBAL_AI
        
        self.app = QApplication(sys.argv)
        
        self.world = WorldSimulator()
        self.rules = ClashCalculator()
        self.story = QuestWeaver()
        self.npc_ai = NPCAI()
        self.lore = SimpleLore()
        self.map_engine = ClusterManager()
        
        self.party = []
        self.active_party_member_idx = 0
        self.player = None
        
        self.chaos_ticks = 0
        self.chaos_number = random.randint(1, 20)
        self.in_zero_state = False
        self.zero_state_turn = 0
        
        self.stealth_mode = False
        
        # Phase 2 Initiative State
        self.combat_active = False
        self.turn_order = []
        self.current_turn_idx = 0
        self.active_clash_target = None
        
        self.ui = SagaDesktopApp(self.bus)
        self._wire_events()
        
        self.player_cx = 12
        self.player_cy = 12
        self.player_px = 50
        self.player_py = 50
        
    def _init_world(self, payload=None):
        self.story.initialize_campaign(self.player_cx, self.player_cy)
        poi_coords = [[14, 22]]
        self.map_engine.generate_cluster(region_id=1, base_biome="Forest", poi_coords=poi_coords, poi_context="Starting Zone")
        self._update_map_render()
        self._update_hud()
        
    def _trigger_chaos_event(self):
        if not hasattr(self, 'current_battlemap') or self.current_battlemap is None:
            return
            
        # Chapter 6: Zone Envelopment (Reality Shattering)
        self.chaos_ticks = 0 # Reset tracker after shatter
        self.chaos_number = random.randint(1, 20)
        
        envelopment_table = [
            "Gravity Flip: Ground actions cost 0 Stamina; occupants must 'swim' to stay in place.",
            "Entropy Flip: Roll Low to succeed (1 is a Critical, 20 is a Fail). Disadvantage becomes Advantage.",
            "Thermal Swap: Fire/Acid heal; healing and regeneration deal Burn damage.",
            "Mirror Ego: All entities swap physical positions and current HP with their nearest enemy.",
            "The Floor is Vapor: Ground is Incorporeal; must use furniture or Vertical surfaces to avoid the void.",
            "Hyper-Lethality: Armor Mods are reduced to 0; all HP and Composure damage is doubled."
        ]
        
        effect = random.choice(envelopment_table)
        
        if "global_tags" not in self.current_battlemap:
            self.current_battlemap["global_tags"] = []
        self.current_battlemap["global_tags"].append(f"REALITY SHATTER: {effect}")
        
        narrative_context = f"ZONE ENVELOPMENT! The local reality completely shatters under the weight of the Drift. NEW PHYSICS: {effect}"
            
        prompt_res = self.ai.generate_llm_prompt("A chaotic breakdown of reality occurs.", narrative_context)
        self.bus.publish("NARRATIVE_OUTPUT", {"response": prompt_res})
        self.bus.publish("SYSTEM_LOG", narrative_context)
        
        self.bus.publish("MAP_RENDER", {
            "battlemap": self.current_battlemap,
            "px": self.player_px, "py": self.player_py,
            "cx": self.player_cx, "cy": self.player_cy
        })

    def _inject_story_node(self, hook: dict):
        self.current_hook = hook
        if "entities" not in self.current_battlemap:
            self.current_battlemap["entities"] = []
            
        narrative_context = f"STORY NODE REACHED: {self.current_hook['objective']}"
            
        pack = self.current_hook.get("grunt_pack")
        social = self.current_hook.get("social_pack")
        hazard = self.current_hook.get("hazard_pack")
        
        if pack:
            for i in range(pack.get("count", 0)):
                ent_name = f"{pack['name']} {i+1}"
                ent_x = random.randint(30, 70)
                ent_y = random.randint(30, 70)
                self.current_battlemap["entities"].append({
                    "name": ent_name, "x": ent_x, "y": ent_y,
                    "health": 10 + (pack.get("level", 1) * 2),
                    "personality": "Hostile", "task": f"Executing objective: {self.current_hook['objective']}"
                })
                if ent_name not in self.rules.entities:
                    self.rules.register_entity(CharacterSheet(ent_name, {"might": 6, "reflexes": 5, "endurance": 5}))
            narrative_context += f" The party is confronted by {pack['count']} {pack['name']} ({pack['pack_type']})."
            
        if social:
            ent_name = social['name']
            ent_x = 50; ent_y = 50
            self.current_battlemap["entities"].append({
                "name": ent_name, "x": ent_x, "y": ent_y, "health": 10,
                "personality": social["personality"], "task": "Waiting to be interacted with."
            })
            if ent_name not in self.rules.entities:
                self.rules.register_entity(CharacterSheet(ent_name, {"might": 3, "reflexes": 3, "endurance": 3}))
            narrative_context += f" You see a {ent_name} looking {social['personality']}."
            
        if hazard:
            ent_name = hazard['name']
            ent_x = 50; ent_y = 50
            self.current_battlemap["entities"].append({
                "name": ent_name, "x": ent_x, "y": ent_y, "health": 50,
                "personality": "Hazard", "task": "Trap or Puzzle"
            })
            if ent_name not in self.rules.entities:
                self.rules.register_entity(CharacterSheet(ent_name, {"might": 1, "reflexes": 1, "endurance": 10}))
            narrative_context += f" WARNING: The area contains a {ent_name}!"
            
        prompt_res = self.ai.generate_llm_prompt("The party arrived at a key location.", narrative_context)
        self.bus.publish("NARRATIVE_OUTPUT", {"response": prompt_res})

    def _update_map_render(self):
        if not hasattr(self, 'current_battlemap') or self.current_battlemap is None:
            self.current_battlemap = self.map_engine.get_battlemap(self.player_cx, self.player_cy)
            
            hook = self.story.check_for_story_node(self.player_cx, self.player_cy, party_level=1)
            if hook:
                self._inject_story_node(hook)
                
        self.bus.publish("MAP_RENDER", {
            "battlemap": self.current_battlemap,
            "px": self.player_px,
            "py": self.player_py,
            "cx": self.player_cx,
            "cy": self.player_cy
        })

    def _update_hud(self):
        if self.player:
            self.bus.publish("HUD_UPDATE", {
                "name": self.player.name,
                "hp": self.player.current_hp,
                "max_hp": self.player.max_hp,
                "stamina": self.player.active_stamina,
                "max_stamina": self.player.max_stamina,
                "focus": self.player.active_focus,
                "max_focus": self.player.max_focus,
                "trauma": self.player.trauma_tokens,
                "level": self.player.level,
                "xp": self.player.xp,
                "unspent_stat": self.player.unspent_stat_points,
                "reserve_pool": self.player.get_reserve_pool(),
                "stats": self.player.stats,
                "inventory": self.player.inventory.to_dict(),
                "physical_tax": self.player.inventory.get_physical_tax(),
                "mental_tax": self.player.inventory.get_mental_tax(),
                "injury_tallies": self.player.injury_tallies,
                "active_bleed": self.player.active_bleed,
                "active_trauma": self.player.active_trauma,
                "is_zero_state": self.player.is_zero_state
            })
        else:
            self.bus.publish("SYSTEM_LOG", "HUD_UPDATE skipped: no player initialized.")

    def _wire_events(self):
        self.bus.subscribe("PLAYER_ACTION", self.handle_player_action)
        self.bus.subscribe("UI_FINALIZE_PARTY", self._finalize_party_and_start)
        self.bus.subscribe("UI_LOAD_GAME", lambda p: self.load_state())
        self.bus.subscribe("UI_CHARACTER_REST", self._handle_character_rest)
        self.bus.subscribe("VENDOR_BUY_ITEM", self._handle_buy_item)
        
    def _handle_buy_item(self, payload):
        item_name = payload.get("item_name")
        if not hasattr(self, "current_vendor_items") or not item_name: return
        
        for item in self.current_vendor_items:
            if item["name"].lower() == item_name.lower():
                if self.player.inventory.gold >= item["cost"]:
                    self.player.inventory.gold -= item["cost"]
                    from rules_engine.inventory import Item
                    new_item = Item(item["name"], "misc", "none", 0, 1) # simple mapping
                    self.player.inventory.bag.append(new_item)
                    self.bus.publish("SYSTEM_LOG", f"Bought {item['name']} for {item['cost']} Gold.")
                    self.bus.publish("VENDOR_DATA_UPDATE", {
                        "vendor_name": getattr(self, "current_vendor_name", "Vendor"),
                        "player_gold": self.player.inventory.gold,
                        "items": self.current_vendor_items
                    })
                    self._update_hud()
                else:
                    self.bus.publish("SYSTEM_LOG", f"Not enough Gold to buy {item['name']}.")
                return
        self.bus.publish("SYSTEM_LOG", f"Vendor does not sell '{item_name}'.")
        self.bus.subscribe("UI_CHARACTER_UPGRADE_STAT", self._handle_upgrade_stat)
        
        self.bus.subscribe("UI_INVENTORY_EQUIP", self._handle_inventory_equip)
        self.bus.subscribe("UI_INVENTORY_UNEQUIP", self._handle_inventory_unequip)
        
        self.bus.subscribe("UI_TOGGLE_STEALTH", self._handle_toggle_stealth)
        self.bus.subscribe("UI_LONG_REST", self._handle_long_rest)
        self.bus.subscribe("PLAYER_ACTION_UI_INJECT", self._handle_injected_action)
        
    def _handle_injected_action(self, payload):
        intent = payload.get("intent", "")
        self.bus.publish("SYSTEM_LOG", f"[PLAYER] {intent}")
        self.handle_player_action(payload)
        
    def _handle_toggle_stealth(self, payload):
        self.stealth_mode = payload.get("stealth", False)
        
    def _handle_long_rest(self, payload=None):
        if self.player:
            self.player.current_hp = self.player.max_hp
            self.player.active_stamina = self.player.max_stamina
            self.player.active_focus = self.player.max_focus
            
            self.world.advance_time(ticks=8)
            sim_messages = self.map_engine.tick_simulation(hours=8)
            
            self.bus.publish("SYSTEM_LOG", f"{self.player.name} sets up camp and rests for 8 hours. Vitals fully restored.")
            for msg in sim_messages:
                self.bus.publish("SYSTEM_LOG", msg)
                
            self._update_hud()
            
    def _finalize_party_and_start(self, payload):
        sheet = CharacterSheet(payload["name"], payload["stats"], payload["origin"])
        sheet.inventory.equip(Item("Rusty Broadsword", "weapon", "might", 2, 1))
        
        self.party = [sheet]
        self.active_party_member_idx = 0
        self.player = sheet
        self.rules.register_entity(sheet)
        self._init_world()
        
    def _handle_character_rest(self, payload=None):
        if self.player:
            reserve = self.player.get_reserve_pool()
            if reserve > 0:
                self.player.active_stamina = self.player.max_stamina
                self.player.active_focus = self.player.max_focus
                self.bus.publish("SYSTEM_LOG", f"{self.player.name} burns reserve pool to restore Stamina and Focus.")
            else:
                self.bus.publish("SYSTEM_LOG", f"{self.player.name} has no reserves left! Must take a full rest in a safe zone.")
            self._update_hud()
            
    def _handle_upgrade_stat(self, payload):
        if self.player:
            stat_name = payload.get("stat")
            if self.player.spend_stat_point(stat_name):
                self.bus.publish("SYSTEM_LOG", f"Upgraded {stat_name}. Unspent points remaining: {self.player.unspent_stat_points}.")
                self._update_hud()
                
    def _handle_inventory_equip(self, payload):
        if self.player:
            index = payload.get("index")
            if 0 <= index < len(self.player.inventory.bag):
                item = self.player.inventory.bag.pop(index)
                target_slot = item.item_type
                
                # Check if slot is occupied
                existing_item = self.player.inventory.slots.get(target_slot)
                if existing_item:
                    self.player.inventory.bag.append(existing_item)
                    
                if self.player.inventory.equip(item, target_slot):
                    self.bus.publish("SYSTEM_LOG", f"{self.player.name} equipped {item.name}.")
                else:
                    self.player.inventory.bag.append(item)
                    self.bus.publish("SYSTEM_LOG", f"Failed to equip {item.name}. No valid slot.")
                    
                self._update_hud()
                
    def _handle_inventory_unequip(self, payload):
        if self.player:
            slot = payload.get("slot")
            if slot in self.player.inventory.slots and self.player.inventory.slots[slot]:
                item = self.player.inventory.slots[slot]
                self.player.inventory.slots[slot] = None
                self.player.inventory.bag.append(item)
                self.bus.publish("SYSTEM_LOG", f"{self.player.name} unequipped {item.name}.")
                self._update_hud()
                
    def handle_player_action(self, payload):
        intent_raw = payload.get("intent", "").lower()
        
        # Handle Clash Tactic Input
        if self.active_clash_target:
            valid_tactics = ["press", "hold", "maneuver", "trick", "feint", "disengage"]
            tactic = next((t for t in valid_tactics if t in intent_raw), None)
            if not tactic:
                self.bus.publish("SYSTEM_LOG", "Invalid Clash Tactic. Choose: Press, Hold, Maneuver, Trick, Feint, or Disengage.")
                return
                
            ai_tactic = random.choice(valid_tactics)
            clash_res = self.rules.resolve_clash("Player", self.active_clash_target, tactic, ai_tactic)
            
            if not clash_res.get("is_clash"):
                self.active_clash_target = None
                
            self.bus.publish("SYSTEM_LOG", clash_res["narrative_hint"])
            prompt = self.ai.generate_llm_prompt(str(clash_res), "Describe the intense clash resolution.")
            self.bus.publish("NARRATIVE_OUTPUT", {"response": prompt})
            self._update_hud()
            return
        
        # Handle Continuous Damage (The Descent)
        if self.player.active_bleed:
            self.player.take_damage(1)
            self.bus.publish("SYSTEM_LOG", f"[CONTINUOUS DAMAGE] {self.player.name} suffers 1 HP loss from active Bleeding.")
            
        if self.player.active_trauma:
            self.player.take_damage(1, is_composure=True)
            self.bus.publish("SYSTEM_LOG", f"[CONTINUOUS DAMAGE] {self.player.name} suffers 1 Composure loss from active Trauma.")
            
        if self.player.is_zero_state:
            # Waking Up Adrenaline Check logic could go here in Phase 2
            if intent_raw not in ["/save", "/load", "/swap"]:
                msg = f"{self.player.name} is in the Zero-State and has collapsed. They cannot act!"
                self.bus.publish("SYSTEM_LOG", msg)
                mech_res = {"action": intent_raw, "success": False, "narrative_hint": msg}
                prompt = self.ai.generate_llm_prompt(str(mech_res), "The player is dying or catatonic.")
                self.bus.publish("LLM_STREAM_REQUEST", prompt)
                self._update_hud()
                return
        
        if self.stealth_mode and not intent_raw.startswith("sneak"):
            intent_raw = f"sneak and {intent_raw}"
        
        if intent_raw == "/save":
            self.save_state()
            return
        elif intent_raw == "/load":
            self.load_state()
            return
        elif intent_raw == "/swap":
            self.active_party_member_idx = (self.active_party_member_idx + 1) % len(self.party)
            self.player = self.party[self.active_party_member_idx]
            self._update_hud()
            self.bus.publish("SYSTEM_LOG", f"Swapped active character to {self.player.name}.")
            return
            
        moved = False
        rested = False
        if "rest" in intent_raw or "camp" in intent_raw or "wait" in intent_raw:
            rested = True
        elif "walk north" in intent_raw or "move north" in intent_raw:
            self.player_py -= 1; moved = True
        elif "walk south" in intent_raw or "move south" in intent_raw:
            self.player_py += 1; moved = True
        elif "walk east" in intent_raw or "move east" in intent_raw:
            self.player_px += 1; moved = True
        elif "walk west" in intent_raw or "move west" in intent_raw:
            self.player_px -= 1; moved = True
        elif "move to" in intent_raw:
            # Parse 'move to X Y'
            parts = intent_raw.replace("sneak and ", "").split()
            try:
                tx = int(parts[2])
                ty = int(parts[3])
                # Move 1 step towards target
                if tx > self.player_px: self.player_px += 1
                elif tx < self.player_px: self.player_px -= 1
                
                if ty > self.player_py: self.player_py += 1
                elif ty < self.player_py: self.player_py -= 1
                
                moved = True
            except (ValueError, IndexError):
                pass
            
        # Handle zero-state (cannot act, but can move and regenerates)
        if not moved and self.player.active_stamina <= 0 and self.player.active_focus <= 0:
            stam_regen = 1 if self.player.is_physically_encumbered() else 2
            focus_regen = 1 if self.player.is_mentally_encumbered() else 2
            
            self.player.active_stamina = min(self.player.max_stamina, self.player.active_stamina + stam_regen)
            self.player.active_focus = min(self.player.max_focus, self.player.active_focus + focus_regen)
            
            if stam_regen == 1 and focus_regen == 1:
                msg = f"{self.player.name} is in the Zero-State and cannot act! Due to extreme encumbrance (Physical & Mental), they only recover +1 Stamina and +1 Focus."
            elif stam_regen == 1:
                msg = f"{self.player.name} is in the Zero-State and cannot act! Due to Physical encumbrance, they only recover +1 Stamina and +2 Focus."
            elif focus_regen == 1:
                msg = f"{self.player.name} is in the Zero-State and cannot act! Due to Mental encumbrance, they only recover +2 Stamina and +1 Focus."
            else:
                msg = f"{self.player.name} is in the Zero-State and cannot act! They spend their turn recovering +2 Stamina and +2 Focus."
                
            self.bus.publish("SYSTEM_LOG", msg)
            mech_res = {"action": intent_raw, "success": False, "narrative_hint": msg}
            prompt = self.ai.generate_llm_prompt(str(mech_res), "The player is exhausted and skipped their turn to recover.")
            self.bus.publish("NARRATIVE_OUTPUT", {"response": prompt})
            self._update_hud()
            return
            
        if self.player_px < 0:
            self.player_px = 99; self.player_cx -= 1; self.current_battlemap = None
        elif self.player_px > 99:
            self.player_px = 0; self.player_cx += 1; self.current_battlemap = None
        if self.player_py < 0:
            self.player_py = 99; self.player_cy -= 1; self.current_battlemap = None
        elif self.player_py > 99:
            self.player_py = 0; self.player_cy += 1; self.current_battlemap = None
            
        if moved:
            if not self.current_battlemap:
                self._update_map_render()
                
            chaos = self.world.global_chaos
            self.tension_meter += (0.02 + (chaos * 0.01))
            
            if random.random() < self.tension_meter:
                self.tension_meter = 0.0
                self._trigger_chaos_event()
                
            entities = self.current_battlemap.get("entities", [])
            grid = self.current_battlemap.get("grid", [])
            self.npc_ai.tick(entities, grid, self.player_px, self.player_py)
            
            self._update_map_render()
            self.world.advance_time()
            
            sim_messages = self.map_engine.tick_simulation(hours=1)
            for msg in sim_messages:
                self.bus.publish("SYSTEM_LOG", msg)
            return
            
        if rested:
            tags = self.current_battlemap.get('global_tags', [])
            is_hazard = any("hazard" in t.lower() for t in tags) or self.combat_active
            if is_hazard:
                self.chaos_ticks += 8
                self.bus.publish("SYSTEM_LOG", "⚠️ Resting in a hazardous zone caused the Chaos Tracker to skyrocket by +8 Ticks!")
                if self.chaos_ticks >= 10:
                    self._trigger_chaos_event()
            else:
                self.player.active_stamina = self.player.max_stamina
                self.player.active_focus = self.player.max_focus
                self.bus.publish("SYSTEM_LOG", f"{self.player.name} rested safely and fully recovered.")
                self.world.advance_time(8)
            self._update_hud()
            return
        
        intent_json = self.ai.parse_intent(intent_raw)
        target = intent_json.get("target", "Goblin")
        
        entities = self.current_battlemap.get("entities", [])
        grid = self.current_battlemap.get("grid", [])
        self.npc_ai.tick(entities, grid, self.player_px, self.player_py)
        self._update_map_render()
        self.world.advance_time()
        
        sim_messages = self.map_engine.tick_simulation(hours=1)
        for msg in sim_messages:
            self.bus.publish("SYSTEM_LOG", msg)
            
        lore = self.lore.get_context_for_location(target)
        personality_context = ""
        for ent in entities:
            if ent["name"].lower() in target.lower() or target.lower() in ent["name"].lower():
                p = ent.get("personality", "neutral")
                t = ent.get("task", "standing around")
                personality_context = f"\nNPC DATA: The target is {ent['name']}. They are currently {t}. Their personality is: {p}."
        
        journal_summary = self.story.journal.get_journal_summary(self.player_cx, self.player_cy)
        explicit_hook_directive = f"\nSYSTEM DIRECTIVE: Narrate within this active context. Active Quests:\n{journal_summary}\nCURRENT LOCAL OBJECTIVE: {self.current_hook.get('objective', 'Wandering')}"
        
        matched_target = None
        for ent in entities:
            if ent["name"].lower() in intent_raw.lower():
                matched_target = ent["name"]
                break
                
        if matched_target:
            target = matched_target
            
        if "trade with" in intent_raw.lower():
            self._handle_vendor_trade(target)
            return
            
        weather_state = self.current_battlemap.get('weather', 'Clear')
        weather_tags = self.current_battlemap.get('global_tags', [])
            
        if target not in self.rules.entities:
            # Check if this is a hostile action to initiate combat
            if any(word in intent_raw for word in ["attack", "strike", "shoot", "kill", "destroy", "hit"]):
                from rules_engine.character_sheet import CharacterSheet
                from rules_engine.inventory import Item
                
                self.bus.publish("SYSTEM_LOG", f"⚔️ COMBAT INITIATED! Constructing Encounter Deck...")
                
                # Room Deck & Twist Deck
                room_tags = ["Normal Terrain"]
                twist_tags = random.choice([["Conductive", "Volatile"], ["Brittle", "Hazard: Sharp"], ["Slowing", "Concealing"], []])
                
                # Twist Override Rule
                active_tags = twist_tags if twist_tags else room_tags
                self.current_battlemap["global_tags"] = active_tags
                
                # Environmental Telegraphing
                perc_threshold = self.player.get_stat("awareness") + self.player.get_stat("logic") + self.player.get_stat("vitality")
                if perc_threshold >= 14:
                    self.bus.publish("SYSTEM_LOG", f"👁️ [PERCEPTION {perc_threshold}]: You notice the terrain has hidden tags: {', '.join(active_tags)}.")
                else:
                    self.bus.publish("SYSTEM_LOG", f"👁️ [PERCEPTION {perc_threshold}]: The environment seems hostile but you lack tactical specifics.")
                    
                # Threat Scaling Matrix
                num_players = len(self.party) if self.party else 1
                elites = 1
                grunts = 1
                if num_players >= 3: elites = 2; grunts = 2
                if num_players >= 5: grunts = 3
                
                self.turn_order = [self.player]
                
                # Generate Elites
                for i in range(elites):
                    elite_name = f"{target} Elite {i+1}" if i > 0 else target
                    enemy_sheet = CharacterSheet(elite_name, {"might": 8, "reflexes": 5, "endurance": 10}, origin="Spawned Elite")
                    enemy_sheet.inventory.equip(Item("Heavy Cleaver", "weapon", "might", 3, 2))
                    enemy_sheet.inventory.equip(Item("Plating", "body", "endurance", 1, 2))
                    self.rules.register_entity(enemy_sheet)
                    self.turn_order.append(enemy_sheet)
                    
                # Generate Grunts
                for i in range(grunts * 3):
                    grunt_name = f"{target} Grunt {i+1}"
                    enemy_sheet = CharacterSheet(grunt_name, {"might": 3, "reflexes": 3, "endurance": 1}, origin="Spawned Grunt")
                    enemy_sheet.current_hp = 1
                    enemy_sheet.max_hp = 1
                    enemy_sheet.inventory.equip(Item("Shiv", "weapon", "finesse", 1, 0))
                    self.rules.register_entity(enemy_sheet)
                    self.turn_order.append(enemy_sheet)
                
                self.combat_active = True
                self.turn_order.sort(key=lambda x: x.get_derived_stat("movement"), reverse=True)
                
                # Retarget to the first enemy spawned
                if target not in self.rules.entities:
                    target = next((e.name for e in self.turn_order if e.name != "Player"), "Unknown")
            else:
                biome = self.current_battlemap.get('biome', 'Unknown Terrain')
                visible_names = [e['name'] for e in entities]
                env_desc = f"You are in a {biome}. Weather is {weather_state}. Visible entities: {', '.join(visible_names) if visible_names else 'None'}."
                mechanical_result = {"action": intent_raw, "success": True, "narrative_hint": f"[WEATHER: {weather_state}] The player interacts with or observes their surroundings. Environment: {env_desc}"}
                
        if target in self.rules.entities:
            chaos_state_in = {"ticks": self.chaos_ticks, "number": self.chaos_number}
            mechanical_result = self.rules.resolve_action(intent_raw, "Player", target, weather=weather_state, global_tags=weather_tags, chaos_state=chaos_state_in)
            
            c_state = mechanical_result.get("chaos_state")
            if c_state:
                self.chaos_ticks = c_state["ticks"]
                self.chaos_number = c_state["number"]
                if self.chaos_ticks >= 10:
                    self._trigger_chaos_event()
            
            if mechanical_result.get("is_clash"):
                self.active_clash_target = target
                msg = f"⚔️ CLASH INITIATED! You are deadlocked with {target}! Type your Clash Tactic (Press, Hold, Maneuver, Trick, Feint, Disengage):"
                self.bus.publish("SYSTEM_LOG", msg)
                self.bus.publish("NARRATIVE_OUTPUT", {"response": msg})
                self._update_hud()
                return
                
            # If combat is active, process all AI turns instantly
            if self.combat_active:
                ai_narratives = []
                for combatant in self.turn_order:
                    if combatant.name != "Player" and combatant.current_hp > 0:
                        ai_intent = "attacks Player"
                        c_in = {"ticks": self.chaos_ticks, "number": self.chaos_number}
                        ai_res = self.rules.resolve_action(ai_intent, combatant.name, "Player", weather=weather_state, global_tags=weather_tags, chaos_state=c_in)
                        
                        c_out = ai_res.get("chaos_state")
                        if c_out:
                            self.chaos_ticks = c_out["ticks"]
                            self.chaos_number = c_out["number"]
                            if self.chaos_ticks >= 10:
                                self._trigger_chaos_event()
                                
                        if ai_res.get("is_clash"):
                            self.active_clash_target = combatant.name
                            msg = f"⚔️ CLASH INITIATED! {combatant.name} locked weapons with you! Type your Clash Tactic (Press, Hold, Maneuver, Trick, Feint, Disengage):"
                            self.bus.publish("SYSTEM_LOG", msg)
                            self.bus.publish("NARRATIVE_OUTPUT", {"response": msg})
                            self._update_hud()
                            return
                            
                        ai_narratives.append(ai_res.get("narrative_hint", ""))
                        
                if ai_narratives:
                    mechanical_result["narrative_hint"] += "\n[ENEMY TURNS]:\n" + "\n".join(ai_narratives)
            
        self.story.log_beat(intent_raw, str(mechanical_result))
        self._update_hud()
        
        prompt = self.ai.generate_llm_prompt(str(mechanical_result), lore + explicit_hook_directive + personality_context)
        self.bus.publish("NARRATIVE_OUTPUT", {"response": prompt})

    def _handle_vendor_trade(self, vendor_name: str):
        self.bus.publish("SYSTEM_LOG", f"Generating dynamic vendor inventory for {vendor_name}...")
        
        biome = self.current_battlemap.get('biome', 'Unknown Terrain')
        lore = self.lore.get_context_for_location(vendor_name)
        
        prompt = f"The player wants to trade with a vendor named {vendor_name} in {biome}. Based on this lore: {lore}. Generate exactly 3 unique items for sale. Return ONLY valid JSON in this exact format, with no markdown formatting or backticks: [{{ \"name\": \"Item Name\", \"cost\": 50, \"desc\": \"What it does\" }}]"
        
        response = self.ai.generate_llm_prompt(prompt, "You are a JSON data generator. Do NOT use markdown. Do NOT wrap in ```json.")
        
        import json
        try:
            items = json.loads(response.strip().replace("```json", "").replace("```", ""))
        except json.JSONDecodeError:
            self.bus.publish("SYSTEM_LOG", f"Failed to parse AI JSON for Vendor. Generating fallback items.")
            items = [
                {"name": "Health Salve", "cost": 25, "desc": "Restores 10 HP."},
                {"name": "Stamina Brew", "cost": 15, "desc": "Restores full stamina."},
                {"name": "Focus Crystal", "cost": 40, "desc": "Restores full focus."}
            ]
            
        self.current_vendor_items = items
        self.current_vendor_name = vendor_name
        self.bus.publish("UI_OPEN_VENDOR", {})
        self.bus.publish("VENDOR_DATA_UPDATE", {
            "vendor_name": vendor_name,
            "player_gold": self.player.inventory.gold,
            "items": items
        })

    def save_state(self, filepath: str = "saves/quicksave.json"):
        import os
        os.makedirs("saves", exist_ok=True)
        entities_data = {name: sheet.to_dict() for name, sheet in self.rules.entities.items()}
        state = {
            "player_coords": {
                "cx": self.player_cx, "cy": self.player_cy,
                "px": self.player_px, "py": self.player_py
            },
            "rules_registry": entities_data,
            "map_engine": self.map_engine.to_dict(),
            "story": self.story.to_dict()
        }
        with open(filepath, "w") as f:
            json.dump(state, f, indent=4)
        self.bus.publish("SYSTEM_LOG", f"Game saved to {filepath}.")
        
    def load_state(self, filepath: str = "saves/quicksave.json"):
        import os
        if not os.path.exists(filepath):
            self.bus.publish("SYSTEM_LOG", "Save file not found.")
            return
        with open(filepath, "r") as f:
            state = json.load(f)
        coords = state.get("player_coords", {})
        self.player_cx = coords.get("cx", 12)
        self.player_cy = coords.get("cy", 12)
        self.player_px = coords.get("px", 50)
        self.player_py = coords.get("py", 50)
        self.rules.entities.clear()
        for name, sheet_data in state.get("rules_registry", {}).items():
            sheet = CharacterSheet.from_dict(sheet_data)
            self.rules.register_entity(sheet)
            if name.startswith("Player"):
                self.party.append(sheet)
        if self.party:
            self.player = self.party[0]
        if "map_engine" in state:
            self.map_engine = ClusterManager.from_dict(state["map_engine"])
        if "story" in state:
            self.story = QuestWeaver.from_dict(state["story"])
        self.current_battlemap = None
        self._update_map_render()
        self._update_hud()
        self.bus.publish("SYSTEM_LOG", "Game loaded.")

    def run(self):
        self.ui.show()
        sys.exit(self.app.exec())

if __name__ == "__main__":
    controller = SagaController()
    controller.run()
