# python_fmg/renderers/renderer.py
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPolygonItem, QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsLineItem
from PyQt6.QtGui import QPolygonF, QPen, QBrush, QColor, QPainter, QTransform, QFont
from PyQt6.QtCore import pyqtSignal, QPointF, Qt
import math
import random
from python_fmg.core.grid import hex_to_pixel, get_neighbors, pixel_to_hex

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
    "Ruins": "🏛️",
    "Dungeon": "🛡️",
    "Cave": "🕳️",
    "Portal": "🌀",
    "Obelisk": "🗿"
}

class HexCellItem(QGraphicsPolygonItem):
    def __init__(self, q, r, hx, size=12.0, viewer=None):
        super().__init__()
        self.q = q
        self.r = r
        self.hx = hx
        self.size = size
        self.viewer = viewer
        
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
        self.update_style()
        
    def update_style(self):
        render_mode = self.viewer.render_mode if self.viewer else "Biomes"
        color = QColor("#333333")
        
        if render_mode == "Biomes":
            color = BIOME_COLORS.get(self.hx.biome, QColor("#333333"))
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
                color = FACTION_COLORS[f_id % len(FACTION_COLORS)]
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
                
        if self.hx.settlement:
            pen = QPen(QColor("#FF00FF"), 1.5)
        elif self.hx.chaos_domain:
            pen = QPen(QColor("#FF3333"), 1.5)
        else:
            pen = QPen(QColor("#1A1A1A"), 0.5)
            
        self.setPen(pen)
        self.setBrush(QBrush(color))

