# python_fmg/renderers/renderer.py
import os
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPolygonItem, QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsLineItem, QGraphicsPixmapItem
from PyQt6.QtGui import QPolygonF, QPen, QBrush, QColor, QPainter, QTransform, QFont, QPixmap
from PyQt6.QtCore import pyqtSignal, QPointF, Qt
from pathlib import Path
import math
BASE_DIR = Path(__file__).resolve().parents[2].parent
from python_fmg.config import paths
OSTRAKA_PICS = paths.OSTRAKA_PICS
PUBLIC_TEXTURES = paths.PUBLIC_TEXTURES
from python_fmg.core.grid import hex_to_pixel, get_neighbors, pixel_to_hex

def interpolate_visual_state(current_year: int, states: list):
    if not states:
        return None
    sorted_states = sorted(states, key=lambda s: s["year"])
    if current_year <= sorted_states[0]["year"]:
        return sorted_states[0]["color"], sorted_states[0].get("opacity", 1.0)
    if current_year >= sorted_states[-1]["year"]:
        return sorted_states[-1]["color"], sorted_states[-1].get("opacity", 1.0)
        
    for i in range(len(sorted_states) - 1):
        s1 = sorted_states[i]
        s2 = sorted_states[i+1]
        if s1["year"] <= current_year <= s2["year"]:
            t = (current_year - s1["year"]) / (s2["year"] - s1["year"])
            c1 = QColor(s1["color"])
            c2 = QColor(s2["color"])
            r = int(c1.red() + t * (c2.red() - c1.red()))
            g = int(c1.green() + t * (c2.green() - c1.green()))
            b = int(c1.blue() + t * (c2.blue() - c1.blue()))
            op1 = s1.get("opacity", 1.0)
            op2 = s2.get("opacity", 1.0)
            opacity = op1 + t * (op2 - op1)
            return QColor(r, g, b), opacity
    return None

BIOME_COLORS = {
    0: QColor("#2E8B57"), # Jungle (Sea Green)
    1: QColor("#228B22"), # Forest (Forest Green)
    2: QColor("#4682B4"), # Taiga (Steel Blue)
    3: QColor("#E6C229"), # Desert (Warm Sand Gold)
    4: QColor("#98FB98"), # Plains (Pale Green)
    5: QColor("#B0C4DE"), # Tundra (Light Steel Blue)
    6: QColor("#708090"), # Mountain (Slate Gray)
    7: QColor("#D35400"), # Volcano (Warm Terracotta/Orange)
    8: QColor("#F0F8FF"), # Arctic (Alice Blue)
    9: QColor("#1F3A52"), # Ocean / Kelp Forest (Rich Deep Blue-Teal)
    10: QColor("#1D8A99"), # Coral Reef (Bright Turquoise)
    11: QColor("#10253C"), # Arctic Ocean (Navy Blue)
    12: QColor("#0A1128"), # Abyssal Trench (Midnight Navy)
    13: QColor("#3D0C5A")  # Prison Wastes (Royal Purple)
}

FACTION_COLORS = [
    QColor("#3498DB"), QColor("#E74C3C"), QColor("#2ECC71"), QColor("#F1C40F"),
    QColor("#9B59B6"), QColor("#1ABC9C"), QColor("#E67E22"), QColor("#34495E"),
    QColor("#D35400"), QColor("#27AE60"), QColor("#2980B9"), QColor("#8E44AD"),
    QColor("#C0392B"), QColor("#16A085")
]

MARKER_ICONS = {
    "Ruins": "R",
    "Dungeon": "D",
    "Cave": "C",
    "Portal": "P",
    "Obelisk": "O"
}

