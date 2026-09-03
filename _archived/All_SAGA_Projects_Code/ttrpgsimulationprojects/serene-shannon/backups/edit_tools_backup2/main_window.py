# python_fmg/ui/main_window.py
import sys
import os
import json
import math
import random
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
    QLabel, QComboBox, QSlider, QCheckBox, QLineEdit, QGroupBox, 
    QFormLayout, QMessageBox, QFileDialog, QInputDialog, QListWidget,
    QRadioButton, QButtonGroup, QSpinBox, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QDoubleSpinBox, QTextEdit,
    QDockWidget, QStackedWidget, QScrollArea, QToolBar, QDialog
)
from PyQt6.QtCore import Qt, QSize, QPoint
from PyQt6.QtGui import QColor, QPalette, QPainter, QPolygon, QPen, QBrush

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

CHAOS_DOMAINS = ["None", "WARP_STORM", "CULT_INSURGENCY", "LUX_ECLIPSE", "NEXUS_BREACH"]

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

# ----------------------------------------------------
# Floating Dialog Subclasses for Individual Editors
# ----------------------------------------------------
class ElevationEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Heightmap (Elevation)", parent)
        layout = QVBoxLayout(self)
        
        self.spin_radius = QSpinBox()
        self.spin_radius.setRange(1, 10)
        self.spin_radius.setValue(parent.brush_radius_val)
        self.spin_radius.valueChanged.connect(parent.on_brush_radius_changed)
        
        self.cb_mode = QComboBox()
        self.cb_mode.addItems(["Align", "Raise", "Lower", "Smooth", "Disrupt"])
        self.cb_mode.setCurrentText(parent.map_viewer.elevation_brush_mode)
        self.cb_mode.currentTextChanged.connect(parent.on_elevation_mode_changed)
        
        self.spin_power = QSpinBox()
        self.spin_power.setRange(1, 10)
        self.spin_power.setValue(parent.map_viewer.brush_power)
        self.spin_power.valueChanged.connect(parent.on_brush_power_changed)
        
        self.btn_paint = QPushButton("🎨 Enable Elevation Brush")
        self.btn_paint.setCheckable(True)
        self.btn_paint.toggled.connect(parent.on_brush_toggled)

        layout.addWidget(QLabel("Brush Radius (Hexes):"))
        layout.addWidget(self.spin_radius)
        layout.addWidget(QLabel("Brush Mode:"))
        layout.addWidget(self.cb_mode)
        layout.addWidget(QLabel("Brush Power (Intensity):"))
        layout.addWidget(self.spin_power)
        layout.addWidget(QLabel("Elevation Align Value (0-15):"))
        layout.addWidget(parent.spin_elev_brush)
        layout.addWidget(self.btn_paint)
        layout.addStretch()

class BiomesEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Biomes Editor", parent)
        layout = QVBoxLayout(self)
        
        self.spin_radius = QSpinBox()
        self.spin_radius.setRange(1, 10)
        self.spin_radius.setValue(parent.brush_radius_val)
        self.spin_radius.valueChanged.connect(parent.on_brush_radius_changed)
        
        self.btn_paint = QPushButton("🎨 Enable Biome Brush")
        self.btn_paint.setCheckable(True)
        self.btn_paint.toggled.connect(parent.on_brush_toggled)

        layout.addWidget(QLabel("Brush Radius (Hexes):"))
        layout.addWidget(self.spin_radius)
        layout.addWidget(QLabel("Biome Material:"))
        layout.addWidget(parent.cb_biome_brush)
        layout.addWidget(self.btn_paint)
        layout.addStretch()

class FactionsEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Factions & States Editor", parent)
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll_layout = QVBoxLayout(content)

        self.spin_radius = QSpinBox()
        self.spin_radius.setRange(1, 10)
        self.spin_radius.setValue(parent.brush_radius_val)
        self.spin_radius.valueChanged.connect(parent.on_brush_radius_changed)

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
        details_form.addRow("Special Rule:", parent.txt_fac_rule)
        details_form.addRow("Shield Division:", parent.cb_coa_div)
        details_form.addRow("Primary Color:", parent.cb_coa_c1)
        details_form.addRow("Secondary Color:", parent.cb_coa_c2)
        details_form.addRow("Charge Motif:", parent.cb_coa_charge)
        details_form.addRow("Charge Color:", parent.cb_coa_charge_color)

        visual_group = QGroupBox("Shield & Diplomacy Matrix")
        visual_layout = QVBoxLayout(visual_group)
        visual_layout.addWidget(parent.coa_visual, alignment=Qt.AlignmentFlag.AlignCenter)
        visual_layout.addWidget(QLabel("Diplomatic Relations:"))
        visual_layout.addWidget(parent.diplomacy_table)

        scroll_layout.addWidget(QLabel("Brush Radius (Hexes):"))
        scroll_layout.addWidget(self.spin_radius)
        scroll_layout.addWidget(self.btn_paint)
        scroll_layout.addWidget(list_group)
        scroll_layout.addWidget(details_group)
        scroll_layout.addWidget(visual_group)
        content.setLayout(scroll_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)

class ProvincesEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Provinces Editor", parent)
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll_layout = QVBoxLayout(content)

        self.spin_radius = QSpinBox()
        self.spin_radius.setRange(1, 10)
        self.spin_radius.setValue(parent.brush_radius_val)
        self.spin_radius.valueChanged.connect(parent.on_brush_radius_changed)

        self.btn_paint = QPushButton("🎨 Paint Province Territory")
        self.btn_paint.setCheckable(True)
        self.btn_paint.toggled.connect(parent.on_brush_toggled)

        list_group = QGroupBox("Provinces List")
        list_layout = QVBoxLayout(list_group)
        list_layout.addWidget(parent.prov_list)
        list_layout.addWidget(parent.btn_add_prov)

        details_group = QGroupBox("Province Settings")
        details_form = QFormLayout(details_group)
        details_form.addRow("Name:", parent.txt_prov_name)
        details_form.addRow("Theme Color:", parent.cb_prov_color)
        details_form.addRow("Owner Faction:", parent.cb_prov_faction)

        scroll_layout.addWidget(QLabel("Brush Radius (Hexes):"))
        scroll_layout.addWidget(self.spin_radius)
        scroll_layout.addWidget(self.btn_paint)
        scroll_layout.addWidget(list_group)
        scroll_layout.addWidget(details_group)
        content.setLayout(scroll_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)

class ReligionsEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Religions Editor", parent)
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll_layout = QVBoxLayout(content)

        self.spin_radius = QSpinBox()
        self.spin_radius.setRange(1, 10)
        self.spin_radius.setValue(parent.brush_radius_val)
        self.spin_radius.valueChanged.connect(parent.on_brush_radius_changed)

        self.btn_paint = QPushButton("🎨 Paint Religion")
        self.btn_paint.setCheckable(True)
        self.btn_paint.toggled.connect(parent.on_brush_toggled)

        list_group = QGroupBox("Religions List")
        list_layout = QVBoxLayout(list_group)
        list_layout.addWidget(parent.rel_list)
        list_layout.addWidget(parent.btn_add_rel)

        details_group = QGroupBox("Religion Settings")
        details_form = QFormLayout(details_group)
        details_form.addRow("Name:", parent.txt_rel_name)
        details_form.addRow("Type:", parent.cb_rel_type)
        details_form.addRow("Theme Color:", parent.cb_rel_color)

        scroll_layout.addWidget(QLabel("Brush Radius (Hexes):"))
        scroll_layout.addWidget(self.spin_radius)
        scroll_layout.addWidget(self.btn_paint)
        scroll_layout.addWidget(list_group)
        scroll_layout.addWidget(details_group)
        content.setLayout(scroll_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)

class CulturesEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Cultures Editor", parent)
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll_layout = QVBoxLayout(content)

        self.spin_radius = QSpinBox()
        self.spin_radius.setRange(1, 10)
        self.spin_radius.setValue(parent.brush_radius_val)
        self.spin_radius.valueChanged.connect(parent.on_brush_radius_changed)

        self.btn_paint = QPushButton("🎨 Paint Culture")
        self.btn_paint.setCheckable(True)
        self.btn_paint.toggled.connect(parent.on_brush_toggled)

        list_group = QGroupBox("Cultures List")
        list_layout = QVBoxLayout(list_group)
        list_layout.addWidget(parent.cul_list)
        list_layout.addWidget(parent.btn_add_cul)

        details_group = QGroupBox("Culture Settings")
        details_form = QFormLayout(details_group)
        details_form.addRow("Name:", parent.txt_cul_name)
        details_form.addRow("Language:", parent.txt_cul_lang)
        details_form.addRow("Color:", parent.cb_cul_color)
        details_form.addRow("Expansionism:", parent.spin_cul_exp)

        scroll_layout.addWidget(QLabel("Brush Radius (Hexes):"))
        scroll_layout.addWidget(self.spin_radius)
        scroll_layout.addWidget(self.btn_paint)
        scroll_layout.addWidget(list_group)
        scroll_layout.addWidget(details_group)
        content.setLayout(scroll_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)

class ClimateEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Climate Editor (Temp & Moisture)", parent)
        layout = QVBoxLayout(self)
        
        self.spin_radius = QSpinBox()
        self.spin_radius.setRange(1, 10)
        self.spin_radius.setValue(parent.brush_radius_val)
        self.spin_radius.valueChanged.connect(parent.on_brush_radius_changed)
        
        self.btn_paint_temp = QPushButton("🌡️ Paint Temperature")
        self.btn_paint_temp.setCheckable(True)
        self.btn_paint_temp.toggled.connect(parent.on_brush_toggled)

        self.btn_paint_moist = QPushButton("💧 Paint Moisture")
        self.btn_paint_moist.setCheckable(True)
        self.btn_paint_moist.toggled.connect(parent.on_brush_toggled)

        layout.addWidget(QLabel("Brush Radius (Hexes):"))
        layout.addWidget(self.spin_radius)
        layout.addWidget(QLabel("Brush Temperature (0-255):"))
        layout.addWidget(parent.spin_temp_brush)
        layout.addWidget(self.btn_paint_temp)
        layout.addWidget(QLabel("Brush Moisture (0-255):"))
        layout.addWidget(parent.spin_moist_brush)
        layout.addWidget(self.btn_paint_moist)
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
        
        self.spin_radius = QSpinBox()
        self.spin_radius.setRange(1, 10)
        self.spin_radius.setValue(parent.brush_radius_val)
        self.spin_radius.valueChanged.connect(parent.on_brush_radius_changed)
        
        self.btn_paint_river = QPushButton("🌊 Paint River Volume")
        self.btn_paint_river.setCheckable(True)
        self.btn_paint_river.toggled.connect(parent.on_brush_toggled)

        self.btn_toggle_lake = QPushButton("💧 Toggle Lake")
        self.btn_toggle_lake.setCheckable(True)
        self.btn_toggle_lake.toggled.connect(parent.on_brush_toggled)

        layout.addWidget(QLabel("Brush Radius (Hexes):"))
        layout.addWidget(self.spin_radius)
        layout.addWidget(QLabel("River Volume:"))
        layout.addWidget(parent.spin_river_brush)
        layout.addWidget(self.btn_paint_river)
        layout.addWidget(QLabel("Lake State Brush:"))
        layout.addWidget(parent.chk_lake_brush)
        layout.addWidget(self.btn_toggle_lake)
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
        
        self.spin_radius = QSpinBox()
        self.spin_radius.setRange(1, 10)
        self.spin_radius.setValue(parent.brush_radius_val)
        self.spin_radius.valueChanged.connect(parent.on_brush_radius_changed)
        
        self.btn_paint = QPushButton("🌀 Paint Chaos Domain")
        self.btn_paint.setCheckable(True)
        self.btn_paint.toggled.connect(parent.on_brush_toggled)

        layout.addWidget(QLabel("Brush Radius (Hexes):"))
        layout.addWidget(self.spin_radius)
        layout.addWidget(QLabel("Domain Type:"))
        layout.addWidget(parent.cb_chaos_brush)
        layout.addWidget(self.btn_paint)
        layout.addStretch()

class SettlementsEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Settlements Directory", parent)
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

        self.txt_pop = QLineEdit()
        self.txt_pop.editingFinished.connect(parent.on_directory_settlement_changed)
        form_layout.addRow("Population:", self.txt_pop)

        self.txt_wealth = QLineEdit()
        self.txt_wealth.editingFinished.connect(parent.on_directory_settlement_changed)
        form_layout.addRow("Wealth Rating:", self.txt_wealth)

        self.txt_security = QLineEdit()
        self.txt_security.editingFinished.connect(parent.on_directory_settlement_changed)
        form_layout.addRow("Security Points:", self.txt_security)

        self.txt_cultists = QLineEdit()
        self.txt_cultists.editingFinished.connect(parent.on_directory_settlement_changed)
        form_layout.addRow("Hidden Cultists:", self.txt_cultists)

        self.txt_inv = QTextEdit()
        self.txt_inv.setMinimumHeight(80)
        self.txt_inv.textChanged.connect(parent.on_directory_settlement_changed)
        form_layout.addRow("Goods (JSON):", self.txt_inv)

        scroll_layout.addWidget(QLabel("<b>All Settlements</b>"))
        scroll_layout.addWidget(self.list_settlements)
        scroll_layout.addWidget(self.btn_snap)
        scroll_layout.addWidget(self.btn_delete)
        scroll_layout.addWidget(form_group)
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

        self.txt_cult_name = QLineEdit()
        self.txt_cult_name.editingFinished.connect(parent.on_culture_naming_changed)
        form_layout.addRow("Culture Name:", self.txt_cult_name)

        self.txt_lang_base = QLineEdit()
        self.txt_lang_base.editingFinished.connect(parent.on_culture_naming_changed)
        form_layout.addRow("Language Base Name:", self.txt_lang_base)

        self.spin_exp = QDoubleSpinBox()
        self.spin_exp.setRange(0.1, 10.0)
        self.spin_exp.setValue(1.0)
        self.spin_exp.valueChanged.connect(parent.on_culture_naming_changed)
        form_layout.addRow("Expansionism Base:", self.spin_exp)

        self.txt_name_preview = QLineEdit()
        self.txt_name_preview.setReadOnly(True)
        self.btn_preview = QPushButton("🎲 Generate Name Preview")
        self.btn_preview.clicked.connect(parent.generate_preview_name)

        form_layout.addRow("Name Sample:", self.txt_name_preview)
        form_layout.addRow("", self.btn_preview)

        scroll_layout.addWidget(form_group)
        content.setLayout(scroll_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)

class MarkersEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Markers Editor (POIs)", parent)
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll_layout = QVBoxLayout(content)

        self.btn_paint = QPushButton("📍 Place/Move Marker on Map")
        self.btn_paint.setCheckable(True)
        self.btn_paint.toggled.connect(parent.on_brush_toggled)

        list_group = QGroupBox("Markers List")
        list_layout = QVBoxLayout(list_group)
        list_layout.addWidget(parent.mark_list)
        list_layout.addWidget(parent.btn_add_mark)
        list_layout.addWidget(parent.btn_del_mark)

        details_group = QGroupBox("Marker Details")
        details_form = QFormLayout(details_group)
        details_form.addRow("Marker Type:", parent.cb_mark_type)
        details_form.addRow("Description:", parent.txt_mark_desc)
        details_form.addRow("q Coordinates:", parent.spin_mark_q)
        details_form.addRow("r Coordinates:", parent.spin_mark_r)
        details_form.addRow("", parent.btn_snap_mark)

        scroll_layout.addWidget(self.btn_paint)
        scroll_layout.addWidget(list_group)
        scroll_layout.addWidget(details_group)
        content.setLayout(scroll_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)

class ForcesEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Active Forces Editor", parent)
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll_layout = QVBoxLayout(content)

        self.btn_paint = QPushButton("⚔️ Deploy/Move Regiment on Map")
        self.btn_paint.setCheckable(True)
        self.btn_paint.toggled.connect(parent.on_brush_toggled)

        list_group = QGroupBox("Active Forces List")
        list_layout = QVBoxLayout(list_group)
        list_layout.addWidget(parent.entity_list)
        list_layout.addWidget(parent.btn_add_ent)
        list_layout.addWidget(parent.btn_del_ent)

        details_group = QGroupBox("Force Attributes")
        details_form = QFormLayout(details_group)
        details_form.addRow("Force Type:", parent.cb_ent_type)
        details_form.addRow("q Coordinates:", parent.spin_ent_q)
        details_form.addRow("r Coordinates:", parent.spin_ent_r)
        details_form.addRow("", parent.btn_snap_coords)
        details_form.addRow("mq Nested Coord:", parent.spin_ent_mq)
        details_form.addRow("mr Nested Coord:", parent.spin_ent_mr)
        details_form.addRow("Action Radius:", parent.spin_ent_radius)
        details_form.addRow("Duration (Ticks):", parent.spin_ent_duration)
        details_form.addRow("Intensity Scale:", parent.spin_ent_intensity)
        details_form.addRow("Faction Alignment:", parent.cb_ent_align)

        scroll_layout.addWidget(self.btn_paint)
        scroll_layout.addWidget(list_group)
        scroll_layout.addWidget(details_group)
        content.setLayout(scroll_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)

