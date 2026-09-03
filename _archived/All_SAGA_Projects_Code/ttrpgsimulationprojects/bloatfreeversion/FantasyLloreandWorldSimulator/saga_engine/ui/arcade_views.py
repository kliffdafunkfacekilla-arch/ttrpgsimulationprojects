import arcade
import arcade.gui
from arcade.gui.widgets.text import UITextArea
from arcade.gui.widgets.buttons import UIFlatButton, UITextureButton
from arcade.gui.widgets.layout import UIBoxLayout, UIAnchorLayout
from saga_engine.core.state import CampaignState
from saga_engine.core.bus import EventBus

# Screen Dimensions
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
SCREEN_TITLE = "S.A.G.A. Engine VTT"

class VTTView(arcade.View):
    """The Master 5-Panel Arcade Interface"""
    
    def __init__(self, bus: EventBus, global_state: CampaignState, static_db: dict = None):
        super().__init__()
        self.bus = bus
        self.state = global_state
        
        # 1. ARCADE CAMERAS
        # We use two cameras: One for the zooming hex map, one for the static UI
        self.camera_map = arcade.camera.Camera2D()
        self.camera_gui = arcade.camera.Camera2D()
        
        # 2. UI MANAGER (The 5-Panel Layout)
        self.ui_manager = arcade.gui.UIManager()
        self.ui_manager.enable()
        
        # --- UI ASSETS ---
        self.ui_db = static_db.get("ui", {}) if static_db else {}
        self.textures = {}
        self.pillar_icons = {}
        self._load_ui_textures()
        
        # --- LEFT PANEL: Director's Log ---
        self.chat_log = UITextArea(
            width=400, height=880, 
            text="[SYSTEM] S.A.G.A. Engine Initialized.\n",
            text_color=arcade.color.WHITE
        )
        left_anchor = UIAnchorLayout()
        left_anchor.add(child=self.chat_log, anchor_x="left", anchor_y="top")
        self.ui_manager.add(left_anchor)
    
        # --- BOTTOM CONSOLE: The Action Deck ---
        # Using textured button from the GUI pack
        btn_tex = self.textures.get("BTN_NORMAL")
        btn_hover = self.textures.get("BTN_HOVER")
        
        self.assault_button = UITextureButton(
            texture=btn_tex,
            hover_texture=btn_hover,
            text="ASSAULT", 
            width=150, height=40
        )
        self.assault_button.on_click = self.on_assault_click
        
        bottom_box = UIBoxLayout(vertical=False, space_between=20)
        bottom_box.add(self.assault_button)
        
        bottom_anchor = UIAnchorLayout()
        bottom_anchor.add(child=bottom_box, anchor_x="center_x", anchor_y="bottom")
        self.ui_manager.add(bottom_anchor)
    
        # 4. SOUND ENGINE
        self.sounds_db = static_db.get("sounds", {}) if static_db else {}
        self.loaded_sounds = {}
        self._load_audio_assets()
        
        # 5. SUBSCRIBE TO THE SPINE
        self.bus.subscribe("STATE_UPDATE", self.handle_state_update)
        self.bus.subscribe("PLAY_SOUND", self.handle_play_sound)
        
        # 6. GLSL CHAOS SHADER PREP
        # Loads a custom GLSL fragment shader to warp the screen during DEADLOCKS
        # self.chaos_shader = arcade.gl.Program(fragment_shader="ui/shaders/chaos_warp.glsl")
    
    # --- INPUT BINDINGS (The Frontend-to-Spine Contract) ---
    
    def on_assault_click(self, event):
        """Fires when the player clicks the Assault button on the Action Deck."""
        if self.state.ui_locked:
            return # The Director is speaking; player cannot act.
            
        # Read the visual UI burn slider (mocked here as 2)
        stamina_burn = 2 
        
        # Publish the event instantly to the Data Bus
        self.bus.publish("CLASH_ATTACK", {
            "type": "ASSAULT", # Consistent with director's handle_action payload check if needed
            "action": "ASSAULT",
            "attacker_stamina_burn": stamina_burn,
            "weapon_damage": 8,
            "attacker_pool": self.state.active_player.attributes.might,
            "defender_pool": 12, # Mock target pool
            "defender_hp": 20
        })
    
    def on_mouse_press(self, x, y, button, modifiers):
        """Translates screen clicks into grid coordinates for the Director to intercept."""
        if self.state.ui_locked: return
        
        # Translate screen pixel X/Y to map coordinates
        grid_coord = f"[{int(x // 64)}, {int(y // 64)}]"
        
        # The Director is listening for this exact event!
        self.bus.publish("MAP_CLICK", {"type": "MOVE", "target": grid_coord})
    
    # --- STATE REDRAW (The UI Loop) ---
    
    def _load_ui_textures(self):
        """Pre-loads pixel art textures."""
        # Main UI Textures
        for category, tex_map in self.ui_db.get("TEXTURES", {}).items():
            for key, path in tex_map.items():
                try:
                    self.textures[key] = arcade.load_texture(path)
                except Exception as e:
                    print(f"[UI ERROR] Failed to load texture {key}: {e}")
        
        # Pillar Icons
        for pillar, path in self.ui_db.get("PILLAR_ICONS", {}).items():
            try:
                self.pillar_icons[pillar] = arcade.load_texture(path)
            except Exception as e:
                print(f"[UI ERROR] Failed to load icon {pillar}: {e}")
    
    def handle_state_update(self, payload: dict):
        """Instantly updates visual UI elements when the math changes in memory."""
        if payload.get("element") == "CHAT_LOG":
            # Append AI narration to the left panel
            current_text = self.chat_log.text
            self.chat_log.text = f"{current_text}\n{payload['text']}"
            
            # If the payload indicates a pillar action, we can theoretically draw an icon
            # For now, we just ensure the text updates.
            
        elif payload.get("action") == "CLASH_RESOLVED":
            # Append mathematical results with an icon hint
            current_text = self.chat_log.text
            self.chat_log.text = f"{current_text}\n[SYSTEM: {payload['margin_result']}! Damage: {payload['damage']}]"
    
    def _load_audio_assets(self):
        """Pre-loads arcade.Sound objects into memory."""
        for category, sounds in self.sounds_db.get("CATEGORIES", {}).items():
            for key, path in sounds.items():
                try:
                    # arcade.Sound expects paths relative to CWD or absolute
                    self.loaded_sounds[key] = arcade.Sound(path)
                    print(f"[AUDIO] Loaded {key}: {path}")
                except Exception as e:
                    print(f"[AUDIO ERROR] Failed to load {key} ({path}): {e}")
    
    def handle_play_sound(self, payload: dict):
        """Triggered by PLAY_SOUND events on the bus."""
        key = payload.get("key")
        sound = self.loaded_sounds.get(key)
        if sound:
            sound.play()
        else:
            print(f"[AUDIO WARNING] Sound key {key} not found in loaded bank.")
    
    def on_draw(self):
        """The 60 FPS Render Loop"""
        self.clear()
        
        # 1. DRAW THE BATTLEMAP (Center Stage)
        self.camera_map.use()
        # If Chaos Level > 3, we would render self.map_sprites through self.chaos_shader here
        # self.map_sprites.draw()
        
        # 2. DRAW THE STATIC UI (The 5 Panels)
        self.camera_gui.use()
        self.ui_manager.draw()
        
        # 3. DRAW DYNAMIC RESOURCE ORBS (Stamina & Focus)
        # Using textured container and stylized bars
        self.camera_gui.use()
        
        # Stamina Bar
        if self.state.active_player.vitals.max_stamina > 0:
            stamina_percent = self.state.active_player.vitals.current_stamina / self.state.active_player.vitals.max_stamina
        else:
            stamina_percent = 0
            
        # Draw Container
        cont_tex = self.textures.get("BAR_CONTAINER")
        if cont_tex:
            arcade.draw_texture_rect(cont_tex, arcade.XYWH(150, 100, 160, 41))
        
        # Draw Fill (Stamina)
        fill_tex = self.textures.get("FILL_RED")
        if fill_tex:
            bar_width = 120 * stamina_percent
            arcade.draw_texture_rect(fill_tex, arcade.XYWH(150 - (120 - bar_width)/2, 100, bar_width, 8))
    
        # Focus Bar (Shifted up)
        if self.state.active_player.vitals.max_focus > 0:
            focus_percent = self.state.active_player.vitals.current_focus / self.state.active_player.vitals.max_focus
        else:
            focus_percent = 0
            
        if cont_tex:
            arcade.draw_texture_rect(cont_tex, arcade.XYWH(150, 60, 160, 41))
        
        fill_blue = self.textures.get("FILL_BLUE")
        if fill_blue:
            bar_width = 120 * focus_percent
            arcade.draw_texture_rect(fill_blue, arcade.XYWH(150 - (120 - bar_width)/2, 60, bar_width, 8))
    
        # Draw Icon (Orb)
        orb_tex = self.textures.get("ORB_CONTAINER")
        if orb_tex:
            arcade.draw_texture_rect(orb_tex, arcade.XYWH(60, 100, 19, 19))
            # If Nexus is active, draw the flame icon inside the orb
            nexus_icon = self.pillar_icons.get("NEXUS")
            if nexus_icon:
                arcade.draw_texture_rect(nexus_icon, arcade.XYWH(60, 100, 16, 16))
    
        # 4. DECORATIVE KNOTS (Four Corners)
        knot_tex = self.textures.get("CORNER")
        if knot_tex:
            arcade.draw_texture_rect(knot_tex, arcade.XYWH(7, 7, 14, 14))
            arcade.draw_texture_rect(knot_tex, arcade.XYWH(SCREEN_WIDTH - 7, 7, 14, 14))
            arcade.draw_texture_rect(knot_tex, arcade.XYWH(7, SCREEN_HEIGHT - 7, 14, 14))
            arcade.draw_texture_rect(knot_tex, arcade.XYWH(SCREEN_WIDTH - 7, SCREEN_HEIGHT - 7, 14, 14))
