"""
Provides the main application window that orchestrates all UI screens and background workers.
"""
from PyQt6.QtWidgets import QMainWindow, QStackedWidget
from PyQt6.QtCore import pyqtSlot

# --- Beta Architecture ---
from ui.components.event_bus import EventBus
from ai.director.llm_worker import LLMWorker
from ai.director.llm_director import AIDirector
from audio.audio_manager import TTSWorker, STTWorker
from core.models.character_sheet import CharacterSheet
from beta_build.core.campaign_manager import CampaignManager
from beta_build.core.save_manager import SaveManager
from beta_build.core.macro_simulator import MacroSimulator
from data.chromadb.memory_store import MemoryStore
from core.world_gen.world_gen_worker import WorldGenWorker
from beta_build.core.journey_manager import JourneyManager
from core.combat.action_resolver import ActionResolver
from beta_build.core.anomaly_resolver import AnomalyResolver
from core.combat.combat_manager import CombatManager

# --- Frontend Components ---
from ui.screens.char_creation import CharacterCreationScreen
from beta_build.ui.character_management import CharacterManagementScreen

from core.mechanics.turn_manager import TurnManager
from core.combat.zone_manager import ZoneManager
from core.mechanics.command_parser import CommandParser
from beta_build.core.enemy_ai import EnemyAIEngine
from ui.views.map_view import MapCanvas
from ui.screens.game_screens import StartMenu, VendorScreen, WorldMapScreen

