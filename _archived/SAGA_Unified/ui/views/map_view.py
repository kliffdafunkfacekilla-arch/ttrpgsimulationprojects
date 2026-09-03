"""
Provides the MapCanvas and BattleMapCanvas components for the left-hand panel of the VTT.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QLineEdit, QGraphicsView, 
                             QGraphicsScene, QMenu, QGraphicsEllipseItem, QGraphicsItem, QGraphicsTextItem, QGraphicsRectItem, QGraphicsPixmapItem, QGraphicsObject)
from PyQt6.QtCore import Qt, pyqtSlot, QRectF, QTimer, QSequentialAnimationGroup, QPropertyAnimation, pyqtProperty, QPointF
from PyQt6.QtGui import QBrush, QColor, QPen, QPainter

from beta_build.ui.sprite_manager import SpriteManager
from beta_build.ui.hud import CharacterHUD, StoryTracker
from beta_build.core.fov_calculator import calculate_fov

class LootItem(QGraphicsEllipseItem):
    """Glowing map token representing a dropped item."""
    def __init__(self, x, y, size, item_data, parent=None):
        super().__init__(size*0.2, size*0.2, size*0.6, size*0.6, parent)
        self.setPos(x * size, y * size)
        self.item_data = item_data
        
        self.setBrush(QBrush(QColor("#FFD700"))) # Gold
        self.setPen(QPen(QColor("white"), 1))
        
        self.label = QGraphicsTextItem(item_data.get("name", "Loot"), self)
        self.label.setDefaultTextColor(QColor("#FFD700"))
        self.label.setPos(-10, -15)
        self.setZValue(1) # Under players, above dead bodies

class TokenItem(QGraphicsObject):
    """Dynamic map token representing an entity (player, monster, etc)."""
    def __init__(self, x, y, size, pixmap, name, uuid, tags=None, parent=None):
        super().__init__(parent)
        self.setPos(x * size, y * size)
        self.uuid = uuid
        self.name = name
        self.tags = tags or []
        self._pixmap = pixmap
        
        # Add label for name
        self.label = QGraphicsTextItem(name, self)
        self.label.setDefaultTextColor(QColor("white"))
        # Give label a dark background so it's readable over textures
        self.label.setPos(0, -15)
        
        self.is_dead = False
        self.setZValue(1)

    def boundingRect(self):
        return QRectF(self._pixmap.rect())

    def paint(self, painter, option, widget=None):
        painter.drawPixmap(0, 0, self._pixmap)

    @pyqtProperty(QPointF)
    def pos_anim(self):
        return self.pos()

    @pos_anim.setter
    def pos_anim(self, val):
        self.setPos(val)

    def move_to_grid(self, x, y, size):
        if not self.is_dead:
            self.setPos(x * size, y * size)
            
    def flash_damage(self):
        if self.is_dead: return
        # A simple opacity flash for pixmaps
        self.setOpacity(0.5)
        QTimer.singleShot(150, lambda: self.setOpacity(1.0) if not self.is_dead else None)
        
    def set_dead(self):
        self.is_dead = True
        self.setOpacity(0.3)
        self.label.setDefaultTextColor(QColor("#555555"))
        # Move to background so living tokens walk over it
        self.setZValue(-1)

class BattleMapCanvas(QGraphicsView):
    """
    Renders the local battle map dynamically.
    Optimized 2D Engine using QGraphicsScene.
    """
    def __init__(self, bus, sprite_manager):
        super().__init__()
        self.bus = bus
        self.sprite_manager = sprite_manager
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setMinimumHeight(350)
        self.setBackgroundBrush(QBrush(QColor("#0a0a0a")))
        
        self.tile_size = 32
        self.entities = {} # Map of UUID -> TokenItem
        self.tile_items = {} # Map of (x,y) -> QGraphicsRectItem
        self.loot_items = []
        self.explored = set()
        self.visible_tiles = set()
        
        # Enable dragging/panning
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        
    def drawBackground(self, painter: QPainter, rect: QRectF):
        """Draws an infinite mathematical grid."""
        super().drawBackground(painter, rect)
        
        left = int(rect.left()) - (int(rect.left()) % self.tile_size)
        top = int(rect.top()) - (int(rect.top()) % self.tile_size)
        
        grid_pen = QPen(QColor("#2a2a2a"), 1, Qt.PenStyle.SolidLine)
        painter.setPen(grid_pen)
        
        x = left
        while x < rect.right():
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
            x += self.tile_size
            
        y = top
        while y < rect.bottom():
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)
            y += self.tile_size

    def wheelEvent(self, event):
        """Zoom in/out with mouse wheel."""
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
            
        self.scale(zoom_factor, zoom_factor)

    def spawn_entity(self, uuid: str, x: int, y: int, color: str, name: str, tags: list = None):
        if uuid in self.entities:
            self.move_entity(uuid, x, y)
            return
            
        if uuid == "player_1":
            pixmap = self.sprite_manager.get_sprite("human_m")
        else:
            # Simple heuristic mapping for enemies for now
            if "goblin" in name.lower() or "orc" in name.lower():
                pixmap = self.sprite_manager.get_sprite("orc")
            elif "wolf" in name.lower():
                pixmap = self.sprite_manager.get_sprite("wolf")
            else:
                pixmap = self.sprite_manager.get_sprite("entity_red")
                
        token = TokenItem(x, y, self.tile_size, pixmap, name, uuid, tags)
        
        # Initially hide if not player and not in visible
        if uuid != "player_1":
            if (x, y) not in self.visible_tiles:
                token.setVisible(False)
                
        self.scene.addItem(token)
        self.entities[uuid] = token
        
        if uuid == "player_1":
            self.update_fov(x, y, 7) # Example radius
        
    def move_entity(self, uuid: str, x: int, y: int):
        if uuid in self.entities:
            token = self.entities[uuid]
            token.move_to_grid(x, y, self.tile_size)
            if uuid == "player_1":
                self.update_fov(x, y, 7)
                self.check_loot_collisions(token)
            else:
                # Update visibility of NPC if it moved
                if (x, y) in self.visible_tiles:
                    token.setVisible(True)
                else:
                    token.setVisible(False)
                    
    def check_loot_collisions(self, player_token):
        colliding = player_token.collidingItems()
        for item in colliding:
            if isinstance(item, LootItem):
                self.bus.publish("LOOT_ACQUIRED", {"item_data": item.item_data})
                self.scene.removeItem(item)
                if item in self.loot_items:
                    self.loot_items.remove(item)
            
    def remove_entity(self, uuid: str):
        if uuid in self.entities:
            token = self.entities.pop(uuid)
            self.scene.removeItem(token)
            
    def damage_entity(self, uuid: str):
        if uuid in self.entities:
            self.entities[uuid].flash_damage()
            
    def kill_entity(self, uuid: str, loot_data: dict = None):
        if uuid in self.entities:
            token = self.entities[uuid]
            token.set_dead()
            if loot_data:
                tx = int(token.pos().x() // self.tile_size)
                ty = int(token.pos().y() // self.tile_size)
                self.spawn_loot(tx, ty, loot_data)
                
    def spawn_loot(self, x, y, item_data):
        loot = LootItem(x, y, self.tile_size, item_data)
        self.scene.addItem(loot)
        self.loot_items.append(loot)
            
    def update_fov(self, px: int, py: int, radius: int):
        """Calculates FOV and updates tile/token opacities."""
        if not hasattr(self, 'grid_data'): return
        
        self.visible_tiles = calculate_fov(self.grid_data, px, py, radius)
        self.explored.update(self.visible_tiles)
        
        # Update tile opacities
        for (tx, ty), rect in self.tile_items.items():
            if (tx, ty) in self.visible_tiles:
                rect.setOpacity(1.0)
            elif (tx, ty) in self.explored:
                rect.setOpacity(0.3)
            else:
                rect.setOpacity(0.0)
                
        # Update token visibilities
        for uid, token in self.entities.items():
            if uid == "player_1": continue
            tx = int(token.pos().x() // self.tile_size)
            ty = int(token.pos().y() // self.tile_size)
            if (tx, ty) in self.visible_tiles:
                token.setVisible(True)
            else:
                token.setVisible(False)

    def load_generated_payload(self, payload: dict):
        """Loads a generated grid and entities from the WorldGenWorker."""
        self.scene.clear()
        self.entities.clear()
        self.tile_items.clear()
        self.explored.clear()
        self.visible_tiles.clear()
        
        grid = payload.get("grid", [])
        self.grid_data = grid
        for y, row in enumerate(grid):
            for x, node in enumerate(row):
                # node is a TerrainTile dict
                # Get appropriate sprite
                node_type = node.get("type", "floor")
                if node_type == "wall":
                    pixmap = self.sprite_manager.get_sprite("stone_dark_0")
                elif node_type == "obstacle":
                    pixmap = self.sprite_manager.get_sprite("tree")
                elif node_type == "water":
                    pixmap = self.sprite_manager.get_sprite("water")
                elif node_type == "door":
                    pixmap = self.sprite_manager.get_sprite("closed_door")
                else:
                    pixmap = self.sprite_manager.get_sprite("grey_dirt_0")
                
                rect = QGraphicsPixmapItem(pixmap)
                rect.setPos(x * self.tile_size, y * self.tile_size)
                rect.setOpacity(0.0) # Start fully unexplored
                # Walls are slightly higher z-index to overlay floors correctly if needed
                if node_type in ("wall", "obstacle"):
                    rect.setZValue(0.5)
                else:
                    rect.setZValue(0)
                    
                self.scene.addItem(rect)
                self.tile_items[(x, y)] = rect
                    
        # Note: Player spawn is now handled via SPAWN_ENTITY from main_window
        
        for ent in payload.get("entities", []):
            self.spawn_entity(
                uuid=ent.get("uuid"),
                x=ent.get("x", 0),
                y=ent.get("y", 0),
                color="red",
                name=ent.get("name", "Unknown"),
                tags=ent.get("tags", [])
            )

    def mousePressEvent(self, event):
        """Handle right/left clicks to open contextual interaction menus."""
        if event.button() == Qt.MouseButton.RightButton or event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            clicked_x = int(scene_pos.x() // self.tile_size)
            clicked_y = int(scene_pos.y() // self.tile_size)
            
            self.show_context_menu(event.globalPosition().toPoint(), clicked_x, clicked_y)
        else:
            super().mousePressEvent(event)
            
    def show_context_menu(self, global_pos, gx, gy):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #333; color: white; border: 1px solid #555; } QMenu::item:selected { background-color: #555; }")
        
        clicked_entity = None
        for uuid, token in self.entities.items():
            tx = int(token.pos().x() // self.tile_size)
            ty = int(token.pos().y() // self.tile_size)
            if tx == gx and ty == gy:
                clicked_entity = token
                break
                
        if clicked_entity:
            name = clicked_entity.name
            menu.addAction(f"Interact with {name}", lambda: self._send_intent(f"interact with {name}"))
            menu.addAction(f"Examine {name}", lambda: self._send_intent(f"examine {name}"))
            menu.addAction(f"Attack {name}", lambda: self._send_intent(f"attack {name}"))
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
        self.animation_queue = []
        self.animation_group = QSequentialAnimationGroup(self)
        
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        
        self.title = QLabel("S.A.G.A. Engine VTT (Beta Async)")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size: 20px; font-weight: bold; color: #44FF44; margin-bottom: 5px;")
        
        self.sprite_manager = SpriteManager(tile_size=32)
        self.battle_map = BattleMapCanvas(self.bus, self.sprite_manager)
        
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
        
        self.btn_world = QPushButton("World Map")
        self.btn_world.setStyleSheet("padding: 10px; font-size: 16px; background-color: #337755; color: white; font-weight: bold;")
        self.btn_world.clicked.connect(lambda: self.bus.publish("UI_REQUEST_WORLD_MAP"))
        
        self.btn_mic = QPushButton("🎙️ Mic: OFF")
        self.btn_mic.setCheckable(True)
        self.btn_mic.setStyleSheet("padding: 10px; font-size: 16px; background-color: #222; color: #888; border: 1px solid #555;")
        self.btn_mic.toggled.connect(self._on_mic_toggled)

        input_layout.addWidget(self.btn_mic)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.btn_submit)
        input_layout.addWidget(self.btn_char)
        input_layout.addWidget(self.btn_world)
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
        self.bus.subscribe("BEAT_UPDATE", lambda p: self.hud.update_beats(p.get("beats", {})))
        self.bus.subscribe("PLAYER_ACTION_UI_INJECT", self._handle_ui_inject)
        
        self.bus.subscribe("SPAWN_ENTITY", self._on_spawn_entity)
        self.bus.subscribe("MOVE_ENTITY", self._on_move_entity)
        self.bus.subscribe("REMOVE_ENTITY", self._on_remove_entity)
        self.bus.subscribe("ENTITY_DAMAGED", self._on_entity_damaged)
        self.bus.subscribe("ENTITY_DIED", self._on_entity_died)
        self.bus.subscribe("MAP_PAYLOAD_READY", self._on_map_payload_ready)

    def _on_spawn_entity(self, payload):
        self.battle_map.spawn_entity(
            uuid=payload.get("uuid"),
            x=payload.get("x", 0),
            y=payload.get("y", 0),
            color=payload.get("color", "red"),
            name=payload.get("name", "Unknown"),
            tags=payload.get("tags", [])
        )
        if payload.get("uuid") == "player_1":
            self.bus.publish("SCENE_STABILIZED", {})

    def _on_move_entity(self, payload):
        self.animation_queue.append({"type": "move", "payload": payload})

    def _on_remove_entity(self, payload):
        self.battle_map.remove_entity(payload.get("uuid"))

    def _on_entity_damaged(self, payload):
        self.animation_queue.append({"type": "damage", "payload": payload})
        
    def _flush_animation_queue(self):
        self.animation_group.clear()
        
        for action in self.animation_queue:
            if action["type"] == "move":
                payload = action["payload"]
                uuid = payload.get("uuid")
                
                # Enemy AI currently passes dx/dy instead of x/y sometimes? Wait. 
                # Enemy AI passes new_x and new_y actually, let's check payload. Oh, enemy AI uses 'dx' and 'dy' in payload for move relative? Wait, let's use absolute x,y if available, else derive.
                # Actually, enemy AI emits dx, dy. But we need absolute for move_entity?
                # Actually _on_move_entity above used `payload.get("x", 0)`.
                x = payload.get("x", 0)
                y = payload.get("y", 0)
                if "dx" in payload and "x" not in payload:
                    if uuid in self.battle_map.entities:
                        token = self.battle_map.entities[uuid]
                        x = int(token.pos().x() // self.battle_map.tile_size) + payload["dx"]
                        y = int(token.pos().y() // self.battle_map.tile_size) + payload["dy"]
                
                if uuid in self.battle_map.entities:
                    token = self.battle_map.entities[uuid]
                    anim = QPropertyAnimation(token, b"pos_anim")
                    anim.setDuration(300)
                    anim.setStartValue(token.pos())
                    anim.setEndValue(QPointF(x * self.battle_map.tile_size, y * self.battle_map.tile_size))
                    self.animation_group.addAnimation(anim)
                    
                    # We need to run the logic after the animation finishes. We can use a lambda connected to the animation's finished signal, but since it's sequential, a QTimer singleShot won't work well.
                    # We can use QPropertyAnimation to just move it, and when the whole group finishes, we sync the FOV and positions.
                    anim.finished.connect(lambda u=uuid, nx=x, ny=y: self.battle_map.move_entity(u, nx, ny))
                    
            elif action["type"] == "damage":
                payload = action["payload"]
                uuid = payload.get("uuid")
                if uuid in self.battle_map.entities:
                    token = self.battle_map.entities[uuid]
                    # Since flash_damage uses QTimer, we can just call it when the sequence reaches it? 
                    # Actually, we can just flash them all at the end, or use a dummy pause animation
                    token.flash_damage()
                    
        self.animation_queue.clear()
        self.animation_group.start()
        
    def _on_entity_died(self, payload):
        self.battle_map.kill_entity(payload.get("uuid"), payload.get("loot_data"))

    def _on_map_payload_ready(self, payload):
        name = payload.get("name", "Unknown")
        self.title.setText(f"S.A.G.A. Engine VTT (Beta Async) - {name}")
        self.battle_map.load_generated_payload(payload)

    def _on_map_render(self, payload):
        # Kept for backward compatibility if we still want to read legacy grids,
        # but the map handles its own infinite grid now.
        pass
        
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