class HexCellItem(QGraphicsPolygonItem):
    def __init__(self, q, r, hx, size=12.0, viewer=None):
        super().__init__()
        self.q = q
        self.r = r
        self.hx = hx
        self.size = size
        self.viewer = viewer
        self.tile_item = None
        self.arrow_lbl = None
        
        # Check if the cell has custom voronoi vertices
        vertices = getattr(hx, "vertices", None)
        if vertices:
            poly = QPolygonF([QPointF(x, y) for x, y in vertices])
            self.setPolygon(poly)
            self.setPos(0, 0) 
            self.cx = sum(v[0] for v in vertices) / len(vertices)
            self.cy = sum(v[1] for v in vertices) / len(vertices)
        else:
            points = []
            for i in range(6):
                angle_rad = math.pi / 3 * i
                px = size * math.cos(angle_rad)
                py = size * math.sin(angle_rad)
                points.append(QPointF(px, py))
            poly = QPolygonF(points)
            self.setPolygon(poly)
            x, y = hex_to_pixel(q, r, size)
            self.setPos(x, y)
            self.cx = x
            self.cy = y
            
        self.update_style()
        
    def update_style(self):
        if hasattr(self, 'tile_item') and self.tile_item:
            try:
                if self.tile_item.scene():
                    self.tile_item.scene().removeItem(self.tile_item)
            except RuntimeError:
                pass
            self.tile_item = None
            
        if hasattr(self, 'arrow_lbl') and self.arrow_lbl:
            try:
                if self.arrow_lbl.scene():
                    self.arrow_lbl.scene().removeItem(self.arrow_lbl)
            except RuntimeError:
                pass
            self.arrow_lbl = None

        render_mode = getattr(self.viewer, 'render_mode', 'Biomes') if self.viewer else "Biomes"
        color = QColor("#333333")
        
        day_in_year = self.viewer.current_year % 360 if self.viewer else 0
        is_winter = math.sin(day_in_year / 360.0 * 2 * math.pi) < -0.5
        is_summer = math.sin(day_in_year / 360.0 * 2 * math.pi) > 0.5
        
        rendered_biome = self.hx.biome
        if is_winter:
            if rendered_biome in (0, 1, 2, 4):
                rendered_biome = 5
        elif is_summer:
            if rendered_biome == 5:
                rendered_biome = 4
        
        if render_mode == "Biomes":
            color = self.viewer.biome_colors.get(rendered_biome, BIOME_COLORS.get(rendered_biome, QColor("#333333"))) if self.viewer else BIOME_COLORS.get(rendered_biome, QColor("#333333"))
        elif render_mode == "Elevation":
            val = self.hx.elevation
            if val < 3:
                d = val / 3.0
                color = QColor(int(10 + d*15), int(20 + d*30), int(50 + d*80))
            else:
                h = (val - 3) / 12.0
                if h < 0.4:
                    color = QColor(int(34 + h*50), int(139 - h*50), int(34 + h*10))
                elif h < 0.8:
                    color = QColor(int(139 + (h-0.4)*100), int(90 - (h-0.4)*40), int(43 - (h-0.4)*20))
                else:
                    color = QColor(int(220 + (h-0.8)*170), int(220 + (h-0.8)*170), int(220 + (h-0.8)*170))
        elif render_mode == "Temperature":
            t = self.hx.p2 / 255.0
            color = QColor(int(50 + t*205), int(100 - t*50), int(250 - t*230))
        elif render_mode == "Moisture":
            m = self.hx.p3 / 255.0
            color = QColor(int(240 - m*200), int(230 - m*180), int(140 + m*115))
        elif render_mode == "Chaos / Infestation":
            c = self.hx.p1 / 255.0
            color = QColor(int(24 + c*220), int(24 - c*24), int(28 + c*180))
        elif render_mode == "Factions & States":
            if self.hx.settlement:
                f_id = self.hx.settlement.faction_id
                active = True
                if self.viewer and self.viewer.last_state:
                    fac = self.viewer.last_state.factions.get(f_id)
                    if fac:
                        v_from = getattr(fac, "valid_from", 0)
                        v_until = getattr(fac, "valid_until", 9999)
                        if not (v_from <= self.viewer.current_year <= v_until):
                            active = False
                if active:
                    color = FACTION_COLORS[f_id % len(FACTION_COLORS)]
                else:
                    color = QColor("#1C1C22")
            else:
                color = QColor("#1C1C22")
        elif render_mode == "Religions":
            if self.hx.religion_id > 0 and self.viewer and self.viewer.last_state:
                rel = self.viewer.last_state.religions.get(self.hx.religion_id)
                if rel: color = QColor(rel.color)
            else:
                color = QColor("#1E1E24")
        elif render_mode == "Cultures":
            if self.hx.culture_id > 0 and self.viewer and self.viewer.last_state:
                cul = self.viewer.last_state.cultures.get(self.hx.culture_id)
                if cul: color = QColor(cul.color)
            else:
                color = QColor("#1E1E24")
        elif render_mode == "Provinces":
            if self.hx.province_id > 0 and self.viewer and self.viewer.last_state:
                prov = self.viewer.last_state.provinces.get(self.hx.province_id)
                if prov: color = QColor(prov.color)
            else:
                color = QColor("#1E1E24")
        elif render_mode == "Ocean Currents":
            if self.hx.elevation < 3:
                color = QColor("#0c1c2b")
            else:
                color = QColor("#222222")

        # Temporal Visual States color/alpha overrides
        if render_mode == "Factions & States" and self.hx.settlement and self.viewer:
            f_id = self.hx.settlement.faction_id
            v_states = self.viewer.worldsmith_config.get("faction_visual_states", {}).get(str(f_id))
            if v_states:
                res = interpolate_visual_state(self.viewer.current_year, v_states)
                if res:
                    col_val, opacity = res
                    color = QColor(col_val)
                    color.setAlpha(int(opacity * 255))
                    
        # Check Unreliable Narrator Fog of War
        main_win = self.viewer.parent() if self.viewer else None
        while main_win and not hasattr(main_win, "cb_narrator") and hasattr(main_win, "parent"):
            main_win = main_win.parent()
            
        if main_win and hasattr(main_win, "cb_narrator"):
            idx = main_win.cb_narrator.currentIndex()
            profile_id = main_win.cb_narrator.itemData(idx)
            if profile_id:
                narrators = self.viewer.worldsmith_config.get("unreliable_narrators", [])
                profile = next((n for n in narrators if n["profile_id"] == profile_id), None)
                if profile:
                    radius = profile.get("fog_of_war_radius", 15)
                    cq = profile.get("center_q", 0)
                    cr = profile.get("center_r", 0)
                    dist = (abs(self.q - cq) + abs(self.q + self.r - cq - cr) + abs(self.r - cr)) / 2
                    if dist > radius:
                        color = QColor(12, 12, 18, 240)
                        if self.tile_item:
                            self.tile_item.setVisible(False)
                            
        if self.hx.settlement:
            pen = QPen(QColor("#FF00FF"), 1.5)
        elif self.hx.chaos_domain:
            pen = QPen(QColor("#FF3333"), 1.5)
        else:
            pen = QPen(QColor("#1A1A1A"), 0.5)
            
        self.setPen(pen)
        
        tile_path = None
        if render_mode == "Biomes":
            # Use a selectable floor texture for all biomes
            # Resolve assets relative to this file's location for a portable package
            from pathlib import Path
            project_root = Path(__file__).resolve().parent.parent  # python_fmg directory
            texture_dir = str(project_root / "assets" / "textures")
            # List of available floor textures (representative samples)
            floor_textures = [
                "volcanic_floor_0.png",
                "swamp_0_new.png",
                "sand_1.png",
                "moss_0.png",
                "mud_0.png",
                "lava_0.png",
                "lair_0_new.png",
                "infernal_1.png",
                "ice_0_new.png",
                "green_bones_0.png",
                "grass0-dirt-mix_1.png",
                "grass_flowers_blue_1_new.png",
                "frozen_0.png",
                "floor_vines_0_new.png",
                "floor_sand_stone_0.png",
                "dirt_0_new.png",
                "cobble_blood_0_new.png",
                "bog_green_0_new.png",
                "acidic_floor_0.png"
            ]
            # Choose a tile based on the biome index to provide variety
            floor_tile = floor_textures[rendered_biome % len(floor_textures)]
            # Choose floor texture as default
            tile_file = floor_tile
            # Additional texture handling for trees and water
            tree_dir = str(OSTRAKA_PICS / "trees")
            water_dir = str(OSTRAKA_PICS / "water")
            if os.path.isdir(tree_dir):
                tree_textures = [f for f in os.listdir(tree_dir) if f.lower().endswith('.png')]
            else:
                tree_textures = []
            if os.path.isdir(water_dir):
                water_textures = [f for f in os.listdir(water_dir) if f.lower().endswith('.png')]
            else:
                water_textures = []
            # Placeholder biome sets (adjust indices as needed)
            water_biomes = {0}
            forest_biomes = {1, 2}
            if self.hx.biome in water_biomes and water_textures:
                tile_file = os.path.join(water_dir, water_textures[rendered_biome % len(water_textures)])
            elif self.hx.biome in forest_biomes and tree_textures:
                tile_file = os.path.join(tree_dir, tree_textures[rendered_biome % len(tree_textures)])
            path = os.path.join(texture_dir, tile_file)
            if os.path.exists(path):
                tile_path = path
                    
        if tile_path:
            self.setBrush(QBrush(color.darker(140)))
            target_w = int(self.size * 2.2)
            target_h = int(self.size * 2.2)
            scaled_pix = self.viewer.get_cached_pixmap(tile_path, target_w) if self.viewer else None
            
            if scaled_pix:
                if self.tile_item:
                    self.tile_item.setPixmap(scaled_pix)
                    self.tile_item.setVisible(True)
                else:
                    self.tile_item = QGraphicsPixmapItem(scaled_pix, self)
                
                vertices = getattr(self.hx, "vertices", None)
                if vertices:
                    self.tile_item.setPos(self.cx - target_w / 2, self.cy - target_h / 2)
                else:
                    self.tile_item.setPos(-target_w / 2, -target_h / 2)
            else:
                if self.tile_item:
                    self.tile_item.setVisible(False)
        else:
            self.setBrush(QBrush(color))
            if self.tile_item:
                self.tile_item.setVisible(False)
            
        # Draw ocean current arrows
        if render_mode == "Ocean Currents" and self.hx.elevation < 3:
            curr_dir = self.hx.current_direction or self.hx.wind_direction
            arrow_str = {"NE": "↗", "SW": "↙", "NW": "↖", "SE": "↘"}.get(curr_dir, "→")
            self.arrow_lbl = QGraphicsTextItem(arrow_str, self)
            self.arrow_lbl.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            self.arrow_lbl.setDefaultTextColor(QColor("#29b6f6"))
            vertices = getattr(self.hx, "vertices", None)
            if vertices:
                self.arrow_lbl.setPos(self.cx - 6, self.cy - 10)
            else:
                self.arrow_lbl.setPos(-6, -10)

