import arcade
import arcade.gui
import json
import math
from typing import Dict, List, Optional, Tuple
from collections import Counter
from saga_engine.core.state import CampaignState
from saga_engine.core.bus import EventBus
from saga_engine.core.chronicler import Chronicler
from saga_engine.core.world_loader import WorldLoader
from saga_engine.core.chronos import ChronosManager
from saga_engine.modules.sim.region import RegionalGenerator
from saga_engine.ui.regional_view import RegionalDashboardView

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
HEX_SIZE = 18

class DashboardView(arcade.View):
    """
    Optimized GM Dashboard with Premium Framed UI Panels.
    Interprets all macro-world data (height, faction, population, and simulation state).
    """
    
    def __init__(self, bus: EventBus, state: CampaignState, 
                 chronicler: Chronicler, loader: WorldLoader, chronos: ChronosManager):
        super().__init__()
        self.bus = bus
        self.state = state
        self.chronicler = chronicler
        self.loader = loader
        self.chronos = chronos
        
        # Cameras
        self.camera_map = arcade.camera.Camera2D()
        self.camera_gui = arcade.camera.Camera2D()
        
        # UI Manager
        self.ui_manager = arcade.gui.UIManager()
        self.ui_manager.enable()
        
        # Biome Palette
        self.palette = {
            0: (30, 90, 160),      # Ocean
            1: (180, 200, 210),    # Tundra
            2: (70, 140, 60),      # Grassland
            3: (20, 60, 30),       # Forest
            4: (200, 160, 100),    # Desert
            5: (90, 90, 100),      # Mountains
            6: (40, 80, 70),       # Swamp
            7: (150, 130, 90),     # Hills
            8: (120, 80, 150),     # Wasteland
            9: (255, 100, 100),    # Mass Zone
            10: (200, 255, 255),   # Ordo Zone
            11: (200, 100, 255),   # Motus Zone
            12: (255, 200, 150)    # Flux Zone
        }
        
        self.biome_names = {
            0: "Ocean", 1: "Tundra", 2: "Grassland", 
            3: "Forest", 4: "Desert", 5: "Mountains",
            6: "Swamp", 7: "Hills", 8: "Wasteland",
            9: "Zone: Mass", 10: "Zone: Ordo", 11: "Zone: Motus", 12: "Zone: Flux"
        }

        # 1. Batch Renderer
        self.hex_shape_list = arcade.shape_list.ShapeElementList()
        self._build_rectangular_map()
        
        # 2. UI Layout
        self._setup_ui()
        
        # 3. Optimized Text Objects
        self.hud_text = arcade.Text(
            f"SYSTEM TIME: {str(self.state.time)}",
            SCREEN_WIDTH - 20, 20, 
            arcade.color.WHITE, 12,
            anchor_x="right"
        )
        self.log_texts: List[arcade.Text] = []
        
        # 4. Legend Text Objects
        self.legend_title = arcade.Text("BIOME LEGEND", 35, 410, arcade.color.GOLD, 11, bold=True)
        self.legend_labels = []
        y_pos = 140
        for b_id in sorted(self.biome_names.keys()):
            name = self.biome_names[b_id]
            txt = arcade.Text(name, 60, y_pos, arcade.color.WHITE, 10)
            self.legend_labels.append((b_id, txt))
            y_pos += 20
        
        # 5. Selection Marker
        self.selection_marker = arcade.shape_list.ShapeElementList()
        
        # 6. Regional Mapping
        self.regional_gen = RegionalGenerator()
        
        # Initial HUD/Log update
        self._update_hud_text()

        # 6. Event Subscriptions for Simulation Reactivity
        self.bus.subscribe("CHRONOS_HOUR", self._on_chronos_pulse)
        self.bus.subscribe("CHRONOS_DAY", self._on_chronos_pulse)
        self.bus.subscribe("STATE_UPDATE", self._on_state_update)

    def _setup_ui(self):
        v_box = arcade.gui.UIBoxLayout(align="right")
        title = arcade.gui.UILabel(text="S.A.G.A. BRAIN INTERFACE", font_size=20, text_color=arcade.color.GOLD)
        v_box.add(title.with_padding(bottom=20))

        pulse_btn = arcade.gui.UIFlatButton(text="Pulse (1h)", width=150)
        @pulse_btn.event("on_click")
        def on_click_pulse(event):
            self.bus.publish("PULSE_START", {"increment_minutes": 60})
        v_box.add(pulse_btn.with_padding(bottom=10))

        stats_btn = arcade.gui.UIFlatButton(text="World Stats", width=150)
        @stats_btn.event("on_click")
        def on_click_stats(event):
            self._show_world_stats()
        v_box.add(stats_btn.with_padding(bottom=10))

        self.pause_btn = arcade.gui.UIFlatButton(text="Pause Sim", width=150)
        @self.pause_btn.event("on_click")
        def on_click_pause(event):
            self.state.simulation_paused = not self.state.simulation_paused
            self.pause_btn.text = "Resume Sim" if self.state.simulation_paused else "Pause Sim"
        v_box.add(self.pause_btn.with_padding(bottom=20))

        zoom_btn = arcade.gui.UIFlatButton(text="Zoom into Hex", width=150)
        @zoom_btn.event("on_click")
        def on_click_zoom(event):
            if not self.state.current_hex_focus:
                self.bus.publish("STATE_UPDATE", {"element": "CHAT_LOG", "text": "Select a hex first!"})
                return
            
            q = self.state.current_hex_focus.get("q")
            r = self.state.current_hex_focus.get("r")
            
            # Generate the Region JIT
            hex_id = f"{q},{r}"
            dynamic_meta = self.state.dynamic_world.hex_metadata.get(hex_id, {})
            region = self.regional_gen.generate_region(q, r, self.state.current_hex_focus, dynamic_meta)
            
            self.state.active_regional_state = region
            
            # Switch view
            reg_view = RegionalDashboardView(self.bus, self.state, self.chronicler, self)
            self.window.show_view(reg_view)
            
        v_box.add(zoom_btn.with_padding(bottom=10))

        # --- Inspector Panel ---
        self.inspector_label = arcade.gui.UITextArea(
            text="HEX INSPECTOR\nClick any hex to see data.",
            width=200, height=220,
            text_color=arcade.color.WHITE
        )
        v_box.add(self.inspector_label.with_padding(top=20))

        header_layout = arcade.gui.UIAnchorLayout()
        header_layout.add(child=v_box.with_padding(right=10, top=50), anchor_x="right", anchor_y="top")
        self.ui_manager.add(header_layout)

    def _on_chronos_pulse(self, payload: dict):
        """Triggered when the simulation clock advances."""
        self._update_hud_text()
        # If a day passed, faction control might have shifted, refresh the map
        self._build_rectangular_map()
        
        # If we have a focused hex, refresh its inspector data
        if self.state.current_hex_focus:
            q = self.state.current_hex_focus.get("q")
            r = self.state.current_hex_focus.get("r")
            if q is not None and r is not None:
                self._inspect_hex((q, r))

    def _on_state_update(self, payload: dict):
        """Refreshes UI elements based on global state updates."""
        if payload.get("element") == "TIME":
            self._update_hud_text()

    def _show_world_stats(self):
        """Aggregates and displays global statistics."""
        total_hexes = len(self.loader.hex_data)
        biomes = [h['biome_id'] for h in self.loader.hex_data.values()]
        counts = Counter(biomes)
        
        summary = "[SYSTEM] World Data Summary:\n"
        summary += f"- Total Hexes: {total_hexes}\n"
        for b_id, count in sorted(counts.items()):
            name = self.biome_names.get(b_id, "Unknown")
            perc = (count / total_hexes) * 100
            summary += f"- {name}: {count} ({perc:.1f}%)\n"
            
        self.bus.publish("STATE_UPDATE", {"element": "CHAT_LOG", "text": summary})

    def _update_hud_text(self):
        self.hud_text.text = f"SYSTEM TIME: {str(self.state.time)}"
        self.log_texts = []
        # Get latest 5 events
        all_events = sorted(self.chronicler.search_events(""), key=lambda x: x['id'], reverse=True)[:5]
        
        y_off = 100
        for event in all_events:
            txt = arcade.Text(
                f"[{event['game_time']}] {event['summary'][:60]}...",
                30, y_off, arcade.color.COOL_GREY, 10
            )
            self.log_texts.append(txt)
            y_off -= 18

    def _build_rectangular_map(self):
        """Builds (or rebuilds) the visual hex grid."""
        self.hex_shape_list = arcade.shape_list.ShapeElementList()
        hex_vertices = []
        for i in range(6):
            angle_rad = math.pi / 180 * (60 * i - 30)
            hex_vertices.append((HEX_SIZE * math.cos(angle_rad), HEX_SIZE * math.sin(angle_rad)))

        all_coords = []
        sum_x, sum_y, count = 0, 0, 0
        self.hex_centers: Dict[Tuple[int, int], Tuple[float, float]] = {}

        for coord_key, hex_data in self.loader.hex_data.items():
            col, row = hex_data['q'], hex_data['r']
            width = math.sqrt(3) * HEX_SIZE
            cx = col * width + (0.5 * width if row % 2 else 0)
            cy = row * (HEX_SIZE * 1.5)
            
            all_coords.append((cx, cy, hex_data))
            self.hex_centers[(col, row)] = (cx, cy)
            sum_x += cx
            sum_y += cy
            count += 1

        avg_x = sum_x / count if count > 0 else 0
        avg_y = sum_y / count if count > 0 else 0

        # Simple mapping for faction colors
        faction_colors = {
            1: (200, 50, 50, 180),  # Reddish
            2: (50, 200, 50, 180),  # Greenish
            3: (50, 50, 200, 180)   # Blueish
        }

        for cx, cy, hex_data in all_coords:
            base_color = self.palette.get(hex_data['biome_id'], (10, 10, 10))
            height = hex_data.get("height", 0.5)
            tint = int((height - 0.5) * 40)
            
            final_color = [
                max(0, min(255, base_color[0] + tint)),
                max(0, min(255, base_color[1] + tint)),
                max(0, min(255, base_color[2] + tint))
            ]
            
            # Subtly tint based on faction control
            faction_id = hex_data.get("faction_id", 0)
            if faction_id != 0:
                f_color = faction_colors.get(faction_id, (255, 255, 255, 100))
                # Mix colors slightly
                final_color[0] = int(final_color[0] * 0.8 + f_color[0] * 0.2)
                final_color[1] = int(final_color[1] * 0.8 + f_color[1] * 0.2)
                final_color[2] = int(final_color[2] * 0.8 + f_color[2] * 0.2)

            points = [(cx + vx, cy + vy) for vx, vy in hex_vertices]
            shape = arcade.shape_list.create_polygon(points, final_color)
            self.hex_shape_list.append(shape)
            
            # Outline color (Darker or colored if owned)
            outline_color = (0, 0, 0, 30)
            if faction_id != 0:
                outline_color = faction_colors.get(faction_id, (255, 255, 255, 200))[:3] + (180,)
            
            outline = arcade.shape_list.create_line_loop(points, outline_color, 1 if faction_id == 0 else 2)
            self.hex_shape_list.append(outline)

        self.camera_map.position = (avg_x, avg_y)
        self.camera_gui.view_data.position = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_LEFT:
            world_pos = self.camera_map.unproject((x, y))
            world_x, world_y = world_pos[0], world_pos[1]
            closest_hex = None
            min_dist = 9999
            for (col, row), (cx, cy) in self.hex_centers.items():
                dist = math.sqrt((world_x - cx)**2 + (world_y - cy)**2)
                if dist < min_dist and dist < HEX_SIZE:
                    min_dist = dist
                    closest_hex = (col, row)
            if closest_hex:
                self._inspect_hex(closest_hex)

    def _inspect_hex(self, coords: Tuple[int, int]):
        q, r = coords
        hex_data = self.loader.get_hex(q, r)
        if not hex_data: return

        # 1. Selection marker
        self.selection_marker = arcade.shape_list.ShapeElementList()
        cx, cy = self.hex_centers[coords]
        hex_vertices = []
        for i in range(6):
            angle_rad = math.pi / 180 * (60 * i - 30)
            hex_vertices.append((cx + (HEX_SIZE+2) * math.cos(angle_rad), cy + (HEX_SIZE+2) * math.sin(angle_rad)))
        selector = arcade.shape_list.create_line_loop(hex_vertices, arcade.color.YELLOW, 3)
        self.selection_marker.append(selector)

        # 2. Update State & UI
        biome = self.biome_names.get(hex_data['biome_id'], "Unknown")
        self.state.current_hex_focus = hex_data.copy()
        self.state.current_hex_focus["biome_name"] = biome
        
        # Pull dynamic meta if available
        hex_id = f"{q},{r}"
        meta = self.state.dynamic_world.hex_metadata.get(hex_id, {})
        mana = meta.get("mana", 0.0)
        moisture = meta.get("moisture", 0.0)
        
        info = (
            f"COORD:  {q}, {r}\n"
            f"BIOME:  {biome.upper()}\n"
            f"POP:    {hex_data.get('population', 0)}\n"
            f"CONTROL:{hex_data.get('faction_id', 0)}\n"
            f"--- DYNAMIC ---\n"
            f"MANA:   {mana:.2f}\n"
            f"MOIST:  {moisture:.2f}\n"
            f"HEIGHT: {round(hex_data.get('height', 0.5), 3)}"
        )
        self.inspector_label.text = info
        
        # 3. Publish to Bus
        self.bus.publish("MAP_CLICK", {"type": "INSPECT", "q": q, "r": r, "data": hex_data})

    def _draw_framed_panel(self, left, right, bottom, top, title=None):
        """Helper to draw a premium panel with background and border."""
        arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, (15, 15, 25, 220))
        arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, (100, 100, 120, 200), 2)
        arcade.draw_lrbt_rectangle_outline(left+2, right-2, bottom+2, top-2, (50, 50, 70, 150), 1)

    def on_draw(self):
        self.clear()
        
        # 1. Draw Map & Markers
        self.camera_map.use()
        self.hex_shape_list.draw()
        
        # --- Player Marker (Cavalry/Wanderer Icon) ---
        if self.state.active_player:
            loc_str = self.state.active_player.location_hex
            try:
                # Parse "[q, r]"
                coords = json.loads(loc_str)
                q, r = coords[0], coords[1]
                if (q, r) in self.hex_centers:
                    cx, cy = self.hex_centers[(q, r)]
                    # Draw a distinct Golden Marker
                    arcade.draw_star_filled(cx, cy, arcade.color.GOLD, 8, 4, 30)
                    arcade.draw_circle_outline(cx, cy, 10, arcade.color.BLACK, 1)
            except:
                pass

        self.selection_marker.draw()
        
        # 2. Draw HUD & Panels
        self.camera_gui.use()
        
        # --- PANEL A: LOGS (Bottom Left) ---
        self._draw_framed_panel(20, 350, 20, 120)
        for txt in self.log_texts:
            txt.draw()
            
        # --- PANEL B: LEGEND (Middle Left) ---
        self._draw_framed_panel(20, 180, 130, 440)
        self.legend_title.draw()
        for b_id, txt in self.legend_labels:
            color = self.palette.get(b_id, (255, 255, 255))
            swatch_rect = arcade.rect.XYWH(40, txt.y + 5, 12, 12)
            arcade.draw_rect_filled(swatch_rect, color)
            arcade.draw_rect_outline(swatch_rect, arcade.color.BLACK, 1)
            txt.draw()
            
        # --- PANEL C: SIDEBAR (Right Side) ---
        self._draw_framed_panel(SCREEN_WIDTH - 220, SCREEN_WIDTH - 2, 5, SCREEN_HEIGHT - 5)
        
        # 3. Draw UI Manager
        self.ui_manager.draw()
        
        # 4. HUD Text (Top Left / Bottom Right)
        self.hud_text.y += 2
        self.hud_text.color = arcade.color.BLACK
        self.hud_text.draw()
        self.hud_text.y -= 2
        self.hud_text.color = arcade.color.WHITE
        self.hud_text.draw()

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        if scroll_y > 0:
            self.camera_map.zoom *= 1.1
        else:
            self.camera_map.zoom *= 0.9

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
        if buttons == arcade.MOUSE_BUTTON_LEFT:
            cur_x, cur_y = self.camera_map.position
            self.camera_map.position = (cur_x - dx, cur_y - dy)
