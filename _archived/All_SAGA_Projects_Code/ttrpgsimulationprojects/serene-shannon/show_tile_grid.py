import os
import sys
import math
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QListWidget, QSpinBox, QCheckBox, QComboBox, QSlider, 
    QScrollArea, QSplitter, QPushButton, QColorDialog, QMessageBox, QFileDialog, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, QRect, pyqtSignal, QPointF
from PyQt6.QtGui import QColor, QPixmap, QPainter, QPen, QFont, QBrush

class GridVisualizerWidget(QWidget):
    cell_clicked = pyqtSignal(int, int)
    box_selected = pyqtSignal(int, int, int, int) # x, y, w, h
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = QPixmap()
        self.grid_w = 32
        self.grid_h = 32
        self.offset_x = 0
        self.offset_y = 0
        self.spacing_x = 0
        self.spacing_y = 0
        self.grid_color = QColor(255, 0, 0)
        self.show_labels = True
        self.show_grid = True
        self.font_size = 8
        self.zoom = 1.0
        
        self.slicing_mode = "grid" # "grid", "manual", "auto_snap"
        self.selected_cell = None
        self.selected_box = None # (x, y, w, h) in original pixels
        
        self.is_dragging = False
        self.drag_start = QPointF()
        self.setMouseTracking(True)
        
    def set_image(self, path):
        self.pixmap = QPixmap(path)
        self.selected_cell = None
        self.selected_box = None
        self.update_geometry()
        self.update()
        
    def update_geometry(self):
        if not self.pixmap.isNull():
            self.setFixedSize(int(self.pixmap.width() * self.zoom), int(self.pixmap.height() * self.zoom))
        else:
            self.setFixedSize(400, 400)
            
    def mousePressEvent(self, event):
        if self.pixmap.isNull():
            return
        
        x = event.position().x()
        y = event.position().y()
        cx = int(x / self.zoom)
        cy = int(y / self.zoom)
        
        if self.slicing_mode == "manual":
            self.is_dragging = True
            self.drag_start = event.position()
            self.selected_box = None
            self.update()
        elif self.slicing_mode == "auto_snap":
            qimg = self.pixmap.toImage()
            box = self.auto_detect_sprite_bounds(qimg, cx, cy)
            if box:
                self.selected_box = box
                self.box_selected.emit(box[0], box[1], box[2], box[3])
                self.update()
        else:
            # Fixed Grid Mode
            zw = self.grid_w * self.zoom
            zh = self.grid_h * self.zoom
            z_off_x = self.offset_x * self.zoom
            z_off_y = self.offset_y * self.zoom
            z_sp_x = self.spacing_x * self.zoom
            z_sp_y = self.spacing_y * self.zoom
            
            x_rel = x - z_off_x
            y_rel = y - z_off_y
            
            if x_rel < 0 or y_rel < 0:
                return
                
            col = int(x_rel // (zw + z_sp_x))
            row = int(y_rel // (zh + z_sp_y))
            
            rem_x = x_rel % (zw + z_sp_x)
            rem_y = y_rel % (zh + z_sp_y)
            
            if rem_x <= zw and rem_y <= zh:
                w = self.pixmap.width()
                h = self.pixmap.height()
                max_col = math.ceil((w - self.offset_x) / (self.grid_w + self.spacing_x)) if w > self.offset_x else 0
                max_row = math.ceil((h - self.offset_y) / (self.grid_h + self.spacing_y)) if h > self.offset_y else 0
                
                if 0 <= col < max_col and 0 <= row < max_row:
                    self.selected_cell = (row, col)
                    self.selected_box = None
                    self.cell_clicked.emit(row, col)
                    self.update()
                    
    def mouseMoveEvent(self, event):
        if self.pixmap.isNull():
            return
        if self.slicing_mode == "manual" and self.is_dragging:
            curr = event.position()
            x1 = min(self.drag_start.x(), curr.x()) / self.zoom
            y1 = min(self.drag_start.y(), curr.y()) / self.zoom
            x2 = max(self.drag_start.x(), curr.x()) / self.zoom
            y2 = max(self.drag_start.y(), curr.y()) / self.zoom
            
            w = self.pixmap.width()
            h = self.pixmap.height()
            
            px = max(0, int(x1))
            py = max(0, int(y1))
            pw = min(w - px, int(x2 - x1))
            ph = min(h - py, int(y2 - y1))
            
            if pw > 0 and ph > 0:
                self.selected_box = (px, py, pw, ph)
                self.box_selected.emit(px, py, pw, ph)
                self.update()
                
    def mouseReleaseEvent(self, event):
        if self.slicing_mode == "manual" and self.is_dragging:
            self.is_dragging = False
            
    def auto_detect_sprite_bounds(self, qimg, start_x, start_y):
        width = qimg.width()
        height = qimg.height()
        if start_x < 0 or start_x >= width or start_y < 0 or start_y >= height:
            return None
            
        bg_pixel = qimg.pixel(0, 0)
        bg_color = QColor(bg_pixel)
        
        def is_bg(x, y):
            p = qimg.pixel(x, y)
            c = QColor(p)
            # Transparent
            if c.alpha() < 15:
                return True
            # Matches top-left pixel with minor threshold tolerance
            if abs(c.red() - bg_color.red()) < 15 and abs(c.green() - bg_color.green()) < 15 and abs(c.blue() - bg_color.blue()) < 15:
                return True
            return False
            
        if is_bg(start_x, start_y):
            return None
            
        visited = set()
        queue = [(start_x, start_y)]
        visited.add((start_x, start_y))
        
        min_x, max_x = start_x, start_x
        min_y, max_y = start_y, start_y
        
        # Limit bounds to 128px radius to keep search efficient
        limit_r = 128
        
        while queue:
            if len(visited) > 8000:
                break
            cx, cy = queue.pop(0)
            
            min_x = min(min_x, cx)
            max_x = max(max_x, cx)
            min_y = min(min_y, cy)
            max_y = max(max_y, cy)
            
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < width and 0 <= ny < height:
                    if abs(nx - start_x) < limit_r and abs(ny - start_y) < limit_r:
                        if (nx, ny) not in visited and not is_bg(nx, ny):
                            visited.add((nx, ny))
                            queue.append((nx, ny))
                            
        w = max_x - min_x + 1
        h = max_y - min_y + 1
        return (min_x, min_y, w, h)

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.pixmap.isNull():
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No Image Loaded")
            return
            
        # Draw base image scaled by zoom
        scaled_rect = QRect(0, 0, int(self.pixmap.width() * self.zoom), int(self.pixmap.height() * self.zoom))
        painter.drawPixmap(scaled_rect, self.pixmap)
        
        # Draw manual box or auto-snap highlight box
        if (self.slicing_mode in ["manual", "auto_snap"]) and self.selected_box is not None:
            x, y, w, h = self.selected_box
            painter.setBrush(QBrush(QColor(0, 102, 204, 90)))
            painter.setPen(QPen(QColor(0, 102, 204), 2))
            painter.drawRect(int(x * self.zoom), int(y * self.zoom), int(w * self.zoom), int(h * self.zoom))
            return
            
        # Calculate fitting cells count
        w = self.pixmap.width()
        h = self.pixmap.height()
        
        cols = 0
        if w > self.offset_x:
            cols = math.ceil((w - self.offset_x) / (self.grid_w + self.spacing_x)) if (self.grid_w + self.spacing_x) > 0 else 0
            
        rows = 0
        if h > self.offset_y:
            rows = math.ceil((h - self.offset_y) / (self.grid_h + self.spacing_y)) if (self.grid_h + self.spacing_y) > 0 else 0
            
        zw = self.grid_w * self.zoom
        zh = self.grid_h * self.zoom
        z_off_x = self.offset_x * self.zoom
        z_off_y = self.offset_y * self.zoom
        z_sp_x = self.spacing_x * self.zoom
        z_sp_y = self.spacing_y * self.zoom
        
        # Draw selected cell highlight
        if self.slicing_mode == "grid" and self.selected_cell is not None:
            r, c = self.selected_cell
            cx = z_off_x + c * (zw + z_sp_x)
            cy = z_off_y + r * (zh + z_sp_y)
            painter.setBrush(QBrush(QColor(0, 255, 0, 80)))
            painter.setPen(QPen(QColor(0, 255, 0), 2))
            painter.drawRect(int(cx), int(cy), int(zw), int(zh))
            
        if self.show_grid and zw > 2 and zh > 2:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(self.grid_color, 1))
            for r in range(rows):
                for c in range(cols):
                    cx = z_off_x + c * (zw + z_sp_x)
                    cy = z_off_y + r * (zh + z_sp_y)
                    painter.drawRect(int(cx), int(cy), int(zw), int(zh))
                    
        # Draw cell coordinates/index labels
        if self.show_labels and zw > 12 and zh > 12:
            painter.setFont(QFont("Arial", self.font_size))
            for r in range(rows):
                for c in range(cols):
                    cx = z_off_x + c * (zw + z_sp_x)
                    cy = z_off_y + r * (zh + z_sp_y)
                    label = f"{r},{c}"
                    # Shadow background for text readability
                    painter.setPen(QColor(0, 0, 0))
                    painter.drawText(int(cx + 3), int(cy + self.font_size + 3), label)
                    painter.setPen(QColor(255, 255, 255))
                    painter.drawText(int(cx + 2), int(cy + self.font_size + 2), label)

class TileGridVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tile Grid Visualizer & Interactive Slicer")
        self.setMinimumSize(1100, 750)
        
        self.texture_dir = r"c:\Users\krazy\Desktop\ostraka-wiki\public\textures"
        self.settings_cache = {}
        self.active_filename = None
        
        # Main Layout split
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(main_splitter)
        
        # Left Panel: File list & Open actions
        left_widget = QWidget()
        left_lay = QVBoxLayout(left_widget)
        
        self.btn_open_sheet = QPushButton("Open OG Sheet...")
        self.btn_open_sheet.setStyleSheet("background-color: #8B5CF6; color: white; font-weight: bold; padding: 6px;")
        self.btn_open_sheet.clicked.connect(self.open_og_sheet)
        left_lay.addWidget(self.btn_open_sheet)
        
        left_lay.addWidget(QLabel("<b>Rendered Tile Sheets</b>"))
        self.file_list = QListWidget()
        self.file_list.currentTextChanged.connect(self.load_selected_asset)
        left_lay.addWidget(self.file_list)
        main_splitter.addWidget(left_widget)
        
        # Center Panel: Scroll area for visualizer
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.visualizer = GridVisualizerWidget()
        self.visualizer.cell_clicked.connect(self.on_cell_clicked)
        self.visualizer.box_selected.connect(self.on_box_selected)
        scroll.setWidget(self.visualizer)
        main_splitter.addWidget(scroll)
        
        # Right Panel: Control Dashboard
        right_widget = QWidget()
        right_lay = QVBoxLayout(right_widget)
        right_lay.setContentsMargins(10, 10, 10, 10)
        
        right_lay.addWidget(QLabel("<b>Slicing Mode</b>"))
        self.grp_mode = QButtonGroup(self)
        
        self.rad_grid = QRadioButton("Fixed Grid Cells")
        self.rad_grid.setChecked(True)
        self.rad_grid.toggled.connect(self.on_mode_changed)
        
        self.rad_manual = QRadioButton("Manual Drag Box Crop")
        self.rad_manual.toggled.connect(self.on_mode_changed)
        
        self.rad_auto = QRadioButton("Auto-Snap Sprite (Magic Wand)")
        self.rad_auto.toggled.connect(self.on_mode_changed)
        
        self.grp_mode.addButton(self.rad_grid)
        self.grp_mode.addButton(self.rad_manual)
        self.grp_mode.addButton(self.rad_auto)
        
        right_lay.addWidget(self.rad_grid)
        right_lay.addWidget(self.rad_manual)
        right_lay.addWidget(self.rad_auto)
        
        self.lbl_grid_title = QLabel("<b>Grid Alignment Dashboard</b>")
        right_lay.addWidget(self.lbl_grid_title)
        
        # Grid dimensions
        self.container_grid_settings = QWidget()
        grid_sett_lay = QVBoxLayout(self.container_grid_settings)
        grid_sett_lay.setContentsMargins(0, 0, 0, 0)
        
        dim_lay = QHBoxLayout()
        dim_lay.addWidget(QLabel("Width (px):"))
        self.spin_w = QSpinBox()
        self.spin_w.setRange(2, 512)
        self.spin_w.setValue(32)
        self.spin_w.valueChanged.connect(self.update_grid_settings)
        dim_lay.addWidget(self.spin_w)
        grid_sett_lay.addLayout(dim_lay)
        
        dim_lay2 = QHBoxLayout()
        dim_lay2.addWidget(QLabel("Height (px):"))
        self.spin_h = QSpinBox()
        self.spin_h.setRange(2, 512)
        self.spin_h.setValue(32)
        self.spin_h.valueChanged.connect(self.update_grid_settings)
        dim_lay2.addWidget(self.spin_h)
        grid_sett_lay.addLayout(dim_lay2)
        
        # Grid Offsets (X & Y margins)
        off_lay = QHBoxLayout()
        off_lay.addWidget(QLabel("Offset X (px):"))
        self.spin_off_x = QSpinBox()
        self.spin_off_x.setRange(0, 512)
        self.spin_off_x.setValue(0)
        self.spin_off_x.valueChanged.connect(self.update_grid_settings)
        off_lay.addWidget(self.spin_off_x)
        grid_sett_lay.addLayout(off_lay)
        
        off_lay2 = QHBoxLayout()
        off_lay2.addWidget(QLabel("Offset Y (px):"))
        self.spin_off_y = QSpinBox()
        self.spin_off_y.setRange(0, 512)
        self.spin_off_y.setValue(0)
        self.spin_off_y.valueChanged.connect(self.update_grid_settings)
        off_lay2.addWidget(self.spin_off_y)
        grid_sett_lay.addLayout(off_lay2)
        
        # Grid Spacing (Padding between tiles)
        sp_lay = QHBoxLayout()
        sp_lay.addWidget(QLabel("Spacing X (px):"))
        self.spin_sp_x = QSpinBox()
        self.spin_sp_x.setRange(0, 512)
        self.spin_sp_x.setValue(0)
        self.spin_sp_x.valueChanged.connect(self.update_grid_settings)
        sp_lay.addWidget(self.spin_sp_x)
        grid_sett_lay.addLayout(sp_lay)
        
        sp_lay2 = QHBoxLayout()
        sp_lay2.addWidget(QLabel("Spacing Y (px):"))
        self.spin_sp_y = QSpinBox()
        self.spin_sp_y.setRange(0, 512)
        self.spin_sp_y.setValue(0)
        self.spin_sp_y.valueChanged.connect(self.update_grid_settings)
        sp_lay2.addWidget(self.spin_sp_y)
        grid_sett_lay.addLayout(sp_lay2)
        
        right_lay.addWidget(self.container_grid_settings)
        
        # Zoom Controls
        zoom_lay = QHBoxLayout()
        zoom_lay.addWidget(QLabel("Zoom:"))
        self.slider_zoom = QSlider(Qt.Orientation.Horizontal)
        self.slider_zoom.setRange(10, 400)
        self.slider_zoom.setValue(100)
        self.slider_zoom.valueChanged.connect(self.update_grid_settings)
        zoom_lay.addWidget(self.slider_zoom)
        right_lay.addLayout(zoom_lay)
        
        # Colors
        col_lay = QHBoxLayout()
        col_lay.addWidget(QLabel("Grid Color:"))
        self.btn_color = QPushButton("Choose Color")
        self.btn_color.clicked.connect(self.choose_color)
        col_lay.addWidget(self.btn_color)
        right_lay.addLayout(col_lay)
        
        # Font size
        font_lay = QHBoxLayout()
        font_lay.addWidget(QLabel("Label Font Size:"))
        self.spin_font = QSpinBox()
        self.spin_font.setRange(4, 32)
        self.spin_font.setValue(8)
        self.spin_font.valueChanged.connect(self.update_grid_settings)
        font_lay.addWidget(self.spin_font)
        right_lay.addLayout(font_lay)
        
        # Checkboxes
        self.chk_grid = QCheckBox("Show Grid Lines")
        self.chk_grid.setChecked(True)
        self.chk_grid.stateChanged.connect(self.update_grid_settings)
        right_lay.addWidget(self.chk_grid)
        
        self.chk_labels = QCheckBox("Show Coordinate Labels")
        self.chk_labels.setChecked(True)
        self.chk_labels.stateChanged.connect(self.update_grid_settings)
        right_lay.addWidget(self.chk_labels)
        
        # --- Interactive Slicing Panel ---
        right_lay.addWidget(QLabel("<b><br>Interactive Crop & Slicer</b>"))
        
        self.lbl_selection = QLabel("Selected: None")
        self.lbl_selection.setStyleSheet("color: #6366F1; font-weight: bold;")
        right_lay.addWidget(self.lbl_selection)
        
        right_lay.addWidget(QLabel("Save Crop As Category:"))
        
        self.target_map = {
            "plains_tile.png (Plains Biome)": "plains_tile.png",
            "mountain_tile.png (Mountain Biome)": "mountain_tile.png",
            "taiga_tile.png (Taiga Biome)": "taiga_tile.png",
            "desert_tile.png (Desert Biome)": "desert_tile.png",
            "jungle_tile.png (Jungle Biome)": "jungle_tile.png",
            "tundra_tile.png (Tundra Biome)": "tundra_tile.png",
            "volcano_tile.png (Volcano Biome)": "volcano_tile.png",
            "ocean_tile.png (Ocean Biome)": "ocean_tile.png",
            "arctic_tile.png (Arctic Biome)": "arctic_tile.png",
            "town_icon.png (Town Icon)": "town_icon.png",
            "keep_icon.png (Keep Icon)": "keep_icon.png",
            "ruins_icon.png (Ruins Icon)": "ruins_icon.png",
            "cave_icon.png (Cave Icon)": "cave_icon.png",
            "dungeon_icon.png (Dungeon Icon)": "dungeon_icon.png",
            "caravan_icon.png (Caravan Icon)": "caravan_icon.png",
            "ship_icon.png (Ship Icon)": "ship_icon.png"
        }
        self.cb_target_type = QComboBox()
        self.cb_target_type.addItems(list(self.target_map.keys()))
        right_lay.addWidget(self.cb_target_type)
        
        self.btn_slice = QPushButton("Slice & Save Asset")
        self.btn_slice.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; padding: 6px;")
        self.btn_slice.clicked.connect(self.slice_and_save)
        right_lay.addWidget(self.btn_slice)
        
        right_lay.addStretch()
        main_splitter.addWidget(right_widget)
        
        main_splitter.setSizes([200, 650, 250])
        
        self.populate_file_list()
        
    def populate_file_list(self):
        self.file_list.clear()
        if os.path.exists(self.texture_dir):
            files = sorted([f for f in os.listdir(self.texture_dir) if f.endswith((".png", ".jpg", ".jpeg", ".webp"))])
            self.file_list.addItems(files)
            
    def cache_current_settings(self):
        if self.active_filename:
            self.settings_cache[self.active_filename] = {
                "grid_w": self.spin_w.value(),
                "grid_h": self.spin_h.value(),
                "offset_x": self.spin_off_x.value(),
                "offset_y": self.spin_off_y.value(),
                "spacing_x": self.spin_sp_x.value(),
                "spacing_y": self.spin_sp_y.value(),
                "zoom": self.slider_zoom.value(),
                "slicing_mode": "manual" if self.rad_manual.isChecked() else ("auto_snap" if self.rad_auto.isChecked() else "grid")
            }
            
    def load_cached_settings(self, filename):
        self.active_filename = filename
        if filename in self.settings_cache:
            cache = self.settings_cache[filename]
            self.spin_w.setValue(cache["grid_w"])
            self.spin_h.setValue(cache["grid_h"])
            self.spin_off_x.setValue(cache["offset_x"])
            self.spin_off_y.setValue(cache["offset_y"])
            self.spin_sp_x.setValue(cache["spacing_x"])
            self.spin_sp_y.setValue(cache["spacing_y"])
            self.slider_zoom.setValue(cache["zoom"])
            m = cache["slicing_mode"]
            if m == "manual":
                self.rad_manual.setChecked(True)
            elif m == "auto_snap":
                self.rad_auto.setChecked(True)
            else:
                self.rad_grid.setChecked(True)
        else:
            self.spin_w.setValue(32)
            self.spin_h.setValue(32)
            self.spin_off_x.setValue(0)
            self.spin_off_y.setValue(0)
            self.spin_sp_x.setValue(0)
            self.spin_sp_y.setValue(0)
            self.slider_zoom.setValue(100)
            self.rad_grid.setChecked(True)
            
    def load_selected_asset(self, filename):
        if not filename:
            return
        self.cache_current_settings()
        self.load_cached_settings(filename)
        
        path = os.path.join(self.texture_dir, filename)
        self.visualizer.set_image(path)
        self.lbl_selection.setText("Selected: None")
        
    def open_og_sheet(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Original Image Sheet", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if file_path:
            self.cache_current_settings()
            name = os.path.basename(file_path)
            self.load_cached_settings(name)
            
            self.visualizer.set_image(file_path)
            self.lbl_selection.setText("Selected: None")
            self.statusBar().showMessage(f"Loaded sheet: {name}")
            
    def on_mode_changed(self):
        if self.rad_manual.isChecked():
            mode = "manual"
        elif self.rad_auto.isChecked():
            mode = "auto_snap"
        else:
            mode = "grid"
            
        self.visualizer.slicing_mode = mode
        show_grid_dashboard = (mode == "grid")
        self.container_grid_settings.setVisible(show_grid_dashboard)
        self.lbl_grid_title.setVisible(show_grid_dashboard)
        
        self.visualizer.selected_cell = None
        self.visualizer.selected_box = None
        self.lbl_selection.setText("Selected: None")
        self.visualizer.update()
        
    def on_cell_clicked(self, row, col):
        self.lbl_selection.setText(f"Selected Cell: Row {row}, Col {col}")
        
    def on_box_selected(self, x, y, w, h):
        self.lbl_selection.setText(f"Selected Box: X:{x}, Y:{y}, W:{w}, H:{h}")
        
    def slice_and_save(self):
        if self.visualizer.pixmap.isNull():
            QMessageBox.warning(self, "No Image Loaded", "Please load an image sheet first.")
            return
            
        mode = self.visualizer.slicing_mode
        if mode in ["manual", "auto_snap"]:
            box = self.visualizer.selected_box
            if box is None:
                QMessageBox.warning(self, "No Selection", "Please select a custom boundary box or click on a sprite to auto-detect its bounds.")
                return
            x, y, gw, gh = box
        else:
            cell = self.visualizer.selected_cell
            if cell is None:
                QMessageBox.warning(self, "No Selection", "Please click on a grid cell to select the tile you want to cut.")
                return
            row, col = cell
            gw = self.visualizer.grid_w
            gh = self.visualizer.grid_h
            
            # Calculate coordinates
            x = self.visualizer.offset_x + col * (gw + self.visualizer.spacing_x)
            y = self.visualizer.offset_y + row * (gh + self.visualizer.spacing_y)
            
        # Validate crop limits
        if x + gw > self.visualizer.pixmap.width() or y + gh > self.visualizer.pixmap.height() or gw <= 0 or gh <= 0:
            QMessageBox.critical(self, "Boundary Error", "The crop area lies outside the original sheet size dimensions.")
            return
            
        cropped = self.visualizer.pixmap.copy(x, y, gw, gh)
        
        # Get target filename
        display_key = self.cb_target_type.currentText()
        target_name = self.target_map.get(display_key)
        if not target_name:
            return
            
        target_path = os.path.join(self.texture_dir, target_name)
        os.makedirs(self.texture_dir, exist_ok=True)
        
        try:
            success = cropped.save(target_path, "PNG")
            if success:
                QMessageBox.information(self, "Crop Saved", f"Successfully saved crop area to:\n{target_path}")
                self.populate_file_list()
            else:
                QMessageBox.critical(self, "Save Error", "Failed to save cropped image.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to crop and save asset: {e}")
            
    def update_grid_settings(self):
        self.visualizer.grid_w = self.spin_w.value()
        self.visualizer.grid_h = self.spin_h.value()
        self.visualizer.offset_x = self.spin_off_x.value()
        self.visualizer.offset_y = self.spin_off_y.value()
        self.visualizer.spacing_x = self.spin_sp_x.value()
        self.visualizer.spacing_y = self.spin_sp_y.value()
        self.visualizer.zoom = self.slider_zoom.value() / 100.0
        self.visualizer.font_size = self.spin_font.value()
        self.visualizer.show_grid = self.chk_grid.isChecked()
        self.visualizer.show_labels = self.chk_labels.isChecked()
        self.visualizer.update_geometry()
        self.visualizer.update()
        
    def choose_color(self):
        color = QColorDialog.getColor(self.visualizer.grid_color, self, "Select Grid Line Color")
        if color.isValid():
            self.visualizer.grid_color = color
            self.visualizer.update()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TileGridVisualizer()
    window.show()
    sys.exit(app.exec())
