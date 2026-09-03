"""
Provides the MapCanvas and BattleMapCanvas components for the left-hand panel of the VTT.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QLineEdit, QGraphicsView, 
                             QGraphicsScene, QMenu)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QBrush, QColor

from beta_build.ui.sprite_manager import SpriteManager
from beta_build.ui.hud import CharacterHUD, StoryTracker

class BattleMapCanvas(QGraphicsView):
    """
    Renders the local battle map dynamically.
    Uses SpriteManager to map graphical assets to the tactical grid.
    """
    def __init__(self, bus):
        super().__init__()
        self.bus = bus
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setMinimumHeight(350)
        self.setBackgroundBrush(QBrush(QColor("#0a0a0a")))
        
        self.tile_size = 32
        self.player_x = 50
        self.player_y = 50
        
        self.sprite_manager = SpriteManager(self.tile_size)
        
    def load_matrix(self, battlemap_data: dict, px: int, py: int):
        """
        Loads grid data and renders the viewable window around the player.
        """
        self.scene.clear()
        self.player_x = px
        self.player_y = py
        
        grid = battlemap_data.get("grid", [])
        width = battlemap_data.get("width", 0)
        height = battlemap_data.get("height", 0)
        
        self.current_battlemap = battlemap_data
        
        if not grid: return
        
        # Viewport logic
        vx_start = max(0, self.player_x - 10)
        vy_start = max(0, self.player_y - 10)
        vx_end = min(width, self.player_x + 10)
        vy_end = min(height, self.player_y + 10)
        
        # Draw Map
        for y in range(vy_start, vy_end):
            for x in range(vx_start, vx_end):
                if y < len(grid) and x < len(grid[y]):
                    tile_val = grid[y][x]
                    draw_x = (x - vx_start) * self.tile_size
                    draw_y = (y - vy_start) * self.tile_size
                    
                    biome = battlemap_data.get("biome", "grass").lower()
                    
                    if tile_val == 1: 
                        if biome in ["forest", "jungle", "taiga"]:
                            sprite_name = "mangrove_1"
                        elif biome in ["mountains", "hills", "volcanic"]:
                            sprite_name = "boulder"
                        else:
                            sprite_name = "brick_brown_1"
                    elif tile_val == 2: 
                        sprite_name = "deep_water"
                    elif tile_val == 3: 
                        sprite_name = "shop_general" if biome == "town" else "abandoned_shop"
                    elif tile_val == 4: 
                        sprite_name = "dirt_0_new"
                    else: 
                        sprite_name = "black_cobalt_1" if biome == "town" else "grass_0_new"
                    
                    pm = self.sprite_manager.get_sprite(sprite_name)
                    self.scene.addPixmap(pm).setPos(draw_x, draw_y)
                    
                    if x == self.player_x and y == self.player_y:
                        player_sprite = self.sprite_manager.get_sprite("statue_ancient_hero")
                        self.scene.addPixmap(player_sprite).setPos(draw_x, draw_y)

        # Draw Entities
        entities = battlemap_data.get("entities", [])
        for ent in entities:
            ex = ent.get("x", 0)
            ey = ent.get("y", 0)
            if vx_start <= ex < vx_end and vy_start <= ey < vy_end:
                draw_x = (ex - vx_start) * self.tile_size
                draw_y = (ey - vy_start) * self.tile_size
                
                sprite_name = ent.get("sprite", "unseen")
                pm = self.sprite_manager.get_sprite(sprite_name)
                self.scene.addPixmap(pm).setPos(draw_x, draw_y)

    def mousePressEvent(self, event):
        """Handle right/left clicks to open contextual interaction menus."""
        if event.button() == Qt.MouseButton.RightButton or event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            vx_start = max(0, self.player_x - 10)
            vy_start = max(0, self.player_y - 10)
            
            clicked_x = int(scene_pos.x() // self.tile_size) + vx_start
            clicked_y = int(scene_pos.y() // self.tile_size) + vy_start
            
            self.show_context_menu(event.globalPosition().toPoint(), clicked_x, clicked_y)
        else:
            super().mousePressEvent(event)
            
    def show_context_menu(self, global_pos, gx, gy):
        if not hasattr(self, 'current_battlemap'):
            return
            
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #333; color: white; border: 1px solid #555; } QMenu::item:selected { background-color: #555; }")
        
        entities = self.current_battlemap.get("entities", [])
        clicked_entity = None
        for ent in entities:
            if ent.get("x") == gx and ent.get("y") == gy:
                clicked_entity = ent
                break
                
        if clicked_entity:
            name = clicked_entity.get("name", "Unknown")
            personality = clicked_entity.get("personality", "Unknown")
            
            if personality.lower() == "hazard" or "trap" in name.lower():
                menu.addAction(f"Interact with {name}", lambda: self._send_intent(f"interact with {name}"))
                menu.addAction(f"Examine {name}", lambda: self._send_intent(f"examine {name}"))
                menu.addAction(f"Pickup {name}", lambda: self._send_intent(f"pickup {name}"))
            elif personality.lower() == "vendor":
                menu.addAction(f"Trade with {name}", lambda: self._send_intent(f"trade with {name}"))
                menu.addAction(f"Talk to {name}", lambda: self._send_intent(f"talk to {name}"))
                menu.addAction(f"Examine {name}", lambda: self._send_intent(f"examine {name}"))
                menu.addAction(f"Attack {name}", lambda: self._send_intent(f"attack {name}"))
            else:
                menu.addAction(f"Attack {name}", lambda: self._send_intent(f"attack {name}"))
                menu.addAction(f"Talk to {name}", lambda: self._send_intent(f"talk to {name}"))
                menu.addAction(f"Examine {name}", lambda: self._send_intent(f"examine {name}"))
        else:
            menu.addAction("Move Here", lambda: self._send_intent(f"move to {gx} {gy}"))
            menu.addAction("Examine Area", lambda: self._send_intent("examine area"))
            
        menu.exec(global_pos)
        
    def _send_intent(self, intent_str):
        self.bus.publish("PLAYER_ACTION_UI_INJECT", {"intent": intent_str})


class MapCanvas(QWidget):
    """
    The main game view housing the BattleMap, Chat Log, Input Field, and Right-hand HUD.
    """
    def __init__(self, bus):
        super().__init__()
        self.bus = bus
        
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        
        self.title = QLabel("S.A.G.A. Engine VTT (Beta Async)")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size: 20px; font-weight: bold; color: #44FF44; margin-bottom: 5px;")
        
        self.battle_map = BattleMapCanvas(self.bus)
        
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet("""
            QTextEdit {
                background-color: #222;
                color: #DDD;
                font-family: monospace;
                font-size: 14px;
                padding: 10px;
                border: 2px solid #555;
            }
        """)
        self.log_view.append(">> Engine Initialized. Map Cluster Loaded.\n")
        
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("State your intent (e.g. 'I walk north' or 'I attack')")
        self.input_field.setStyleSheet("padding: 10px; font-size: 16px; background-color: #333; color: white; border: 1px solid #777;")
        self.input_field.returnPressed.connect(self._on_action_submitted)
        
        self.btn_submit = QPushButton("Execute")
        self.btn_submit.setStyleSheet("padding: 10px; font-size: 16px; background-color: #555; color: white; font-weight: bold;")
        self.btn_submit.clicked.connect(self._on_action_submitted)
        
        self.btn_char = QPushButton("Character Sheet")
        self.btn_char.setStyleSheet("padding: 10px; font-size: 16px; background-color: #335577; color: white; font-weight: bold;")
        self.btn_char.clicked.connect(lambda: self.bus.publish("UI_OPEN_CHAR_MANAGEMENT"))
        
        self.btn_stealth = QPushButton("Stealth: OFF")
        self.btn_stealth.setCheckable(True)
        self.btn_stealth.setStyleSheet("padding: 10px; font-size: 16px; background-color: #222; color: #888; border: 1px solid #555;")
        self.btn_stealth.toggled.connect(self._on_stealth_toggled)
        
        self.btn_dm = QPushButton("DM Dashboard")
        self.btn_dm.setStyleSheet("padding: 10px; font-size: 16px; background-color: #551111; color: #ff5555; font-weight: bold; border: 1px solid #ff5555;")
        self.btn_dm.clicked.connect(lambda: self.bus.publish("OPEN_DM_DASHBOARD"))
        
        self.btn_camp = QPushButton("Camp (Long Rest)")
        self.btn_camp.setStyleSheet("padding: 10px; font-size: 16px; background-color: #773333; color: white; font-weight: bold;")
        self.btn_camp.clicked.connect(lambda: self.bus.publish("UI_LONG_REST"))
        
        self.btn_mic = QPushButton("🎙️ Mic: OFF")
        self.btn_mic.setCheckable(True)
        self.btn_mic.setStyleSheet("padding: 10px; font-size: 16px; background-color: #222; color: #888; border: 1px solid #555;")
        self.btn_mic.toggled.connect(self._on_mic_toggled)

        input_layout.addWidget(self.btn_mic)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.btn_submit)
        input_layout.addWidget(self.btn_char)
        input_layout.addWidget(self.btn_stealth)
        input_layout.addWidget(self.btn_dm)
        input_layout.addWidget(self.btn_camp)
        
        left_layout.addWidget(self.title)
        left_layout.addWidget(self.battle_map)
        left_layout.addWidget(self.log_view)
        left_layout.addLayout(input_layout)
        
        right_panel = QVBoxLayout()
        self.hud = CharacterHUD()
        self.story_tracker = StoryTracker()
        right_panel.addWidget(self.hud)
        right_panel.addWidget(self.story_tracker)
        right_panel.addStretch()
        
        main_layout.addLayout(left_layout, stretch=4)
        main_layout.addLayout(right_panel, stretch=1)
        self.setLayout(main_layout)
        
        self.bus.subscribe("MAP_RENDER", self._on_map_render)
        self.bus.subscribe("HUD_UPDATE", self._on_hud_update)
        self.bus.subscribe("PLAYER_ACTION_UI_INJECT", self._handle_ui_inject)

    def _on_map_render(self, payload):
        battlemap_data = payload.get("battlemap")
        px = payload.get("px", 50)
        py = payload.get("py", 50)
        cx = payload.get("cx", 0)
        cy = payload.get("cy", 0)
        self.title.setText(f"S.A.G.A. Engine VTT (Beta) [Cluster {cx},{cy}] [Local {px},{py}]")
        if battlemap_data:
            self.battle_map.load_matrix(battlemap_data, px, py)
        
    def _on_hud_update(self, payload):
        if "character" in payload:
            self.hud.update_stats(payload["character"])
        if "dm_data" in payload:
            quest = payload["dm_data"].get("current_quest", "")
            seeds = payload["dm_data"].get("active_seeds", [])
            self.story_tracker.update_story(quest, seeds)
        
    def _on_stealth_toggled(self, checked):
        if checked:
            self.btn_stealth.setText("Stealth: ON")
            self.btn_stealth.setStyleSheet("padding: 10px; font-size: 16px; background-color: #44FF44; color: black; font-weight: bold;")
            self.bus.publish("UI_TOGGLE_STEALTH", {"stealth": True})
            self.log_view.append("\n[SYS] You have entered Stealth Mode. Movement and actions will use Finesse.")
        else:
            self.btn_stealth.setText("Stealth: OFF")
            self.btn_stealth.setStyleSheet("padding: 10px; font-size: 16px; background-color: #222; color: #888; border: 1px solid #555;")
            self.bus.publish("UI_TOGGLE_STEALTH", {"stealth": False})
            self.log_view.append("\n[SYS] You have left Stealth Mode.")
            
    def _on_mic_toggled(self, checked):
        if checked:
            self.btn_mic.setText("🎙️ Mic: ON")
            self.btn_mic.setStyleSheet("padding: 10px; font-size: 16px; background-color: #FF4444; color: white; font-weight: bold;")
            self.bus.publish("UI_TOGGLE_MIC", {"active": True})
        else:
            self.btn_mic.setText("🎙️ Mic: OFF")
            self.btn_mic.setStyleSheet("padding: 10px; font-size: 16px; background-color: #222; color: #888; border: 1px solid #555;")
            self.bus.publish("UI_TOGGLE_MIC", {"active": False})

    def _handle_ui_inject(self, payload):
        intent = payload.get("intent", "")
        if intent:
            # Re-publish to the main app to trigger the LLM
            self.bus.publish("EXECUTE_INTENT", {"intent": intent})

    def _on_action_submitted(self):
        intent = self.input_field.text().strip()
        if not intent: return
        self.input_field.clear()
        
        self.log_view.append(f"\n<b>Player:</b> {intent}")
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())
        
        self.bus.publish("EXECUTE_INTENT", {"intent": intent})

    # --- Signals from Workers ---
    @pyqtSlot(str)
    def on_token_received(self, token: str):
        # Insert token into log for typewriter effect
        cursor = self.log_view.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(token)
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())

    @pyqtSlot(str, str)
    def on_generation_complete(self, tag: str, full_text: str):
        self.log_view.append("\n")
        
    @pyqtSlot(str)
    def on_speech_recognized(self, text: str):
        self.input_field.setText(text)
        self._on_action_submitted()
        
    @pyqtSlot(str)
    def on_error(self, err: str):
        self.log_view.append(f"\n<font color='red'>[ERROR] {err}</font>\n")