class WorldMapViewer(QGraphicsView):
    hex_selected = pyqtSignal(int, int) # coordinates q, r
    hex_painted = pyqtSignal(int, int, str, int) # q, r, attribute_name, new_val
    place_settlement_requested = pyqtSignal(int, int)
    place_marker_requested = pyqtSignal(int, int)
    place_force_requested = pyqtSignal(int, int)
    link_route_requested = pyqtSignal(int, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        
        self.cell_items = {}
        self.selected_item = None
        self.cell_size = 12.0
        self.last_state = None
        
        self.tool_mode = "Select"
        self.brush_value = 0
        self.brush_str_value = ""
        self.brush_radius = 1
        self.brush_power = 5
        self.elevation_brush_mode = "Align"
        self.is_painting = False
        self.is_panning = False
        self.pan_last_mouse_pos = None
        self.render_mode = "Biomes"
        
        self.setBackgroundBrush(QBrush(QColor("#08080C")))
        
    def set_tool_mode(self, mode: str, value = 0):
        self.tool_mode = mode
        if isinstance(value, str):
            self.brush_str_value = value
            self.brush_value = 0
        else:
            self.brush_value = value
            self.brush_str_value = ""
            
        if mode == "Select":
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            
    def set_render_mode(self, mode: str):
        self.render_mode = mode
        for item in self.cell_items.values():
            item.update_style()
            
    def load_map(self, state):
        self.last_state = state
        self.scene.clear()
        self.cell_items.clear()
        self.selected_item = None
        
        # Draw Hexes
        for (q, r), hx in state.hexes.items():
            item = HexCellItem(q, r, hx, self.cell_size, self)
            self.scene.addItem(item)
            self.cell_items[(q, r)] = item
            
            # Settlement indicator + labels
            if hx.settlement:
                sett_marker = QGraphicsEllipseItem(-3, -3, 6, 6, item)
                sett_marker.setBrush(QBrush(QColor("#FF00FF")))
                sett_marker.setPen(QPen(Qt.PenStyle.NoPen))
                
                # Label
                lbl = QGraphicsTextItem(hx.settlement.name, item)
                lbl.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
                lbl.setDefaultTextColor(QColor("#FFFFFF"))
                lbl.setPos(-15, 6)
                
        # Draw world entities
        for ent in state.entities:
            cell_item = self.cell_items.get((ent.global_q, ent.global_r))
            if cell_item:
                text_marker = QGraphicsTextItem("⚔️" if "regiment" in ent.type.lower() else "🌪️", cell_item)
                text_marker.setFont(QFont("Arial", 8))
                text_marker.setPos(-8, -10)
                
        # Draw custom markers (POIs)
        for mark in state.markers:
            cell_item = self.cell_items.get((mark.global_q, mark.global_r))
            if cell_item:
                icon = MARKER_ICONS.get(mark.type, "📍")
                marker_lbl = QGraphicsTextItem(icon, cell_item)
                marker_lbl.setFont(QFont("Arial", 8))
                marker_lbl.setPos(-8, -16)
                
        # Draw trade routes
        sett_id_to_pos = {}
        for (q, r), hx in state.hexes.items():
            if hx.settlement and hx.settlement.id:
                sett_id_to_pos[hx.settlement.id] = hex_to_pixel(q, r, self.cell_size)
                
        for route in state.routes:
            p1 = sett_id_to_pos.get(route.settlement_a_id)
            p2 = sett_id_to_pos.get(route.settlement_b_id)
            if p1 and p2:
                line = QGraphicsLineItem(p1[0], p1[1], p2[0], p2[1])
                pen = QPen(QColor("#E67E22"), 1.2, Qt.PenStyle.DashLine)
                line.setPen(pen)
                self.scene.addItem(line)
                
        items_rect = self.scene.itemsBoundingRect()
        # Set a large scene rect to allow scrollbars to pan freely around the map
        self.scene.setSceneRect(items_rect.adjusted(-2000, -2000, 2000, 2000))
        self.fitInView(items_rect, Qt.AspectRatioMode.KeepAspectRatio)
        
    def select_hex(self, q, r):
        if self.selected_item:
            self.selected_item.update_style()
            
        item = self.cell_items.get((q, r))
        if item:
            self.selected_item = item
            item.setPen(QPen(QColor("#F1C40F"), 2.5))

    def get_hexes_in_brush_radius(self, q, r, radius):
        if radius <= 1:
            return [(q, r)]
        coords = []
        max_dist = radius - 1
        for dq in range(-max_dist, max_dist + 1):
            for dr in range(max(-max_dist, -dq - max_dist), min(max_dist, -dq + max_dist) + 1):
                nq, nr = q + dq, r + dr
                if (nq, nr) in self.cell_items:
                    coords.append((nq, nr))
        return coords
            
    def paint_cell_at_pos(self, scene_pos):
        q, r = pixel_to_hex(scene_pos.x(), scene_pos.y(), self.cell_size)
        target_item = self.cell_items.get((q, r))
        if not target_item:
            return

        affected_coords = self.get_hexes_in_brush_radius(q, r, self.brush_radius)
        
        if self.tool_mode == "Paint Elevation":
            orig_heights = {}
            for nq, nr in affected_coords:
                item = self.cell_items.get((nq, nr))
                if item:
                    orig_heights[(nq, nr)] = item.hx.elevation
                    
            for nq, nr in affected_coords:
                item = self.cell_items.get((nq, nr))
                if not item:
                    continue
                
                if self.elevation_brush_mode == "Align":
                    item.hx.elevation = max(0, min(15, self.brush_value))
                elif self.elevation_brush_mode == "Raise":
                    item.hx.elevation = max(0, min(15, item.hx.elevation + int(self.brush_power)))
                elif self.elevation_brush_mode == "Lower":
                    item.hx.elevation = max(0, min(15, item.hx.elevation - int(self.brush_power)))
                elif self.elevation_brush_mode == "Smooth":
                    neighbors = get_neighbors(nq, nr)
                    sum_h = item.hx.elevation
                    count = 1
                    for nq2, nr2 in neighbors:
                        if (nq2, nr2) in orig_heights:
                            sum_h += orig_heights[(nq2, nr2)]
                            count += 1
                        elif (nq2, nr2) in self.cell_items:
                            sum_h += self.cell_items[(nq2, nr2)].hx.elevation
                            count += 1
                    avg_h = round(sum_h / count)
                    item.hx.elevation = max(0, min(15, avg_h))
                elif self.elevation_brush_mode == "Disrupt":
                    noise = random.randint(-int(self.brush_power), int(self.brush_power))
                    item.hx.elevation = max(0, min(15, item.hx.elevation + noise))
                
                item.update_style()
                self.hex_painted.emit(nq, nr, "elevation", item.hx.elevation)
                
        elif self.tool_mode == "Paint Biome":
            for nq, nr in affected_coords:
                item = self.cell_items.get((nq, nr))
                if item:
                    item.hx.biome = self.brush_value
                    item.update_style()
                    self.hex_painted.emit(nq, nr, "biome", self.brush_value)
        elif self.tool_mode == "Paint Religion":
            for nq, nr in affected_coords:
                item = self.cell_items.get((nq, nr))
                if item:
                    item.hx.religion_id = self.brush_value
                    item.update_style()
                    self.hex_painted.emit(nq, nr, "religion_id", self.brush_value)
        elif self.tool_mode == "Paint Culture":
            for nq, nr in affected_coords:
                item = self.cell_items.get((nq, nr))
                if item:
                    item.hx.culture_id = self.brush_value
                    item.update_style()
                    self.hex_painted.emit(nq, nr, "culture_id", self.brush_value)
        elif self.tool_mode == "Paint Province":
            for nq, nr in affected_coords:
                item = self.cell_items.get((nq, nr))
                if item:
                    item.hx.province_id = self.brush_value
                    item.update_style()
                    self.hex_painted.emit(nq, nr, "province_id", self.brush_value)
        elif self.tool_mode == "Paint Faction":
            for nq, nr in affected_coords:
                item = self.cell_items.get((nq, nr))
                if item and item.hx.settlement:
                    item.hx.settlement.faction_id = self.brush_value
                    item.update_style()
                    self.hex_painted.emit(nq, nr, "faction_id", self.brush_value)
        elif self.tool_mode == "Paint Temperature":
            for nq, nr in affected_coords:
                item = self.cell_items.get((nq, nr))
                if item:
                    item.hx.p2 = self.brush_value
                    item.update_style()
                    self.hex_painted.emit(nq, nr, "temp", self.brush_value)
        elif self.tool_mode == "Paint Moisture":
            for nq, nr in affected_coords:
                item = self.cell_items.get((nq, nr))
                if item:
                    item.hx.p3 = self.brush_value
                    item.update_style()
                    self.hex_painted.emit(nq, nr, "moist", self.brush_value)
        elif self.tool_mode == "Paint River Volume":
            for nq, nr in affected_coords:
                item = self.cell_items.get((nq, nr))
                if item:
                    item.hx.river_volume = self.brush_value
                    item.update_style()
                    self.hex_painted.emit(nq, nr, "river_volume", self.brush_value)
        elif self.tool_mode == "Toggle Lake":
            for nq, nr in affected_coords:
                item = self.cell_items.get((nq, nr))
                if item:
                    item.hx.is_lake = bool(self.brush_value)
                    item.update_style()
                    self.hex_painted.emit(nq, nr, "is_lake", self.brush_value)
        elif self.tool_mode == "Paint Chaos":
            for nq, nr in affected_coords:
                item = self.cell_items.get((nq, nr))
                if item:
                    item.hx.chaos_domain = self.brush_str_value if self.brush_str_value != "None" else None
                    item.update_style()
                    self.hex_painted.emit(nq, nr, "chaos_domain_str", 0)
            
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
        if self.is_panning:
            delta = event.pos() - self.pan_last_mouse_pos
            self.pan_last_mouse_pos = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        elif self.is_painting and self.tool_mode.startswith("Paint"):
            scene_pos = self.mapToScene(event.pos())
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
