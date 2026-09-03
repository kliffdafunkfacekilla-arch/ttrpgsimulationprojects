# python_fmg/ui/main_window.py
import sys
import os
import json
import math
import random
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
    QLabel, QComboBox, QSlider, QCheckBox, QLineEdit, QGroupBox, 
    QFormLayout, QMessageBox, QFileDialog, QInputDialog, QListWidget, QListWidgetItem,
    QRadioButton, QButtonGroup, QSpinBox, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QDoubleSpinBox, QTextEdit,
    QDockWidget, QStackedWidget, QScrollArea, QToolBar, QDialog
)
from PyQt6.QtCore import Qt, QSize, QPoint
from PyQt6.QtGui import QColor, QPalette, QPainter, QPolygon, QPen, QBrush, QPixmap, QIcon

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from python_fmg.core.models import MapState, GlobalHex, Settlement, Faction, Paragon, WorldEntity, TradeRoute, Religion, Culture, Province, Marker
from python_fmg.core.generators import generate_world
from python_fmg.core.db_sync import load_from_db, save_to_db
from python_fmg.core.converter import convert_azgaar_to_hex_grid
from python_fmg.renderers.renderer import WorldMapViewer

BIOME_NAMES = {
    0: "Jungle",
    1: "Forest",
    2: "Taiga",
    3: "Desert",
    4: "Plains",
    5: "Tundra",
    6: "Mountain",
    7: "Volcano",
    8: "Arctic",
    9: "Kelp Forest (Ocean)",
    10: "Coral Reef (Ocean)",
    11: "Arctic Ocean (Ocean)",
    12: "Abyssal Trench (Ocean)",
    13: "Prison Wastes"
}

BIOME_COLORS_HEX = {
    0: "#2E8B57", 1: "#228B22", 2: "#4682B4", 3: "#E6C229", 4: "#98FB98",
    5: "#B0C4DE", 6: "#708090", 7: "#D35400", 8: "#F0F8FF", 9: "#1F3A52",
    10: "#1D8A99", 11: "#10253C", 12: "#0A1128", 13: "#3D0C5A"
}

FACTION_COLORS_HEX = [
    "#3498DB", "#E74C3C", "#2ECC71", "#F1C40F", "#9B59B6", "#1ABC9C", "#E67E22",
    "#34495E", "#D35400", "#27AE60", "#2980B9", "#8E44AD", "#C0392B", "#16A085"
]

CHAOS_DOMAINS = ["None", "WARP_STORM", "CULT_INSURGENCY", "LUX_ECLIPSE", "NEXUS_BREACH"]
CHAOS_COLORS_HEX = {
    "None": "#333333",
    "WARP_STORM": "#9b59b6",
    "CULT_INSURGENCY": "#e74c3c",
    "LUX_ECLIPSE": "#34495e",
    "NEXUS_BREACH": "#e67e22"
}

COA_TINCTURES = {
    "Or": QColor("#F1C40F"),      # Gold/Yellow
    "Argent": QColor("#ECEFF1"),  # Silver/White
    "Gules": QColor("#E74C3C"),   # Red
    "Azure": QColor("#2980B9"),   # Blue
    "Vert": QColor("#27AE60"),    # Green
    "Purpure": QColor("#9B59B6"), # Purple
    "Sable": QColor("#2C3E50")    # Black
}

COA_DIVISIONS = ["Plain", "Per Pale (Split Left/Right)", "Per Fess (Split Top/Bottom)", "Quarterly"]
COA_CHARGES = ["None", "Cross", "Star", "Roundel (Circle)"]

def create_color_icon(color):
    pixmap = QPixmap(16, 16)
    if isinstance(color, str):
        pixmap.fill(QColor(color))
    else:
        pixmap.fill(color)
    return QIcon(pixmap)

class CoatOfArmsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(100, 120)
        self.setMaximumSize(150, 180)
        self.coa_data = {"division": "Plain", "color1": "Or", "color2": "Azure", "charge": "None", "charge_color": "Argent"}
        
    def set_coa(self, coa_json_str):
        try:
            self.coa_data = json.loads(coa_json_str)
        except Exception:
            self.coa_data = {"division": "Plain", "color1": "Or", "color2": "Azure", "charge": "None", "charge_color": "Argent"}
        self.update()
        
    def get_coa_json(self):
        return json.dumps(self.coa_data)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        
        shield = QPolygon([
            QPoint(10, 10),
            QPoint(w - 10, 10),
            QPoint(w - 10, int(h * 0.6)),
            QPoint(int(w / 2), h - 10),
            QPoint(10, int(h * 0.6))
        ])
        
        c1 = COA_TINCTURES.get(self.coa_data.get("color1", "Or"), QColor("#F1C40F"))
        c2 = COA_TINCTURES.get(self.coa_data.get("color2", "Azure"), QColor("#2980B9"))
        cg_color = COA_TINCTURES.get(self.coa_data.get("charge_color", "Argent"), QColor("#FFFFFF"))
        division = self.coa_data.get("division", "Plain")
        charge = self.coa_data.get("charge", "None")
        
        painter.setClipPolygon(shield)
        
        if division == "Plain":
            painter.fillRect(self.rect(), c1)
        elif division == "Per Pale (Split Left/Right)":
            painter.fillRect(0, 0, int(w/2), h, c1)
            painter.fillRect(int(w/2), 0, int(w/2), h, c2)
        elif division == "Per Fess (Split Top/Bottom)":
            painter.fillRect(0, 0, w, int(h/2), c1)
            painter.fillRect(0, int(h/2), w, int(h/2), c2)
        elif division == "Quarterly":
            painter.fillRect(0, 0, int(w/2), int(h/2), c1)
            painter.fillRect(int(w/2), 0, int(w/2), int(h/2), c2)
            painter.fillRect(0, int(h/2), int(w/2), int(h/2), c2)
            painter.fillRect(int(w/2), int(h/2), int(w/2), int(h/2), c1)
            
        cx, cy = int(w/2), int(h/2)
        painter.setBrush(QBrush(cg_color))
        painter.setPen(QPen(QColor("#1A1A1A"), 1))
        
        if charge == "Cross":
            painter.drawRect(cx - 8, 20, 16, h - 40)
            painter.drawRect(20, cy - 8, w - 40, 16)
        elif charge == "Star":
            points = []
            for i in range(10):
                angle = i * math.pi / 5 - math.pi / 2
                r = 20 if i % 2 == 0 else 8
                points.append(QPoint(cx + int(r * math.cos(angle)), cy + int(r * math.sin(angle))))
            painter.drawPolygon(QPolygon(points))
        elif charge == "Roundel (Circle)":
            painter.drawEllipse(cx - 15, cy - 15, 30, 30)
            
        painter.setClipping(False)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor("#FFFFFF"), 3))
        painter.drawPolygon(shield)

# ----------------------------------------------------
# Base Floating Tool Window Dialog Class
# ----------------------------------------------------
class FloatingEditorDialog(QDialog):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.resize(360, 480)
        self.setStyleSheet("""
            QDialog {
                background-color: #16161a;
                border: 2px solid #202024;
                border-radius: 8px;
            }
            QWidget {
                color: #E1E1E6;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox {
                border: 1px solid #29292E;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                background-color: #1c1c21;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 5px 0 5px;
                color: #04D361;
            }
            QPushButton {
                background-color: #202024;
                border: 1px solid #29292E;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #29292E;
                border-color: #04D361;
            }
            QComboBox, QLineEdit, QSlider, QSpinBox, QDoubleSpinBox, QListWidget, QTableWidget, QTextEdit {
                background-color: #121214;
                border: 1px solid #29292E;
                border-radius: 4px;
                padding: 4px;
            }
            QComboBox:focus, QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
                border-color: #04D361;
            }
        """)
        self.btn_paint = None

    def uncheck_paint_button(self):
        if self.btn_paint:
            self.btn_paint.blockSignals(True)
            self.btn_paint.setChecked(False)
            self.btn_paint.setStyleSheet("")
            self.btn_paint.blockSignals(False)

    def add_save_load_buttons(self, layout, parent, save_method, load_method):
        btn_layout = QHBoxLayout()
        btn_load = QPushButton("📥 Load State")
        btn_load.clicked.connect(load_method)
        btn_save = QPushButton("💾 Save State")
        btn_save.clicked.connect(save_method)
        btn_layout.addWidget(btn_load)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

# ----------------------------------------------------
# Floating Dialog Subclasses for Individual Editors
# ----------------------------------------------------
# ----------------------------------------------------
# Floating Dialog Subclasses for Individual Editors
# ----------------------------------------------------
class ElevationEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Heightmap (Elevation)", parent)
        layout = QVBoxLayout(self)
        
        self.lbl_radius = QLabel(f"Brush Radius: {parent.brush_radius_val}")
        self.slider_radius = QSlider(Qt.Orientation.Horizontal)
        self.slider_radius.setRange(1, 10)
        self.slider_radius.setValue(parent.brush_radius_val)
        self.slider_radius.valueChanged.connect(parent.on_brush_radius_changed)
        self.slider_radius.valueChanged.connect(lambda v: self.lbl_radius.setText(f"Brush Radius: {v}"))
        
        self.cb_mode = QComboBox()
        self.cb_mode.addItems(["Align", "Raise", "Lower", "Smooth", "Disrupt"])
        self.cb_mode.setCurrentText(parent.map_viewer.elevation_brush_mode)
        self.cb_mode.currentTextChanged.connect(parent.on_elevation_mode_changed)
        
        self.lbl_power = QLabel(f"Brush Power: {parent.map_viewer.brush_power}")
        self.slider_power = QSlider(Qt.Orientation.Horizontal)
        self.slider_power.setRange(1, 10)
        self.slider_power.setValue(parent.map_viewer.brush_power)
        self.slider_power.valueChanged.connect(parent.on_brush_power_changed)
        self.slider_power.valueChanged.connect(lambda v: self.lbl_power.setText(f"Brush Power: {v}"))
        
        self.btn_paint = QPushButton("🎨 Enable Elevation Brush")
        self.btn_paint.setCheckable(True)
        self.btn_paint.toggled.connect(parent.on_brush_toggled)

        layout.addWidget(self.lbl_radius)
        layout.addWidget(self.slider_radius)
        layout.addWidget(QLabel("Brush Mode:"))
        layout.addWidget(self.cb_mode)
        layout.addWidget(self.lbl_power)
        layout.addWidget(self.slider_power)
        layout.addWidget(QLabel("Elevation Align Value (0-15):"))
        layout.addWidget(parent.spin_elev_brush)
        layout.addWidget(self.btn_paint)
        
        self.btn_import_image = QPushButton("🖼️ Import Heightmap Image")
        self.btn_import_image.clicked.connect(parent.import_heightmap_image)
        layout.addWidget(self.btn_import_image)
        
        self.add_save_load_buttons(layout, parent, parent.save_elevation_layer, parent.load_elevation_layer)
        layout.addStretch()

class BiomesEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Biomes Editor", parent)
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll_layout = QVBoxLayout(content)
        
        self.lbl_radius = QLabel(f"Brush Radius: {parent.brush_radius_val}")
        self.slider_radius = QSlider(Qt.Orientation.Horizontal)
        self.slider_radius.setRange(1, 10)
        self.slider_radius.setValue(parent.brush_radius_val)
        self.slider_radius.valueChanged.connect(parent.on_brush_radius_changed)
        self.slider_radius.valueChanged.connect(lambda v: self.lbl_radius.setText(f"Brush Radius: {v}"))
        
        self.btn_paint = QPushButton("🎨 Enable Biome Brush")
        self.btn_paint.setCheckable(True)
        self.btn_paint.toggled.connect(parent.on_brush_toggled)
        
        list_group = QGroupBox("Biomes List (Click row to select active paint material)")
        list_layout = QVBoxLayout(list_group)
        self.biome_list_brush = QListWidget()
        self.biome_list_brush.currentRowChanged.connect(parent.on_biome_list_selection)
        list_layout.addWidget(self.biome_list_brush)
        
        self.btn_add_biome = QPushButton("➕ Add Custom Biome")
        self.btn_add_biome.clicked.connect(parent.add_new_biome)
        list_layout.addWidget(self.btn_add_biome)
        
        details_group = QGroupBox("Biome Settings")
        details_form = QFormLayout(details_group)
        
        self.txt_biome_name = QLineEdit()
        self.txt_biome_name.textChanged.connect(parent.on_biome_details_changed)
        details_form.addRow("Name:", self.txt_biome_name)
        
        self.btn_biome_color = QPushButton()
        self.btn_biome_color.setMinimumHeight(24)
        self.btn_biome_color.clicked.connect(parent.choose_biome_color)
        details_form.addRow("Color:", self.btn_biome_color)
        
        self.spin_biome_habitability = QSpinBox()
        self.spin_biome_habitability.setRange(0, 100)
        self.spin_biome_habitability.setSuffix("%")
        self.spin_biome_habitability.valueChanged.connect(parent.on_biome_details_changed)
        details_form.addRow("Habitability:", self.spin_biome_habitability)
        
        self.spin_biome_move_cost = QDoubleSpinBox()
        self.spin_biome_move_cost.setRange(1.0, 10.0)
        self.spin_biome_move_cost.setSingleStep(0.5)
        self.spin_biome_move_cost.setValue(2.0)
        self.spin_biome_move_cost.valueChanged.connect(parent.on_biome_details_changed)
        details_form.addRow("Move Cost:", self.spin_biome_move_cost)
        
        scroll_layout.addWidget(self.lbl_radius)
        scroll_layout.addWidget(self.slider_radius)
        scroll_layout.addWidget(self.btn_paint)
        scroll_layout.addWidget(list_group)
        scroll_layout.addWidget(details_group)
        
        self.add_save_load_buttons(scroll_layout, parent, parent.save_biomes_layer, parent.load_biomes_layer)
        
        content.setLayout(scroll_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)

class FactionsEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Factions & States Editor", parent)
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll_layout = QVBoxLayout(content)

        self.lbl_radius = QLabel(f"Brush Radius: {parent.brush_radius_val}")
        self.slider_radius = QSlider(Qt.Orientation.Horizontal)
        self.slider_radius.setRange(1, 10)
        self.slider_radius.setValue(parent.brush_radius_val)
        self.slider_radius.valueChanged.connect(parent.on_brush_radius_changed)
        self.slider_radius.valueChanged.connect(lambda v: self.lbl_radius.setText(f"Brush Radius: {v}"))

        self.btn_paint = QPushButton("🎨 Paint Faction Territory")
        self.btn_paint.setCheckable(True)
        self.btn_paint.toggled.connect(parent.on_brush_toggled)

        list_group = QGroupBox("Factions List")
        list_layout = QVBoxLayout(list_group)
        list_layout.addWidget(parent.faction_list)
        list_layout.addWidget(parent.btn_add_fac)

        details_group = QGroupBox("Faction Attributes")
        details_form = QFormLayout(details_group)
        details_form.addRow("Faction Name:", parent.txt_fac_name)
        details_form.addRow("Treasury:", parent.txt_fac_treasury)
        details_form.addRow("Tech Level:", parent.spin_fac_tech)
        details_form.addRow("Bonus / Trait:", parent.txt_fac_rule)
        
        # Aggression and Trade Level sliders
        self.slider_aggression = QSlider(Qt.Orientation.Horizontal)
        self.slider_aggression.setRange(0, 10)
        self.slider_aggression.valueChanged.connect(parent.on_faction_details_changed)
        details_form.addRow("Aggression Level:", self.slider_aggression)

        self.slider_trade = QSlider(Qt.Orientation.Horizontal)
        self.slider_trade.setRange(0, 10)
        self.slider_trade.valueChanged.connect(parent.on_faction_details_changed)
        details_form.addRow("Trade Level:", self.slider_trade)

        # Species Population makeup
        pop_group = QGroupBox("Species Makeup (%)")
        pop_layout = QVBoxLayout(pop_group)
        self.species_list = QListWidget()
        pop_layout.addWidget(self.species_list)
        
        spec_btn_layout = QHBoxLayout()
        self.btn_add_spec = QPushButton("➕ Add Species")
        self.btn_add_spec.clicked.connect(parent.add_faction_species)
        self.btn_del_spec = QPushButton("➖ Remove Species")
        self.btn_del_spec.clicked.connect(parent.remove_faction_species)
        spec_btn_layout.addWidget(self.btn_add_spec)
        spec_btn_layout.addWidget(self.btn_del_spec)
        pop_layout.addLayout(spec_btn_layout)

        # Sparkborn Attunements
        att_group = QGroupBox("Sparkborn Attunements")
        att_layout = QVBoxLayout(att_group)
        self.att_list = QListWidget()
        for att in ["Fire", "Water", "Earth", "Air", "Void", "Lightning", "Aether", "Chaos"]:
            item = QListWidgetItem(att)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.att_list.addItem(item)
        self.att_list.itemChanged.connect(parent.on_faction_attunement_changed)
        att_layout.addWidget(self.att_list)

        scroll_layout.addWidget(self.lbl_radius)
        scroll_layout.addWidget(self.slider_radius)
        scroll_layout.addWidget(self.btn_paint)
        scroll_layout.addWidget(list_group)
        scroll_layout.addWidget(details_group)
        scroll_layout.addWidget(pop_group)
        scroll_layout.addWidget(att_group)
        
        self.add_save_load_buttons(scroll_layout, parent, parent.save_factions_layer, parent.load_factions_layer)
        
        content.setLayout(scroll_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)

class ParagonsEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Paragons & Influence Editor", parent)
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll_layout = QVBoxLayout(content)

        self.lbl_radius = QLabel(f"Brush Radius: {parent.brush_radius_val}")
        self.slider_radius = QSlider(Qt.Orientation.Horizontal)
        self.slider_radius.setRange(1, 10)
        self.slider_radius.setValue(parent.brush_radius_val)
        self.slider_radius.valueChanged.connect(parent.on_brush_radius_changed)
        self.slider_radius.valueChanged.connect(lambda v: self.lbl_radius.setText(f"Brush Radius: {v}"))

        self.btn_paint = QPushButton("🎨 Paint Paragon Influence Zone")
        self.btn_paint.setCheckable(True)
        self.btn_paint.toggled.connect(parent.on_brush_toggled)

        list_group = QGroupBox("Paragons Directory")
        list_layout = QVBoxLayout(list_group)
        self.paragon_list = QListWidget()
        self.paragon_list.currentRowChanged.connect(parent.on_paragon_list_selection)
        list_layout.addWidget(self.paragon_list)
        
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ Add Paragon")
        self.btn_add.clicked.connect(parent.add_new_paragon)
        self.btn_delete = QPushButton("➖ Delete Paragon")
        self.btn_delete.clicked.connect(parent.delete_selected_paragon)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_delete)
        list_layout.addLayout(btn_layout)

        details_group = QGroupBox("Paragon Characteristics")
        details_form = QFormLayout(details_group)
        self.txt_name = QLineEdit()
        self.txt_name.textChanged.connect(parent.on_paragon_details_changed)
        details_form.addRow("Name:", self.txt_name)
        
        self.cb_faction = QComboBox()
        self.cb_faction.currentIndexChanged.connect(parent.on_paragon_details_changed)
        details_form.addRow("Faction Country:", self.cb_faction)

        self.cb_archetype = QComboBox()
        self.cb_archetype.addItems(["Commander", "Merchant", "Mage", "Priest", "Diplomat"])
        self.cb_archetype.currentIndexChanged.connect(parent.on_paragon_details_changed)
        details_form.addRow("Archetype:", self.cb_archetype)

        self.spin_level = QSpinBox()
        self.spin_level.setRange(1, 100)
        self.spin_level.valueChanged.connect(parent.on_paragon_details_changed)
        details_form.addRow("Level:", self.spin_level)

        self.txt_motivation = QLineEdit()
        self.txt_motivation.textChanged.connect(parent.on_paragon_details_changed)
        details_form.addRow("Motivation:", self.txt_motivation)

        stats_group = QGroupBox("Paragon Stats")
        stats_layout = QFormLayout(stats_group)
        self.stat_sliders = {}
        for stat in ["Might", "Endurance", "Finesse", "Reflex", "Vitality", "Fortitude", "Knowledge", "Logic", "Awareness", "Intuition", "Charm", "Willpower"]:
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(1, 20)
            slider.setValue(10)
            slider.valueChanged.connect(parent.on_paragon_details_changed)
            stats_layout.addRow(f"{stat}:", slider)
            self.stat_sliders[stat] = slider

        traits_group = QGroupBox("Paragon Traits")
        traits_layout = QVBoxLayout(traits_group)
        self.traits_list = QListWidget()
        self.traits_list.itemChanged.connect(parent.on_paragon_traits_changed)
        traits_layout.addWidget(self.traits_list)

        scroll_layout.addWidget(self.lbl_radius)
        scroll_layout.addWidget(self.slider_radius)
        scroll_layout.addWidget(self.btn_paint)
        scroll_layout.addWidget(list_group)
        scroll_layout.addWidget(details_group)
        scroll_layout.addWidget(stats_group)
        scroll_layout.addWidget(traits_group)
        
        self.add_save_load_buttons(scroll_layout, parent, parent.save_provinces_layer, parent.load_provinces_layer)
        
        content.setLayout(scroll_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)

class TraitPoolEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Traits Pool Manager", parent)
        layout = QVBoxLayout(self)
        
        self.table_traits = QTableWidget()
        self.table_traits.setColumnCount(3)
        self.table_traits.setHorizontalHeaderLabels(["Name", "Type", "Effect"])
        self.table_traits.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_traits.itemChanged.connect(parent.on_trait_pool_table_changed)
        layout.addWidget(self.table_traits)
        
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ Add Trait")
        self.btn_add.clicked.connect(parent.add_new_pool_trait)
        self.btn_delete = QPushButton("➖ Delete Trait")
        self.btn_delete.clicked.connect(parent.delete_pool_trait)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_delete)
        layout.addLayout(btn_layout)

class ChaosPathsEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Chaos Paths (12 Prisons & Convergence)", parent)
        layout = QVBoxLayout(self)
        
        self.lbl_radius = QLabel(f"Brush Radius: {parent.brush_radius_val}")
        self.slider_radius = QSlider(Qt.Orientation.Horizontal)
        self.slider_radius.setRange(1, 10)
        self.slider_radius.setValue(parent.brush_radius_val)
        self.slider_radius.valueChanged.connect(parent.on_brush_radius_changed)
        
        self.btn_paint = QPushButton("🎨 Paint Chaos Path")
        self.btn_paint.setCheckable(True)
        self.btn_paint.toggled.connect(parent.on_brush_toggled)

        self.list_paths = QListWidget()
        self.list_paths.currentRowChanged.connect(parent.on_chaos_path_selection)
        layout.addWidget(QLabel("Select Chaos Path / Convergence:"))
        layout.addWidget(self.list_paths)

        self.chk_prison = QCheckBox("Prison Active at Path Source")
        self.chk_prison.toggled.connect(parent.on_chaos_prison_toggled)
        layout.addWidget(self.chk_prison)

        layout.addWidget(self.lbl_radius)
        layout.addWidget(self.slider_radius)
        layout.addWidget(self.btn_paint)
        
        self.add_save_load_buttons(layout, parent, parent.save_religions_layer, parent.load_religions_layer)

class FringeGroupsEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Fringe Groups (Cartels & Pirates)", parent)
        layout = QVBoxLayout(self)
        
        self.lbl_radius = QLabel(f"Brush Radius: {parent.brush_radius_val}")
        self.slider_radius = QSlider(Qt.Orientation.Horizontal)
        self.slider_radius.setRange(1, 10)
        self.slider_radius.setValue(parent.brush_radius_val)
        self.slider_radius.valueChanged.connect(parent.on_brush_radius_changed)
        
        self.btn_paint = QPushButton("🎨 Paint Operations Area")
        self.btn_paint.setCheckable(True)
        self.btn_paint.toggled.connect(parent.on_brush_toggled)

        self.list_groups = QListWidget()
        self.list_groups.currentRowChanged.connect(parent.on_fringe_group_selection)
        layout.addWidget(self.list_groups)
        
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ Add Group")
        self.btn_add.clicked.connect(parent.add_fringe_group)
        self.btn_delete = QPushButton("➖ Delete Group")
        self.btn_delete.clicked.connect(parent.delete_fringe_group)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_delete)
        layout.addLayout(btn_layout)

        form_layout = QFormLayout()
        self.txt_name = QLineEdit()
        self.txt_name.textChanged.connect(parent.on_fringe_group_changed)
        form_layout.addRow("Group Name:", self.txt_name)
        
        self.cb_type = QComboBox()
        self.cb_type.addItems(["Cartel", "Pirates", "Smugglers"])
        self.cb_type.currentIndexChanged.connect(parent.on_fringe_group_changed)
        form_layout.addRow("Type:", self.cb_type)
        layout.addLayout(form_layout)

        layout.addWidget(self.lbl_radius)
        layout.addWidget(self.slider_radius)
        layout.addWidget(self.btn_paint)
        
        self.add_save_load_buttons(layout, parent, parent.save_cultures_layer, parent.load_cultures_layer)

class ClimateEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Climate Editor (Temp & Moisture)", parent)
        layout = QVBoxLayout(self)
        
        self.lbl_radius = QLabel(f"Brush Radius: {parent.brush_radius_val}")
        self.slider_radius = QSlider(Qt.Orientation.Horizontal)
        self.slider_radius.setRange(1, 10)
        self.slider_radius.setValue(parent.brush_radius_val)
        self.slider_radius.valueChanged.connect(parent.on_brush_radius_changed)
        self.slider_radius.valueChanged.connect(lambda v: self.lbl_radius.setText(f"Brush Radius: {v}"))
        
        self.btn_paint_temp = QPushButton("🌡️ Paint Temperature")
        self.btn_paint_temp.setCheckable(True)
        self.btn_paint_temp.toggled.connect(parent.on_brush_toggled)

        self.btn_paint_moist = QPushButton("💧 Paint Moisture")
        self.btn_paint_moist.setCheckable(True)
        self.btn_paint_moist.toggled.connect(parent.on_brush_toggled)

        self.lbl_temp = QLabel(f"Brush Temperature: 128")
        self.slider_temp = QSlider(Qt.Orientation.Horizontal)
        self.slider_temp.setRange(0, 255)
        self.slider_temp.setValue(128)
        self.slider_temp.valueChanged.connect(parent.update_active_brush_mode)
        self.slider_temp.valueChanged.connect(lambda v: self.lbl_temp.setText(f"Brush Temperature: {v}"))

        self.lbl_moist = QLabel(f"Brush Moisture: 128")
        self.slider_moist = QSlider(Qt.Orientation.Horizontal)
        self.slider_moist.setRange(0, 255)
        self.slider_moist.setValue(128)
        self.slider_moist.valueChanged.connect(parent.update_active_brush_mode)
        self.slider_moist.valueChanged.connect(lambda v: self.lbl_moist.setText(f"Brush Moisture: {v}"))

        layout.addWidget(self.lbl_radius)
        layout.addWidget(self.slider_radius)
        layout.addWidget(self.lbl_temp)
        layout.addWidget(self.slider_temp)
        layout.addWidget(self.btn_paint_temp)
        layout.addWidget(self.lbl_moist)
        layout.addWidget(self.slider_moist)
        layout.addWidget(self.btn_paint_moist)
        
        self.add_save_load_buttons(layout, parent, parent.save_climate_layer, parent.load_climate_layer)
        layout.addStretch()

    def uncheck_paint_button(self):
        for btn in [self.btn_paint_temp, self.btn_paint_moist]:
            btn.blockSignals(True)
            btn.setChecked(False)
            btn.setStyleSheet("")
            btn.blockSignals(False)

class RiversEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Rivers & Hydrology", parent)
        layout = QVBoxLayout(self)
        
        self.lbl_radius = QLabel(f"Brush Radius: {parent.brush_radius_val}")
        self.slider_radius = QSlider(Qt.Orientation.Horizontal)
        self.slider_radius.setRange(1, 10)
        self.slider_radius.setValue(parent.brush_radius_val)
        self.slider_radius.valueChanged.connect(parent.on_brush_radius_changed)
        self.slider_radius.valueChanged.connect(lambda v: self.lbl_radius.setText(f"Brush Radius: {v}"))
        
        self.btn_paint_river = QPushButton("🌊 Paint River Volume")
        self.btn_paint_river.setCheckable(True)
        self.btn_paint_river.toggled.connect(parent.on_brush_toggled)

        self.btn_toggle_lake = QPushButton("💧 Toggle Lake")
        self.btn_toggle_lake.setCheckable(True)
        self.btn_toggle_lake.toggled.connect(parent.on_brush_toggled)

        self.lbl_river = QLabel(f"River Volume: 10")
        self.slider_river = QSlider(Qt.Orientation.Horizontal)
        self.slider_river.setRange(0, 100)
        self.slider_river.setValue(10)
        self.slider_river.valueChanged.connect(parent.update_active_brush_mode)
        self.slider_river.valueChanged.connect(lambda v: self.lbl_river.setText(f"River Volume: {v}"))

        self.btn_regen_rivers = QPushButton("⚡ Regenerate All Rivers/Hydrology")
        self.btn_regen_rivers.clicked.connect(parent.regenerate_rivers_simulation)

        layout.addWidget(self.lbl_radius)
        layout.addWidget(self.slider_radius)
        layout.addWidget(self.lbl_river)
        layout.addWidget(self.slider_river)
        layout.addWidget(self.btn_paint_river)
        layout.addWidget(QLabel("Lake State Brush:"))
        layout.addWidget(parent.chk_lake_brush)
        layout.addWidget(self.btn_toggle_lake)
        layout.addWidget(self.btn_regen_rivers)
        
        self.add_save_load_buttons(layout, parent, parent.save_rivers_layer, parent.load_rivers_layer)
        layout.addStretch()

    def uncheck_paint_button(self):
        for btn in [self.btn_paint_river, self.btn_toggle_lake]:
            btn.blockSignals(True)
            btn.setChecked(False)
            btn.setStyleSheet("")
            btn.blockSignals(False)

class ChaosEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Chaos Domains Zones", parent)
        layout = QVBoxLayout(self)
        
        self.lbl_radius = QLabel(f"Brush Radius: {parent.brush_radius_val}")
        self.slider_radius = QSlider(Qt.Orientation.Horizontal)
        self.slider_radius.setRange(1, 10)
        self.slider_radius.setValue(parent.brush_radius_val)
        self.slider_radius.valueChanged.connect(parent.on_brush_radius_changed)
        self.slider_radius.valueChanged.connect(lambda v: self.lbl_radius.setText(f"Brush Radius: {v}"))
        
        self.chaos_list_brush = QListWidget()
        for dom in CHAOS_DOMAINS:
            item = QListWidgetItem(dom)
            item.setIcon(create_color_icon(CHAOS_COLORS_HEX[dom]))
            self.chaos_list_brush.addItem(item)
        self.chaos_list_brush.setCurrentRow(0)
        self.chaos_list_brush.currentRowChanged.connect(parent.update_active_brush_mode)

        self.btn_paint = QPushButton("🌀 Paint Chaos Domain")
        self.btn_paint.setCheckable(True)
        self.btn_paint.toggled.connect(parent.on_brush_toggled)

        layout.addWidget(self.lbl_radius)
        layout.addWidget(self.slider_radius)
        layout.addWidget(QLabel("Select Domain Type to Paint:"))
        layout.addWidget(self.chaos_list_brush)
        layout.addWidget(self.btn_paint)
        
        self.add_save_load_buttons(layout, parent, parent.save_chaos_layer, parent.load_chaos_layer)

class SettlementsEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Settlements Directory & Buildings", parent)
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll_layout = QVBoxLayout(content)

        self.list_settlements = QListWidget()
        self.list_settlements.currentRowChanged.connect(parent.on_settlement_directory_selection)

        self.btn_snap = QPushButton("📍 Locate on Map")
        self.btn_snap.clicked.connect(parent.snap_to_directory_settlement)

        self.btn_delete = QPushButton("➖ Dissolve Settlement")
        self.btn_delete.clicked.connect(parent.delete_directory_settlement)

        form_group = QGroupBox("Settlement Properties")
        form_layout = QFormLayout(form_group)

        self.txt_name = QLineEdit()
        self.txt_name.editingFinished.connect(parent.on_directory_settlement_changed)
        form_layout.addRow("Name:", self.txt_name)

        self.cb_faction = QComboBox()
        self.cb_faction.currentIndexChanged.connect(parent.on_directory_settlement_changed)
        form_layout.addRow("Faction Alignment:", self.cb_faction)
        
        self.cb_linked_paragon = QComboBox()
        self.cb_linked_paragon.currentIndexChanged.connect(parent.on_directory_settlement_changed)
        form_layout.addRow("Linked Paragon:", self.cb_linked_paragon)

        self.txt_pop = QLineEdit()
        self.txt_pop.editingFinished.connect(parent.on_directory_settlement_changed)
        form_layout.addRow("Population:", self.txt_pop)

        self.txt_wealth = QLineEdit()
        self.txt_wealth.editingFinished.connect(parent.on_directory_settlement_changed)
        form_layout.addRow("Wealth Rating:", self.txt_wealth)

        # Buildings Slots around settlement
        build_group = QGroupBox("Buildings Slots (Farms, Mines, etc.)")
        build_layout = QVBoxLayout(build_group)
        self.table_buildings = QTableWidget()
        self.table_buildings.setColumnCount(3)
        self.table_buildings.setHorizontalHeaderLabels(["Type", "Count", "Efficiency (%)"])
        self.table_buildings.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_buildings.itemChanged.connect(parent.on_settlement_buildings_changed)
        build_layout.addWidget(self.table_buildings)
        
        btn_b_layout = QHBoxLayout()
        self.btn_add_b = QPushButton("➕ Add Building")
        self.btn_add_b.clicked.connect(parent.add_settlement_building)
        self.btn_del_b = QPushButton("➖ Delete Building")
        self.btn_del_b.clicked.connect(parent.delete_settlement_building)
        btn_b_layout.addWidget(self.btn_add_b)
        btn_b_layout.addWidget(self.btn_del_b)
        build_layout.addLayout(btn_b_layout)

        scroll_layout.addWidget(QLabel("<b>All Settlements</b>"))
        scroll_layout.addWidget(self.list_settlements)
        scroll_layout.addWidget(self.btn_snap)
        scroll_layout.addWidget(self.btn_delete)
        scroll_layout.addWidget(form_group)
        scroll_layout.addWidget(build_group)
        
        self.add_save_load_buttons(scroll_layout, parent, parent.save_settlements_layer, parent.load_settlements_layer)
        
        content.setLayout(scroll_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)

class NameStyleEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Language & Naming Styles", parent)
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll_layout = QVBoxLayout(content)

        scroll_layout.addWidget(QLabel("<b>Cultures List</b>"))
        scroll_layout.addWidget(parent.cul_list_names)

        form_group = QGroupBox("Culture Naming Rules")
        form_layout = QFormLayout(form_group)

        self.txt_base_lang = QLineEdit()
        self.txt_base_lang.editingFinished.connect(parent.on_culture_names_changed)
        form_layout.addRow("Phonetic Style Template:", self.txt_base_lang)

        scroll_layout.addWidget(form_group)
        self.add_save_load_buttons(scroll_layout, parent, parent.save_names_layer, parent.load_names_layer)
        
        content.setLayout(scroll_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)

class MarkersEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Resource Markers & POIs", parent)
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll_layout = QVBoxLayout(content)

        self.btn_paint = QPushButton("🎨 Place Resource Marker")
        self.btn_paint.setCheckable(True)
        self.btn_paint.toggled.connect(parent.on_brush_toggled)

        list_group = QGroupBox("All Map Markers")
        list_layout = QVBoxLayout(list_group)
        list_layout.addWidget(parent.mark_list)
        list_layout.addWidget(parent.btn_add_mark)
        list_layout.addWidget(parent.btn_del_mark)

        details_group = QGroupBox("Resource Marker Attributes")
        details_form = QFormLayout(details_group)
        
        self.cb_res_type = QComboBox()
        self.cb_res_type.currentIndexChanged.connect(parent.on_marker_details_changed)
        details_form.addRow("Resource Type:", self.cb_res_type)
        
        self.txt_res_val = QLineEdit("1.0")
        self.txt_res_val.editingFinished.connect(parent.on_marker_details_changed)
        details_form.addRow("Harvest Potential Value:", self.txt_res_val)

        details_form.addRow("Description:", parent.txt_mark_desc)
        details_form.addRow("Grid Coord Q:", parent.spin_mark_q)
        details_form.addRow("Grid Coord R:", parent.spin_mark_r)
        details_form.addRow(parent.btn_snap_mark)

        scroll_layout.addWidget(self.btn_paint)
        scroll_layout.addWidget(list_group)
        scroll_layout.addWidget(details_group)
        
        self.add_save_load_buttons(scroll_layout, parent, parent.save_markers_layer, parent.load_markers_layer)
        
        content.setLayout(scroll_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)

class ForcesEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Moving Units Manager (Merchants/Monsters)", parent)
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll_layout = QVBoxLayout(content)

        self.btn_paint = QPushButton("🎨 Deploy Moving Unit")
        self.btn_paint.setCheckable(True)
        self.btn_paint.toggled.connect(parent.on_brush_toggled)

        list_group = QGroupBox("Units Directory")
        list_layout = QVBoxLayout(list_group)
        list_layout.addWidget(parent.ent_list)
        list_layout.addWidget(parent.btn_add_ent)
        list_layout.addWidget(parent.btn_del_ent)

        details_group = QGroupBox("Unit Settings")
        details_form = QFormLayout(details_group)
        
        self.cb_unit_type = QComboBox()
        self.cb_unit_type.addItems(["Merchant Caravan", "Military Regiment", "Diplomatic Envoy", "Chaos Monster"])
        self.cb_unit_type.currentIndexChanged.connect(parent.on_entity_details_changed)
        details_form.addRow("Unit Type:", self.cb_unit_type)

        details_form.addRow("Owner Faction:", parent.cb_ent_align)
        details_form.addRow("Hex Radius Impact:", parent.spin_ent_radius)
        details_form.addRow("Ticks Remaining duration:", parent.spin_ent_duration)
        details_form.addRow("Force Strength Index:", parent.txt_ent_intensity)
        details_form.addRow("Target Hex Q:", parent.spin_ent_q)
        details_form.addRow("Target Hex R:", parent.spin_ent_r)
        details_form.addRow(parent.btn_snap_ent)

        scroll_layout.addWidget(self.btn_paint)
        scroll_layout.addWidget(list_group)
        scroll_layout.addWidget(details_group)
        
        self.add_save_load_buttons(scroll_layout, parent, parent.save_forces_layer, parent.load_forces_layer)
        
        content.setLayout(scroll_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)

class RoutesEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Trade & Travel Routes", parent)
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll_layout = QVBoxLayout(content)

        self.btn_paint = QPushButton("🎨 Construct Trade Route Link")
        self.btn_paint.setCheckable(True)
        self.btn_paint.toggled.connect(parent.on_brush_toggled)

        list_group = QGroupBox("Routes Index")
        list_layout = QVBoxLayout(list_group)
        list_layout.addWidget(parent.route_list)
        list_layout.addWidget(parent.btn_del_route)

        details_group = QGroupBox("Selected Route Details")
        details_form = QFormLayout(details_group)
        details_form.addRow("Owner Faction:", parent.cb_rt_faction)
        details_form.addRow("Transport Capacity (Bandwidth):", parent.spin_rt_bandwidth)
        details_form.addRow("Route Type Terrain:", parent.cb_rt_type)

        self.btn_regen_roads = QPushButton("⚡ Regenerate All Trade Roads")
        self.btn_regen_roads.clicked.connect(parent.regenerate_roads_simulation)

        scroll_layout.addWidget(self.btn_paint)
        scroll_layout.addWidget(list_group)
        scroll_layout.addWidget(details_group)
        scroll_layout.addWidget(self.btn_regen_roads)
        
        self.add_save_load_buttons(scroll_layout, parent, parent.save_routes_layer, parent.load_routes_layer)
        
        content.setLayout(scroll_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)

class CalendarEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Calendar & Seasons Editor", parent)
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll_layout = QVBoxLayout(content)

        week_group = QGroupBox("Week Configuration")
        week_layout = QVBoxLayout(week_group)
        self.txt_week_days = QLineEdit()
        self.txt_week_days.textChanged.connect(parent.on_calendar_changed)
        week_layout.addWidget(QLabel("Day Names (comma separated):"))
        week_layout.addWidget(self.txt_week_days)
        
        months_group = QGroupBox("Months List")
        months_layout = QVBoxLayout(months_group)
        self.table_months = QTableWidget()
        self.table_months.setColumnCount(2)
        self.table_months.setHorizontalHeaderLabels(["Month Name", "Weeks Count"])
        self.table_months.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_months.itemChanged.connect(parent.on_calendar_months_changed)
        months_layout.addWidget(self.table_months)
        
        btn_m_layout = QHBoxLayout()
        self.btn_add_m = QPushButton("➕ Add Month")
        self.btn_add_m.clicked.connect(parent.add_calendar_month)
        self.btn_del_m = QPushButton("➖ Delete Month")
        self.btn_del_m.clicked.connect(parent.delete_calendar_month)
        btn_m_layout.addWidget(self.btn_add_m)
        btn_m_layout.addWidget(self.btn_del_m)
        months_layout.addLayout(btn_m_layout)

        seasons_group = QGroupBox("Seasons Config")
        seasons_layout = QVBoxLayout(seasons_group)
        self.table_seasons = QTableWidget()
        self.table_seasons.setColumnCount(4)
        self.table_seasons.setHorizontalHeaderLabels(["Season", "Active Months", "Temp Adjust", "Precipitation (%)"])
        self.table_seasons.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_seasons.itemChanged.connect(parent.on_calendar_seasons_changed)
        seasons_layout.addWidget(self.table_seasons)
        
        btn_s_layout = QHBoxLayout()
        self.btn_add_s = QPushButton("➕ Add Season")
        self.btn_add_s.clicked.connect(parent.add_calendar_season)
        self.btn_del_s = QPushButton("➖ Delete Season")
        self.btn_del_s.clicked.connect(parent.delete_calendar_season)
        btn_s_layout.addWidget(self.btn_add_s)
        btn_s_layout.addWidget(self.btn_del_s)
        seasons_layout.addLayout(btn_s_layout)

        scroll_layout.addWidget(week_group)
        scroll_layout.addWidget(months_group)
        scroll_layout.addWidget(seasons_group)

        content.setLayout(scroll_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)

class EconomyEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Economy, Cost & Base Resources Manager", parent)
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        tab_res = QWidget()
        layout_res = QVBoxLayout(tab_res)
        self.table_res = QTableWidget()
        self.table_res.setColumnCount(3)
        self.table_res.setHorizontalHeaderLabels(["Resource", "Value", "Source Biomes (IDs)"])
        self.table_res.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_res.itemChanged.connect(parent.on_econ_res_changed)
        layout_res.addWidget(self.table_res)
        
        btn_res_lay = QHBoxLayout()
        self.btn_add_res = QPushButton("Add Base Resource")
        self.btn_add_res.clicked.connect(parent.add_econ_res)
        self.btn_del_res = QPushButton("Delete Resource")
        self.btn_del_res.clicked.connect(parent.delete_econ_res)
        btn_res_lay.addWidget(self.btn_add_res)
        btn_res_lay.addWidget(self.btn_del_res)
        layout_res.addLayout(btn_res_lay)
        self.tabs.addTab(tab_res, "Base Resources")

        tab_goods = QWidget()
        layout_goods = QVBoxLayout(tab_goods)
        self.table_goods = QTableWidget()
        self.table_goods.setColumnCount(4)
        self.table_goods.setHorizontalHeaderLabels(["Good", "Cost", "Effect / Use", "Type"])
        self.table_goods.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_goods.itemChanged.connect(parent.on_econ_goods_changed)
        layout_goods.addWidget(self.table_goods)
        
        btn_goods_lay = QHBoxLayout()
        self.btn_add_goods = QPushButton("Add Good")
        self.btn_add_goods.clicked.connect(parent.add_econ_good)
        self.btn_del_goods = QPushButton("Delete Good")
        self.btn_del_goods.clicked.connect(parent.delete_econ_good)
        btn_goods_lay.addWidget(self.btn_add_goods)
        btn_goods_lay.addWidget(self.btn_del_goods)
        layout_goods.addLayout(btn_goods_lay)
        self.tabs.addTab(tab_goods, "Manufactured Goods")

        tab_build = QWidget()
        layout_build = QVBoxLayout(tab_build)
        self.table_build = QTableWidget()
        self.table_build.setColumnCount(2)
        self.table_build.setHorizontalHeaderLabels(["Building Type", "Resource Costs (JSON)"])
        self.table_build.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_build.itemChanged.connect(parent.on_econ_build_changed)
        layout_build.addWidget(self.table_build)
        
        btn_build_lay = QHBoxLayout()
        self.btn_add_build = QPushButton("Add Building Cost")
        self.btn_add_build.clicked.connect(parent.add_econ_build_type)
        self.btn_del_build = QPushButton("Delete Building")
        self.btn_del_build.clicked.connect(parent.delete_econ_build_type)
        btn_build_lay.addWidget(self.btn_add_build)
        btn_build_lay.addWidget(self.btn_del_build)
        layout_build.addLayout(btn_build_lay)
        self.tabs.addTab(tab_build, "Building Costs")

class CellInspectorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Cell / Settlement Inspector", parent)
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll_layout = QVBoxLayout(content)

        scroll_layout.addWidget(parent.hex_group)
        scroll_layout.addWidget(parent.sett_group)
        scroll_layout.addWidget(parent.plist_group)
        scroll_layout.addWidget(parent.peditor_group)
        scroll_layout.addStretch()

        content.setLayout(scroll_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)

