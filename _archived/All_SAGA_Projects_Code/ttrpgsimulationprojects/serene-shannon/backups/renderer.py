# python_fmg/renderers/renderer.py
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPolygonItem, QGraphicsEllipseItem
from PyQt6.QtGui import QPolygonF, QPen, QBrush, QColor, QPainter, QTransform
from PyQt6.QtCore import pyqtSignal, QPointF, Qt
import math
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

class HexCellItem(QGraphicsPolygonItem):
    def __init__(self, q, r, hx, size=12.0):
        super().__init__()
        self.q = q
        self.r = r
        self.hx = hx
        self.size = size
        
        # Calculate polygon points for flat-topped hex
        points = []
        for i in range(6):
            angle_rad = math.pi / 3 * i
            px = size * math.cos(angle_rad)
            py = size * math.sin(angle_rad)
            points.append(QPointF(px, py))
            
        poly = QPolygonF(points)
        self.setPolygon(poly)
        
        # Position cell
        x, y = hex_to_pixel(q, r, size)
        self.setPos(x, y)
        self.update_style()
        
    def update_style(self):
        color = BIOME_COLORS.get(self.hx.biome, QColor("#333333"))
        
        # If settlement exists, give a slightly different border or indicator
        if self.hx.settlement:
            pen = QPen(QColor("#FF00FF"), 1.5)  # Magenta border for settlements
        elif self.hx.chaos_domain:
            pen = QPen(QColor("#FF3333"), 1.5)  # Red border for Chaos Domains
        else:
            pen = QPen(QColor("#1A1A1A"), 0.5)  # Subtle dark border
            
        self.setPen(pen)
        self.setBrush(QBrush(color))

class WorldMapViewer(QGraphicsView):
    hex_selected = pyqtSignal(int, int) # coordinates q, r
    
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
        
        # Background color
        self.setBackgroundBrush(QBrush(QColor("#08080C")))
        
    def load_map(self, state):
        self.scene.clear()
        self.cell_items.clear()
        self.selected_item = None
        
        for (q, r), hx in state.hexes.items():
            item = HexCellItem(q, r, hx, self.cell_size)
            self.scene.addItem(item)
            self.cell_items[(q, r)] = item
            
            # If settlement exists, draw a small symbol
            if hx.settlement:
                sett_marker = QGraphicsEllipseItem(-3, -3, 6, 6, item)
                sett_marker.setBrush(QBrush(QColor("#FF00FF")))
                sett_marker.setPen(QPen(Qt.PenStyle.NoPen))
                
        # Fit in view initially
        self.scene.setSceneRect(self.scene.itemsBoundingRect())
        self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        
    def select_hex(self, q, r):
        # Deselect old
        if self.selected_item:
            self.selected_item.update_style()
            
        item = self.cell_items.get((q, r))
        if item:
            self.selected_item = item
            # Highlight selected item with a bright golden/white border
            item.setPen(QPen(QColor("#F1C40F"), 2.5))
            
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Map viewport pixel coordinates to scene coordinates
            scene_pos = self.mapToScene(event.pos())
            # Find matching hex axial coordinate
            q, r = pixel_to_hex(scene_pos.x(), scene_pos.y(), self.cell_size)
            
            if (q, r) in self.cell_items:
                self.select_hex(q, r)
                self.hex_selected.emit(q, r)
                
        super().mousePressEvent(event)

    def wheelEvent(self, event):
        zoom_factor = 1.25
        if event.angleDelta().y() < 0:
            zoom_factor = 1.0 / zoom_factor
            
        self.scale(zoom_factor, zoom_factor)