class WorldMapViewer(QGraphicsView):
    hex_selected = pyqtSignal(int, int) # coordinates q, r
    hex_hovered = pyqtSignal(int, int)  # hovered coordinates q, r
    hex_painted = pyqtSignal(int, int, str, int) # q, r, attribute_name, new_val
    place_settlement_requested = pyqtSignal(int, int)
    place_marker_requested = pyqtSignal(int, int)
    place_force_requested = pyqtSignal(int, int)
    link_route_requested = pyqtSignal(int, int)
    
    def get_cached_pixmap(self, icon_path, size=18):
        cache_key = (icon_path, size)
        if cache_key not in self.pixmap_cache:
            if os.path.exists(icon_path):
                pix = QPixmap(icon_path)
                scaled_pix = pix.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.pixmap_cache[cache_key] = scaled_pix
            else:
                self.pixmap_cache[cache_key] = None
        return self.pixmap_cache[cache_key]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.pixmap_cache = {}
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setMouseTracking(True)
        
        self.cell_items = {}
        self.selected_item = None
        self.cell_size = 12.0
        self.last_state = None
        
        self.tool_mode = "Select"
        self.render_mode = "Biomes"
        self.brush_value = 0
        self.brush_str_value = ""
        self.brush_radius = 1
        self.brush_power = 1.0
        self.elevation_brush_mode = "Align"
        
        self.is_panning = False
        self.pan_last_mouse_pos = None
        self.is_painting = False
        
        self.biome_colors = {}
        self.current_year = 9999
        self.current_z_layer = "surface"
        self.name_overrides = {}
        self.suggested_pins = [] # List of tuples: (q, r, text)
        
    def set_tool_mode(self, mode: str, value = 0):
        self.tool_mode = mode
        if isinstance(value, str):
            self.brush_str_value = value
        else:
            self.brush_value = value
            
    def set_render_mode(self, mode: str):
        self.render_mode = mode

    def select_hex(self, q, r):
        if self.selected_item:
            self.selected_item.update_style()
        self.selected_item = self.cell_items.get((q, r))
        if self.selected_item:
            self.selected_item.setPen(QPen(QColor("#00FFCC"), 2.0))
            self.centerOn(self.selected_item)

    def paint_cell_at_pos(self, scene_pos):
        q, r = pixel_to_hex(scene_pos.x(), scene_pos.y(), self.cell_size)
        if (q, r) not in self.cell_items:
            return
            
        affected = [(q, r)]
        if self.brush_radius > 1:
            affected = get_neighbors(q, r, self.brush_radius - 1)
            affected.append((q, r))
            
        for nq, nr in affected:
            if (nq, nr) in self.cell_items:
                if self.tool_mode == "Paint Biome":
                    self.hex_painted.emit(nq, nr, "biome", self.brush_value)
                elif self.tool_mode == "Paint Elevation":
                    # Heuristics for elevation editing
                    current_val = self.cell_items[(nq, nr)].hx.elevation
                    if self.elevation_brush_mode == "Raise":
                        new_val = min(15, current_val + 1)
                    elif self.elevation_brush_mode == "Lower":
                        new_val = max(1, current_val - 1)
                    else: # Align
                        new_val = self.brush_value
                    self.hex_painted.emit(nq, nr, "elevation", new_val)
                elif self.tool_mode == "Paint Chaos":
                    self.hex_painted.emit(nq, nr, "chaos", self.brush_value)
                elif self.tool_mode == "Paint Temp":
                    self.hex_painted.emit(nq, nr, "temp", self.brush_value)
                elif self.tool_mode == "Paint Moisture":
                    self.hex_painted.emit(nq, nr, "moisture", self.brush_value)

    def mousePressEvent(self, event):
        if event.button() in (Qt.MouseButton.RightButton, Qt.MouseButton.MiddleButton):
            self.is_panning = True
            self.pan_last_mouse_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        elif event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            if self.tool_mode == "Select":
                q, r = pixel_to_hex(scene_pos.x(), scene_pos.y(), self.cell_size)
                if (q, r) in self.cell_items:
                    self.select_hex(q, r)
                    self.hex_selected.emit(q, r)
            elif self.tool_mode == "Place Settlement":
                q, r = pixel_to_hex(scene_pos.x(), scene_pos.y(), self.cell_size)
                if (q, r) in self.cell_items:
                    self.place_settlement_requested.emit(q, r)
            elif self.tool_mode == "Place Marker":
                q, r = pixel_to_hex(scene_pos.x(), scene_pos.y(), self.cell_size)
                if (q, r) in self.cell_items:
                    self.place_marker_requested.emit(q, r)
            elif self.tool_mode == "Place Force":
                q, r = pixel_to_hex(scene_pos.x(), scene_pos.y(), self.cell_size)
                if (q, r) in self.cell_items:
                    self.place_force_requested.emit(q, r)
            elif self.tool_mode == "Link Route":
                q, r = pixel_to_hex(scene_pos.x(), scene_pos.y(), self.cell_size)
                if (q, r) in self.cell_items:
                    self.link_route_requested.emit(q, r)
            else:
                self.is_painting = True
                self.paint_cell_at_pos(scene_pos)
                
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        q, r = pixel_to_hex(scene_pos.x(), scene_pos.y(), self.cell_size)
        if (q, r) in self.cell_items:
            self.hex_hovered.emit(q, r)

        if self.is_panning:
            delta = event.pos() - self.pan_last_mouse_pos
            self.pan_last_mouse_pos = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        elif self.is_painting and self.tool_mode.startswith("Paint"):
            self.paint_cell_at_pos(scene_pos)
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        if event.button() in (Qt.MouseButton.RightButton, Qt.MouseButton.MiddleButton):
            self.is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        elif event.button() == Qt.MouseButton.LeftButton:
            self.is_painting = False
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        zoom_factor = 1.25
        if event.angleDelta().y() < 0:
            zoom_factor = 1.0 / zoom_factor
            
        self.scale(zoom_factor, zoom_factor)

    def load_map(self, state):
        self.last_state = state
        self.scene.clear()
        self.cell_items.clear()
        self.selected_item = None
        
        # Draw Hexes
        for (q, r), hx in state.hexes.items():
            item = HexCellItem(q, r, hx, self.cell_size, self)
            
            if hx.settlement:
                valid_from = getattr(hx.settlement, "valid_from", 0)
                valid_until = getattr(hx.settlement, "valid_until", 9999)
                z_lay = getattr(hx.settlement, "z_layer", "surface")
                
                if (z_lay != self.current_z_layer) or not (valid_from <= self.current_year <= valid_until):
                    self.scene.addItem(item)
                    self.cell_items[(q, r)] = item
                    
                    if self.current_z_layer == "magic" and hx.res >= 50000:
                        magic_dot = QGraphicsEllipseItem(-5, -5, 10, 10, item)
                        magic_dot.setBrush(QBrush(QColor("#9933FF")))
                        magic_dot.setPen(QPen(QColor("#D9A3FF"), 1))
                    continue
                else:
                    self.scene.addItem(item)
                    self.cell_items[(q, r)] = item
                    
                    town_icon_path = str(PUBLIC_TEXTURES / "town_icon.png")
                    keep_icon_path = str(PUBLIC_TEXTURES / "keep_icon.png")
                    icon_path = keep_icon_path if hx.settlement.settlement_level >= 3 else town_icon_path
                    
                    scaled_pix = self.get_cached_pixmap(icon_path, 18)
                    if scaled_pix:
                        sett_marker = QGraphicsPixmapItem(scaled_pix, item)
                        sett_marker.setPos(-9, -9)
                    else:
                        sett_marker = QGraphicsEllipseItem(-3, -3, 6, 6, item)
                        sett_marker.setBrush(QBrush(QColor("#FF00FF")))
                        sett_marker.setPen(QPen(Qt.PenStyle.NoPen))
                    
                    name = hx.settlement.name
                    if self.name_overrides:
                        name = self.name_overrides.get(name, name)
                        
                    lbl = QGraphicsTextItem(name, item)
                    lbl.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
                    lbl.setDefaultTextColor(QColor("#FFFFFF"))
                    lbl.setPos(-15, 6)
                    continue
                    
            self.scene.addItem(item)
            self.cell_items[(q, r)] = item
            
            if self.current_z_layer == "magic" and hx.res >= 50000:
                magic_dot = QGraphicsEllipseItem(-5, -5, 10, 10, item)
                magic_dot.setBrush(QBrush(QColor("#9933FF")))
                magic_dot.setPen(QPen(QColor("#D9A3FF"), 1))
            
        # Draw world entities
        for ent in state.entities:
            cell_item = self.cell_items.get((ent.global_q, ent.global_r))
            if cell_item:
                ent_type = ent.type.lower()
                icon_file = None
                if "caravan" in ent_type:
                    icon_file = "caravan_icon.png"
                elif "ship" in ent_type:
                    icon_file = "ship_icon.png"
                icon_path = os.path.join(PUBLIC_TEXTURES, icon_file) if icon_file else None
                scaled_pix = self.get_cached_pixmap(icon_path, 18) if icon_path else None
                if scaled_pix:
                    text_marker = QGraphicsPixmapItem(scaled_pix, cell_item)
                    text_marker.setPos(-9, -9)
                else:
                    text_marker = QGraphicsTextItem("R" if "regiment" in ent.type.lower() else "E", cell_item)
                    text_marker.setFont(QFont("Arial", 8))
                    text_marker.setPos(-8, -10)
                
        # Draw custom markers (POIs)
        for mark in state.markers:
            cell_item = self.cell_items.get((mark.global_q, mark.global_r))
            if cell_item:
                # Determine marker icon from multiple asset folders
                def find_marker_path(mark_type: str) -> str:
                    asset_dirs = [
                        str(OSTRAKA_PICS / "effect"),
                        str(OSTRAKA_PICS / "icons"),
                        str(OSTRAKA_PICS / "objects"),
                        str(OSTRAKA_PICS / "spells"),
                    ]
                    candidates = [
                        f"{mark_type.lower()}.png",
                        f"{mark_type.lower()}.jpg",
                        f"{mark_type.lower()}.jpeg",
                        f"{mark_type.lower()}_icon.png",
                        f"{mark_type.lower()}_icon.jpg",
                        f"{mark_type.lower()}_icon.jpeg",
                    ]
                    for d in asset_dirs:
                        if os.path.isdir(d):
                            for cand in candidates:
                                p = os.path.join(d, cand)
                                if os.path.isfile(p):
                                    return p
                    return None
                icon_path = find_marker_path(mark.type)
                scaled_pix = self.get_cached_pixmap(icon_path, 18) if icon_path else None
                if scaled_pix:
                    marker_lbl = QGraphicsPixmapItem(scaled_pix, cell_item)
                    marker_lbl.setPos(-9, -12)
                else:
                    icon = MARKER_ICONS.get(mark.type, "*")
                    marker_lbl = QGraphicsTextItem(icon, cell_item)
                    marker_lbl.setFont(QFont("Arial", 8))
                    marker_lbl.setPos(-8, -16)
                
        # Draw trade routes
        sett_id_to_pos = {}
        for (q, r), hx in state.hexes.items():
            if hx.settlement and hx.settlement.id and (q, r) in self.cell_items:
                valid_from = getattr(hx.settlement, "valid_from", 0)
                valid_until = getattr(hx.settlement, "valid_until", 9999)
                z_lay = getattr(hx.settlement, "z_layer", "surface")
                if z_lay == self.current_z_layer and (valid_from <= self.current_year <= valid_until):
                    item = self.cell_items[(q, r)]
                    sett_id_to_pos[hx.settlement.id] = (item.cx, item.cy)
                
        for route in state.routes:
            z_lay = getattr(route, "z_layer", "surface")
            if z_lay != self.current_z_layer:
                continue
                
            p1 = sett_id_to_pos.get(route.settlement_a_id)
            p2 = sett_id_to_pos.get(route.settlement_b_id)
            if p1 and p2:
                line = QGraphicsLineItem(p1[0], p1[1], p2[0], p2[1])
                line.setPen(QPen(QColor("#FFCC00"), 1.2, Qt.PenStyle.DashLine))
                self.scene.addItem(line)
                
        # Draw AI Suggested Pins
        if hasattr(self, "suggested_pins") and self.suggested_pins:
            for q, r, text in self.suggested_pins:
                cell_item = self.cell_items.get((q, r))
                if cell_item:
                    pin_dot = QGraphicsEllipseItem(-7, -7, 14, 14, cell_item)
                    pin_dot.setBrush(QBrush(QColor("#00FF66")))
                    pin_dot.setPen(QPen(QColor("#FFFFFF"), 2))
                    lbl = QGraphicsTextItem(text, cell_item)
                    lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                    lbl.setDefaultTextColor(QColor("#00FF66"))
                    lbl.setPos(-15, -24)