# ----------------------------------------------------
# Main Application Window
# ----------------------------------------------------
class FMGMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shatterlands Python World Builder & Configuration App")
        self.resize(1550, 950)
        
        # State
        self.state = MapState()
        self.selected_coord = None
        self.selected_faction_id = None
        self.selected_paragon_idx = None
        self.selected_entity_idx = None
        self.selected_route_idx = None
        self.selected_religion_id = None
        self.selected_culture_id = None
        self.selected_province_id = None
        self.selected_marker_idx = None
        self.selected_directory_settlement_id = None
        self.selected_culture_names_id = None
        self.route_start_sett_id = None
        # World Configurator parameters
        self.temperature_equator = 30.0
        self.temperature_pole = -15.0
        self.temperature_offset = 0.0
        self.precipitation_multiplier = 1.0
        self.wind_direction_angle = 90.0
        self.brush_radius_val = 1
        self.db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "shatterlands_simulator", "core_engine", "world_state.db"))
        
        # Dialog Window References
        self.dialog_elevation = None
        self.dialog_biomes = None
        self.dialog_factions = None
        self.dialog_provinces = None
        self.dialog_religions = None
        self.dialog_cultures = None
        self.dialog_markers = None
        self.dialog_forces = None
        self.dialog_routes = None
        self.dialog_cell_inspector = None
        self.dialog_climate = None
        self.dialog_rivers = None
        self.dialog_chaos = None
        self.dialog_settlements = None
        self.dialog_names = None
        self.dialog_trait_pool = None
        self.dialog_economy = None

        # UI Styles
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121214;
            }
            QWidget {
                color: #E1E1E6;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox {
                border: 1px solid #29292E;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                background-color: #18181B;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 5px 0 5px;
                color: #04D361;
            }
            QPushButton {
                background-color: #202024;
                border: 1px solid #29292E;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #29292E;
                border-color: #04D361;
            }
            QComboBox, QLineEdit, QSlider, QSpinBox, QDoubleSpinBox, QListWidget, QTableWidget, QTextEdit {
                background-color: #121214;
                border: 1px solid #29292E;
                border-radius: 4px;
                padding: 4px;
            }
            QComboBox:focus, QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
                border-color: #04D361;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        # Central Widget: The persistent full-screen Map View
        self.map_viewer = WorldMapViewer(self)
        self.map_viewer.hex_selected.connect(self.on_hex_selected)
        self.map_viewer.hex_painted.connect(self.on_hex_painted)
        self.map_viewer.place_settlement_requested.connect(self.place_settlement_at)
        self.map_viewer.place_marker_requested.connect(self.place_marker_at)
        self.map_viewer.place_force_requested.connect(self.place_force_at)
        self.map_viewer.link_route_requested.connect(self.link_route_at)
        self.setCentralWidget(self.map_viewer)

        # Build Top Toolbar (Database sync, generation, export)
        toolbar = QToolBar("Main Controls", self)
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        btn_load_db = QPushButton("📥 Load DB")
        btn_load_db.clicked.connect(self.load_db)
        toolbar.addWidget(btn_load_db)

        btn_save_db = QPushButton("💾 Save DB")
        btn_save_db.clicked.connect(self.save_db)
        toolbar.addWidget(btn_save_db)

        btn_run_tick = QPushButton("▶ Run Tick")
        btn_run_tick.clicked.connect(self.run_sim_tick)
        toolbar.addWidget(btn_run_tick)

        toolbar.addSeparator()

        btn_gen = QPushButton("🌌 Generate World")
        btn_gen.clicked.connect(self.generate_new_world)
        toolbar.addWidget(btn_gen)
        btn_config = QPushButton("🌍 World Configurator")
        btn_config.clicked.connect(self.open_world_configurator)
        toolbar.addWidget(btn_config)

        btn_import_map = QPushButton("📂 Import Map")
        btn_import_map.clicked.connect(self.import_azgaar_map)
        toolbar.addWidget(btn_import_map)

        btn_export_json = QPushButton("📤 Export JSON")
        btn_export_json.clicked.connect(self.export_json)
        toolbar.addWidget(btn_export_json)

        toolbar.addSeparator()

        lbl_layer = QLabel("  View Layer: ")
        toolbar.addWidget(lbl_layer)
        self.cb_view_layer = QComboBox()
        self.cb_view_layer.addItems(["Biomes", "Elevation", "Temperature", "Moisture", "Chaos / Infestation", "Factions & States", "Religions", "Cultures", "Provinces"])
        self.cb_view_layer.currentIndexChanged.connect(self.on_view_layer_changed)
        toolbar.addWidget(self.cb_view_layer)

        # Initialize shared brush settings & data controls
        self.cb_biome_brush = QComboBox()
        for idx, b_name in BIOME_NAMES.items():
            self.cb_biome_brush.addItem(b_name, idx)
        self.cb_biome_brush.currentIndexChanged.connect(self.update_active_brush_mode)

        self.spin_elev_brush = QSpinBox()
        self.spin_elev_brush.setRange(0, 15)
        self.spin_elev_brush.setValue(5)
        self.spin_elev_brush.valueChanged.connect(self.update_active_brush_mode)

        self.cb_rel_brush = QComboBox()
        self.cb_rel_brush.currentIndexChanged.connect(self.update_active_brush_mode)

        self.cb_cul_brush = QComboBox()
        self.cb_cul_brush.currentIndexChanged.connect(self.update_active_brush_mode)

        self.spin_prov_brush = QSpinBox()
        self.spin_prov_brush.setRange(0, 100)
        self.spin_prov_brush.setValue(1)
        self.spin_prov_brush.valueChanged.connect(self.update_active_brush_mode)

        self.cb_fac_paint_brush = QComboBox()
        self.cb_fac_paint_brush.currentIndexChanged.connect(self.update_active_brush_mode)

        # New brushes
        self.spin_temp_brush = QSpinBox()
        self.spin_temp_brush.setRange(0, 255)
        self.spin_temp_brush.setValue(128)
        self.spin_temp_brush.valueChanged.connect(self.update_active_brush_mode)

        self.spin_moist_brush = QSpinBox()
        self.spin_moist_brush.setRange(0, 255)
        self.spin_moist_brush.setValue(128)
        self.spin_moist_brush.valueChanged.connect(self.update_active_brush_mode)

        self.spin_river_brush = QSpinBox()
        self.spin_river_brush.setRange(0, 1000)
        self.spin_river_brush.setValue(10)
        self.spin_river_brush.valueChanged.connect(self.update_active_brush_mode)

        self.chk_lake_brush = QCheckBox("Lake")
        self.chk_lake_brush.setChecked(True)
        self.chk_lake_brush.toggled.connect(self.update_active_brush_mode)

        self.cb_chaos_brush = QComboBox()
        for dom in CHAOS_DOMAINS:
            self.cb_chaos_brush.addItem(dom)
        self.cb_chaos_brush.currentIndexChanged.connect(self.update_active_brush_mode)

        self.cul_list_names = QListWidget()
        self.cul_list_names.currentRowChanged.connect(self.on_cul_names_selection)

        # Left Customize Panel (Collapsible tools sidebar)
        self.left_dock = QDockWidget("Tools Panel", self)
        self.left_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        self.left_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.left_dock.setMinimumWidth(200)
        self.left_dock.setMaximumWidth(240)
        
        dock_content = QWidget()
        dock_layout = QVBoxLayout(dock_content)
        dock_layout.addWidget(QLabel("<b>CUSTOMIZE LAYER EDITORS</b>"))
        
        btn_show_inspector = QPushButton("🔍 Cell Inspector")
        btn_show_inspector.clicked.connect(self.open_cell_inspector)
        dock_layout.addWidget(btn_show_inspector)
        
        btn_show_elev = QPushButton("🏔️ Heightmap (Elevation)")
        btn_show_elev.clicked.connect(self.open_elevation_editor)
        dock_layout.addWidget(btn_show_elev)

        btn_show_biomes = QPushButton("🌱 Biomes Editor")
        btn_show_biomes.clicked.connect(self.open_biomes_editor)
        dock_layout.addWidget(btn_show_biomes)

        btn_show_factions = QPushButton("🛡️ Factions & States")
        btn_show_factions.clicked.connect(self.open_factions_editor)
        dock_layout.addWidget(btn_show_factions)

        btn_show_provinces = QPushButton("🏛️ Provinces Editor")
        btn_show_provinces.clicked.connect(self.open_provinces_editor)
        dock_layout.addWidget(btn_show_provinces)

        btn_show_religions = QPushButton("🕍 Religions Editor")
        btn_show_religions.clicked.connect(self.open_religions_editor)
        dock_layout.addWidget(btn_show_religions)

        btn_show_cultures = QPushButton("🎨 Cultures Editor")
        btn_show_cultures.clicked.connect(self.open_cultures_editor)
        dock_layout.addWidget(btn_show_cultures)

        btn_show_climate = QPushButton("🌡️ Climate Editor")
        btn_show_climate.clicked.connect(self.open_climate_editor)
        dock_layout.addWidget(btn_show_climate)

        btn_show_rivers = QPushButton("🌊 Rivers & Hydrology")
        btn_show_rivers.clicked.connect(self.open_rivers_editor)
        dock_layout.addWidget(btn_show_rivers)

        btn_show_chaos = QPushButton("🌀 Chaos Domains")
        btn_show_chaos.clicked.connect(self.open_chaos_editor)
        dock_layout.addWidget(btn_show_chaos)

        btn_show_settlements = QPushButton("🏰 Settlements Directory")
        btn_show_settlements.clicked.connect(self.open_settlements_directory)
        dock_layout.addWidget(btn_show_settlements)

        btn_show_names = QPushButton("📜 Language & Names")
        btn_show_names.clicked.connect(self.open_names_editor)
        dock_layout.addWidget(btn_show_names)

        btn_show_markers = QPushButton("📍 Markers & POIs")
        btn_show_markers.clicked.connect(self.open_markers_editor)
        dock_layout.addWidget(btn_show_markers)

        btn_show_forces = QPushButton("⚔️ Regiments & Forces")
        btn_show_forces.clicked.connect(self.open_forces_editor)
        dock_layout.addWidget(btn_show_forces)

        btn_show_routes = QPushButton("🛣️ Trade Routes Editor")
        btn_show_routes.clicked.connect(self.open_routes_editor)
        dock_layout.addWidget(btn_show_routes)

        dock_layout.addStretch()
        self.left_dock.setWidget(dock_content)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.left_dock)

        # Instantiate inspector & data fields
        self.hex_group = QGroupBox("Hex Coordinates")
        self.hex_form = QFormLayout(self.hex_group)
        self.lbl_coord = QLabel("Select a hex on the map")
        self.hex_form.addRow("Coordinates:", self.lbl_coord)
        
        self.cb_biome = QComboBox()
        for idx, b_name in BIOME_NAMES.items():
            self.cb_biome.addItem(b_name, idx)
        self.cb_biome.currentIndexChanged.connect(self.on_biome_changed)
        self.hex_form.addRow("Biome:", self.cb_biome)
        
        self.sld_elev = QSlider(Qt.Orientation.Horizontal)
        self.sld_elev.setRange(0, 15)
        self.sld_elev.valueChanged.connect(self.on_elevation_changed)
        self.hex_form.addRow("Elevation:", self.sld_elev)
        
        self.txt_river = QLineEdit("0")
        self.txt_river.editingFinished.connect(self.on_river_changed)
        self.hex_form.addRow("River Volume:", self.txt_river)
        
        self.chk_lake = QCheckBox("Is Lake")
        self.chk_lake.toggled.connect(self.on_lake_changed)
        self.hex_form.addRow("Hydrology:", self.chk_lake)
        
        self.cb_chaos = QComboBox()
        for dom in CHAOS_DOMAINS:
            self.cb_chaos.addItem(dom)
        self.cb_chaos.currentIndexChanged.connect(self.on_chaos_changed)
        self.hex_form.addRow("Chaos Domain:", self.cb_chaos)

        self.sett_group = QGroupBox("Settlement Inventory")
        self.sett_form = QFormLayout(self.sett_group)
        self.chk_has_sett = QCheckBox("Exists")
        self.chk_has_sett.toggled.connect(self.on_has_sett_changed)
        self.sett_form.addRow("Settlement:", self.chk_has_sett)
        
        self.txt_sett_name = QLineEdit()
        self.txt_sett_name.editingFinished.connect(self.on_sett_name_changed)
        self.sett_form.addRow("Name:", self.txt_sett_name)
        
        self.cb_sett_faction = QComboBox()
        self.cb_sett_faction.currentIndexChanged.connect(self.on_sett_faction_changed)
        self.sett_form.addRow("Faction:", self.cb_sett_faction)
        
        self.txt_sett_pop = QLineEdit()
        self.txt_sett_pop.editingFinished.connect(self.on_sett_pop_changed)
        self.sett_form.addRow("Population:", self.txt_sett_pop)
        
        self.txt_sett_inv = QTextEdit()
        self.txt_sett_inv.setMinimumHeight(80)
        self.txt_sett_inv.textChanged.connect(self.on_sett_inv_changed)
        self.sett_form.addRow("Goods (JSON):", self.txt_sett_inv)

        self.btn_paint_settlement = QPushButton("🏰 Click Map to Place Settlement")
        self.btn_paint_settlement.setCheckable(True)
        self.btn_paint_settlement.toggled.connect(self.on_brush_toggled)
        self.sett_form.addRow("", self.btn_paint_settlement)

        # Factions Widgets
        self.faction_list = QListWidget()
        self.faction_list.currentRowChanged.connect(self.on_faction_list_selection)
        self.btn_add_fac = QPushButton("➕ Add Faction")
        self.btn_add_fac.clicked.connect(self.add_new_faction)
        self.txt_fac_name = QLineEdit()
        self.txt_fac_name.editingFinished.connect(self.on_faction_details_changed)
        self.txt_fac_treasury = QLineEdit()
        self.txt_fac_treasury.editingFinished.connect(self.on_faction_details_changed)
        self.spin_fac_tech = QSpinBox()
        self.spin_fac_tech.setRange(1, 100)
        self.spin_fac_tech.valueChanged.connect(self.on_faction_details_changed)
        self.txt_fac_rule = QLineEdit()
        self.txt_fac_rule.editingFinished.connect(self.on_faction_details_changed)
        self.cb_coa_div = QComboBox()
        self.cb_coa_div.addItems(COA_DIVISIONS)
        self.cb_coa_div.currentIndexChanged.connect(self.on_coa_changed)
        self.cb_coa_c1 = QComboBox()
        self.cb_coa_c1.addItems(list(COA_TINCTURES.keys()))
        self.cb_coa_c1.currentIndexChanged.connect(self.on_coa_changed)
        self.cb_coa_c2 = QComboBox()
        self.cb_coa_c2.addItems(list(COA_TINCTURES.keys()))
        self.cb_coa_c2.currentIndexChanged.connect(self.on_coa_changed)
        self.cb_coa_charge = QComboBox()
        self.cb_coa_charge.addItems(COA_CHARGES)
        self.cb_coa_charge.currentIndexChanged.connect(self.on_coa_changed)
        self.cb_coa_charge_color = QComboBox()
        self.cb_coa_charge_color.addItems(list(COA_TINCTURES.keys()))
        self.cb_coa_charge_color.currentIndexChanged.connect(self.on_coa_changed)
        self.coa_visual = CoatOfArmsWidget()
        self.diplomacy_table = QTableWidget()
        self.diplomacy_table.setColumnCount(3)
        self.diplomacy_table.setHorizontalHeaderLabels(["Target Faction", "Status", "Trust"])
        self.diplomacy_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.diplomacy_table.cellChanged.connect(self.on_diplomacy_table_changed)

        # Provinces Widgets
        self.prov_list = QListWidget()
        self.prov_list.currentRowChanged.connect(self.on_prov_list_selection)
        self.btn_add_prov = QPushButton("➕ Add Province")
        self.btn_add_prov.clicked.connect(self.add_new_province)
        self.txt_prov_name = QLineEdit()
        self.txt_prov_name.editingFinished.connect(self.on_province_details_changed)
        self.cb_prov_color = QComboBox()
        self.cb_prov_color.addItems(["#1ABC9C", "#2ECC71", "#3498DB", "#9B59B6", "#F1C40F", "#E67E22", "#E74C3C"])
        self.cb_prov_color.currentIndexChanged.connect(self.on_province_details_changed)
        self.cb_prov_faction = QComboBox()
        self.cb_prov_faction.currentIndexChanged.connect(self.on_province_details_changed)

        # Religions Widgets
        self.rel_list = QListWidget()
        self.rel_list.currentRowChanged.connect(self.on_rel_list_selection)
        self.btn_add_rel = QPushButton("➕ Add Religion")
        self.btn_add_rel.clicked.connect(self.add_new_religion)
        self.txt_rel_name = QLineEdit()
        self.txt_rel_name.editingFinished.connect(self.on_religion_details_changed)
        self.cb_rel_type = QComboBox()
        self.cb_rel_type.addItems(["Polytheism", "Monotheism", "Animism", "Shamanism"])
        self.cb_rel_type.currentIndexChanged.connect(self.on_religion_details_changed)
        self.cb_rel_color = QComboBox()
        self.cb_rel_color.addItems(["#8E44AD", "#E74C3C", "#3498DB", "#2ECC71", "#F1C40F", "#E67E22", "#1ABC9C"])
        self.cb_rel_color.currentIndexChanged.connect(self.on_religion_details_changed)

        # Cultures Widgets
        self.cul_list = QListWidget()
        self.cul_list.currentRowChanged.connect(self.on_cul_list_selection)
        self.btn_add_cul = QPushButton("➕ Add Culture")
        self.btn_add_cul.clicked.connect(self.add_new_culture)
        self.txt_cul_name = QLineEdit()
        self.txt_cul_name.editingFinished.connect(self.on_culture_details_changed)
        self.txt_cul_lang = QLineEdit()
        self.txt_cul_lang.editingFinished.connect(self.on_culture_details_changed)
        self.cb_cul_color = QComboBox()
        self.cb_cul_color.addItems(["#E67E22", "#F1C40F", "#2ECC71", "#3498DB", "#9B59B6", "#1ABC9C", "#E74C3C"])
        self.cb_cul_color.currentIndexChanged.connect(self.on_culture_details_changed)
        self.spin_cul_exp = QDoubleSpinBox()
        self.spin_cul_exp.setRange(0.1, 10.0)
        self.spin_cul_exp.setValue(1.0)
        self.spin_cul_exp.valueChanged.connect(self.on_culture_details_changed)

        # Paragons Widgets
        self.lbl_paragon_sett = QLabel("No settlement selected")
        self.paragon_list = QListWidget()
        self.paragon_list.currentRowChanged.connect(self.on_paragon_list_selection)
        self.btn_add_par = QPushButton("➕ Add Paragon")
        self.btn_add_par.clicked.connect(self.add_new_paragon)
        self.btn_del_par = QPushButton("➖ Remove Paragon")
        self.btn_del_par.clicked.connect(self.delete_selected_paragon)
        self.txt_p_name = QLineEdit()
        self.txt_p_name.editingFinished.connect(self.on_paragon_form_changed)
        self.cb_p_archetype = QComboBox()
        self.cb_p_archetype.addItems(["Commander", "Merchant", "Mage", "Scholar", "Rogue"])
        self.cb_p_archetype.currentIndexChanged.connect(self.on_paragon_form_changed)
        self.spin_p_level = QSpinBox()
        self.spin_p_level.setRange(1, 100)
        self.spin_p_level.valueChanged.connect(self.on_paragon_form_changed)
        self.txt_p_motivation = QLineEdit()
        self.txt_p_motivation.editingFinished.connect(self.on_paragon_form_changed)
        self.txt_p_stats = QLineEdit()
        self.txt_p_stats.editingFinished.connect(self.on_paragon_form_changed)
        self.txt_p_traits = QLineEdit()
        self.txt_p_traits.editingFinished.connect(self.on_paragon_form_changed)
        self.plist_group = QGroupBox("Paragons List")
        self.plist_layout = QVBoxLayout(self.plist_group)
        self.plist_layout.addWidget(self.lbl_paragon_sett)
        self.plist_layout.addWidget(self.paragon_list)
        self.plist_layout.addWidget(self.btn_add_par)
        self.plist_layout.addWidget(self.btn_del_par)
        self.peditor_group = QGroupBox("Paragon Attributes")
        self.peditor_form = QFormLayout(self.peditor_group)
        self.peditor_form.addRow("Name:", self.txt_p_name)
        self.peditor_form.addRow("Archetype:", self.cb_p_archetype)
        self.peditor_form.addRow("Level:", self.spin_p_level)
        self.peditor_form.addRow("Motivation:", self.txt_p_motivation)
        self.peditor_form.addRow("Stats (JSON):", self.txt_p_stats)
        self.peditor_form.addRow("Traits (JSON):", self.txt_p_traits)

        # Forces/Entities Widgets
        self.entity_list = QListWidget()
        self.entity_list.currentRowChanged.connect(self.on_entity_list_selection)
        self.btn_add_ent = QPushButton("➕ Deploy Regiment")
        self.btn_add_ent.clicked.connect(self.add_new_entity)
        self.btn_del_ent = QPushButton("➖ Delete Regiment")
        self.btn_del_ent.clicked.connect(self.delete_selected_entity)
        self.cb_ent_type = QComboBox()
        self.cb_ent_type.addItems(["Regiment", "Cult Monster", "Null Zealots", "Chaos Creature", "Hurricane", "Chaos Storm"])
        self.cb_ent_type.currentIndexChanged.connect(self.on_entity_form_changed)
        self.spin_ent_q = QSpinBox()
        self.spin_ent_q.setRange(-100, 100)
        self.spin_ent_q.valueChanged.connect(self.on_entity_form_changed)
        self.spin_ent_r = QSpinBox()
        self.spin_ent_r.setRange(-100, 100)
        self.spin_ent_r.valueChanged.connect(self.on_entity_form_changed)
        self.btn_snap_coords = QPushButton("📍 Snap Selected Hex")
        self.btn_snap_coords.clicked.connect(self.snap_entity_to_selected_hex)
        self.spin_ent_mq = QSpinBox()
        self.spin_ent_mq.setRange(-5, 5)
        self.spin_ent_mq.valueChanged.connect(self.on_entity_form_changed)
        self.spin_ent_mr = QSpinBox()
        self.spin_ent_mr.setRange(-5, 5)
        self.spin_ent_mr.valueChanged.connect(self.on_entity_form_changed)
        self.spin_ent_radius = QSpinBox()
        self.spin_ent_radius.setRange(1, 100)
        self.spin_ent_radius.valueChanged.connect(self.on_entity_form_changed)
        self.spin_ent_duration = QSpinBox()
        self.spin_ent_duration.setRange(1, 1000)
        self.spin_ent_duration.valueChanged.connect(self.on_entity_form_changed)
        self.spin_ent_intensity = QDoubleSpinBox()
        self.spin_ent_intensity.setRange(0.1, 100.0)
        self.spin_ent_intensity.setValue(1.0)
        self.spin_ent_intensity.valueChanged.connect(self.on_entity_form_changed)
        self.cb_ent_align = QComboBox()
        self.cb_ent_align.currentIndexChanged.connect(self.on_entity_form_changed)

        # Trade Routes Widgets
        self.route_list = QListWidget()
        self.route_list.currentRowChanged.connect(self.on_route_list_selection)
        self.btn_add_rt = QPushButton("➕ Establish Route")
        self.btn_add_rt.clicked.connect(self.add_new_route)
        self.btn_del_rt = QPushButton("➖ Dissolve Route")
        self.btn_del_rt.clicked.connect(self.delete_selected_route)
        self.cb_rt_sett_a = QComboBox()
        self.cb_rt_sett_a.currentIndexChanged.connect(self.on_route_form_changed)
        self.cb_rt_sett_b = QComboBox()
        self.cb_rt_sett_b.currentIndexChanged.connect(self.on_route_form_changed)
        self.spin_rt_bandwidth = QSpinBox()
        self.spin_rt_bandwidth.setRange(1, 1000)
        self.spin_rt_bandwidth.setValue(10)
        self.spin_rt_bandwidth.valueChanged.connect(self.on_route_form_changed)
        self.cb_rt_type = QComboBox()
        self.cb_rt_type.addItems(["Land", "Sea", "Underground"])
        self.cb_rt_type.currentIndexChanged.connect(self.on_route_form_changed)
        self.cb_rt_faction = QComboBox()
        self.cb_rt_faction.currentIndexChanged.connect(self.on_route_form_changed)

        # Markers Widgets
        self.mark_list = QListWidget()
        self.mark_list.currentRowChanged.connect(self.on_mark_list_selection)
        self.btn_add_mark = QPushButton("➕ Place POI")
        self.btn_add_mark.clicked.connect(self.add_new_marker)
        self.btn_del_mark = QPushButton("➖ Delete POI")
        self.btn_del_mark.clicked.connect(self.delete_selected_marker)
        self.cb_mark_type = QComboBox()
        self.cb_mark_type.addItems(["Ruins", "Dungeon", "Cave", "Portal", "Obelisk"])
        self.cb_mark_type.currentIndexChanged.connect(self.on_marker_details_changed)
        self.txt_mark_desc = QLineEdit()
        self.txt_mark_desc.editingFinished.connect(self.on_marker_details_changed)
        self.spin_mark_q = QSpinBox()
        self.spin_mark_q.setRange(-100, 100)
        self.spin_mark_q.valueChanged.connect(self.on_marker_details_changed)
        self.spin_mark_r = QSpinBox()
        self.spin_mark_r.setRange(-100, 100)
        self.spin_mark_r.valueChanged.connect(self.on_marker_details_changed)
        self.btn_snap_mark = QPushButton("📍 Snap Selected Hex")
        self.btn_snap_mark.clicked.connect(self.snap_marker_to_selected_hex)

        # Set initial world state
        self.generate_new_world(seed=100, prompt=False)

    # ----------------------------------------------------
    # Launch Floating Editor Windows Methods
    # ----------------------------------------------------
    def open_cell_inspector(self):
        if not self.dialog_cell_inspector:
            self.dialog_cell_inspector = CellInspectorDialog(self)
        self.dialog_cell_inspector.show()
        self.dialog_cell_inspector.raise_()
        self.dialog_cell_inspector.activateWindow()

    def open_elevation_editor(self):
        if not self.dialog_elevation:
            self.dialog_elevation = ElevationEditorDialog(self)
        self.dialog_elevation.show()
        self.dialog_elevation.raise_()
        self.dialog_elevation.activateWindow()

    def open_biomes_editor(self):
        if not self.dialog_biomes:
            self.dialog_biomes = BiomesEditorDialog(self)
        self.dialog_biomes.show()
        self.dialog_biomes.raise_()
        self.dialog_biomes.activateWindow()

    def open_factions_editor(self):
        if not self.dialog_factions:
            self.dialog_factions = FactionsEditorDialog(self)
        self.dialog_factions.show()
        self.dialog_factions.raise_()
        self.dialog_factions.activateWindow()

    def open_provinces_editor(self):
        if not self.dialog_provinces:
            self.dialog_provinces = ProvincesEditorDialog(self)
        self.dialog_provinces.show()
        self.dialog_provinces.raise_()
        self.dialog_provinces.activateWindow()

    def open_religions_editor(self):
        if not self.dialog_religions:
            self.dialog_religions = ReligionsEditorDialog(self)
        self.dialog_religions.show()
        self.dialog_religions.raise_()
        self.dialog_religions.activateWindow()

    def open_cultures_editor(self):
        if not self.dialog_cultures:
            self.dialog_cultures = CulturesEditorDialog(self)
        self.dialog_cultures.show()
        self.dialog_cultures.raise_()
        self.dialog_cultures.activateWindow()

    def open_climate_editor(self):
        if not self.dialog_climate:
            self.dialog_climate = ClimateEditorDialog(self)
        self.dialog_climate.show()
        self.dialog_climate.raise_()
        self.dialog_climate.activateWindow()

    def open_rivers_editor(self):
        if not self.dialog_rivers:
            self.dialog_rivers = RiversEditorDialog(self)
        self.dialog_rivers.show()
        self.dialog_rivers.raise_()
        self.dialog_rivers.activateWindow()

    def open_chaos_editor(self):
        if not self.dialog_chaos:
            self.dialog_chaos = ChaosEditorDialog(self)
        self.dialog_chaos.show()
        self.dialog_chaos.raise_()
        self.dialog_chaos.activateWindow()

    def open_settlements_directory(self):
        if not self.dialog_settlements:
            self.dialog_settlements = SettlementsEditorDialog(self)
        self.update_settlements_directory_ui()
        self.dialog_settlements.show()
        self.dialog_settlements.raise_()
        self.dialog_settlements.activateWindow()

    def open_names_editor(self):
        if not self.dialog_names:
            self.dialog_names = NameStyleEditorDialog(self)
        self.update_culture_names_ui()
        self.dialog_names.show()
        self.dialog_names.raise_()
        self.dialog_names.activateWindow()

    def open_markers_editor(self):
        if not self.dialog_markers:
            self.dialog_markers = MarkersEditorDialog(self)
        self.dialog_markers.show()
        self.dialog_markers.raise_()
        self.dialog_markers.activateWindow()

    def open_forces_editor(self):
        if not self.dialog_forces:
            self.dialog_forces = ForcesEditorDialog(self)
        self.dialog_forces.show()
        self.dialog_forces.raise_()
        self.dialog_forces.activateWindow()

    def open_routes_editor(self):
        if not self.dialog_routes:
            self.dialog_routes = RoutesEditorDialog(self)
        self.dialog_routes.show()
        self.dialog_routes.raise_()
        self.dialog_routes.activateWindow()

    def open_trait_pool_editor(self):
        if not self.dialog_trait_pool:
            self.dialog_trait_pool = TraitPoolEditorDialog(self)
        self.update_trait_pool_ui()
        self.dialog_trait_pool.show()
        self.dialog_trait_pool.raise_()
        self.dialog_trait_pool.activateWindow()

    def open_economy_editor(self):
        if not self.dialog_economy:
            self.dialog_economy = EconomyEditorDialog(self)
        self.update_economy_ui()
        self.dialog_economy.show()
        self.dialog_economy.raise_()
        self.dialog_economy.activateWindow()

    # --- NEW SIMULATION TOOLS HELPERS ---
    
    def import_heightmap_image(self):
        from PyQt6.QtGui import QImage, QColor
        path, _ = QFileDialog.getOpenFileName(self, "Import Heightmap Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if not path:
            return
        
        image = QImage()
        if not image.load(path):
            QMessageBox.critical(self, "Error", "Failed to load image file.")
            return
            
        coords = list(self.state.hexes.keys())
        if not coords:
            return
            
        from python_fmg.core.grid import hex_to_pixel, is_in_20_triangle_net
        xs = []
        ys = []
        for q, r in coords:
            x, y = hex_to_pixel(q, r)
            xs.append(x)
            ys.append(y)
            
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        range_x = max_x - min_x if max_x != min_x else 1.0
        range_y = max_y - min_y if max_y != min_y else 1.0
        
        img_w = image.width()
        img_h = image.height()
        
        R = 0
        for q, r in coords:
            R = max(R, abs(q), abs(r), abs(q + r))
            
        for (q, r), hx in self.state.hexes.items():
            if not is_in_20_triangle_net(q, r, R):
                hx.elevation = 0
                hx.biome = 12  # Abyssal Trench
                continue
                
            x, y = hex_to_pixel(q, r)
            u = (x - min_x) / range_x
            v = (y - min_y) / range_y
            
            px = max(0, min(img_w - 1, int(u * (img_w - 1))))
            py = max(0, min(img_h - 1, int(v * (img_h - 1))))
            
            color = QColor(image.pixel(px, py))
            brightness = (color.red() + color.green() + color.blue()) / 3.0
            
            scaled_elev = int((brightness / 255.0) * 15)
            hx.elevation = scaled_elev
            
            if scaled_elev <= 0:
                hx.biome = 9  # Kelp Forest
            elif scaled_elev > 10:
                hx.biome = 6  # Mountain
            else:
                hx.biome = 4  # Plains
                
        self.map_viewer.load_map(self.state)
        self.statusBar().showMessage("Successfully imported heightmap image and conformed to 20-triangle layout.", 3000)
    
    def update_trait_pool_ui(self):
        if not self.dialog_trait_pool: return
        self.dialog_trait_pool.table_traits.blockSignals(True)
        self.dialog_trait_pool.table_traits.setRowCount(0)
        self.dialog_trait_pool.table_traits.setRowCount(len(self.state.trait_pool))
        for row, trait in enumerate(self.state.trait_pool):
            self.dialog_trait_pool.table_traits.setItem(row, 0, QTableWidgetItem(trait.name))
            self.dialog_trait_pool.table_traits.setItem(row, 1, QTableWidgetItem(trait.type))
            self.dialog_trait_pool.table_traits.setItem(row, 2, QTableWidgetItem(trait.effect))
        self.dialog_trait_pool.table_traits.blockSignals(False)
        self.update_paragons_list()

    def add_new_pool_trait(self):
        name, ok = QInputDialog.getText(self, "New Trait", "Enter trait name:")
        if ok and name:
            from python_fmg.core.models import Trait
            self.state.trait_pool.append(Trait(name=name, type="Magic", effect="None"))
            self.update_trait_pool_ui()

    def delete_pool_trait(self):
        if not self.dialog_trait_pool: return
        row = self.dialog_trait_pool.table_traits.currentRow()
        if row >= 0 and row < len(self.state.trait_pool):
            del self.state.trait_pool[row]
            self.update_trait_pool_ui()

    def on_trait_pool_table_changed(self, row, col):
        if not self.dialog_trait_pool: return
        if row >= len(self.state.trait_pool): return
        trait = self.state.trait_pool[row]
        name_item = self.dialog_trait_pool.table_traits.item(row, 0)
        type_item = self.dialog_trait_pool.table_traits.item(row, 1)
        eff_item = self.dialog_trait_pool.table_traits.item(row, 2)
        if name_item: trait.name = name_item.text()
        if type_item: trait.type = type_item.text()
        if eff_item: trait.effect = eff_item.text()

    def add_faction_species(self):
        if self.selected_faction_id is None: return
        f = self.state.factions[self.selected_faction_id]
        name, ok = QInputDialog.getText(self, "Add Species", "Enter species name:")
        if ok and name:
            pop = f.species_population
            pop[name] = 0.0
            f.species_population = pop
            self.update_factions_ui()
            self.on_faction_list_selection(self.faction_list.currentRow())

    def remove_faction_species(self):
        if self.selected_faction_id is None: return
        f = self.state.factions[self.selected_faction_id]
        if not self.dialog_factions: return
        row = self.dialog_factions.species_list.currentRow()
        if row >= 0:
            spec_names = list(f.species_population.keys())
            if row < len(spec_names):
                pop = f.species_population
                del pop[spec_names[row]]
                f.species_population = pop
                self.update_factions_ui()
                self.on_faction_list_selection(self.faction_list.currentRow())

    def on_faction_attunement_changed(self, item):
        if self.selected_faction_id is None: return
        f = self.state.factions[self.selected_faction_id]
        checked_list = []
        if self.dialog_factions:
            for r in range(self.dialog_factions.att_list.count()):
                it = self.dialog_factions.att_list.item(r)
                if it.checkState() == Qt.CheckState.Checked:
                    checked_list.append(it.text())
        f.sparkborn_attunement = checked_list

    def update_paragons_list(self):
        self.state.provinces.clear()
        if self.dialog_provinces:
            self.dialog_provinces.paragon_list.blockSignals(True)
            self.dialog_provinces.paragon_list.clear()
            self.dialog_provinces.cb_faction.blockSignals(True)
            self.dialog_provinces.cb_faction.clear()
            for f_id, f in self.state.factions.items():
                self.dialog_provinces.cb_faction.addItem(f.name, f_id)
            self.dialog_provinces.cb_faction.blockSignals(False)

        paragons_found = []
        for hx in self.state.hexes.values():
            if hx.settlement:
                for p in hx.settlement.paragons:
                    p.id = p.id or (len(paragons_found) + 1)
                    paragons_found.append(p)
                    from python_fmg.core.models import Province
                    self.state.provinces[p.id] = Province(id=p.id, name=p.name, faction_id=p.faction_id, color=p.color)
                    
        if self.dialog_provinces:
            for p in paragons_found:
                self.dialog_provinces.paragon_list.addItem(f"{p.name} (Lvl {p.level} {p.archetype})")
            self.dialog_provinces.paragon_list.blockSignals(False)

    def on_paragon_list_selection(self, row):
        if row < 0: return
        paragons = []
        for hx in self.state.hexes.values():
            if hx.settlement:
                paragons.extend(hx.settlement.paragons)
        if row >= len(paragons): return
        p = paragons[row]
        self.selected_paragon_idx = row
        
        if self.dialog_provinces:
            self.dialog_provinces.txt_name.blockSignals(True)
            self.dialog_provinces.cb_faction.blockSignals(True)
            self.dialog_provinces.cb_archetype.blockSignals(True)
            self.dialog_provinces.spin_level.blockSignals(True)
            self.dialog_provinces.txt_motivation.blockSignals(True)
            
            self.dialog_provinces.txt_name.setText(p.name)
            idx = self.dialog_provinces.cb_faction.findData(p.faction_id)
            if idx >= 0: self.dialog_provinces.cb_faction.setCurrentIndex(idx)
            self.dialog_provinces.cb_archetype.setCurrentText(p.archetype)
            self.dialog_provinces.spin_level.setValue(p.level)
            self.dialog_provinces.txt_motivation.setText(p.motivation)
            
            stats = p.stats
            for stat, slider in self.dialog_provinces.stat_sliders.items():
                slider.blockSignals(True)
                slider.setValue(stats.get(stat, 10))
                slider.blockSignals(False)
                
            self.dialog_provinces.traits_list.blockSignals(True)
            self.dialog_provinces.traits_list.clear()
            p_traits = p.traits
            for tr in self.state.trait_pool:
                item = QListWidgetItem(tr.name)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked if tr.name in p_traits else Qt.CheckState.Unchecked)
                self.dialog_provinces.traits_list.addItem(item)
            self.dialog_provinces.traits_list.blockSignals(False)
            
            self.dialog_provinces.txt_name.blockSignals(False)
            self.dialog_provinces.cb_faction.blockSignals(False)
            self.dialog_provinces.cb_archetype.blockSignals(False)
            self.dialog_provinces.spin_level.blockSignals(False)
            self.dialog_provinces.txt_motivation.blockSignals(False)

        self.selected_province_id = p.id
        self.update_active_brush_mode()

    def add_new_paragon(self):
        settlements = [hx.settlement for hx in self.state.hexes.values() if hx.settlement]
        if not settlements:
            QMessageBox.warning(self, "No Settlements", "Please create a settlement first to host the Paragon.")
            return
        name, ok = QInputDialog.getText(self, "New Paragon", "Enter paragon name:")
        if ok and name:
            from python_fmg.core.models import Paragon
            p = Paragon(name=name, faction_id=1, color="#2ECC71")
            settlements[0].paragons.append(p)
            self.update_paragons_list()
            if self.dialog_provinces:
                self.dialog_provinces.paragon_list.setCurrentRow(self.dialog_provinces.paragon_list.count() - 1)

    def delete_selected_paragon(self):
        if self.selected_paragon_idx is None: return
        paragons = []
        for hx in self.state.hexes.values():
            if hx.settlement:
                for idx, p in enumerate(hx.settlement.paragons):
                    paragons.append((hx.settlement, idx, p))
        if self.selected_paragon_idx < len(paragons):
            sett, s_idx, p = paragons[self.selected_paragon_idx]
            del sett.paragons[s_idx]
            self.selected_paragon_idx = None
            self.update_paragons_list()

    def on_paragon_details_changed(self):
        if self.selected_paragon_idx is None: return
        paragons = []
        for hx in self.state.hexes.values():
            if hx.settlement:
                paragons.extend(hx.settlement.paragons)
        if self.selected_paragon_idx >= len(paragons): return
        p = paragons[self.selected_paragon_idx]
        
        if self.dialog_provinces:
            p.name = self.dialog_provinces.txt_name.text()
            p.faction_id = self.dialog_provinces.cb_faction.currentData() or 1
            p.archetype = self.dialog_provinces.cb_archetype.currentText()
            p.level = self.dialog_provinces.spin_level.value()
            p.motivation = self.dialog_provinces.txt_motivation.text()
            
            stats = {}
            for stat, slider in self.dialog_provinces.stat_sliders.items():
                stats[stat] = slider.value()
            p.stats = stats
            
            if p.id in self.state.provinces:
                self.state.provinces[p.id].name = p.name
                self.state.provinces[p.id].faction_id = p.faction_id
            
            self.update_paragons_list()

    def on_paragon_traits_changed(self, item):
        if self.selected_paragon_idx is None: return
        paragons = []
        for hx in self.state.hexes.values():
            if hx.settlement:
                paragons.extend(hx.settlement.paragons)
        if self.selected_paragon_idx >= len(paragons): return
        p = paragons[self.selected_paragon_idx]
        
        checked = []
        if self.dialog_provinces:
            for r in range(self.dialog_provinces.traits_list.count()):
                it = self.dialog_provinces.traits_list.item(r)
                if it.checkState() == Qt.CheckState.Checked:
                    checked.append(it.text())
        p.traits = checked

    def update_chaos_paths_ui(self):
        if not self.dialog_religions: return
        self.dialog_religions.list_paths.blockSignals(True)
        self.dialog_religions.list_paths.clear()
        
        from python_fmg.core.models import Religion
        for i in range(1, 14):
            if i not in self.state.religions:
                name = f"Chaos Path {i}" if i < 13 else "Convergence Point"
                color = "#9b59b6" if i < 13 else "#e74c3c"
                self.state.religions[i] = Religion(id=i, name=name, color=color)
                
        for i in range(1, 14):
            rel = self.state.religions[i]
            status = " (Prison Active)" if rel.is_prison else ""
            item = QListWidgetItem(f"{rel.name}{status}")
            item.setIcon(create_color_icon(rel.color))
            self.dialog_religions.list_paths.addItem(item)
        self.dialog_religions.list_paths.blockSignals(False)

    def on_chaos_path_selection(self, row):
        if row < 0: return
        self.selected_religion_id = row + 1
        rel = self.state.religions[self.selected_religion_id]
        if self.dialog_religions:
            self.dialog_religions.chk_prison.blockSignals(True)
            self.dialog_religions.chk_prison.setChecked(rel.is_prison)
            self.dialog_religions.chk_prison.blockSignals(False)
        self.update_active_brush_mode()

    def on_chaos_prison_toggled(self, checked):
        if self.selected_religion_id is None: return
        rel = self.state.religions[self.selected_religion_id]
        rel.is_prison = checked
        self.update_chaos_paths_ui()

    def update_fringe_groups_ui(self):
        if not self.dialog_cultures: return
        self.dialog_cultures.list_groups.blockSignals(True)
        self.dialog_cultures.list_groups.clear()
        for idx, (c_id, cul) in enumerate(self.state.cultures.items()):
            item = QListWidgetItem(f"{cul.name} ({cul.language_base})")
            item.setIcon(create_color_icon(cul.color))
            self.dialog_cultures.list_groups.addItem(item)
        self.dialog_cultures.list_groups.blockSignals(False)

    def add_fringe_group(self):
        name, ok = QInputDialog.getText(self, "New Fringe Group", "Enter name:")
        if ok and name:
            from python_fmg.core.models import Culture
            new_id = max(list(self.state.cultures.keys()) + [0]) + 1
            self.state.cultures[new_id] = Culture(id=new_id, name=name, language_base="Cartel")
            self.update_fringe_groups_ui()
            if self.dialog_cultures:
                self.dialog_cultures.list_groups.setCurrentRow(self.dialog_cultures.list_groups.count() - 1)

    def delete_fringe_group(self):
        if not self.dialog_cultures: return
        row = self.dialog_cultures.list_groups.currentRow()
        c_ids = list(self.state.cultures.keys())
        if row >= 0 and row < len(c_ids):
            del self.state.cultures[c_ids[row]]
            self.update_fringe_groups_ui()

    def on_fringe_group_selection(self, row):
        if row < 0: return
        c_ids = list(self.state.cultures.keys())
        self.selected_culture_id = c_ids[row]
        cul = self.state.cultures[self.selected_culture_id]
        if self.dialog_cultures:
            self.dialog_cultures.txt_name.blockSignals(True)
            self.dialog_cultures.cb_type.blockSignals(True)
            self.dialog_cultures.txt_name.setText(cul.name)
            self.dialog_cultures.cb_type.setCurrentText(cul.language_base)
            self.dialog_cultures.txt_name.blockSignals(False)
            self.dialog_cultures.cb_type.blockSignals(False)
        self.update_active_brush_mode()

    def on_fringe_group_changed(self):
        if self.selected_culture_id is None: return
        cul = self.state.cultures[self.selected_culture_id]
        if self.dialog_cultures:
            cul.name = self.dialog_cultures.txt_name.text()
            cul.language_base = self.dialog_cultures.cb_type.currentText()
            self.update_fringe_groups_ui()

    def on_settlement_buildings_changed(self, item):
        pass

    def add_settlement_building(self):
        if self.selected_directory_settlement_id is None: return
        for hx in self.state.hexes.values():
            if hx.settlement and hx.settlement.id == self.selected_directory_settlement_id:
                s = hx.settlement
                try:
                    b_data = json.loads(s.inventory_json)
                except Exception:
                    b_data = {}
                b_type, ok = QInputDialog.getItem(self, "Building", "Type:", ["Farm", "Mine", "Barracks", "Granary"], 0, False)
                if ok:
                    b_data[b_type] = b_data.get(b_type, 0) + 1
                    s.inventory_json = json.dumps(b_data)
                    self.on_settlement_directory_selection(self.dialog_settlements.list_settlements.currentRow())

    def delete_settlement_building(self):
        if self.selected_directory_settlement_id is None: return
        for hx in self.state.hexes.values():
            if hx.settlement and hx.settlement.id == self.selected_directory_settlement_id:
                s = hx.settlement
                try:
                    b_data = json.loads(s.inventory_json)
                except Exception:
                    b_data = {}
                row = self.dialog_settlements.table_buildings.currentRow()
                if row >= 0:
                    b_types = list(b_data.keys())
                    if row < len(b_types):
                        del b_data[b_types[row]]
                        s.inventory_json = json.dumps(b_data)
                        self.on_settlement_directory_selection(self.dialog_settlements.list_settlements.currentRow())

    def on_calendar_changed(self):
        if not self.dialog_names: return
        text = self.dialog_names.txt_week_days.text()
        self.state.calendar_week_names = [d.strip() for d in text.split(",") if d.strip()]

    def on_calendar_months_changed(self, item):
        if not self.dialog_names: return
        row = item.row()
        col = item.column()
        if row >= len(self.state.calendar_months): return
        month = self.state.calendar_months[row]
        if col == 0:
            month["name"] = item.text()
        elif col == 1:
            try:
                month["weeks"] = int(item.text())
            except ValueError:
                item.setText(str(month["weeks"]))

    def add_calendar_month(self):
        name, ok = QInputDialog.getText(self, "New Month", "Name:")
        if ok and name:
            self.state.calendar_months.append({"name": name, "weeks": 4})
            self.update_calendar_ui()

    def delete_calendar_month(self):
        if not self.dialog_names: return
        row = self.dialog_names.table_months.currentRow()
        if row >= 0 and row < len(self.state.calendar_months):
            del self.state.calendar_months[row]
            self.update_calendar_ui()

    def on_calendar_seasons_changed(self, item):
        if not self.dialog_names: return
        row = item.row()
        col = item.column()
        if row >= len(self.state.calendar_seasons): return
        season = self.state.calendar_seasons[row]
        if col == 0:
            season["name"] = item.text()
        elif col == 1:
            season["months"] = [m.strip() for m in item.text().split(",") if m.strip()]
        elif col == 2:
            try:
                season["temp_adjust"] = float(item.text())
            except ValueError:
                item.setText(str(season["temp_adjust"]))
        elif col == 3:
            try:
                season["precip"] = float(item.text())
            except ValueError:
                item.setText(str(season["precip"]))

    def add_calendar_season(self):
        name, ok = QInputDialog.getText(self, "New Season", "Name:")
        if ok and name:
            self.state.calendar_seasons.append({"name": name, "months": [], "temp_adjust": 0.0, "precip": 50.0})
            self.update_calendar_ui()

    def delete_calendar_season(self):
        if not self.dialog_names: return
        row = self.dialog_names.table_seasons.currentRow()
        if row >= 0 and row < len(self.state.calendar_seasons):
            del self.state.calendar_seasons[row]
            self.update_calendar_ui()

    def update_calendar_ui(self):
        if not self.dialog_names: return
        self.dialog_names.txt_week_days.blockSignals(True)
        self.dialog_names.txt_week_days.setText(", ".join(self.state.calendar_week_names))
        self.dialog_names.txt_week_days.blockSignals(False)

        self.dialog_names.table_months.blockSignals(True)
        self.dialog_names.table_months.setRowCount(0)
        self.dialog_names.table_months.setRowCount(len(self.state.calendar_months))
        for row, month in enumerate(self.state.calendar_months):
            self.dialog_names.table_months.setItem(row, 0, QTableWidgetItem(month["name"]))
            self.dialog_names.table_months.setItem(row, 1, QTableWidgetItem(str(month["weeks"])))
        self.dialog_names.table_months.blockSignals(False)

        self.dialog_names.table_seasons.blockSignals(True)
        self.dialog_names.table_seasons.setRowCount(0)
        self.dialog_names.table_seasons.setRowCount(len(self.state.calendar_seasons))
        for row, season in enumerate(self.state.calendar_seasons):
            self.dialog_names.table_seasons.setItem(row, 0, QTableWidgetItem(season["name"]))
            self.dialog_names.table_seasons.setItem(row, 1, QTableWidgetItem(", ".join(season["months"])))
            self.dialog_names.table_seasons.setItem(row, 2, QTableWidgetItem(str(season["temp_adjust"])))
            self.dialog_names.table_seasons.setItem(row, 3, QTableWidgetItem(str(season["precip"])))
        self.dialog_names.table_seasons.blockSignals(False)

    def update_economy_ui(self):
        if not self.dialog_economy: return
        self.dialog_economy.table_res.blockSignals(True)
        self.dialog_economy.table_res.setRowCount(0)
        self.dialog_economy.table_res.setRowCount(len(self.state.base_resources))
        for row, res in enumerate(self.state.base_resources):
            self.dialog_economy.table_res.setItem(row, 0, QTableWidgetItem(res["name"]))
            self.dialog_economy.table_res.setItem(row, 1, QTableWidgetItem(str(res["value"])))
            biomes_str = ", ".join(map(str, res.get("source_biomes", [])))
            self.dialog_economy.table_res.setItem(row, 2, QTableWidgetItem(biomes_str))
        self.dialog_economy.table_res.blockSignals(False)

        if self.dialog_markers:
            self.dialog_markers.cb_res_type.blockSignals(True)
            self.dialog_markers.cb_res_type.clear()
            for res in self.state.base_resources:
                self.dialog_markers.cb_res_type.addItem(res["name"])
            self.dialog_markers.cb_res_type.blockSignals(False)

        self.dialog_economy.table_goods.blockSignals(True)
        self.dialog_economy.table_goods.setRowCount(0)
        all_goods = [{"name": g["name"], "cost": g["cost"], "effect": g["effect"], "type": "Refined"} for g in self.state.refined_goods] +                     [{"name": g["name"], "cost": g["cost"], "effect": g["effect"], "type": "Luxury"} for g in self.state.luxury_goods]
        self.dialog_economy.table_goods.setRowCount(len(all_goods))
        for row, g in enumerate(all_goods):
            self.dialog_economy.table_goods.setItem(row, 0, QTableWidgetItem(g["name"]))
            self.dialog_economy.table_goods.setItem(row, 1, QTableWidgetItem(str(g["cost"])))
            self.dialog_economy.table_goods.setItem(row, 2, QTableWidgetItem(g["effect"]))
            self.dialog_economy.table_goods.setItem(row, 3, QTableWidgetItem(g["type"]))
        self.dialog_economy.table_goods.blockSignals(False)

        self.dialog_economy.table_build.blockSignals(True)
        self.dialog_economy.table_build.setRowCount(0)
        self.dialog_economy.table_build.setRowCount(len(self.state.building_costs))
        for row, (b_type, cost_dict) in enumerate(self.state.building_costs.items()):
            self.dialog_economy.table_build.setItem(row, 0, QTableWidgetItem(b_type))
            self.dialog_economy.table_build.setItem(row, 1, QTableWidgetItem(json.dumps(cost_dict)))
        self.dialog_economy.table_build.blockSignals(False)

    def on_econ_res_changed(self, item):
        if not self.dialog_economy: return
        row = item.row()
        col = item.column()
        if row >= len(self.state.base_resources): return
        res = self.state.base_resources[row]
        if col == 0:
            res["name"] = item.text()
        elif col == 1:
            try:
                res["value"] = float(item.text())
            except ValueError:
                item.setText(str(res["value"]))
        elif col == 2:
            try:
                res["source_biomes"] = [int(i.strip()) for i in item.text().split(",") if i.strip()]
            except ValueError:
                pass

    def add_econ_res(self):
        self.state.base_resources.append({"name": "New Resource", "value": 10, "source_biomes": []})
        self.update_economy_ui()

    def delete_econ_res(self):
        if not self.dialog_economy: return
        row = self.dialog_economy.table_res.currentRow()
        if row >= 0 and row < len(self.state.base_resources):
            del self.state.base_resources[row]
            self.update_economy_ui()

    def on_econ_goods_changed(self, item):
        if not self.dialog_economy: return
        row = item.row()
        col = item.column()
        all_goods = self.state.refined_goods + self.state.luxury_goods
        if row >= len(all_goods): return
        good = all_goods[row]
        if col == 0:
            good["name"] = item.text()
        elif col == 1:
            try:
                good["cost"] = float(item.text())
            except ValueError:
                item.setText(str(good["cost"]))
        elif col == 2:
            good["effect"] = item.text()

    def add_econ_good(self):
        self.state.refined_goods.append({"name": "New Good", "cost": 50, "effect": "None"})
        self.update_economy_ui()

    def delete_econ_good(self):
        if not self.dialog_economy: return
        row = self.dialog_economy.table_goods.currentRow()
        all_goods = self.state.refined_goods + self.state.luxury_goods
        if row >= 0 and row < len(all_goods):
            if row < len(self.state.refined_goods):
                del self.state.refined_goods[row]
            else:
                del self.state.luxury_goods[row - len(self.state.refined_goods)]
            self.update_economy_ui()

    def on_econ_build_changed(self, item):
        if not self.dialog_economy: return
        row = item.row()
        col = item.column()
        b_types = list(self.state.building_costs.keys())
        if row >= len(b_types): return
        b_type = b_types[row]
        if col == 1:
            try:
                self.state.building_costs[b_type] = json.loads(item.text())
            except Exception:
                item.setText(json.dumps(self.state.building_costs[b_type]))

    def add_econ_build_type(self):
        name, ok = QInputDialog.getText(self, "New Building Type", "Name:")
        if ok and name:
            self.state.building_costs[name] = {"Gold": 100}
            self.update_economy_ui()

    def delete_econ_build_type(self):
        if not self.dialog_economy: return
        row = self.dialog_economy.table_build.currentRow()
        b_types = list(self.state.building_costs.keys())
        if row >= 0 and row < len(b_types):
            del self.state.building_costs[b_types[row]]
            self.update_economy_ui()

    def regenerate_rivers_simulation(self):
        from python_fmg.core.generators import generate_world
        existing_coords = list(self.state.hexes.keys()) if (self.state and self.state.hexes) else None
        new_state = generate_world(R=110, elevation_seed=random.randint(1, 9999), coords_list=existing_coords)
        for coord, hx in self.state.hexes.items():
            if coord in new_state.hexes:
                hx.river_volume = new_state.hexes[coord].river_volume
                hx.is_lake = new_state.hexes[coord].is_lake
        self.map_viewer.load_map(self.state)
        self.statusBar().showMessage("Successfully rerouted all river volumes and lakes across map.", 3000)

    def regenerate_roads_simulation(self):
        self.state.routes.clear()
        settlements = []
        for hx in self.state.hexes.values():
            if hx.settlement:
                settlements.append(hx.settlement)
        from python_fmg.core.models import TradeRoute
        for i in range(len(settlements)):
            for j in range(i + 1, len(settlements)):
                self.state.routes.append(TradeRoute(
                    faction_id=settlements[i].faction_id,
                    settlement_a_id=settlements[i].id,
                    settlement_b_id=settlements[j].id,
                    bandwidth=25,
                    route_type="Land"
                ))
        self.update_routes_ui()
        self.map_viewer.load_map(self.state)
        self.statusBar().showMessage("Successfully regenerated connecting trade routes link structures.", 3000)


    def on_view_layer_changed(self):
        self.map_viewer.set_render_mode(self.cb_view_layer.currentText())

    def clear_all_brushes_except(self, active_button):
        all_dialogs = [
            self.dialog_elevation,
            self.dialog_biomes,
            self.dialog_factions,
            self.dialog_provinces,
            self.dialog_religions,
            self.dialog_cultures,
            self.dialog_markers,
            self.dialog_forces,
            self.dialog_routes,
            self.dialog_climate,
            self.dialog_rivers,
            self.dialog_chaos
        ]
        for d in all_dialogs:
            if d:
                d.uncheck_paint_button()
                
        # Settlement button sits on main hex inspector
        if active_button != self.btn_paint_settlement:
            self.btn_paint_settlement.blockSignals(True)
            self.btn_paint_settlement.setChecked(False)
            self.btn_paint_settlement.setStyleSheet("")
            self.btn_paint_settlement.blockSignals(False)

        # Highlight active checked button
        if active_button and active_button.isChecked():
            active_button.setStyleSheet("background-color: #04D361; color: #121214;")
        elif active_button:
            active_button.setStyleSheet("")

    def on_brush_toggled(self, checked):
        sender = self.sender()
        if checked:
            self.clear_all_brushes_except(sender)
            self.update_active_brush_mode()
        else:
            if sender:
                sender.setStyleSheet("")
            self.map_viewer.set_tool_mode("Select")

    def on_brush_radius_changed(self, val):
        self.brush_radius_val = val
        self.map_viewer.brush_radius = val
        for dialog in [self.dialog_elevation, self.dialog_biomes, self.dialog_factions, 
                       self.dialog_provinces, self.dialog_religions, self.dialog_cultures,
                       self.dialog_climate, self.dialog_rivers, self.dialog_chaos]:
            if dialog and hasattr(dialog, 'slider_radius'):
                dialog.slider_radius.blockSignals(True)
                dialog.slider_radius.setValue(val)
                dialog.slider_radius.blockSignals(False)

    def on_elevation_mode_changed(self, mode):
        self.map_viewer.elevation_brush_mode = mode

    def on_brush_power_changed(self, val):
        self.map_viewer.brush_power = val

    def update_active_brush_mode(self):
        self.map_viewer.brush_radius = self.brush_radius_val
        
        # Pull slider values if dialogs exist to maintain reactive updates
        temp_val = self.dialog_climate.slider_temp.value() if self.dialog_climate else 128
        moist_val = self.dialog_climate.slider_moist.value() if self.dialog_climate else 128
        river_val = self.dialog_rivers.slider_river.value() if self.dialog_rivers else 10
        
        if self.dialog_elevation and self.dialog_elevation.btn_paint.isChecked():
            self.map_viewer.set_tool_mode("Paint Elevation", self.spin_elev_brush.value())
        elif self.dialog_biomes and self.dialog_biomes.btn_paint.isChecked():
            row = self.dialog_biomes.biome_list_brush.currentRow()
            val = row if row >= 0 else 0
            self.map_viewer.set_tool_mode("Paint Biome", val)
        elif self.dialog_factions and self.dialog_factions.btn_paint.isChecked():
            val = self.selected_faction_id if self.selected_faction_id is not None else 0
            self.map_viewer.set_tool_mode("Paint Faction", val)
        elif self.dialog_provinces and self.dialog_provinces.btn_paint.isChecked():
            val = self.selected_province_id if self.selected_province_id is not None else 0
            self.map_viewer.set_tool_mode("Paint Province", val)
        elif self.dialog_religions and self.dialog_religions.btn_paint.isChecked():
            val = self.selected_religion_id if self.selected_religion_id is not None else 0
            self.map_viewer.set_tool_mode("Paint Religion", val)
        elif self.dialog_cultures and self.dialog_cultures.btn_paint.isChecked():
            val = self.selected_culture_id if self.selected_culture_id is not None else 0
            self.map_viewer.set_tool_mode("Paint Culture", val)
        elif self.dialog_markers and self.dialog_markers.btn_paint.isChecked():
            self.map_viewer.set_tool_mode("Place Marker")
        elif self.dialog_forces and self.dialog_forces.btn_paint.isChecked():
            self.map_viewer.set_tool_mode("Place Force")
        elif self.dialog_routes and self.dialog_routes.btn_paint.isChecked():
            self.map_viewer.set_tool_mode("Link Route")
            self.route_start_sett_id = None
        elif self.btn_paint_settlement.isChecked():
            self.map_viewer.set_tool_mode("Place Settlement")
        elif self.dialog_climate and self.dialog_climate.btn_paint_temp.isChecked():
            self.map_viewer.set_tool_mode("Paint Temperature", temp_val)
        elif self.dialog_climate and self.dialog_climate.btn_paint_moist.isChecked():
            self.map_viewer.set_tool_mode("Paint Moisture", moist_val)
        elif self.dialog_rivers and self.dialog_rivers.btn_paint_river.isChecked():
            self.map_viewer.set_tool_mode("Paint River Volume", river_val)
        elif self.dialog_rivers and self.dialog_rivers.btn_toggle_lake.isChecked():
            self.map_viewer.set_tool_mode("Toggle Lake", int(self.chk_lake_brush.isChecked()))
        elif self.dialog_chaos and self.dialog_chaos.btn_paint.isChecked():
            row = self.dialog_chaos.chaos_list_brush.currentRow()
            dom = CHAOS_DOMAINS[row] if (row >= 0 and row < len(CHAOS_DOMAINS)) else "None"
            self.map_viewer.set_tool_mode("Paint Chaos", dom)
        else:
            self.map_viewer.set_tool_mode("Select")

    # --- INDIVIDUAL LAYER SAVE/LOAD STATE METHODS ---
    def save_elevation_layer(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Elevation Layer JSON", "", "JSON Files (*.json)")
        if path:
            data = {"elevation": {f"{q},{r}": hx.elevation for (q, r), hx in self.state.hexes.items()}}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.statusBar().showMessage(f"Saved Elevation layer to {os.path.basename(path)}", 3000)

    def load_elevation_layer(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Elevation Layer JSON", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                elev_map = data.get("elevation", {})
                for (q, r), hx in self.state.hexes.items():
                    key = f"{q},{r}"
                    if key in elev_map:
                        hx.elevation = int(elev_map[key])
                self.map_viewer.load_map(self.state)
                self.statusBar().showMessage(f"Loaded Elevation layer from {os.path.basename(path)}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load Elevation layer:\n{e}")

    def save_biomes_layer(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Biomes Layer JSON", "", "JSON Files (*.json)")
        if path:
            data = {"biomes": {f"{q},{r}": hx.biome for (q, r), hx in self.state.hexes.items()}}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.statusBar().showMessage(f"Saved Biomes layer to {os.path.basename(path)}", 3000)

    def load_biomes_layer(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Biomes Layer JSON", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                biomes_map = data.get("biomes", {})
                for (q, r), hx in self.state.hexes.items():
                    key = f"{q},{r}"
                    if key in biomes_map:
                        hx.biome = int(biomes_map[key])
                self.map_viewer.load_map(self.state)
                self.statusBar().showMessage(f"Loaded Biomes layer from {os.path.basename(path)}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load Biomes layer:\n{e}")

    def save_factions_layer(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Factions Layer JSON", "", "JSON Files (*.json)")
        if path:
            factions_data = {
                f_id: {
                    "name": f.name,
                    "treasury": f.treasury,
                    "technology_level": f.technology_level,
                    "special_rule": f.special_rule,
                    "coa_json": f.coa_json,
                    "relations": f.relations
                } for f_id, f in self.state.factions.items()
            }
            settlement_factions = {
                f"{q},{r}": hx.settlement.faction_id for (q, r), hx in self.state.hexes.items() if hx.settlement
            }
            data = {"factions": factions_data, "settlement_factions": settlement_factions}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.statusBar().showMessage(f"Saved Factions layer to {os.path.basename(path)}", 3000)

    def load_factions_layer(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Factions Layer JSON", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                factions_map = data.get("factions", {})
                self.state.factions.clear()
                for f_id_str, f_data in factions_map.items():
                    f_id = int(f_id_str)
                    faction = Faction(
                        id=f_id,
                        name=f_data.get("name", ""),
                        treasury=f_data.get("treasury", 0.0),
                        technology_level=f_data.get("technology_level", 1),
                        special_rule=f_data.get("special_rule", ""),
                        coa_json=f_data.get("coa_json", "")
                    )
                    # Convert string target IDs to int for diplomatic relations
                    raw_relations = f_data.get("relations", {})
                    faction.relations = {int(k): v for k, v in raw_relations.items()}
                    self.state.factions[f_id] = faction
                
                settlement_factions = data.get("settlement_factions", {})
                for (q, r), hx in self.state.hexes.items():
                    if hx.settlement:
                        key = f"{q},{r}"
                        if key in settlement_factions:
                            hx.settlement.faction_id = settlement_factions[key]
                
                self.update_factions_ui()
                self.map_viewer.load_map(self.state)
                self.statusBar().showMessage(f"Loaded Factions layer from {os.path.basename(path)}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load Factions layer:\n{e}")

    def save_provinces_layer(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Provinces Layer JSON", "", "JSON Files (*.json)")
        if path:
            prov_data = {
                p_id: {
                    "name": prov.name,
                    "color": prov.color,
                    "faction_id": prov.faction_id
                } for p_id, prov in self.state.provinces.items()
            }
            hex_provinces = {
                f"{q},{r}": hx.province_id for (q, r), hx in self.state.hexes.items()
            }
            data = {"provinces": prov_data, "hex_provinces": hex_provinces}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.statusBar().showMessage(f"Saved Provinces layer to {os.path.basename(path)}", 3000)

    def load_provinces_layer(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Provinces Layer JSON", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                prov_map = data.get("provinces", {})
                self.state.provinces.clear()
                for p_id_str, p_data in prov_map.items():
                    p_id = int(p_id_str)
                    prov = Province(
                        id=p_id,
                        name=p_data.get("name", ""),
                        color=p_data.get("color", "#FFFFFF"),
                        faction_id=p_data.get("faction_id", 1)
                    )
                    self.state.provinces[p_id] = prov
                
                hex_provinces = data.get("hex_provinces", {})
                for (q, r), hx in self.state.hexes.items():
                    key = f"{q},{r}"
                    if key in hex_provinces:
                        hx.province_id = int(hex_provinces[key])
                
                self.update_provinces_ui()
                self.map_viewer.load_map(self.state)
                self.statusBar().showMessage(f"Loaded Provinces layer from {os.path.basename(path)}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load Provinces layer:\n{e}")

    def save_religions_layer(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Religions Layer JSON", "", "JSON Files (*.json)")
        if path:
            rel_data = {
                r_id: {
                    "name": rel.name,
                    "type": rel.type,
                    "color": rel.color
                } for r_id, rel in self.state.religions.items()
            }
            hex_religions = {
                f"{q},{r}": hx.religion_id for (q, r), hx in self.state.hexes.items()
            }
            data = {"religions": rel_data, "hex_religions": hex_religions}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.statusBar().showMessage(f"Saved Religions layer to {os.path.basename(path)}", 3000)

    def load_religions_layer(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Religions Layer JSON", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                rel_map = data.get("religions", {})
                self.state.religions.clear()
                for r_id_str, r_data in rel_map.items():
                    r_id = int(r_id_str)
                    rel = Religion(
                        id=r_id,
                        name=r_data.get("name", ""),
                        type=r_data.get("type", "Polytheism"),
                        color=r_data.get("color", "#FFFFFF")
                    )
                    self.state.religions[r_id] = rel
                
                hex_religions = data.get("hex_religions", {})
                for (q, r), hx in self.state.hexes.items():
                    key = f"{q},{r}"
                    if key in hex_religions:
                        hx.religion_id = int(hex_religions[key])
                
                self.update_religions_ui()
                self.map_viewer.load_map(self.state)
                self.statusBar().showMessage(f"Loaded Religions layer from {os.path.basename(path)}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load Religions layer:\n{e}")

    def save_cultures_layer(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Cultures Layer JSON", "", "JSON Files (*.json)")
        if path:
            cul_data = {
                c_id: {
                    "name": cul.name,
                    "color": cul.color,
                    "language_base": cul.language_base,
                    "expansionism": cul.expansionism
                } for c_id, cul in self.state.cultures.items()
            }
            hex_cultures = {
                f"{q},{r}": hx.culture_id for (q, r), hx in self.state.hexes.items()
            }
            data = {"cultures": cul_data, "hex_cultures": hex_cultures}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.statusBar().showMessage(f"Saved Cultures layer to {os.path.basename(path)}", 3000)

    def load_cultures_layer(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Cultures Layer JSON", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                cul_map = data.get("cultures", {})
                self.state.cultures.clear()
                for c_id_str, c_data in cul_map.items():
                    c_id = int(c_id_str)
                    cul = Culture(
                        id=c_id,
                        name=c_data.get("name", ""),
                        color=c_data.get("color", "#FFFFFF"),
                        language_base=c_data.get("language_base", ""),
                        expansionism=c_data.get("expansionism", 1.0)
                    )
                    self.state.cultures[c_id] = cul
                
                hex_cultures = data.get("hex_cultures", {})
                for (q, r), hx in self.state.hexes.items():
                    key = f"{q},{r}"
                    if key in hex_cultures:
                        hx.culture_id = int(hex_cultures[key])
                
                self.update_cultures_ui()
                self.update_culture_names_ui()
                self.map_viewer.load_map(self.state)
                self.statusBar().showMessage(f"Loaded Cultures layer from {os.path.basename(path)}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load Cultures layer:\n{e}")

    def save_climate_layer(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Climate Layer JSON", "", "JSON Files (*.json)")
        if path:
            data = {
                "temperature": {f"{q},{r}": hx.p2 for (q, r), hx in self.state.hexes.items()},
                "moisture": {f"{q},{r}": hx.p3 for (q, r), hx in self.state.hexes.items()}
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.statusBar().showMessage(f"Saved Climate layer to {os.path.basename(path)}", 3000)

    def load_climate_layer(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Climate Layer JSON", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                temp_map = data.get("temperature", {})
                moist_map = data.get("moisture", {})
                for (q, r), hx in self.state.hexes.items():
                    key = f"{q},{r}"
                    if key in temp_map:
                        hx.p2 = int(temp_map[key])
                    if key in moist_map:
                        hx.p3 = int(moist_map[key])
                self.map_viewer.load_map(self.state)
                self.statusBar().showMessage(f"Loaded Climate layer from {os.path.basename(path)}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load Climate layer:\n{e}")

    def save_rivers_layer(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Rivers Layer JSON", "", "JSON Files (*.json)")
        if path:
            data = {
                "rivers": {f"{q},{r}": hx.river_volume for (q, r), hx in self.state.hexes.items()},
                "lakes": {f"{q},{r}": hx.is_lake for (q, r), hx in self.state.hexes.items()}
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.statusBar().showMessage(f"Saved Rivers layer to {os.path.basename(path)}", 3000)

    def load_rivers_layer(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Rivers Layer JSON", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                river_map = data.get("rivers", {})
                lake_map = data.get("lakes", {})
                for (q, r), hx in self.state.hexes.items():
                    key = f"{q},{r}"
                    if key in river_map:
                        hx.river_volume = int(river_map[key])
                    if key in lake_map:
                        hx.is_lake = bool(lake_map[key])
                self.map_viewer.load_map(self.state)
                self.statusBar().showMessage(f"Loaded Rivers layer from {os.path.basename(path)}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load Rivers layer:\n{e}")

    def save_chaos_layer(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Chaos Layer JSON", "", "JSON Files (*.json)")
        if path:
            data = {"chaos": {f"{q},{r}": hx.chaos_domain for (q, r), hx in self.state.hexes.items()}}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.statusBar().showMessage(f"Saved Chaos layer to {os.path.basename(path)}", 3000)

    def load_chaos_layer(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Chaos Layer JSON", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                chaos_map = data.get("chaos", {})
                for (q, r), hx in self.state.hexes.items():
                    key = f"{q},{r}"
                    if key in chaos_map:
                        hx.chaos_domain = chaos_map[key]
                self.map_viewer.load_map(self.state)
                self.statusBar().showMessage(f"Loaded Chaos layer from {os.path.basename(path)}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load Chaos layer:\n{e}")

    def save_settlements_layer(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Settlements Layer JSON", "", "JSON Files (*.json)")
        if path:
            sett_data = {}
            for (q, r), hx in self.state.hexes.items():
                if hx.settlement:
                    s = hx.settlement
                    sett_data[f"{q},{r}"] = {
                        "id": s.id,
                        "name": s.name,
                        "population": s.population,
                        "wealth": s.wealth,
                        "security_points": s.security_points,
                        "hidden_cultists": s.hidden_cultists,
                        "inventory_json": s.inventory_json,
                        "faction_id": s.faction_id,
                        "paragons": [
                            {
                                "name": p.name,
                                "archetype": p.archetype,
                                "level": p.level,
                                "motivation": p.motivation,
                                "stats_json": p.stats_json,
                                "traits_json": p.traits_json
                            } for p in s.paragons
                        ]
                    }
            data = {"settlements": sett_data}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.statusBar().showMessage(f"Saved Settlements layer to {os.path.basename(path)}", 3000)

    def load_settlements_layer(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Settlements Layer JSON", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sett_map = data.get("settlements", {})
                for (q, r), hx in self.state.hexes.items():
                    key = f"{q},{r}"
                    if key in sett_map:
                        s_data = sett_map[key]
                        s = Settlement(
                            id=s_data.get("id", 1),
                            name=s_data.get("name", "Unnamed"),
                            population=s_data.get("population", 50),
                            wealth=s_data.get("wealth", 1.0),
                            security_points=s_data.get("security_points", 0.0),
                            hidden_cultists=s_data.get("hidden_cultists", 0),
                            inventory_json=s_data.get("inventory_json", "{}"),
                            faction_id=s_data.get("faction_id", 1)
                        )
                        s.paragons = []
                        for p_data in s_data.get("paragons", []):
                            p = Paragon(
                                name=p_data.get("name", ""),
                                archetype=p_data.get("archetype", "Commander"),
                                level=p_data.get("level", 1),
                                motivation=p_data.get("motivation", ""),
                                stats_json=p_data.get("stats_json", "{}"),
                                traits_json=p_data.get("traits_json", "[]")
                            )
                            s.paragons.append(p)
                        hx.settlement = s
                    else:
                        hx.settlement = None
                self.update_settlements_directory_ui()
                self.map_viewer.load_map(self.state)
                self.statusBar().showMessage(f"Loaded Settlements layer from {os.path.basename(path)}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load Settlements layer:\n{e}")

    def save_names_layer(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Name Styles JSON", "", "JSON Files (*.json)")
        if path:
            data = {
                "naming_styles": {
                    c_id: {
                        "name": cul.name,
                        "language_base": cul.language_base,
                        "expansionism": cul.expansionism
                    } for c_id, cul in self.state.cultures.items()
                }
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.statusBar().showMessage(f"Saved Name Styles to {os.path.basename(path)}", 3000)

    def load_names_layer(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Name Styles JSON", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                styles_map = data.get("naming_styles", {})
                for c_id_str, c_data in styles_map.items():
                    c_id = int(c_id_str)
                    cul = self.state.cultures.get(c_id)
                    if cul:
                        cul.name = c_data.get("name", cul.name)
                        cul.language_base = c_data.get("language_base", cul.language_base)
                        cul.expansionism = c_data.get("expansionism", cul.expansionism)
                self.update_culture_names_ui()
                self.update_cultures_ui()
                self.statusBar().showMessage(f"Loaded Name Styles from {os.path.basename(path)}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load Name Styles:\n{e}")

    def save_markers_layer(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Markers Layer JSON", "", "JSON Files (*.json)")
        if path:
            data = {
                "markers": [
                    {
                        "id": m.id,
                        "type": m.type,
                        "description": m.description,
                        "global_q": m.global_q,
                        "global_r": m.global_r
                    } for m in self.state.markers
                ]
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.statusBar().showMessage(f"Saved Markers layer to {os.path.basename(path)}", 3000)

    def load_markers_layer(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Markers Layer JSON", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                markers_list = data.get("markers", [])
                self.state.markers.clear()
                for m_data in markers_list:
                    m = Marker(
                        id=m_data.get("id", 1),
                        type=m_data.get("type", "Ruins"),
                        global_q=m_data.get("global_q", 0),
                        global_r=m_data.get("global_r", 0)
                    )
                    m.description = m_data.get("description", "")
                    self.state.markers.append(m)
                self.update_markers_ui()
                self.map_viewer.load_map(self.state)
                self.statusBar().showMessage(f"Loaded Markers layer from {os.path.basename(path)}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load Markers layer:\n{e}")

    def save_forces_layer(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Forces Layer JSON", "", "JSON Files (*.json)")
        if path:
            data = {
                "entities": [
                    {
                        "id": ent.id,
                        "type": ent.type,
                        "global_hex_id": ent.global_hex_id,
                        "global_q": ent.global_q,
                        "global_r": ent.global_r,
                        "micro_q": ent.micro_q,
                        "micro_r": ent.micro_r,
                        "radius": ent.radius,
                        "duration": ent.duration,
                        "intensity": ent.intensity,
                        "alignment": ent.alignment
                    } for ent in self.state.entities
                ]
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.statusBar().showMessage(f"Saved Forces layer to {os.path.basename(path)}", 3000)

    def load_forces_layer(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Forces Layer JSON", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                entities_list = data.get("entities", [])
                self.state.entities.clear()
                for ent_data in entities_list:
                    ent = WorldEntity(
                        id=ent_data.get("id", 1),
                        type=ent_data.get("type", "Regiment"),
                        global_hex_id=ent_data.get("global_hex_id", 1),
                        global_q=ent_data.get("global_q", 0),
                        global_r=ent_data.get("global_r", 0),
                        radius=ent_data.get("radius", 1),
                        duration=ent_data.get("duration", 50),
                        intensity=ent_data.get("intensity", 1.0),
                        alignment=ent_data.get("alignment", None)
                    )
                    ent.micro_q = ent_data.get("micro_q", 0)
                    ent.micro_r = ent_data.get("micro_r", 0)
                    self.state.entities.append(ent)
                self.update_entities_ui()
                self.map_viewer.load_map(self.state)
                self.statusBar().showMessage(f"Loaded Forces layer from {os.path.basename(path)}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load Forces layer:\n{e}")

    def save_routes_layer(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Trade Routes JSON", "", "JSON Files (*.json)")
        if path:
            data = {
                "routes": [
                    {
                        "faction_id": rt.faction_id,
                        "settlement_a_id": rt.settlement_a_id,
                        "settlement_b_id": rt.settlement_b_id,
                        "bandwidth": rt.bandwidth,
                        "route_type": rt.route_type
                    } for rt in self.state.routes
                ]
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.statusBar().showMessage(f"Saved Trade Routes to {os.path.basename(path)}", 3000)

    def load_routes_layer(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Trade Routes JSON", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                routes_list = data.get("routes", [])
                self.state.routes.clear()
                for rt_data in routes_list:
                    rt = TradeRoute(
                        faction_id=rt_data.get("faction_id", 1),
                        settlement_a_id=rt_data.get("settlement_a_id", 1),
                        settlement_b_id=rt_data.get("settlement_b_id", 2),
                        bandwidth=rt_data.get("bandwidth", 10),
                        route_type=rt_data.get("route_type", "Land")
                    )
                    self.state.routes.append(rt)
                self.update_routes_ui()
                self.map_viewer.load_map(self.state)
                self.statusBar().showMessage(f"Loaded Trade Routes from {os.path.basename(path)}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load Trade Routes:\n{e}")

    def on_view_layer_changed(self):
        self.map_viewer.set_render_mode(self.cb_view_layer.currentText())

    def clear_all_brushes_except(self, active_button):
        all_dialogs = [
            self.dialog_elevation,
            self.dialog_biomes,
            self.dialog_factions,
            self.dialog_provinces,
            self.dialog_religions,
            self.dialog_cultures,
            self.dialog_markers,
            self.dialog_forces,
            self.dialog_routes,
            self.dialog_climate,
            self.dialog_rivers,
            self.dialog_chaos
        ]
        for d in all_dialogs:
            if d:
                d.uncheck_paint_button()
                
        # Settlement button sits on main hex inspector
        if active_button != self.btn_paint_settlement:
            self.btn_paint_settlement.blockSignals(True)
            self.btn_paint_settlement.setChecked(False)
            self.btn_paint_settlement.setStyleSheet("")
            self.btn_paint_settlement.blockSignals(False)

        # Highlight active checked button
        if active_button and active_button.isChecked():
            active_button.setStyleSheet("background-color: #04D361; color: #121214;")
        elif active_button:
            active_button.setStyleSheet("")

    def on_brush_toggled(self, checked):
        sender = self.sender()
        if checked:
            self.clear_all_brushes_except(sender)
            self.update_active_brush_mode()
        else:
            if sender:
                sender.setStyleSheet("")
            self.map_viewer.set_tool_mode("Select")

    def on_brush_radius_changed(self, val):
        self.brush_radius_val = val
        self.map_viewer.brush_radius = val
        for dialog in [self.dialog_elevation, self.dialog_biomes, self.dialog_factions, 
                       self.dialog_provinces, self.dialog_religions, self.dialog_cultures,
                       self.dialog_climate, self.dialog_rivers, self.dialog_chaos]:
            if dialog and hasattr(dialog, 'slider_radius'):
                dialog.slider_radius.blockSignals(True)
                dialog.slider_radius.setValue(val)
                dialog.slider_radius.blockSignals(False)

    def on_elevation_mode_changed(self, mode):
        self.map_viewer.elevation_brush_mode = mode

    def on_brush_power_changed(self, val):
        self.map_viewer.brush_power = val

    def update_active_brush_mode(self):
        self.map_viewer.brush_radius = self.brush_radius_val
        
        # Pull slider values if dialogs exist to maintain reactive updates
        temp_val = self.dialog_climate.slider_temp.value() if self.dialog_climate else 128
        moist_val = self.dialog_climate.slider_moist.value() if self.dialog_climate else 128
        river_val = self.dialog_rivers.slider_river.value() if self.dialog_rivers else 10
        
        if self.dialog_elevation and self.dialog_elevation.btn_paint.isChecked():
            self.map_viewer.set_tool_mode("Paint Elevation", self.spin_elev_brush.value())
        elif self.dialog_biomes and self.dialog_biomes.btn_paint.isChecked():
            row = self.dialog_biomes.biome_list_brush.currentRow()
            val = row if row >= 0 else 0
            self.map_viewer.set_tool_mode("Paint Biome", val)
        elif self.dialog_factions and self.dialog_factions.btn_paint.isChecked():
            val = self.selected_faction_id if self.selected_faction_id is not None else 0
            self.map_viewer.set_tool_mode("Paint Faction", val)
        elif self.dialog_provinces and self.dialog_provinces.btn_paint.isChecked():
            val = self.selected_province_id if self.selected_province_id is not None else 0
            self.map_viewer.set_tool_mode("Paint Province", val)
        elif self.dialog_religions and self.dialog_religions.btn_paint.isChecked():
            val = self.selected_religion_id if self.selected_religion_id is not None else 0
            self.map_viewer.set_tool_mode("Paint Religion", val)
        elif self.dialog_cultures and self.dialog_cultures.btn_paint.isChecked():
            val = self.selected_culture_id if self.selected_culture_id is not None else 0
            self.map_viewer.set_tool_mode("Paint Culture", val)
        elif self.dialog_markers and self.dialog_markers.btn_paint.isChecked():
            self.map_viewer.set_tool_mode("Place Marker")
        elif self.dialog_forces and self.dialog_forces.btn_paint.isChecked():
            self.map_viewer.set_tool_mode("Place Force")
        elif self.dialog_routes and self.dialog_routes.btn_paint.isChecked():
            self.map_viewer.set_tool_mode("Link Route")
            self.route_start_sett_id = None
        elif self.btn_paint_settlement.isChecked():
            self.map_viewer.set_tool_mode("Place Settlement")
        elif self.dialog_climate and self.dialog_climate.btn_paint_temp.isChecked():
            self.map_viewer.set_tool_mode("Paint Temperature", temp_val)
        elif self.dialog_climate and self.dialog_climate.btn_paint_moist.isChecked():
            self.map_viewer.set_tool_mode("Paint Moisture", moist_val)
        elif self.dialog_rivers and self.dialog_rivers.btn_paint_river.isChecked():
            self.map_viewer.set_tool_mode("Paint River Volume", river_val)
        elif self.dialog_rivers and self.dialog_rivers.btn_toggle_lake.isChecked():
            self.map_viewer.set_tool_mode("Toggle Lake", int(self.chk_lake_brush.isChecked()))
        elif self.dialog_chaos and self.dialog_chaos.btn_paint.isChecked():
            row = self.dialog_chaos.chaos_list_brush.currentRow()
            dom = CHAOS_DOMAINS[row] if (row >= 0 and row < len(CHAOS_DOMAINS)) else "None"
            self.map_viewer.set_tool_mode("Paint Chaos", dom)
        else:
            self.map_viewer.set_tool_mode("Select")

    # Map Click Handlers
    def place_settlement_at(self, q, r):
        hx = self.state.hexes.get((q, r))
        if hx:
            if hx.settlement:
                QMessageBox.information(self, "Info", f"Hex already contains settlement: {hx.settlement.name}")
                return
            name, ok = QInputDialog.getText(self, "Place Settlement", "Enter settlement name:")
            if ok and name:
                max_id = 0
                for cell in self.state.hexes.values():
                    if cell.settlement and cell.settlement.id:
                        max_id = max(max_id, cell.settlement.id)
                new_id = max_id + 1
                hx.settlement = Settlement(id=new_id, name=name, population=50)
                self.map_viewer.load_map(self.state)
                self.on_hex_selected(q, r)
                self.update_settlements_directory_ui()
                self.statusBar().showMessage(f"Created settlement '{name}' at q={q}, r={r}", 3000)

    def place_marker_at(self, q, r):
        if self.selected_marker_idx is None:
            m_type, ok = QInputDialog.getItem(self, "Place Marker", "Select Marker Type to Create:", ["Ruins", "Dungeon", "Cave", "Portal", "Obelisk"], 0, False)
            if ok and m_type:
                new_id = len(self.state.markers) + 1
                new_marker = Marker(id=new_id, type=m_type, global_q=q, global_r=r)
                self.state.markers.append(new_marker)
                self.update_markers_ui()
                self.map_viewer.load_map(self.state)
                self.mark_list.setCurrentRow(len(self.state.markers) - 1)
                self.statusBar().showMessage(f"Placed new {m_type} marker at q={q}, r={r}", 3000)
        else:
            m = self.state.markers[self.selected_marker_idx]
            m.global_q = q
            m.global_r = r
            self.spin_mark_q.setValue(q)
            self.spin_mark_r.setValue(r)
            self.update_markers_ui()
            self.map_viewer.load_map(self.state)
            self.statusBar().showMessage(f"Relocated marker '{m.type}' to q={q}, r={r}", 3000)

    def place_force_at(self, q, r):
        if self.selected_entity_idx is None:
            f_type, ok = QInputDialog.getItem(self, "Deploy Force", "Select Force Type:", ["Regiment", "Cult Monster", "Null Zealots", "Chaos Creature"], 0, False)
            if ok and f_type:
                new_id = len(self.state.entities) + 1
                matching_hex = self.state.hexes.get((q, r))
                new_ent = WorldEntity(
                    id=new_id,
                    type=f_type,
                    global_hex_id=matching_hex.id if matching_hex else 1,
                    global_q=q,
                    global_r=r,
                    radius=1,
                    duration=50,
                    intensity=1.0,
                    alignment=None
                )
                self.state.entities.append(new_ent)
                self.update_entities_ui()
                self.map_viewer.load_map(self.state)
                self.entity_list.setCurrentRow(len(self.state.entities) - 1)
                self.statusBar().showMessage(f"Deployed new {f_type} at q={q}, r={r}", 3000)
        else:
            ent = self.state.entities[self.selected_entity_idx]
            ent.global_q = q
            ent.global_r = r
            matching_hex = self.state.hexes.get((q, r))
            if matching_hex:
                ent.global_hex_id = matching_hex.id
            self.spin_ent_q.setValue(q)
            self.spin_ent_r.setValue(r)
            self.update_entities_ui()
            self.map_viewer.load_map(self.state)
            self.statusBar().showMessage(f"Relocated force '{ent.type}' to q={q}, r={r}", 3000)

    def link_route_at(self, q, r):
        hx = self.state.hexes.get((q, r))
        if not hx or not hx.settlement:
            self.statusBar().showMessage("Click on a settlement to establish/link a route.", 3000)
            return
            
        sett = hx.settlement
        if self.route_start_sett_id is None:
            self.route_start_sett_id = sett.id
            self.statusBar().showMessage(f"Selected starting settlement: {sett.name}. Click another settlement to link.", 5000)
        else:
            if self.route_start_sett_id == sett.id:
                self.route_start_sett_id = None
                self.statusBar().showMessage("Canceled trade route creation.", 3000)
                return
            new_route = TradeRoute(
                faction_id=1,
                settlement_a_id=self.route_start_sett_id,
                settlement_b_id=sett.id,
                bandwidth=10,
                route_type="Land"
            )
            self.state.routes.append(new_route)
            self.update_routes_ui()
            self.map_viewer.load_map(self.state)
            self.route_list.setCurrentRow(len(self.state.routes) - 1)
            self.statusBar().showMessage(f"Established route from settlement ID {self.route_start_sett_id} to {sett.name}!", 4000)
            self.route_start_sett_id = None
            
    def open_world_configurator(self):
        from PyQt6.QtWidgets import QFormLayout, QDialog, QDoubleSpinBox
        dialog = QDialog(self)
        dialog.setWindowTitle("World Configurator")
        dialog.resize(380, 300)
        dialog.setStyleSheet(self.styleSheet())
        
        layout = QFormLayout(dialog)
        
        spin_equator = QDoubleSpinBox()
        spin_equator.setRange(-40.0, 60.0)
        spin_equator.setValue(self.temperature_equator)
        layout.addRow("Equator Temperature (°C):", spin_equator)
        
        spin_polar = QDoubleSpinBox()
        spin_polar.setRange(-80.0, 20.0)
        spin_polar.setValue(self.temperature_pole)
        layout.addRow("Polar Temperature (°C):", spin_polar)
        
        spin_offset = QDoubleSpinBox()
        spin_offset.setRange(-20.0, 20.0)
        spin_offset.setValue(self.temperature_offset)
        layout.addRow("Temperature Offset (°C):", spin_offset)
        
        spin_precip = QDoubleSpinBox()
        spin_precip.setRange(0.1, 5.0)
        spin_precip.setValue(self.precipitation_multiplier)
        layout.addRow("Precipitation Multiplier:", spin_precip)
        
        spin_wind = QDoubleSpinBox()
        spin_wind.setRange(0.0, 360.0)
        spin_wind.setValue(self.wind_direction_angle)
        layout.addRow("Wind Direction Angle (°):", spin_wind)
        
        btn_apply = QPushButton("Apply Settings & Regenerate")
        layout.addRow(btn_apply)
        
        def apply_settings():
            self.temperature_equator = spin_equator.value()
            self.temperature_pole = spin_polar.value()
            self.temperature_offset = spin_offset.value()
            self.precipitation_multiplier = spin_precip.value()
            self.wind_direction_angle = spin_wind.value()
            self.generate_new_world(prompt=False)
            dialog.accept()
            
        btn_apply.clicked.connect(apply_settings)
        dialog.exec()

    def generate_new_world(self, seed=100, prompt=True):
        if prompt:
            seed_val, ok = QInputDialog.getInt(self, "Generate Map", "Enter Seed Value:", seed, 1, 999999)
            if not ok:
                return
            seed = seed_val
            
        self.state = generate_world(
            R=57, 
            elevation_seed=seed,
            temp_offset=self.temperature_offset,
            temp_equator=self.temperature_equator,
            temp_pole=self.temperature_pole,
            precip_mult=self.precipitation_multiplier,
            wind_angle=self.wind_direction_angle
        )
        self.map_viewer.load_map(self.state)
        self.update_factions_ui()
        self.update_provinces_ui()
        self.update_entities_ui()
        self.update_routes_ui()
        self.update_religions_ui()
        self.update_cultures_ui()
        self.update_markers_ui()
        self.update_settlements_directory_ui()
        self.update_culture_names_ui()
        self.statusBar().showMessage(f"Generated new procedural map state (Seed: {seed}).", 3000)
        self.open_cell_inspector()
            
    def import_azgaar_map(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Azgaar .map / JSON", "", "JSON Files (*.json *.map)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.state = convert_azgaar_to_hex_grid(data, R=57)
                self.map_viewer.load_map(self.state)
                self.update_factions_ui()
                self.update_provinces_ui()
                self.update_entities_ui()
                self.update_routes_ui()
                self.update_religions_ui()
                self.update_cultures_ui()
                self.update_markers_ui()
                self.update_settlements_directory_ui()
                self.update_culture_names_ui()
                self.statusBar().showMessage(f"Successfully converted and loaded map: {os.path.basename(path)}", 3000)
                self.open_cell_inspector()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import/convert Azgaar map:\n{e}")
            
    def load_db(self):
        if not os.path.exists(self.db_path):
            QMessageBox.critical(self, "Error", f"Simulator DB not found at: {self.db_path}")
            return
        
        state = load_from_db(self.db_path)
        if state:
            self.state = state
            self.map_viewer.load_map(self.state)
            self.update_factions_ui()
            self.update_provinces_ui()
            self.update_entities_ui()
            self.update_routes_ui()
            self.update_religions_ui()
            self.update_cultures_ui()
            self.update_markers_ui()
            self.update_settlements_directory_ui()
            self.update_culture_names_ui()
            self.statusBar().showMessage("Successfully loaded map state from simulator DB.", 3000)
            self.open_cell_inspector()
        else:
            QMessageBox.critical(self, "Error", "Failed to parse map from database.")
            
    def save_db(self):
        try:
            save_to_db(self.state, self.db_path)
            self.statusBar().showMessage("Successfully synchronized state to simulator DB.", 3000)
            QMessageBox.information(self, "Success", "World State synced successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save to database:\n{e}")
            
    def run_sim_tick(self):
        try:
            from shatterlands_simulator.core_engine.engine import GlobalEngine
            engine = GlobalEngine(self.db_path)
            engine.trigger_tick()
            self.load_db()
            self.statusBar().showMessage("Tick executed and state updated.", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not run simulation tick:\n{e}")
            
    def export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export JSON Map", "", "JSON Files (*.json)")
        if path:
            with open(path, "w") as f:
                f.write(self.state.serialize_to_azgaar_json())
            self.statusBar().showMessage(f"Exported JSON to {os.path.basename(path)}", 3000)
            
    def on_hex_painted(self, q, r, attr, val):
        hx = self.state.hexes.get((q, r))
        if hx:
            if attr == "elevation": hx.elevation = val
            elif attr == "biome": hx.biome = val
            elif attr == "religion_id": hx.religion_id = val
            elif attr == "culture_id": hx.culture_id = val
            elif attr == "province_id":
                prov = self.state.provinces.get(val)
                if prov:
                    closest_faction = 0
                    min_dist = 999999
                    for (sq, sr), shx in self.state.hexes.items():
                        if shx.settlement:
                            h_dist = (abs(q - sq) + abs(q + r - sq - sr) + abs(r - sr)) // 2
                            if h_dist < min_dist:
                                min_dist = h_dist
                                closest_faction = shx.settlement.faction_id
                    if closest_faction == prov.faction_id:
                        hx.province_id = val
            elif attr == "faction_id": 
                if hx.settlement: hx.settlement.faction_id = val
            elif attr == "temp": hx.p2 = val
            elif attr == "moist": hx.p3 = val
            elif attr == "river_volume": hx.river_volume = val
            elif attr == "is_lake": hx.is_lake = bool(val)
            elif attr == "chaos_domain_str":
                hx.chaos_domain = self.dialog_chaos.chaos_list_brush.currentItem().text() if (self.dialog_chaos and self.dialog_chaos.chaos_list_brush.currentItem()) else "None"
                if hx.chaos_domain == "None":
                    hx.chaos_domain = None
            if self.selected_coord == (q, r):
                self.on_hex_selected(q, r)
                
    def on_hex_selected(self, q, r):
        self.selected_coord = (q, r)
        hx = self.state.hexes.get((q, r))
        if hx:
            self.cb_biome.blockSignals(True)
            self.sld_elev.blockSignals(True)
            self.txt_river.blockSignals(True)
            self.chk_lake.blockSignals(True)
            self.cb_chaos.blockSignals(True)
            
            self.chk_has_sett.blockSignals(True)
            self.txt_sett_name.blockSignals(True)
            self.cb_sett_faction.blockSignals(True)
            self.txt_sett_pop.blockSignals(True)
            self.txt_sett_inv.blockSignals(True)
            
            self.lbl_coord.setText(f"q={q}, r={r} (Hex ID: {hx.id})")
            
            biome_idx = self.cb_biome.findData(hx.biome)
            if biome_idx >= 0:
                self.cb_biome.setCurrentIndex(biome_idx)
                
            self.sld_elev.setValue(hx.elevation)
            self.txt_river.setText(str(hx.river_volume))
            self.chk_lake.setChecked(hx.is_lake)
            
            chaos_idx = self.cb_chaos.findText(hx.chaos_domain or "None")
            if chaos_idx >= 0:
                self.cb_chaos.setCurrentIndex(chaos_idx)
                
            if hx.settlement:
                self.chk_has_sett.setChecked(True)
                self.txt_sett_name.setText(hx.settlement.name)
                self.txt_sett_pop.setText(str(hx.settlement.population))
                self.txt_sett_inv.setText(hx.settlement.inventory_json)
                
                f_idx = self.cb_sett_faction.findData(hx.settlement.faction_id)
                if f_idx >= 0:
                    self.cb_sett_faction.setCurrentIndex(f_idx)
                    
                self.lbl_paragon_sett.setText(f"Inside: {hx.settlement.name}")
                self.update_paragons_list()
            else:
                self.chk_has_sett.setChecked(False)
                self.txt_sett_name.setText("")
                self.txt_sett_pop.setText("")
                self.txt_sett_inv.setText("")
                self.lbl_paragon_sett.setText("No settlement selected")
                self.paragon_list.clear()
                
            self.cb_biome.blockSignals(False)
            self.sld_elev.blockSignals(False)
            self.txt_river.blockSignals(False)
            self.chk_lake.blockSignals(False)
            self.cb_chaos.blockSignals(False)
            
            self.chk_has_sett.blockSignals(False)
            self.txt_sett_name.blockSignals(False)
            self.cb_sett_faction.blockSignals(False)
            self.txt_sett_pop.blockSignals(False)
            self.txt_sett_inv.blockSignals(False)

    def update_factions_ui(self):
        self.cb_sett_faction.blockSignals(True)
        self.cb_sett_faction.clear()
        
        self.cb_ent_align.blockSignals(True)
        self.cb_ent_align.clear()
        self.cb_ent_align.addItem("Neutral / None")
        
        self.cb_rt_faction.blockSignals(True)
        self.cb_rt_faction.clear()
        self.cb_rt_faction.addItem("Neutral / None", 1)

        self.cb_fac_paint_brush.blockSignals(True)
        self.cb_fac_paint_brush.clear()
        
        self.faction_list.blockSignals(True)
        self.faction_list.clear()
        for f_id, f in self.state.factions.items():
            self.cb_sett_faction.addItem(f.name, f_id)
            self.cb_ent_align.addItem(f.name)
            self.cb_rt_faction.addItem(f.name, f_id)
            self.cb_fac_paint_brush.addItem(f.name, f_id)
            
            item = QListWidgetItem(f"{f.name} (ID: {f_id})")
            item.setIcon(create_color_icon(FACTION_COLORS_HEX[f_id % len(FACTION_COLORS_HEX)]))
            self.faction_list.addItem(item)
            
        self.cb_sett_faction.blockSignals(False)
        self.cb_ent_align.blockSignals(False)
        self.cb_rt_faction.blockSignals(False)
        self.cb_fac_paint_brush.blockSignals(False)
        self.faction_list.blockSignals(False)
        
    def add_new_faction(self):
        name, ok = QInputDialog.getText(self, "New Faction", "Enter faction name:")
        if ok and name:
            new_id = max(list(self.state.factions.keys()) + [0]) + 1
            self.state.factions[new_id] = Faction(id=new_id, name=name)
            self.update_factions_ui()
            
    def on_faction_list_selection(self, row):
        if row < 0: return
        f_ids = list(self.state.factions.keys())
        self.selected_faction_id = f_ids[row]
        f = self.state.factions[self.selected_faction_id]
        
        self.txt_fac_name.blockSignals(True)
        self.txt_fac_treasury.blockSignals(True)
        self.spin_fac_tech.blockSignals(True)
        self.txt_fac_rule.blockSignals(True)
        
        self.txt_fac_name.setText(f.name)
        self.txt_fac_treasury.setText(str(f.treasury))
        self.spin_fac_tech.setValue(f.technology_level)
        self.txt_fac_rule.setText(f.special_rule or "")
        
        try:
            coa = json.loads(f.coa_json)
        except Exception:
            coa = {}
            
        self.cb_coa_div.blockSignals(True)
        self.cb_coa_c1.blockSignals(True)
        self.cb_coa_c2.blockSignals(True)
        self.cb_coa_charge.blockSignals(True)
        self.cb_coa_charge_color.blockSignals(True)
        
        self.cb_coa_div.setCurrentText(coa.get("division", "Plain"))
        self.cb_coa_c1.setCurrentText(coa.get("color1", "Or"))
        self.cb_coa_c2.setCurrentText(coa.get("color2", "Azure"))
        self.cb_coa_charge.setCurrentText(coa.get("charge", "None"))
        self.cb_coa_charge_color.setCurrentText(coa.get("charge_color", "Argent"))
        
        self.cb_coa_div.blockSignals(False)
        self.cb_coa_c1.blockSignals(False)
        self.cb_coa_c2.blockSignals(False)
        self.cb_coa_charge.blockSignals(False)
        self.cb_coa_charge_color.blockSignals(False)
        
        self.coa_visual.set_coa(f.coa_json)
        self.update_diplomacy_table()
        
        self.txt_fac_name.blockSignals(False)
        self.txt_fac_treasury.blockSignals(False)
        self.spin_fac_tech.blockSignals(False)
        self.txt_fac_rule.blockSignals(False)
        
        if self.dialog_factions:
            self.dialog_factions.slider_aggression.blockSignals(True)
            self.dialog_factions.slider_trade.blockSignals(True)
            self.dialog_factions.slider_aggression.setValue(int(f.aggression_level))
            self.dialog_factions.slider_trade.setValue(int(f.trade_level))
            self.dialog_factions.slider_aggression.blockSignals(False)
            self.dialog_factions.slider_trade.blockSignals(False)
            
            self.dialog_factions.species_list.blockSignals(True)
            self.dialog_factions.species_list.clear()
            for s_name, pct in f.species_population.items():
                self.dialog_factions.species_list.addItem(f"{s_name}: {pct*100:.1f}%")
            self.dialog_factions.species_list.blockSignals(False)
            
            self.dialog_factions.att_list.blockSignals(True)
            for r in range(self.dialog_factions.att_list.count()):
                it = self.dialog_factions.att_list.item(r)
                it.setCheckState(Qt.CheckState.Checked if it.text() in f.sparkborn_attunement else Qt.CheckState.Unchecked)
            self.dialog_factions.att_list.blockSignals(False)

        self.update_active_brush_mode()
        
    def on_faction_details_changed(self):
        if self.selected_faction_id is None: return
        f = self.state.factions[self.selected_faction_id]
        f.name = self.txt_fac_name.text()
        try:
            f.treasury = float(self.txt_fac_treasury.text())
        except ValueError:
            self.txt_fac_treasury.setText(str(f.treasury))
        f.technology_level = self.spin_fac_tech.value()
        f.special_rule = self.txt_fac_rule.text()
        
        if self.dialog_factions:
            f.aggression_level = float(self.dialog_factions.slider_aggression.value())
            f.trade_level = float(self.dialog_factions.slider_trade.value())
            
        self.update_factions_ui()
        
    def on_coa_changed(self):
        if self.selected_faction_id is None: return
        f = self.state.factions[self.selected_faction_id]
        coa = {
            "division": self.cb_coa_div.currentText(),
            "color1": self.cb_coa_c1.currentText(),
            "color2": self.cb_coa_c2.currentText(),
            "charge": self.cb_coa_charge.currentText(),
            "charge_color": self.cb_coa_charge_color.currentText()
        }
        f.coa_json = json.dumps(coa)
        self.coa_visual.set_coa(f.coa_json)
        
    def update_diplomacy_table(self):
        self.diplomacy_table.blockSignals(True)
        self.diplomacy_table.setRowCount(0)
        if self.selected_faction_id is None:
            self.diplomacy_table.blockSignals(False)
            return
            
        f = self.state.factions[self.selected_faction_id]
        target_factions = [tgt for tgt in self.state.factions.values() if tgt.id != f.id]
        self.diplomacy_table.setRowCount(len(target_factions))
        
        for row_idx, tgt in enumerate(target_factions):
            status, trust = f.relations.get(tgt.id, ("Neutral", 0))
            name_item = QTableWidgetItem(tgt.name)
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            name_item.setData(Qt.ItemDataRole.UserRole, tgt.id)
            self.diplomacy_table.setItem(row_idx, 0, name_item)
            status_item = QTableWidgetItem(status)
            self.diplomacy_table.setItem(row_idx, 1, status_item)
            
            trust_item = QTableWidgetItem(str(trust))
            self.diplomacy_table.setItem(row_idx, 2, trust_item)
        self.diplomacy_table.blockSignals(False)
        
    def on_diplomacy_table_changed(self, row, col):
        if self.selected_faction_id is None: return
        f = self.state.factions[self.selected_faction_id]
        name_item = self.diplomacy_table.item(row, 0)
        if not name_item: return
        tgt_id = name_item.data(Qt.ItemDataRole.UserRole)
        status = self.diplomacy_table.item(row, 1).text() if self.diplomacy_table.item(row, 1) else "Neutral"
        try:
            trust = int(self.diplomacy_table.item(row, 2).text()) if self.diplomacy_table.item(row, 2) else 0
        except ValueError:
            trust = 0
        f.relations[tgt_id] = (status, trust)

    # --- PROVINCES ---
    def update_provinces_ui(self):
        self.prov_list.blockSignals(True)
        self.prov_list.clear()
        
        self.cb_prov_faction.blockSignals(True)
        self.cb_prov_faction.clear()
        for f_id, f in self.state.factions.items():
            self.cb_prov_faction.addItem(f.name, f_id)
            
        for p_id, prov in self.state.provinces.items():
            item = QListWidgetItem(prov.name)
            item.setIcon(create_color_icon(prov.color))
            self.prov_list.addItem(item)
            
        self.prov_list.blockSignals(False)
        self.cb_prov_faction.blockSignals(False)

    def add_new_province(self):
        name, ok = QInputDialog.getText(self, "New Province", "Enter province name:")
        if ok and name:
            new_id = max(list(self.state.provinces.keys()) + [0]) + 1
            color = random.choice(["#1ABC9C", "#2ECC71", "#3498DB", "#9B59B6", "#F1C40F", "#E67E22", "#E74C3C"])
            self.state.provinces[new_id] = Province(id=new_id, name=name, color=color)
            self.update_provinces_ui()

    def on_prov_list_selection(self, row):
        if row < 0: return
        p_ids = list(self.state.provinces.keys())
        self.selected_province_id = p_ids[row]
        prov = self.state.provinces[self.selected_province_id]
        
        self.txt_prov_name.blockSignals(True)
        self.cb_prov_color.blockSignals(True)
        self.cb_prov_faction.blockSignals(True)
        
        self.txt_prov_name.setText(prov.name)
        self.cb_prov_color.setCurrentText(prov.color)
        f_idx = self.cb_prov_faction.findData(prov.faction_id)
        if f_idx >= 0:
            self.cb_prov_faction.setCurrentIndex(f_idx)
            
        self.txt_prov_name.blockSignals(False)
        self.cb_prov_color.blockSignals(False)
        self.cb_prov_faction.blockSignals(False)
        
        self.update_active_brush_mode()

    def on_province_details_changed(self):
        if self.selected_province_id is None: return
        prov = self.state.provinces[self.selected_province_id]
        prov.name = self.txt_prov_name.text()
        prov.color = self.cb_prov_color.currentText()
        prov.faction_id = self.cb_prov_faction.currentData()
        self.update_provinces_ui()
        self.map_viewer.load_map(self.state)
        
    # --- PARAGON & AGENT MANAGEMENT ---
    def update_paragons_list(self):
        self.paragon_list.clear()
        if not self.selected_coord: return
        hx = self.state.hexes.get(self.selected_coord)
        if hx and hx.settlement:
            for idx, p in enumerate(hx.settlement.paragons):
                self.paragon_list.addItem(f"{p.name} ({p.archetype} Lvl {p.level})")
                
    def on_paragon_list_selection(self, row):
        if row < 0:
            self.selected_paragon_idx = None
            return
        self.selected_paragon_idx = row
        hx = self.state.hexes.get(self.selected_coord)
        if hx and hx.settlement:
            p = hx.settlement.paragons[row]
            self.txt_p_name.blockSignals(True)
            self.cb_p_archetype.blockSignals(True)
            self.spin_p_level.blockSignals(True)
            self.txt_p_motivation.blockSignals(True)
            self.txt_p_stats.blockSignals(True)
            self.txt_p_traits.blockSignals(True)
            
            self.txt_p_name.setText(p.name)
            self.cb_p_archetype.setCurrentText(p.archetype)
            self.spin_p_level.setValue(p.level)
            self.txt_p_motivation.setText(p.motivation)
            self.txt_p_stats.setText(p.stats_json)
            self.txt_p_traits.setText(p.traits_json)
            
            self.txt_p_name.blockSignals(False)
            self.cb_p_archetype.blockSignals(False)
            self.spin_p_level.blockSignals(False)
            self.txt_p_motivation.blockSignals(False)
            self.txt_p_stats.blockSignals(False)
            self.txt_p_traits.blockSignals(False)
            
    def add_new_paragon(self):
        if not self.selected_coord: return
        hx = self.state.hexes.get(self.selected_coord)
        if hx and hx.settlement:
            p = Paragon(name="New Paragon", archetype="Commander", level=1)
            hx.settlement.paragons.append(p)
            self.update_paragons_list()
            self.paragon_list.setCurrentRow(len(hx.settlement.paragons) - 1)
            
    def delete_selected_paragon(self):
        if self.selected_paragon_idx is None or not self.selected_coord: return
        hx = self.state.hexes.get(self.selected_coord)
        if hx and hx.settlement:
            hx.settlement.paragons.pop(self.selected_paragon_idx)
            self.update_paragons_list()
            self.selected_paragon_idx = None
            
    def on_paragon_form_changed(self):
        if self.selected_paragon_idx is None or not self.selected_coord: return
        hx = self.state.hexes.get(self.selected_coord)
        if hx and hx.settlement:
            p = hx.settlement.paragons[self.selected_paragon_idx]
            p.name = self.txt_p_name.text()
            p.archetype = self.cb_p_archetype.currentText()
            p.level = self.spin_p_level.value()
            p.motivation = self.txt_p_motivation.text()
            p.stats_json = self.txt_p_stats.text()
            p.traits_json = self.txt_p_traits.text()
            self.update_paragons_list()

    # --- WORLD ENTITIES & REGIMENTS ---
    def update_entities_ui(self):
        self.entity_list.clear()
        for idx, ent in enumerate(self.state.entities):
            self.entity_list.addItem(f"{ent.type} (Coord: q={ent.global_q}, r={ent.global_r})")
            
    def on_entity_list_selection(self, row):
        if row < 0:
            self.selected_entity_idx = None
            return
        self.selected_entity_idx = row
        ent = self.state.entities[row]
        
        self.cb_ent_type.blockSignals(True)
        self.spin_ent_q.blockSignals(True)
        self.spin_ent_r.blockSignals(True)
        self.spin_ent_mq.blockSignals(True)
        self.spin_ent_mr.blockSignals(True)
        self.spin_ent_radius.blockSignals(True)
        self.spin_ent_duration.blockSignals(True)
        self.spin_ent_intensity.blockSignals(True)
        self.cb_ent_align.blockSignals(True)
        
        self.cb_ent_type.setCurrentText(ent.type)
        self.spin_ent_q.setValue(ent.global_q)
        self.spin_ent_r.setValue(ent.global_r)
        self.spin_ent_mq.setValue(ent.micro_q)
        self.spin_ent_mr.setValue(ent.micro_r)
        self.spin_ent_radius.setValue(ent.radius)
        self.spin_ent_duration.setValue(ent.duration)
        self.spin_ent_intensity.setValue(ent.intensity)
        
        align_text = ent.alignment if ent.alignment else "Neutral / None"
        align_idx = self.cb_ent_align.findText(align_text)
        if align_idx >= 0:
            self.cb_ent_align.setCurrentIndex(align_idx)
            
        self.cb_ent_type.blockSignals(False)
        self.spin_ent_q.blockSignals(False)
        self.spin_ent_r.blockSignals(False)
        self.spin_ent_mq.blockSignals(False)
        self.spin_ent_mr.blockSignals(False)
        self.spin_ent_radius.blockSignals(False)
        self.spin_ent_duration.blockSignals(False)
        self.spin_ent_intensity.blockSignals(False)
        self.cb_ent_align.blockSignals(False)
        
        self.map_viewer.select_hex(ent.global_q, ent.global_r)
        self.update_active_brush_mode()
        
    def add_new_entity(self):
        new_ent = WorldEntity(
            type="Regiment",
            global_hex_id=1,
            global_q=0,
            global_r=0,
            radius=1,
            duration=50,
            intensity=1.0,
            alignment=None
        )
        self.state.entities.append(new_ent)
        self.update_entities_ui()
        self.map_viewer.load_map(self.state)
        self.entity_list.setCurrentRow(len(self.state.entities) - 1)
        
    def delete_selected_entity(self):
        if self.selected_entity_idx is None: return
        self.state.entities.pop(self.selected_entity_idx)
        self.update_entities_ui()
        self.map_viewer.load_map(self.state)
        self.selected_entity_idx = None
        
    def snap_entity_to_selected_hex(self):
        if self.selected_entity_idx is None or not self.selected_coord: return
        ent = self.state.entities[self.selected_entity_idx]
        q, r = self.selected_coord
        matching_hex = self.state.hexes.get((q, r))
        if matching_hex:
            ent.global_hex_id = matching_hex.id
            ent.global_q = q
            ent.global_r = r
            
            self.spin_ent_q.blockSignals(True)
            self.spin_ent_r.blockSignals(True)
            self.spin_ent_q.setValue(q)
            self.spin_ent_r.setValue(r)
            self.spin_ent_q.blockSignals(False)
            self.spin_ent_r.blockSignals(False)
            
            self.update_entities_ui()
            self.map_viewer.load_map(self.state)
            
    def on_entity_form_changed(self):
        if self.selected_entity_idx is None: return
        ent = self.state.entities[self.selected_entity_idx]
        ent.type = self.cb_ent_type.currentText()
        ent.global_q = self.spin_ent_q.value()
        ent.global_r = self.spin_ent_r.value()
        ent.micro_q = self.spin_ent_mq.value()
        ent.micro_r = self.spin_ent_mr.value()
        ent.radius = self.spin_ent_radius.value()
        ent.duration = self.spin_ent_duration.value()
        ent.intensity = self.spin_ent_intensity.value()
        
        align_text = self.cb_ent_align.currentText()
        ent.alignment = None if align_text == "Neutral / None" else align_text
        
        matching_hex = self.state.hexes.get((ent.global_q, ent.global_r))
        if matching_hex:
            ent.global_hex_id = matching_hex.id
            
        self.update_entities_ui()
        self.map_viewer.load_map(self.state)

    # --- TRADE ROUTES ---
    def update_routes_ui(self):
        self.route_list.blockSignals(True)
        self.route_list.clear()
        
        self.cb_rt_sett_a.blockSignals(True)
        self.cb_rt_sett_b.blockSignals(True)
        self.cb_rt_sett_a.clear()
        self.cb_rt_sett_b.clear()
        
        settlements_list = []
        for (q, r), hx in self.state.hexes.items():
            if hx.settlement:
                s = hx.settlement
                settlements_list.append(s)
                self.cb_rt_sett_a.addItem(f"{s.name} (ID: {s.id})", s.id)
                self.cb_rt_sett_b.addItem(f"{s.name} (ID: {s.id})", s.id)
                
        sett_name_map = {s.id: s.name for s in settlements_list}
        
        for idx, route in enumerate(self.state.routes):
            sa_name = sett_name_map.get(route.settlement_a_id, f"Settlement {route.settlement_a_id}")
            sb_name = sett_name_map.get(route.settlement_b_id, f"Settlement {route.settlement_b_id}")
            self.route_list.addItem(f"Route {idx+1}: {sa_name} ◄-► {sb_name} ({route.route_type})")
            
        self.route_list.blockSignals(False)
        self.cb_rt_sett_a.blockSignals(False)
        self.cb_rt_sett_b.blockSignals(False)
        
    def on_route_list_selection(self, row):
        if row < 0:
            self.selected_route_idx = None
            return
        self.selected_route_idx = row
        route = self.state.routes[row]
        
        self.cb_rt_sett_a.blockSignals(True)
        self.cb_rt_sett_b.blockSignals(True)
        self.spin_rt_bandwidth.blockSignals(True)
        self.cb_rt_type.blockSignals(True)
        self.cb_rt_faction.blockSignals(True)
        
        idx_a = self.cb_rt_sett_a.findData(route.settlement_a_id)
        if idx_a >= 0: self.cb_rt_sett_a.setCurrentIndex(idx_a)
        
        idx_b = self.cb_rt_sett_b.findData(route.settlement_b_id)
        if idx_b >= 0: self.cb_rt_sett_b.setCurrentIndex(idx_b)
        
        self.spin_rt_bandwidth.setValue(route.bandwidth)
        self.cb_rt_type.setCurrentText(route.route_type)
        
        idx_fac = self.cb_rt_faction.findData(route.faction_id)
        if idx_fac >= 0: self.cb_rt_faction.setCurrentIndex(idx_fac)
        
        self.cb_rt_sett_a.blockSignals(False)
        self.cb_rt_sett_b.blockSignals(False)
        self.spin_rt_bandwidth.blockSignals(False)
        self.cb_rt_type.blockSignals(False)
        self.cb_rt_faction.blockSignals(False)

        self.update_active_brush_mode()
        
    def add_new_route(self):
        settlements = [hx.settlement for hx in self.state.hexes.values() if hx.settlement]
        if len(settlements) < 2:
            QMessageBox.warning(self, "Warning", "You need at least 2 settlements to build a trade route!")
            return
            
        new_route = TradeRoute(
            faction_id=1,
            settlement_a_id=settlements[0].id,
            settlement_b_id=settlements[1].id,
            bandwidth=10,
            route_type="Land"
        )
        self.state.routes.append(new_route)
        self.update_routes_ui()
        self.map_viewer.load_map(self.state)
        self.route_list.setCurrentRow(len(self.state.routes) - 1)
        
    def delete_selected_route(self):
        if self.selected_route_idx is None: return
        self.state.routes.pop(self.selected_route_idx)
        self.update_routes_ui()
        self.map_viewer.load_map(self.state)
        self.selected_route_idx = None
        
    def on_route_form_changed(self):
        if self.selected_route_idx is None: return
        route = self.state.routes[self.selected_route_idx]
        route.settlement_a_id = self.cb_rt_sett_a.currentData()
        route.settlement_b_id = self.cb_rt_sett_b.currentData()
        route.bandwidth = self.spin_rt_bandwidth.value()
        route.route_type = self.cb_rt_type.currentText()
        route.faction_id = self.cb_rt_faction.currentData()
        self.map_viewer.load_map(self.state)
        
    # --- RELIGIONS ---
    def update_religions_ui(self):
        self.rel_list.blockSignals(True)
        self.rel_list.clear()
        self.cb_rel_brush.blockSignals(True)
        self.cb_rel_brush.clear()
        self.cb_rel_brush.addItem("None / Cleanse", 0)
        
        for r_id, rel in self.state.religions.items():
            self.cb_rel_brush.addItem(rel.name, r_id)
            
            item = QListWidgetItem(f"{rel.name} (Type: {rel.type})")
            item.setIcon(create_color_icon(rel.color))
            self.rel_list.addItem(item)
            
        self.rel_list.blockSignals(False)
        self.cb_rel_brush.blockSignals(False)
        self.update_chaos_paths_ui()
        self.update_fringe_groups_ui()
        self.update_paragons_list()
        
    def add_new_religion(self):
        name, ok = QInputDialog.getText(self, "New Religion", "Enter religion name:")
        if ok and name:
            new_id = max(list(self.state.religions.keys()) + [0]) + 1
            color = random.choice(["#8E44AD", "#E74C3C", "#3498DB", "#2ECC71", "#F1C40F", "#E67E22", "#1ABC9C"])
            self.state.religions[new_id] = Religion(id=new_id, name=name, color=color)
            self.update_religions_ui()
            
    def on_rel_list_selection(self, row):
        if row < 0: return
        r_ids = list(self.state.religions.keys())
        self.selected_religion_id = r_ids[row]
        rel = self.state.religions[self.selected_religion_id]
        
        self.txt_rel_name.blockSignals(True)
        self.cb_rel_type.blockSignals(True)
        self.cb_rel_color.blockSignals(True)
        
        self.txt_rel_name.setText(rel.name)
        self.cb_rel_type.setCurrentText(rel.type)
        self.cb_rel_color.setCurrentText(rel.color)
        
        self.txt_rel_name.blockSignals(False)
        self.cb_rel_type.blockSignals(False)
        self.cb_rel_color.blockSignals(False)

        self.update_active_brush_mode()
        
    def on_religion_details_changed(self):
        if self.selected_religion_id is None: return
        rel = self.state.religions[self.selected_religion_id]
        rel.name = self.txt_rel_name.text()
        rel.type = self.cb_rel_type.currentText()
        rel.color = self.cb_rel_color.currentText()
        self.update_religions_ui()
        self.map_viewer.load_map(self.state)

    # --- CULTURES ---
    def update_cultures_ui(self):
        self.cul_list.blockSignals(True)
        self.cul_list.clear()
        self.cb_cul_brush.blockSignals(True)
        self.cb_cul_brush.clear()
        self.cb_cul_brush.addItem("None / Cleanse", 0)
        
        for c_id, cul in self.state.cultures.items():
            self.cb_cul_brush.addItem(cul.name, c_id)
            
            item = QListWidgetItem(f"{cul.name} (Lang: {cul.language_base})")
            item.setIcon(create_color_icon(cul.color))
            self.cul_list.addItem(item)
            
        self.cul_list.blockSignals(False)
        self.cb_cul_brush.blockSignals(False)
        
    def add_new_culture(self):
        name, ok = QInputDialog.getText(self, "New Culture", "Enter culture name:")
        if ok and name:
            new_id = max(list(self.state.cultures.keys()) + [0]) + 1
            color = random.choice(["#E67E22", "#F1C40F", "#2ECC71", "#3498DB", "#9B59B6", "#1ABC9C", "#E74C3C"])
            self.state.cultures[new_id] = Culture(id=new_id, name=name, color=color)
            self.update_cultures_ui()
            self.update_culture_names_ui()
            
    def on_cul_list_selection(self, row):
        if row < 0: return
        c_ids = list(self.state.cultures.keys())
        self.selected_culture_id = c_ids[row]
        cul = self.state.cultures[self.selected_culture_id]
        
        self.txt_cul_name.blockSignals(True)
        self.txt_cul_lang.blockSignals(True)
        self.cb_cul_color.blockSignals(True)
        self.spin_cul_exp.blockSignals(True)
        
        self.txt_cul_name.setText(cul.name)
        self.txt_cul_lang.setText(cul.language_base)
        self.cb_cul_color.setCurrentText(cul.color)
        self.spin_cul_exp.setValue(cul.expansionism)
        
        self.txt_cul_name.blockSignals(False)
        self.txt_cul_lang.blockSignals(False)
        self.cb_cul_color.blockSignals(False)
        self.spin_cul_exp.blockSignals(False)

        self.update_active_brush_mode()
        
    def on_culture_details_changed(self):
        if self.selected_culture_id is None: return
        cul = self.state.cultures[self.selected_culture_id]
        cul.name = self.txt_cul_name.text()
        cul.language_base = self.txt_cul_lang.text()
        cul.color = self.cb_cul_color.currentText()
        cul.expansionism = self.spin_cul_exp.value()
        self.update_cultures_ui()
        self.update_culture_names_ui()
        self.map_viewer.load_map(self.state)

    # --- MARKERS (POIS) ---
    def update_markers_ui(self):
        self.mark_list.clear()
        for idx, m in enumerate(self.state.markers):
            self.mark_list.addItem(f"{m.type} @ (q={m.global_q}, r={m.global_r})")
            
    def on_mark_list_selection(self, row):
        if row < 0:
            self.selected_marker_idx = None
            return
        self.selected_marker_idx = row
        m = self.state.markers[row]
        
        self.cb_mark_type.blockSignals(True)
        self.txt_mark_desc.blockSignals(True)
        self.spin_mark_q.blockSignals(True)
        self.spin_mark_r.blockSignals(True)
        
        self.cb_mark_type.setCurrentText(m.type)
        self.txt_mark_desc.setText(m.description)
        self.spin_mark_q.setValue(m.global_q)
        self.spin_mark_r.setValue(m.global_r)
        
        self.cb_mark_type.blockSignals(False)
        self.txt_mark_desc.blockSignals(False)
        self.spin_mark_q.blockSignals(False)
        self.spin_mark_r.blockSignals(False)

        self.update_active_brush_mode()
        
    def add_new_marker(self):
        m = Marker(id=len(self.state.markers)+1, type="Ruins", global_q=0, global_r=0)
        self.state.markers.append(m)
        self.update_markers_ui()
        self.map_viewer.load_map(self.state)
        self.mark_list.setCurrentRow(len(self.state.markers) - 1)
        
    def delete_selected_marker(self):
        if self.selected_marker_idx is None: return
        self.state.markers.pop(self.selected_marker_idx)
        self.update_markers_ui()
        self.map_viewer.load_map(self.state)
        self.selected_marker_idx = None
        
    def snap_marker_to_selected_hex(self):
        if self.selected_marker_idx is None or not self.selected_coord: return
        m = self.state.markers[self.selected_marker_idx]
        q, r = self.selected_coord
        m.global_q = q
        m.global_r = r
        self.spin_mark_q.setValue(q)
        self.spin_mark_r.setValue(r)
        self.update_markers_ui()
        self.map_viewer.load_map(self.state)
        
    def on_marker_details_changed(self):
        if self.selected_marker_idx is None: return
        m = self.state.markers[self.selected_marker_idx]
        m.type = self.cb_mark_type.currentText()
        m.description = self.txt_mark_desc.text()
        m.global_q = self.spin_mark_q.value()
        m.global_r = self.spin_mark_r.value()
        self.update_markers_ui()
        self.map_viewer.load_map(self.state)

    # --- SETTLEMENTS DIRECTORY ---
    def update_settlements_directory_ui(self):
        if not self.dialog_settlements: return
        # Populate buildings table
        if self.dialog_settlements:
            self.dialog_settlements.table_buildings.blockSignals(True)
            self.dialog_settlements.table_buildings.setRowCount(0)
            try:
                b_data = json.loads(s.inventory_json)
            except Exception:
                b_data = {}
            self.dialog_settlements.table_buildings.setRowCount(len(b_data))
            for row_idx, (b_type, count) in enumerate(b_data.items()):
                self.dialog_settlements.table_buildings.setItem(row_idx, 0, QTableWidgetItem(b_type))
                self.dialog_settlements.table_buildings.setItem(row_idx, 1, QTableWidgetItem(str(count)))
                self.dialog_settlements.table_buildings.setItem(row_idx, 2, QTableWidgetItem("100.0"))
            self.dialog_settlements.table_buildings.blockSignals(False)

        self.dialog_settlements.list_settlements.blockSignals(True)
        self.dialog_settlements.list_settlements.clear()
        
        self.dialog_settlements.cb_faction.blockSignals(True)
        self.dialog_settlements.cb_faction.clear()
        for f_id, f in self.state.factions.items():
            self.dialog_settlements.cb_faction.addItem(f.name, f_id)
        self.dialog_settlements.cb_faction.blockSignals(False)
        
        # Populate linked paragons combobox
        self.dialog_settlements.cb_linked_paragon.blockSignals(True)
        self.dialog_settlements.cb_linked_paragon.clear()
        self.dialog_settlements.cb_linked_paragon.addItem("None", 0)
        for hx_val in self.state.hexes.values():
            if hx_val.settlement:
                for p in hx_val.settlement.paragons:
                    self.dialog_settlements.cb_linked_paragon.addItem(p.name, p.id)
        self.dialog_settlements.cb_linked_paragon.blockSignals(False)
        
        self.settlement_directory_items = []
        for (q, r), hx in self.state.hexes.items():
            if hx.settlement:
                self.settlement_directory_items.append((hx.settlement, q, r))
                self.dialog_settlements.list_settlements.addItem(f"{hx.settlement.name} (Pop: {hx.settlement.population}, q={q}, r={r})")
                
        self.dialog_settlements.list_settlements.blockSignals(False)

    def on_settlement_directory_selection(self, row):
        if row < 0 or row >= len(self.settlement_directory_items):
            self.selected_directory_settlement_id = None
            return
        
        sett, q, r = self.settlement_directory_items[row]
        self.selected_directory_settlement_id = sett.id
        
        dlg = self.dialog_settlements
        dlg.txt_name.blockSignals(True)
        dlg.cb_faction.blockSignals(True)
        dlg.txt_pop.blockSignals(True)
        dlg.txt_wealth.blockSignals(True)
        dlg.txt_security.blockSignals(True)
        dlg.txt_cultists.blockSignals(True)
        dlg.txt_inv.blockSignals(True)
        
        dlg.txt_name.setText(sett.name)
        f_idx = dlg.cb_faction.findData(sett.faction_id)
        if f_idx >= 0:
            dlg.cb_faction.setCurrentIndex(f_idx)
        dlg.txt_pop.setText(str(sett.population))
        dlg.txt_wealth.setText(str(sett.wealth))
        dlg.txt_security.setText(str(sett.security_points))
        dlg.txt_cultists.setText(str(sett.hidden_cultists))
        dlg.txt_inv.setText(sett.inventory_json)
        
        dlg.txt_name.blockSignals(False)
        dlg.cb_faction.blockSignals(False)
        dlg.txt_pop.blockSignals(False)
        dlg.txt_wealth.blockSignals(False)
        dlg.txt_security.blockSignals(False)
        dlg.txt_cultists.blockSignals(False)
        dlg.txt_inv.blockSignals(False)
        
        self.map_viewer.select_hex(q, r)
        self.selected_coord = (q, r)
        self.on_hex_selected(q, r)

    def snap_to_directory_settlement(self):
        if self.selected_directory_settlement_id is None: return
        for (q, r), hx in self.state.hexes.items():
            if hx.settlement and hx.settlement.id == self.selected_directory_settlement_id:
                self.map_viewer.select_hex(q, r)
                self.selected_coord = (q, r)
                self.on_hex_selected(q, r)
                break

    def delete_directory_settlement(self):
        if self.selected_directory_settlement_id is None: return
        for (q, r), hx in self.state.hexes.items():
            if hx.settlement and hx.settlement.id == self.selected_directory_settlement_id:
                hx.settlement = None
                self.selected_directory_settlement_id = None
                self.update_settlements_directory_ui()
                self.map_viewer.load_map(self.state)
                break

    def on_directory_settlement_changed(self):
        if self.selected_directory_settlement_id is None: return
        for (q, r), hx in self.state.hexes.items():
            if hx.settlement and hx.settlement.id == self.selected_directory_settlement_id:
                sett = hx.settlement
                dlg = self.dialog_settlements
                sett.name = dlg.txt_name.text()
                sett.faction_id = dlg.cb_faction.currentData()
                try:
                    sett.population = int(dlg.txt_pop.text())
                except ValueError:
                    pass
                try:
                    sett.wealth = float(dlg.txt_wealth.text())
                except ValueError:
                    pass
                try:
                    sett.security_points = float(dlg.txt_security.text())
                except ValueError:
                    pass
                try:
                    sett.hidden_cultists = int(dlg.txt_cultists.text())
                except ValueError:
                    pass
                sett.inventory_json = dlg.txt_inv.toPlainText()
                
                # sync to other UIs
                self.update_settlements_directory_ui()
                self.on_hex_selected(q, r)
                self.map_viewer.load_map(self.state)
                break

    # --- NAME STYLE & LANGUAGES ---
    def update_culture_names_ui(self):
        if not self.dialog_names: return
        self.dialog_names.cul_list_names.blockSignals(True)
        self.dialog_names.cul_list_names.clear()
        self.culture_names_items = []
        for c_id, cul in self.state.cultures.items():
            self.culture_names_items.append(cul)
            self.dialog_names.cul_list_names.addItem(f"{cul.name} (Lang: {cul.language_base})")
        self.dialog_names.cul_list_names.blockSignals(False)

    def on_cul_names_selection(self, row):
        if row < 0 or row >= len(self.culture_names_items):
            self.selected_culture_names_id = None
            return
        
        cul = self.culture_names_items[row]
        self.selected_culture_names_id = cul.id
        
        dlg = self.dialog_names
        dlg.txt_cult_name.blockSignals(True)
        dlg.txt_lang_base.blockSignals(True)
        dlg.spin_exp.blockSignals(True)
        
        dlg.txt_cult_name.setText(cul.name)
        dlg.txt_lang_base.setText(cul.language_base)
        dlg.spin_exp.setValue(cul.expansionism)
        
        dlg.txt_cult_name.blockSignals(False)
        dlg.txt_lang_base.blockSignals(False)
        dlg.spin_exp.blockSignals(False)
        
        self.generate_preview_name()

    def on_culture_naming_changed(self):
        if self.selected_culture_names_id is None: return
        cul = self.state.cultures.get(self.selected_culture_names_id)
        if cul:
            dlg = self.dialog_names
            cul.name = dlg.txt_cult_name.text()
            cul.language_base = dlg.txt_lang_base.text()
            cul.expansionism = dlg.spin_exp.value()
            self.update_culture_names_ui()
            self.update_cultures_ui()

    def generate_preview_name(self):
        if self.selected_culture_names_id is None or not self.dialog_names: return
        cul = self.state.cultures.get(self.selected_culture_names_id)
        if cul:
            lang = cul.language_base.lower()
            prefixes = ["ael", "bel", "cor", "dar", "el", "fal", "gil", "had", "il", "jor"]
            suffixes = ["ond", "or", "ath", "en", "ius", "eth", "ian", "tor", "gan", "dor"]
            name = random.choice(prefixes).capitalize() + random.choice(suffixes)
            self.dialog_names.txt_name_preview.setText(name)

    # --- MAP PROPERTY UPDATES ---
    def on_sett_inv_changed(self):
        if not self.selected_coord: return
        hx = self.state.hexes.get(self.selected_coord)
        if hx and hx.settlement:
            hx.settlement.inventory_json = self.txt_sett_inv.toPlainText()

    def on_biome_changed(self, index):
        if not self.selected_coord: return
        hx = self.state.hexes.get(self.selected_coord)
        if hx:
            hx.biome = self.cb_biome.currentData()
            self.map_viewer.selected_item.update_style()
            
    def on_elevation_changed(self, value):
        if not self.selected_coord: return
        hx = self.state.hexes.get(self.selected_coord)
        if hx:
            hx.elevation = value
            
    def on_river_changed(self):
        if not self.selected_coord: return
        hx = self.state.hexes.get(self.selected_coord)
        if hx:
            try:
                hx.river_volume = int(self.txt_river.text())
            except ValueError:
                self.txt_river.setText(str(hx.river_volume))
                
    def on_lake_changed(self, checked):
        if not self.selected_coord: return
        hx = self.state.hexes.get(self.selected_coord)
        if hx:
            hx.is_lake = checked
            
    def on_chaos_changed(self, index):
        if not self.selected_coord: return
        hx = self.state.hexes.get(self.selected_coord)
        if hx:
            dom = self.cb_chaos.currentText()
            hx.chaos_domain = None if dom == "None" else dom
            self.map_viewer.selected_item.update_style()
            
    def on_has_sett_changed(self, checked):
        if not self.selected_coord: return
        hx = self.state.hexes.get(self.selected_coord)
        if hx:
            if checked and not hx.settlement:
                hx.settlement = Settlement(name="New Settlement", population=50)
                self.txt_sett_name.setText(hx.settlement.name)
                self.txt_sett_pop.setText(str(hx.settlement.population))
            elif not checked:
                hx.settlement = None
                self.txt_sett_name.setText("")
                self.txt_sett_pop.setText("")
            self.map_viewer.selected_item.update_style()
            self.on_hex_selected(*self.selected_coord)
            self.update_settlements_directory_ui()
            
    def on_sett_name_changed(self):
        if not self.selected_coord: return
        hx = self.state.hexes.get(self.selected_coord)
        if hx and hx.settlement:
            hx.settlement.name = self.txt_sett_name.text()
            self.update_settlements_directory_ui()
            
    def on_sett_faction_changed(self, index):
        if not self.selected_coord: return
        hx = self.state.hexes.get(self.selected_coord)
        if hx and hx.settlement:
            hx.settlement.faction_id = self.cb_sett_faction.currentData()
            self.update_settlements_directory_ui()
            
    def on_sett_pop_changed(self):
        if not self.selected_coord: return
        hx = self.state.hexes.get(self.selected_coord)
        if hx and hx.settlement:
            try:
                hx.settlement.population = int(self.txt_sett_pop.text())
            except ValueError:
                self.txt_sett_pop.setText(str(hx.settlement.population))
            self.update_settlements_directory_ui()

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = FMGMainWindow()
    window.show()
    sys.exit(app.exec())