class RoutesEditorDialog(FloatingEditorDialog):
    def __init__(self, parent):
        super().__init__("Trade Routes Editor", parent)
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll_layout = QVBoxLayout(content)

        self.btn_paint = QPushButton("🛣️ Link Trade Route on Map")
        self.btn_paint.setCheckable(True)
        self.btn_paint.toggled.connect(parent.on_brush_toggled)

        list_group = QGroupBox("Trade Routes List")
        list_layout = QVBoxLayout(list_group)
        list_layout.addWidget(parent.route_list)
        list_layout.addWidget(parent.btn_add_rt)
        list_layout.addWidget(parent.btn_del_rt)

        details_group = QGroupBox("Route Details")
        details_form = QFormLayout(details_group)
        details_form.addRow("Settlement A:", parent.cb_rt_sett_a)
        details_form.addRow("Settlement B:", parent.cb_rt_sett_b)
        details_form.addRow("Bandwidth:", parent.spin_rt_bandwidth)
        details_form.addRow("Route Type:", parent.cb_rt_type)
        details_form.addRow("Owner Faction:", parent.cb_rt_faction)

        scroll_layout.addWidget(self.btn_paint)
        scroll_layout.addWidget(list_group)
        scroll_layout.addWidget(details_group)
        content.setLayout(scroll_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)

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
            if dialog and hasattr(dialog, 'spin_radius'):
                dialog.spin_radius.blockSignals(True)
                dialog.spin_radius.setValue(val)
                dialog.spin_radius.blockSignals(False)

    def on_elevation_mode_changed(self, mode):
        self.map_viewer.elevation_brush_mode = mode

    def on_brush_power_changed(self, val):
        self.map_viewer.brush_power = val

    def update_active_brush_mode(self):
        self.map_viewer.brush_radius = self.brush_radius_val
        if self.dialog_elevation and self.dialog_elevation.btn_paint.isChecked():
            self.map_viewer.set_tool_mode("Paint Elevation", self.spin_elev_brush.value())
        elif self.dialog_biomes and self.dialog_biomes.btn_paint.isChecked():
            self.map_viewer.set_tool_mode("Paint Biome", self.cb_biome_brush.currentData())
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
            self.map_viewer.set_tool_mode("Paint Temperature", self.spin_temp_brush.value())
        elif self.dialog_climate and self.dialog_climate.btn_paint_moist.isChecked():
            self.map_viewer.set_tool_mode("Paint Moisture", self.spin_moist_brush.value())
        elif self.dialog_rivers and self.dialog_rivers.btn_paint_river.isChecked():
            self.map_viewer.set_tool_mode("Paint River Volume", self.spin_river_brush.value())
        elif self.dialog_rivers and self.dialog_rivers.btn_toggle_lake.isChecked():
            self.map_viewer.set_tool_mode("Toggle Lake", int(self.chk_lake_brush.isChecked()))
        elif self.dialog_chaos and self.dialog_chaos.btn_paint.isChecked():
            self.map_viewer.set_tool_mode("Paint Chaos", self.cb_chaos_brush.currentText())
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
            
    def generate_new_world(self, seed=100, prompt=True):
        if prompt:
            seed_val, ok = QInputDialog.getInt(self, "Generate Map", "Enter Seed Value:", seed, 1, 999999)
            if not ok:
                return
            seed = seed_val
            
        self.state = generate_world(R=57, elevation_seed=seed)
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
            elif attr == "province_id": hx.province_id = val
            elif attr == "faction_id": 
                if hx.settlement: hx.settlement.faction_id = val
            elif attr == "temp": hx.p2 = val
            elif attr == "moist": hx.p3 = val
            elif attr == "river_volume": hx.river_volume = val
            elif attr == "is_lake": hx.is_lake = bool(val)
            elif attr == "chaos_domain_str":
                hx.chaos_domain = self.cb_chaos_brush.currentText()
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
        
        self.faction_list.clear()
        for f_id, f in self.state.factions.items():
            self.cb_sett_faction.addItem(f.name, f_id)
            self.cb_ent_align.addItem(f.name)
            self.cb_rt_faction.addItem(f.name, f_id)
            self.cb_fac_paint_brush.addItem(f.name, f_id)
            self.faction_list.addItem(f"{f.name} (ID: {f_id})")
            
        self.cb_sett_faction.blockSignals(False)
        self.cb_ent_align.blockSignals(False)
        self.cb_rt_faction.blockSignals(False)
        self.cb_fac_paint_brush.blockSignals(False)
        
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
            self.prov_list.addItem(f"{prov.name} (ID: {p_id})")
            
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
            self.rel_list.addItem(f"{rel.name} (Type: {rel.type})")
            self.cb_rel_brush.addItem(rel.name, r_id)
            
        self.rel_list.blockSignals(False)
        self.cb_rel_brush.blockSignals(False)
        
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
            self.cul_list.addItem(f"{cul.name} (Lang: {cul.language_base})")
            self.cb_cul_brush.addItem(cul.name, c_id)
            
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
        self.dialog_settlements.list_settlements.blockSignals(True)
        self.dialog_settlements.list_settlements.clear()
        
        self.dialog_settlements.cb_faction.blockSignals(True)
        self.dialog_settlements.cb_faction.clear()
        for f_id, f in self.state.factions.items():
            self.dialog_settlements.cb_faction.addItem(f.name, f_id)
        self.dialog_settlements.cb_faction.blockSignals(False)
        
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
