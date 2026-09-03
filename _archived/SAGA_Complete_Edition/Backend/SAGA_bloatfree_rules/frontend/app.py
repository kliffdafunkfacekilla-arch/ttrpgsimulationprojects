from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                             QLabel, QPushButton, QTextEdit, QLineEdit, 
                             QGraphicsView, QGraphicsScene, QFrame, QStackedWidget,
                             QSpinBox, QComboBox, QFormLayout, QMenu)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QBrush, QColor, QPen, QPixmap
from frontend.char_creation import CharacterCreationScreen
from frontend.character_management import CharacterManagementScreen

from frontend.sprite_manager import SpriteManager

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
        self.scene.clear()
        self.player_x = px
        self.player_y = py
        
        grid = battlemap_data["grid"]
        width = battlemap_data["width"]
        height = battlemap_data["height"]
        
        self.current_battlemap = battlemap_data
        
        # Viewport logic
        vx_start = max(0, self.player_x - 10)
        vy_start = max(0, self.player_y - 10)
        vx_end = min(width, self.player_x + 10)
        vy_end = min(height, self.player_y + 10)
        
        # Draw Map
        for y in range(vy_start, vy_end):
            for x in range(vx_start, vx_end):
                tile_val = grid[y][x]
                draw_x = (x - vx_start) * self.tile_size
                draw_y = (y - vy_start) * self.tile_size
                
                # Fetch Terrain Sprite
                biome = battlemap_data.get("biome", "grass").lower()
                
                if tile_val == 1: 
                    # Obstacles (Trees/Rocks)
                    if biome in ["forest", "jungle", "taiga"]:
                        sprite_name = "forest"
                    elif biome in ["mountains", "hills", "volcanic"]:
                        sprite_name = "mountains"
                    else:
                        sprite_name = "wall"
                elif tile_val == 2: 
                    sprite_name = "water"
                elif tile_val == 3: 
                    # Buildings / POI
                    sprite_name = "village" if biome == "town" else "ruins"
                elif tile_val == 4: 
                    sprite_name = "road"
                else: 
                    # Base Ground (Empty) -> use the biome's tile directly!
                    sprite_name = biome
                
                pm = self.sprite_manager.get_sprite(sprite_name)
                self.scene.addPixmap(pm).setPos(draw_x, draw_y)
                
                # Draw Player
                if x == self.player_x and y == self.player_y:
                    player_sprite = self.sprite_manager.get_sprite("player")
                    self.scene.addPixmap(player_sprite).setPos(draw_x, draw_y)

        # Draw Entities
        entities = battlemap_data.get("entities", [])
        for ent in entities:
            ex = ent.get("x", 0)
            ey = ent.get("y", 0)
            if vx_start <= ex < vx_end and vy_start <= ey < vy_end:
                draw_x = (ex - vx_start) * self.tile_size
                draw_y = (ey - vy_start) * self.tile_size
                
                sprite_name = ent.get("sprite", "enemy")
                pm = self.sprite_manager.get_sprite(sprite_name)
                self.scene.addPixmap(pm).setPos(draw_x, draw_y)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton or event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            vx_start = max(0, self.player_x - 10)
            vy_start = max(0, self.player_y - 10)
            
            clicked_x = int(scene_pos.x() // self.tile_size) + vx_start
            clicked_y = int(scene_pos.y() // self.tile_size) + vy_start
            
            self.show_context_menu(event.globalPos(), clicked_x, clicked_y)
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
        if hasattr(self, 'bus'):
            self.bus.publish("PLAYER_ACTION_UI_INJECT", {"intent": intent_str})

class CharacterHUD(QFrame):
    """
    Displays the character sheet (HP, Stamina, Focus) using graphical elements.
    """
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 2px solid #555;
                border-radius: 5px;
                padding: 10px;
            }
            QLabel { color: #ddd; font-weight: bold; font-family: monospace; font-size: 14px; border: none; }
        """)
        self.setFixedWidth(250)
        
        layout = QVBoxLayout()
        
        # UI Polish: Asset injection
        self.portrait_label = QLabel()
        portrait_pixmap = QPixmap("assets/gui/Fantasy Minimal Pixel Art GUI by eta-commercial-free/UI/CharacterBox_56x57.png")
        if not portrait_pixmap.isNull():
            self.portrait_label.setPixmap(portrait_pixmap)
            self.portrait_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.portrait_label)
        
        self.name_label = QLabel("Player Name")
        self.name_label.setStyleSheet("font-size: 18px; color: #44FF44; margin-bottom: 10px;")
        
        # Use HealthBarPanel background if possible
        bar_bg = QPixmap("assets/gui/Fantasy Minimal Pixel Art GUI by eta-commercial-free/UI/HealthBarPanel_160x41.png")
        
        self.hp_label = QLabel("HP: --/--")
        if not bar_bg.isNull():
            self.hp_label.setStyleSheet("color: #FF5555; background-image: url('assets/gui/Fantasy Minimal Pixel Art GUI by eta-commercial-free/UI/HealthBarPanel_160x41.png'); padding: 5px;")
        
        self.stamina_label = QLabel("Stamina: --/--")
        self.focus_label = QLabel("Focus: --/--")
        if not bar_bg.isNull():
            self.focus_label.setStyleSheet("color: #5555FF; background-image: url('assets/gui/Fantasy Minimal Pixel Art GUI by eta-commercial-free/UI/HealthBarPanel_160x41.png'); padding: 5px;")
            
        self.trauma_label = QLabel("Trauma Tokens: 0")
        
        layout.addWidget(self.name_label)
        layout.addWidget(self.hp_label)
        layout.addWidget(self.stamina_label)
        layout.addWidget(self.focus_label)
        layout.addWidget(self.trauma_label)
        layout.addStretch()
        
        self.setLayout(layout)
        
    def update_stats(self, stats: dict):
        self.name_label.setText(stats.get("name", "Player"))
        self.hp_label.setText(f"HP: {stats.get('hp', 0)} / {stats.get('max_hp', 0)}")
        self.stamina_label.setText(f"Stamina: {stats.get('stamina', 0)} / {stats.get('max_stamina', 0)}")
        self.focus_label.setText(f"Focus: {stats.get('focus', 0)} / {stats.get('max_focus', 0)}")
        self.trauma_label.setText(f"Trauma Tokens: {stats.get('trauma', 0)}")


class MapCanvas(QWidget):
    def __init__(self, bus):
        super().__init__()
        self.bus = bus
        
        main_layout = QHBoxLayout()
        
        # Left Panel (Map + Log + Input)
        left_layout = QVBoxLayout()
        
        self.title = QLabel("S.A.G.A. Engine VTT")
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
        
        self.btn_camp = QPushButton("Camp (Long Rest)")
        self.btn_camp.setStyleSheet("padding: 10px; font-size: 16px; background-color: #773333; color: white; font-weight: bold;")
        self.btn_camp.clicked.connect(lambda: self.bus.publish("UI_LONG_REST"))
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.btn_submit)
        input_layout.addWidget(self.btn_stealth)
        input_layout.addWidget(self.btn_camp)
        input_layout.addWidget(self.btn_char)
        
        left_layout.addWidget(self.title)
        left_layout.addWidget(self.battle_map)
        left_layout.addWidget(self.log_view)
        left_layout.addLayout(input_layout)
        
        # Right Panel (HUD)
        self.hud = CharacterHUD()
        
        main_layout.addLayout(left_layout, stretch=4)
        main_layout.addWidget(self.hud, stretch=1)
        self.setLayout(main_layout)
        
        self.bus.subscribe("NARRATIVE_OUTPUT", self._on_narrative)
        self.bus.subscribe("SYSTEM_LOG", self._on_log)
        self.bus.subscribe("MAP_RENDER", self._on_map_render)
        self.bus.subscribe("HUD_UPDATE", self._on_hud_update)
        
    def _on_map_render(self, payload):
        battlemap_data = payload.get("battlemap")
        px = payload.get("px", 50)
        py = payload.get("py", 50)
        cx = payload.get("cx", 0)
        cy = payload.get("cy", 0)
        self.title.setText(f"S.A.G.A. Engine VTT [Cluster {cx},{cy}] [Local {px},{py}]")
        self.battle_map.load_matrix(battlemap_data, px, py)
        
    def _on_hud_update(self, payload):
        self.hud.update_stats(payload)
        
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
            
    def _on_action_submitted(self):
        intent = self.input_field.text().strip()
        if not intent: return
        self.input_field.clear()
        self.bus.publish("PLAYER_ACTION_UI_INJECT", {"intent": intent})
        
    def _on_narrative(self, payload):
        text = payload.get('response', '')
        self.log_view.append(f"\n[AI TRANSLATOR LOG]\n{text}\n")
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())
        
    def _on_log(self, text):
        self.log_view.append(f"[SYS] {text}")
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())

class StartMenu(QWidget):
    def __init__(self, bus):
        super().__init__()
        self.bus = bus
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("S.A.G.A. ENGINE V1")
        title.setStyleSheet("font-size: 36px; font-weight: bold; color: #44FF44; margin-bottom: 30px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        btn_new = QPushButton("New Game (Create Party)")
        btn_new.setStyleSheet("padding: 15px; font-size: 18px; background-color: #333; color: white; width: 300px;")
        btn_new.clicked.connect(lambda: self.bus.publish("UI_START_NEW_GAME"))
        
        btn_load = QPushButton("Load Saved Game")
        btn_load.setStyleSheet("padding: 15px; font-size: 18px; background-color: #333; color: white; width: 300px; margin-top: 10px;")
        btn_load.clicked.connect(lambda: self.bus.publish("UI_LOAD_GAME"))
        
        layout.addWidget(title)
        layout.addWidget(btn_new)
        layout.addWidget(btn_load)
        
        self.setLayout(layout)

class VendorScreen(QWidget):
    def __init__(self, bus):
        super().__init__()
        self.bus = bus
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.title = QLabel("Vendor Shop")
        self.title.setStyleSheet("font-size: 24px; font-weight: bold; color: gold;")
        
        self.gold_label = QLabel("Gold: 0")
        self.gold_label.setStyleSheet("font-size: 18px; color: white;")
        
        self.item_list = QTextEdit()
        self.item_list.setReadOnly(True)
        self.item_list.setStyleSheet("background-color: #222; color: #ddd; font-family: monospace; font-size: 14px;")
        self.item_list.setMinimumHeight(400)
        
        self.buy_input = QLineEdit()
        self.buy_input.setPlaceholderText("Type item name to buy...")
        self.buy_input.setStyleSheet("padding: 5px; font-size: 16px; background-color: #333; color: white; border: 1px solid #555;")
        self.buy_input.returnPressed.connect(self._on_buy)
        
        btn_leave = QPushButton("Leave Shop")
        btn_leave.setStyleSheet("padding: 10px; background-color: #552222; color: white;")
        btn_leave.clicked.connect(lambda: self.bus.publish("UI_CLOSE_VENDOR"))
        
        self.layout.addWidget(self.title)
        self.layout.addWidget(self.gold_label)
        self.layout.addWidget(self.item_list)
        self.layout.addWidget(self.buy_input)
        self.layout.addWidget(btn_leave)
        self.setLayout(self.layout)
        
        self.bus.subscribe("VENDOR_DATA_UPDATE", self._on_vendor_update)
        
    def _on_vendor_update(self, payload):
        self.title.setText(f"Trading with: {payload.get('vendor_name', 'Merchant')}")
        self.gold_label.setText(f"Gold: {payload.get('player_gold', 0)}")
        
        items = payload.get("items", [])
        text = "Items for Sale:\n\n"
        for i in items:
            text += f"- {i['name']} ({i['cost']} Gold) : {i['desc']}\n"
            
        self.item_list.setText(text)
        
    def _on_buy(self):
        item_name = self.buy_input.text().strip()
        if item_name:
            self.bus.publish("VENDOR_BUY_ITEM", {"item_name": item_name})
            self.buy_input.clear()
class SagaDesktopApp(QMainWindow):
    def __init__(self, bus):
        super().__init__()
        self.bus = bus
        self.setWindowTitle("S.A.G.A. Engine")
        self.setGeometry(100, 100, 1100, 768)
        self.setStyleSheet("background-color: #111; color: white;")
        
        self.stack = QStackedWidget()
        
        self.start_menu = StartMenu(bus)
        self.char_creation = CharacterCreationScreen(bus)
        self.map_canvas = MapCanvas(bus)
        self.char_management = CharacterManagementScreen(bus)
        self.vendor_screen = VendorScreen(bus)
        
        self.stack.addWidget(self.start_menu)      # 0
        self.stack.addWidget(self.char_creation)   # 1
        self.stack.addWidget(self.map_canvas)      # 2
        self.stack.addWidget(self.char_management) # 3
        self.stack.addWidget(self.vendor_screen)   # 4
        
        self.setCentralWidget(self.stack)
        
        self.bus.subscribe("UI_START_NEW_GAME", lambda p: self.stack.setCurrentIndex(1))
        self.bus.subscribe("UI_LOAD_GAME", self._show_game)
        self.bus.subscribe("UI_FINALIZE_PARTY", self._show_game)
        
        self.bus.subscribe("UI_OPEN_CHAR_MANAGEMENT", lambda p: self.stack.setCurrentIndex(3))
        self.bus.subscribe("UI_CLOSE_CHAR_MANAGEMENT", lambda p: self.stack.setCurrentIndex(2))
        
        self.bus.subscribe("UI_OPEN_VENDOR", lambda p: self.stack.setCurrentIndex(4))
        self.bus.subscribe("UI_CLOSE_VENDOR", lambda p: self.stack.setCurrentIndex(2))
        
    def _show_game(self, payload=None):
        self.stack.setCurrentIndex(2)
