import arcade
import arcade.gui
from typing import Dict, List, Optional, Tuple
from saga_engine.core.state import CampaignState, RegionalState
from saga_engine.core.bus import EventBus
from saga_engine.core.chronicler import Chronicler

TILE_SIZE = 16 # Pixels for micro-tiles

class RegionalDashboardView(arcade.View):
    """
    Detailed 32x32 micro-view of a single macro hex.
    """
    
    def __init__(self, bus: EventBus, state: CampaignState, 
                 chronicler: Chronicler, macro_view: arcade.View):
        super().__init__()
        self.bus = bus
        self.state = state
        self.chronicler = chronicler
        self.macro_view = macro_view # To return back
        
        self.camera_map = arcade.camera.Camera2D()
        self.camera_gui = arcade.camera.Camera2D()
        
        self.ui_manager = arcade.gui.UIManager()
        self.ui_manager.enable()
        
        # Tile Palette (Regional)
        # 0: Water, 1: Sand/Dirt, 2: Grass, 3: Trees, 4: Rock/Mountain, 5: Swamp/Mud
        self.tile_palette = {
            0: (50, 100, 200),    # Water
            1: (210, 180, 140),   # Sand/Dirt
            2: (100, 180, 80),    # Grass
            3: (40, 90, 40),      # Trees
            4: (110, 110, 120),   # Rock
            5: (70, 60, 40)       # Mud/Swamp
        }
        
        self.tile_shape_list = arcade.shape_list.ShapeElementList()
        self._build_regional_map()
        self._setup_ui()

    def _setup_ui(self):
        v_box = arcade.gui.UIBoxLayout()
        back_btn = arcade.gui.UIFlatButton(text="Return to World Map", width=200)
        @back_btn.event("on_click")
        def on_click_back(event):
            self.window.show_view(self.macro_view)
        
        v_box.add(back_btn.with_padding(bottom=10))
        
        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(child=v_box.with_padding(left=10, top=10), anchor_x="left", anchor_y="top")
        self.ui_manager.add(anchor)

    def _build_regional_map(self):
        reg_state: RegionalState = self.state.active_regional_state
        if not reg_state: return
        
        self.tile_shape_list = arcade.shape_list.ShapeElementList()
        
        # Center the 32x32 grid
        offset_x = -(32 * TILE_SIZE) / 2
        offset_y = -(32 * TILE_SIZE) / 2
        
        for idx, tile in enumerate(reg_state.tiles):
            x_idx = idx % 32
            y_idx = idx // 32
            
            cx = offset_x + x_idx * TILE_SIZE + TILE_SIZE/2
            cy = offset_y + y_idx * TILE_SIZE + TILE_SIZE/2
            
            base_color = self.tile_palette.get(tile.type_id, (128, 128, 128))
            # Apply slight height/mana tinting
            tint = int((tile.height - 0.5) * 30)
            color = (
                max(0, min(255, base_color[0] + tint)),
                max(0, min(255, base_color[1] + tint)),
                max(0, min(255, base_color[2] + tint))
            )
            
            rect = arcade.shape_list.create_rectangle_filled(cx, cy, TILE_SIZE, TILE_SIZE, color)
            self.tile_shape_list.append(rect)
            
        self.camera_map.position = (0, 0)
        self.camera_gui.view_data.position = (self.window.width // 2, self.window.height // 2)

    def on_draw(self):
        self.clear()
        
        self.camera_map.use()
        self.tile_shape_list.draw()
        
        # Draw Player Marker (Regional)
        # For now, let's just draw it at center of map
        arcade.draw_circle_filled(0, 0, 8, arcade.color.GOLD)
        arcade.draw_circle_outline(0, 0, 8, arcade.color.BLACK, 2)
        
        self.camera_gui.use()
        self.ui_manager.draw()
        
        # HUD Info
        arcade.draw_text(
            f"REGION: Parent Hex {self.state.active_regional_state.parent_hex_id if self.state.active_regional_state else 'N/A'}",
            self.window.width - 20, 20, arcade.color.WHITE, 12, anchor_x="right"
        )

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        if scroll_y > 0:
            self.camera_map.zoom *= 1.1
        else:
            self.camera_map.zoom *= 0.9

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
        if buttons == arcade.MOUSE_BUTTON_LEFT:
            cur_x, cur_y = self.camera_map.position
            self.camera_map.position = (cur_x - dx, cur_y - dy)