class SagaDesktopApp(QMainWindow):
    """
    The main window for the S.A.G.A Engine.
    Handles the initialization of background workers (LLM, Audio), the central EventBus,
    and the StackedWidget to navigate between UI views.
    """
    def __init__(self):
        super().__init__()
        self.bus = EventBus()
        self.setWindowTitle("S.A.G.A. Engine Beta")
        self.setGeometry(100, 100, 1600, 900)
        self.showMaximized()
        
        premium_css = """
        QMainWindow { background-color: #0f1115; }
        QWidget { color: #d8d8d8; font-family: 'Segoe UI', Arial, sans-serif; }
        QPushButton {
            background-color: #1c2026;
            border: 1px solid #3a414c;
            border-radius: 4px;
            color: #4CAF50;
            padding: 8px 16px;
            font-weight: bold;
            font-size: 14px;
        }
        QPushButton:hover { background-color: #2b323b; border: 1px solid #4CAF50; }
        QPushButton:pressed { background-color: #4CAF50; color: #0f1115; }
        QLabel { font-size: 14px; }
        QTextEdit, QLineEdit, QComboBox, QSpinBox {
            background-color: #14171c;
            border: 1px solid #2b323b;
            border-radius: 3px;
            color: #e0e0e0;
            padding: 6px;
        }
        QTextEdit:focus, QLineEdit:focus { border: 1px solid #4CAF50; }
        """
        # Boot state
        self._pending_boot_location = "Aloa"
        
        self.setStyleSheet(premium_css)
        
        # UI Stack
        self.stack = QStackedWidget()
        
        # Initialize UI Screens
        self.start_menu = StartMenu(self.bus)
        self.char_creation = CharacterCreationScreen(self.bus)
        self.map_canvas = MapCanvas(self.bus)
        self.char_management = CharacterManagementScreen(self.bus)
        self.vendor_screen = VendorScreen(self.bus)
        
        self.stack.addWidget(self.start_menu)      # 0
        self.stack.addWidget(self.char_creation)   # 1
        self.stack.addWidget(self.map_canvas)      # 2
        self.stack.addWidget(self.char_management) # 3
        self.stack.addWidget(self.vendor_screen)   # 4
        
        self.setCentralWidget(self.stack)
        
        # Navigation Subs
        self.bus.subscribe("UI_START_NEW_GAME", lambda p: self.stack.setCurrentIndex(1))
        self.bus.subscribe("UI_LOAD_GAME", self._on_load_game)
        self.bus.subscribe("UI_SAVE_GAME", self._on_save_game)
        self.bus.subscribe("UI_FINALIZE_PARTY", self._show_game)
        self.bus.subscribe("PLAYER_CREATED", self._on_player_created)
        
        self.bus.subscribe("UI_OPEN_CHAR_MANAGEMENT", lambda p: self.stack.setCurrentIndex(3))
        self.bus.subscribe("UI_CLOSE_CHAR_MANAGEMENT", lambda p: self.stack.setCurrentIndex(2))
        
        self.bus.subscribe("UI_OPEN_VENDOR", lambda p: self.stack.setCurrentIndex(4))
        self.bus.subscribe("UI_CLOSE_VENDOR", lambda p: self.stack.setCurrentIndex(2))
        
        self.bus.subscribe("UI_OPEN_WORLD_MAP", lambda p: self.stack.setCurrentIndex(5))
        self.bus.subscribe("UI_CLOSE_WORLD_MAP", lambda p: self.stack.setCurrentIndex(2))
        
        self.bus.subscribe("UI_REQUEST_WORLD_MAP", self._on_request_world_map)
        self.bus.subscribe("EDGE_TRANSITION_REQUESTED", self._on_edge_transition_requested)

        # Intent Execution Sub
        self.bus.subscribe("EXECUTE_INTENT", self._handle_intent)
        self.bus.subscribe("EXECUTE_AI_INTENT", self._handle_ai_intent)
        self.bus.subscribe("UI_TOGGLE_MIC", self._handle_mic_toggle)
        
        self.bus.subscribe("GENERATE_SAFE_MAP", lambda p: self.world_gen_worker.request_generation(p.get("location"), False))
        self.bus.subscribe("GENERATE_AMBUSH_MAP", lambda p: self.world_gen_worker.request_generation(p.get("location"), True))
        
        self.bus.subscribe("MAP_PAYLOAD_READY", self._on_map_payload_ready)
        self.bus.subscribe("SCENE_STABILIZED", self._on_scene_stabilized)
        self.bus.subscribe("COMBAT_RESOLVED", self._on_combat_resolved)
        
        self.bus.subscribe("AI_NARRATED", self._handle_ai_narrated)
        self.bus.subscribe("MECHANICS_TRIGGERED", self._handle_mechanics_triggered)
        self.bus.subscribe("LOOT_ACQUIRED", self._on_loot_acquired)
        self.bus.subscribe("SYSTEM_LOG", self._on_system_log)
        
        self.bus.subscribe("GENERATE_NEXT_NODE", self._handle_generate_next_node)
        self.bus.subscribe("EVALUATE_WORLD_MUTATION", self._handle_world_mutation)
        
        self.bus.subscribe("UI_INVENTORY_EQUIP", self._on_inventory_equip)
        self.bus.subscribe("UI_INVENTORY_UNEQUIP", self._on_inventory_unequip)

        # Background Workers Initialization
        self.init_workers()
        
        # Core State
        self.player_character = None
        self._pending_boot_location = None
        
        # Instantiate Backend State and Parser
        self.zone_manager = ZoneManager(self.bus)
        self.turn_manager = TurnManager(self.bus)
        self.enemy_ai = EnemyAIEngine(self.bus, self.zone_manager, self.turn_manager)
        self.command_parser = CommandParser(self.bus, self.zone_manager, self.turn_manager)
        self.ai_director = AIDirector(load_model=False)
        self.memory = MemoryStore()
        self.journey_manager = JourneyManager(self.bus)
        self.action_resolver = ActionResolver(self.bus)
        self.save_manager = SaveManager()
        self.anomaly_resolver = AnomalyResolver(self.bus)
        self.combat_manager = CombatManager(self.bus)
        self.macro_simulator = MacroSimulator()
        self.campaign_manager = CampaignManager(self.bus, self.macro_simulator)
        
        self.world_map_screen = WorldMapScreen(self.bus, self.macro_simulator)
        self.stack.addWidget(self.world_map_screen) # 5
        
        self.macro_x = 0.0
        self.macro_y = 0.0
        
        self.bus.subscribe("WORLD_TICK", lambda p: self.macro_simulator.simulate_tick())

    def init_workers(self):
        """Initializes and connects QThreads for background AI and audio tasks."""
        # 1. LLM Worker
        self.llm_worker = LLMWorker(self.bus, parent=self)
        self.llm_worker.token_generated.connect(self.map_canvas.on_token_received)
        self.llm_worker.generation_complete.connect(self._on_llm_complete)
        self.llm_worker.error_occurred.connect(self.map_canvas.on_error)
        self.llm_worker.start()

        # 2. TTS Worker
        self.tts_worker = TTSWorker(parent=self)
        self.tts_worker.error_occurred.connect(self.map_canvas.on_error)
        self.tts_worker.start()

        # 3. STT Worker
        self.stt_worker = STTWorker(parent=self)
        self.stt_worker.speech_recognized.connect(self.map_canvas.on_speech_recognized)
        self.stt_worker.error_occurred.connect(self.map_canvas.on_error)

        # 4. World Gen Worker
        self.world_gen_worker = WorldGenWorker(parent=self)
        self.world_gen_worker.map_ready.connect(self._on_worker_map_ready)
        self.world_gen_worker.error_occurred.connect(self.map_canvas.on_error)
        self.world_gen_worker.start()
        
    @pyqtSlot(dict)
    def _on_worker_map_ready(self, payload):
        self.bus.publish("MAP_PAYLOAD_READY", payload)
        
    def _show_game(self, payload=None):
        self.stack.setCurrentIndex(2)
        
        if not self.player_character:
            self.map_canvas.log_view.append("<font color='red'>[ERROR] No player character loaded.</font>")
            return
            
        # Hook up the Pydantic character state to the UI HUD
        self.bus.publish("HUD_UPDATE", {"character": self.player_character.model_dump()})
        
        if payload and payload.get("map_data"):
            self.map_canvas.log_view.append("<i><font color='#a0a0a0'>Engine resuming saved state...</font></i>\n")
            self.bus.publish("MAP_PAYLOAD_READY", payload.get("map_data"))
            return
            
        self.map_canvas.log_view.append("<i><font color='#a0a0a0'>Engine booting. The AI Game Master is designing the world...</font></i>\n")
        
        # 1. Generate the base map IMMEDIATELY so the user isn't staring at a blank screen
        location = "Aloa"
        # Set initial macro coordinates based on boot location
        self.macro_x, self.macro_y = self.macro_simulator.get_burg_coords(location)
            
        self._pending_boot_location = location
        self.bus.publish("GENERATE_SAFE_MAP", {"location": location})
        
    def _on_request_world_map(self, payload):
        self.bus.publish("UI_OPEN_WORLD_MAP", {
            "player_macro_x": self.macro_x, 
            "player_macro_y": self.macro_y
        })
        
    def _on_edge_transition_requested(self, payload):
        direction = payload.get("direction", "north")
        
        # Define travel step in macro coordinates
        step_size = 5.0
        
        if direction == "north":
            self.macro_y -= step_size
        elif direction == "south":
            self.macro_y += step_size
        elif direction == "east":
            self.macro_x += step_size
        elif direction == "west":
            self.macro_x -= step_size
            
        location_context = self.macro_simulator.get_location_context(self.macro_x, self.macro_y)
        self.bus.publish("SYSTEM_LOG", {"message": f"<font color='#00FF00'>[SYSTEM] Traveling {direction}. Entering: {location_context}.</font>"})
        
        stats = self.player_character.stats if self.player_character else {}
        self._pending_boot_location = location_context
        
        self.bus.publish("TRAVEL_REQUESTED", {"location": location_context, "stats": stats})

    def _on_save_game(self, payload):
        if not self.player_character: return
        
        # Enforce "Camp Save" only: Cannot save if hostile entities exist
        hostiles = [ent for ent in self.map_canvas.battle_map.entities.values() if hasattr(ent, 'tags') and "hostile" in ent.tags]
        if hostiles:
            self.map_canvas.log_view.append("<font color='red'>[SYSTEM] You cannot save while hostiles are nearby! Clear the area or find a camp first.</font>")
            return
            
        map_data = {
            "name": self.map_canvas.battle_map.map_name,
            "width": self.map_canvas.battle_map.grid_width,
            "height": self.map_canvas.battle_map.grid_height,
            "grid": [[t.model_dump() for t in row] for row in self.map_canvas.battle_map.grid],
            "entities": self.map_canvas.battle_map.entities
        }
        
        data = {
            "character": self.player_character.model_dump(),
            "campaign": {
                "current_node_id": self.campaign_manager.current_node_id,
                "remaining_dynamic_slots": self.campaign_manager.remaining_dynamic_slots,
                "nodes": self.campaign_manager.nodes
            },
            "map_data": map_data
        }
        
        if self.save_manager.save_game(1, data):
            self.bus.publish("SYSTEM_LOG", {"message": "<font color='#00FF00'>[SYSTEM] Game state saved successfully.</font>"})

    def _on_load_game(self, payload):
        data = self.save_manager.load_game(1)
        if not data:
            self.start_menu.append_log("<font color='red'>Failed to load game. No save file found.</font>")
            return
            
        from core.models.character_sheet import CharacterSheet
        self.player_character = CharacterSheet(**data.get("character", {}))
        
        camp_data = data.get("campaign", {})
        self.campaign_manager.current_node_id = camp_data.get("current_node_id")
        self.campaign_manager.remaining_dynamic_slots = camp_data.get("remaining_dynamic_slots", 0)
        self.campaign_manager.nodes = camp_data.get("nodes", {})
        
        # Switch to game view and pass the map data
        self._show_game({"map_data": data.get("map_data")})

    def _on_map_payload_ready(self, payload):
        """Called when WorldGen finishes. If entities are present, it's combat."""
        
        # Spawn the player in the center
        width = payload.get("width", 40)
        height = payload.get("height", 40)
        
        self.bus.publish("SPAWN_ENTITY", {
            "uuid": "player_1",
            "x": width // 2,
            "y": height // 2,
            "color": "gold",
            "name": self.player_character.name if self.player_character else "Wanderer",
            "tags": ["player"]
        })
        
        # Start combat / turn economy
        combatants = []
        if self.player_character:
            stats = self.player_character.stats
            combatants.append({"uuid": "player_1", "stats": stats})
        else:
            combatants.append({"uuid": "player_1", "stats": {"awareness": 5, "reflexes": 5, "logic": 5}})
            
        combatants.append({"uuid": "enemy_stub", "stats": {"awareness": 3, "reflexes": 3, "logic": 3}})
        
        self.turn_manager.start_combat(combatants)
        
        # Now that the map is ready, we wait for the SCENE_STABILIZED signal 
        # (which triggers when the player token drops) to kick off the narrative.
        
        # Start ambush if flagged
        if payload.get("is_ambush", False):
            self.bus.publish("COMBAT_START", {
                "entities": payload.get("entities", []), 
                "player_stats": self.player_character.stats
            })

    def _on_scene_stabilized(self, payload):
        """Called when the player is physically dropped onto the board."""
        self.bus.publish("LOAD_CAMPAIGN", {})
        self.bus.publish("INITIATE_BOOT_SEQUENCE", {"location": self._pending_boot_location})

    def _on_loot_acquired(self, payload):
        from core.models.character_sheet import Item
        item_data = payload.get("item_data", {})
        item = Item(**item_data)
        self.player_character.inventory.bag.append(item)
        self.bus.publish("HUD_UPDATE", {"character": self.player_character.model_dump()})
        self.bus.publish("SYSTEM_LOG", {"message": f"<font color='#FFD700'><b>Loot Acquired:</b> {item.name}</font>"})
        
        intent_prompt = f"LOOT ACQUIRED: The player picked up {item.name}. Generate a brief narrative about them finding it."
        self.bus.publish("EXECUTE_INTENT", {"intent": intent_prompt})

    def _on_inventory_equip(self, payload):
        if not self.player_character: return
        index = payload.get("index")
        bag = self.player_character.inventory.bag
        
        if 0 <= index < len(bag):
            item = bag[index]
            target_slot = getattr(item, "item_type", "unknown")
            
            if target_slot not in self.player_character.inventory.slots:
                self.bus.publish("SYSTEM_LOG", {"message": f"<font color='red'>Cannot equip {item.name}: Invalid slot '{target_slot}'.</font>"})
                return
                
            bag.pop(index) # Safe to pop now
            old_item = self.player_character.inventory.slots.get(target_slot)
            if old_item:
                bag.append(old_item)
                
            self.player_character.inventory.slots[target_slot] = item
            self.bus.publish("HUD_UPDATE", {"character": self.player_character.model_dump()})
            self.bus.publish("SYSTEM_LOG", {"message": f"<font color='#00FFFF'><b>Equipped:</b> {item.name}</font>"})

    def _on_inventory_unequip(self, payload):
        if not self.player_character: return
        slot = payload.get("slot")
        
        if slot in self.player_character.inventory.slots:
            item = self.player_character.inventory.slots[slot]
            if item:
                self.player_character.inventory.slots[slot] = None
                self.player_character.inventory.bag.append(item)
                self.bus.publish("HUD_UPDATE", {"character": self.player_character.model_dump()})
                self.bus.publish("SYSTEM_LOG", {"message": f"<font color='#FFAA00'><b>Unequipped:</b> {item.name}</font>"})

    def _on_player_created(self, payload):
        """Handoff from Character Creation to the active Game Screen."""
        self.player_character = CharacterSheet(**payload)
        self._show_game()

    def _on_combat_resolved(self, payload):
        target = payload.get("target")
        if target == self.player_character.name:
            self.player_character.take_damage(payload.get("damage", 0), payload.get("is_physical", True))
            if payload.get("trauma"):
                self.player_character.trauma_tokens += 1
            self.bus.publish("HUD_UPDATE", {"character": self.player_character.model_dump()})
        else:
            # In a full game, we'd update the specific NPC token on the map here
            pass
            
    def _handle_intent(self, payload):
        intent = payload.get("intent", "").strip()
        if not intent: return
        
        # We don't want to show raw backend prompts in the UI
        if not intent.startswith("COMBAT RESOLUTION:") and not intent.startswith("The player attempted to travel"):
            self.map_canvas.log_view.append(f"<b>You:</b> {intent}")
            
        # Route through strict CommandParser
        action_result = self.command_parser.parse_intent(intent, player_character=self.player_character)
        
        if action_result.get("type") == "movement_success":
            # Deduct stamina (example basic math hook)
            if self.player_character:
                self.player_character.stamina = max(0, self.player_character.stamina - 1)
                self.bus.publish("HUD_UPDATE", {"character": self.player_character.model_dump()})
            
            # Command AI to narrate the result
            self.bus.publish("EXECUTE_AI_INTENT", {
                "intent": action_result["system_prompt"],
                "system_prompt": True
            })
            return
            
        elif action_result.get("type") in ("movement_failed", "combat_failed", "combat_success", "interaction_failed", "interaction_success", "turn_ended"):
            self.bus.publish("EXECUTE_AI_INTENT", {
                "intent": action_result["system_prompt"],
                "system_prompt": True
            })
            return
            
        elif action_result.get("type") == "error":
            self.map_canvas.log_view.append(f"<font color='red'>{action_result['system_prompt']}</font>")
            return
            
        elif action_result.get("type") == "handled_by_resolver":
            return
            
            
        self.map_canvas.log_view.append("\n<i>Narrator is thinking...</i>\n")
        self.map_canvas.log_view.append("<font color='#a0a0ff'>[NARRATOR]:</font> ")
        
        # Extract mechanical result if provided
        mech_res = "The action resolves successfully."
        if intent.startswith("COMBAT RESOLUTION:"):
            mech_res = "The engine resolved this mechanically. Follow the Result described in the user prompt."

        # 1. Recall past memories related to the player's intent
        past_memories = self.memory.recall_context(intent)
        
        # 2. Inject memories into the current context
        current_context = "The player is in the current location.\n"
        if past_memories:
            current_context += f"\n{past_memories}"
            
        # 3. Generate context-aware prompt
        prompt = self.ai_director.generate_llm_prompt(
            mechanical_result=mech_res,
            context=current_context,
            intent_raw=intent
        )
        self.llm_worker.request_generation(prompt=prompt, tag="narrative")

    def _handle_ai_intent(self, payload):
        intent = payload.get("intent", "")
        tag = payload.get("tag", "narrative")
        
        if tag != "silent_setup":
            self.map_canvas.log_view.append("\n<i>AI Director is generating...</i>\n")
            self.map_canvas.log_view.append("<font color='#ff5555'>[AI]:</font> ")
        
        if payload.get("system_prompt", False):
            prompt = intent
            if tag == "boot_sequence":
                self._pending_boot_location = payload.get("location", "Aloa")
        else:
            # Inject memory for combat/system intents too!
            past_memories = self.memory.recall_context(intent)
            current_context = "Current phase: " + intent
            if past_memories:
                current_context += f"\n{past_memories}"
                
            # Wrap the system/NPC intent in the director's prompt format
            prompt = self.ai_director.generate_llm_prompt(
                mechanical_result="The engine has triggered a system override or combat event.",
                context=current_context,
                intent_raw="[SYSTEM COMMAND]: " + intent
            )
        
        self.llm_worker.request_generation(prompt=prompt, tag=tag)

    def _handle_mic_toggle(self, payload):
        if payload.get("active", False):
            if not self.stt_worker.isRunning():
                self.stt_worker.start()
        else:
            self.stt_worker.stop_listening()

    def _handle_ai_narrated(self, payload):
        # Text is now streamed live character-by-character via token_generated.
        # We don't append the final block here to avoid duplication.
        pass
        
    def _handle_mechanics_triggered(self, payload):
        actions = payload.get("actions", [])
        for action in actions:
            if action.get("type") == "attack":
                # Convert AI intent to ActionResolver payload
                combat_payload = {
                    "attacker": action.get("actor_uuid"),
                    "defender": action.get("target_uuid"),
                    "offense_stat": 5, # We'd pull real stats here
                    "weapon_mod": 0,
                    "defense_stat": 5, 
                    "armor_mod": 0,
                    "is_physical": True
                }
                self.bus.publish("COMBAT_ACTION_DECLARED", combat_payload)

    def _on_system_log(self, payload):
        msg = payload.get("message", "")
        if msg:
            self.map_canvas.log_view.append(msg)

    def _handle_generate_next_node(self, payload):
        current_node = payload.get("current_node", {})
        
        past_memories = self.memory.recall_context("Summarize the player's recent actions and their consequences.")
        
        prompt = (
            f"The player has just completed the campaign phase: '{current_node.get('title')}'. "
            f"Here is what happened recently:\n{past_memories}\n\n"
            f"Based on their actions, generate the NEXT major plot node for the campaign. "
            f"You MUST return a raw JSON object with this exact structure:\n"
            "{\n"
            '  "node_id": "unique_id_here",\n'
            '  "title": "Title of the next phase",\n'
            '  "description": "Brief description of the new situation and goal",\n'
            '  "is_major_plot_point": true,\n'
            '  "dynamic_slots": 2\n'
            "}"
        )
        self.bus.publish("EXECUTE_AI_INTENT", {"intent": prompt, "system_prompt": True, "tag": "generate_next_node"})
        
    def _handle_world_mutation(self, payload):
        resolution = payload.get("resolution", "")
        
        prompt = (
            f"The player just resolved an event with this outcome: '{resolution}'. "
            f"Based on this, what immediate physical change happens in the world? "
            f"You MUST return a raw JSON object with this structure:\n"
            "{\n"
            '  "narrative": "A scout spots you and calls for backup!",\n'
            '  "world_updates": {\n'
            '    "spawn_entities": [\n'
            '      {"name": "Bandit Reinforcement", "sprite": "hostile", "tags": ["humanoid", "hostile"], "x": 10, "y": 10}\n'
            '    ]\n'
            '  }\n'
            "}"
        )
        self.bus.publish("EXECUTE_AI_INTENT", {"intent": prompt, "system_prompt": True, "tag": "world_mutation"})

    @pyqtSlot(str, str)
    def _on_llm_complete(self, tag: str, full_text: str):
        import json
        
        if tag == "generate_next_node":
            try:
                # Find the JSON block
                start = full_text.find("{")
                end = full_text.rfind("}") + 1
                if start != -1 and end != 0:
                    data = json.loads(full_text[start:end])
                    self.campaign_manager.append_and_transition(data)
                return
            except Exception as e:
                self.map_canvas.log_view.append(f"<font color='red'>[ERROR] Failed to parse generated node: {e}</font>")
                return
                
        if tag == "world_mutation":
            try:
                start = full_text.find("{")
                end = full_text.rfind("}") + 1
                if start != -1 and end != 0:
                    data = json.loads(full_text[start:end])
                    narrative = data.get("narrative", "")
                    if narrative:
                        self.map_canvas.log_view.append(f"\n<font color='#FFAA00'>[WORLD UPDATE]: {narrative}</font>\n")
                        
                    updates = data.get("world_updates", {})
                    for ent in updates.get("spawn_entities", []):
                        self.bus.publish("SPAWN_ENTITY", {
                            "uuid": f"mutated_{hash(ent.get('name', 'ent'))}",
                            "x": ent.get("x", 20),
                            "y": ent.get("y", 20),
                            "color": "red" if "hostile" in ent.get("tags", []) else "blue",
                            "name": ent.get("name", "Unknown"),
                            "tags": ent.get("tags", [])
                        })
                return
            except Exception as e:
                self.map_canvas.log_view.append(f"<font color='red'>[ERROR] Failed to parse world mutation: {e}</font>")
                return
                
        if tag == "boot_sequence":
            try:
                data = json.loads(full_text)
                world_updates = data.get("world_updates", {})
                entities = world_updates.get("entities", [])
                
                # Instead of regenerating the map, dynamically inject the entities onto the already loaded map!
                for ent in entities:
                    self.bus.publish("SPAWN_ENTITY", {
                        "uuid": ent.get("uuid", f"npc_{hash(ent.get('name'))}"),
                        "x": ent.get("x", 20),
                        "y": ent.get("y", 20),
                        "color": "red" if "hostile" in ent.get("tags", []) else "blue",
                        "name": ent.get("name", "NPC"),
                        "tags": ent.get("tags", [])
                    })
            except Exception as e:
                print(f"Failed to parse boot sequence JSON: {e}")

        # Feed the fully generated text to the TTS worker
        self.tts_worker.speak(full_text)
        self.map_canvas.log_view.append("\n")
        # Store the final generated narrative into long-term memory
        self.memory.store_event(text=full_text, metadata={"type": tag})
        
        # Theatrical Trigger: Execute all queued UI animations!
        self.map_canvas._flush_animation_queue()
            
        self.bus.publish("END_TURN")

    def closeEvent(self, event):
        """Ensure threads are properly closed when shutting down."""
        self.llm_worker.requestInterruption()
        self.tts_worker.requestInterruption()
        self.stt_worker.requestInterruption()
        self.world_gen_worker.requestInterruption()
        super().closeEvent(event)
