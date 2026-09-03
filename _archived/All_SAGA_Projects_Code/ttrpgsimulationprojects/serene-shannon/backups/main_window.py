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
    QRadioButton, QButtonGroup, QSpinBox, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QDoubleSpinBox, QTextEdit
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

class FMGMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shatterlands Python World Builder & Configuration App")
        self.resize(1450, 950)
        
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
        self.db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "shatterlands_simulator", "core_engine", "world_state.db"))
        
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
            QTabWidget::pane {
                border: 1px solid #29292E;
                background-color: #121214;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #202024;
                border: 1px solid #29292E;
                padding: 8px 16px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #18181B;
                border-bottom-color: #18181B;
                color: #04D361;
            }
        """)

        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # 1. Left Panel: Map & Global Setup Controls
        left_panel = QVBoxLayout()
        main_layout.addLayout(left_panel, 1)
        
        db_group = QGroupBox("Database & Sync")
        db_layout = QVBoxLayout(db_group)
        self.db_label = QLabel(f"DB Path: {os.path.basename(self.db_path)}")
        db_layout.addWidget(self.db_label)
        
        btn_load_db = QPushButton("📥 Load from Simulator DB")
        btn_load_db.clicked.connect(self.load_db)
        db_layout.addWidget(btn_load_db)
        
        btn_save_db = QPushButton("💾 Push to Simulator DB")
        btn_save_db.clicked.connect(self.save_db)
        db_layout.addWidget(btn_save_db)
        
        btn_run_tick = QPushButton("▶ Run 1 Simulation Tick")
        btn_run_tick.clicked.connect(self.run_sim_tick)
        db_layout.addWidget(btn_run_tick)
        left_panel.addWidget(db_group)
        
        gen_group = QGroupBox("Generator Operations")
        gen_layout = QVBoxLayout(gen_group)
        btn_gen = QPushButton("🌌 Generate New World")
        btn_gen.clicked.connect(self.generate_new_world)
        gen_layout.addWidget(btn_gen)
        
        btn_import_map = QPushButton("📂 Import Azgaar .map / JSON")
        btn_import_map.clicked.connect(self.import_azgaar_map)
        gen_layout.addWidget(btn_import_map)
        
        btn_export_json = QPushButton("📤 Export JSON to File")
        btn_export_json.clicked.connect(self.export_json)
        gen_layout.addWidget(btn_export_json)
        left_panel.addWidget(gen_group)
        
        # Map View Options Section
        view_group = QGroupBox("Map View Layers")
        view_layout = QVBoxLayout(view_group)
        self.cb_view_layer = QComboBox()
        self.cb_view_layer.addItems(["Biomes", "Elevation", "Temperature", "Moisture", "Chaos / Infestation", "Factions & States", "Religions", "Cultures", "Provinces"])
        self.cb_view_layer.currentIndexChanged.connect(self.on_view_layer_changed)
        view_layout.addWidget(self.cb_view_layer)
        left_panel.addWidget(view_group)
        
        # Paint brushes in Left Column
        brush_group = QGroupBox("Visual Painting Brushes")
        brush_layout = QVBoxLayout(brush_group)
        self.tool_group = QButtonGroup(self)
        
        self.radio_select = QRadioButton("Select / Inspect Mode")
        self.radio_select.setChecked(True)
        self.radio_select.toggled.connect(self.update_tool_mode)
        self.tool_group.addButton(self.radio_select)
        brush_layout.addWidget(self.radio_select)
        
        self.radio_paint_elev = QRadioButton("Paint Elevation Mode")
        self.radio_paint_elev.toggled.connect(self.update_tool_mode)
        self.tool_group.addButton(self.radio_paint_elev)
        brush_layout.addWidget(self.radio_paint_elev)
        
        self.spin_elev_brush = QSpinBox()
        self.spin_elev_brush.setRange(0, 15)
        self.spin_elev_brush.setValue(5)
        self.spin_elev_brush.valueChanged.connect(self.update_tool_mode)
        brush_layout.addWidget(self.spin_elev_brush)
        
        self.radio_paint_biome = QRadioButton("Paint Biome Mode")
        self.radio_paint_biome.toggled.connect(self.update_tool_mode)
        self.tool_group.addButton(self.radio_paint_biome)
        brush_layout.addWidget(self.radio_paint_biome)
        
        self.cb_biome_brush = QComboBox()
        for idx, b_name in BIOME_NAMES.items():
            self.cb_biome_brush.addItem(b_name, idx)
        self.cb_biome_brush.currentIndexChanged.connect(self.update_tool_mode)
        brush_layout.addWidget(self.cb_biome_brush)
        
        # Paint custom layers: Religion, Culture, Province
        self.radio_paint_rel = QRadioButton("Paint Religion Mode")
        self.radio_paint_rel.toggled.connect(self.update_tool_mode)
        self.tool_group.addButton(self.radio_paint_rel)
        brush_layout.addWidget(self.radio_paint_rel)
        self.cb_rel_brush = QComboBox()
        brush_layout.addWidget(self.cb_rel_brush)
        
        self.radio_paint_cul = QRadioButton("Paint Culture Mode")
        self.radio_paint_cul.toggled.connect(self.update_tool_mode)
        self.tool_group.addButton(self.radio_paint_cul)
        brush_layout.addWidget(self.radio_paint_cul)
        self.cb_cul_brush = QComboBox()
        brush_layout.addWidget(self.cb_cul_brush)
        
        left_panel.addWidget(brush_group)
        left_panel.addStretch()

        # 2. Main Tabbed Widget Area
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs, 4.5)
        
        # --- TAB 1: WORLD MAP EDITOR ---
        map_tab = QWidget()
        map_tab_layout = QHBoxLayout(map_tab)
        
        self.map_viewer = WorldMapViewer()
        self.map_viewer.hex_selected.connect(self.on_hex_selected)
        self.map_viewer.hex_painted.connect(self.on_hex_painted)
        map_tab_layout.addWidget(self.map_viewer, 3)
        
        hex_sidebar = QVBoxLayout()
        map_tab_layout.addLayout(hex_sidebar, 1.3)
        
        self.hex_group = QGroupBox("Hex Inspector")
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
        hex_sidebar.addWidget(self.hex_group)
        
        self.sett_group = QGroupBox("Settlement & Goods Inventory")
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
        self.sett_form.addRow("Goods Inventory (JSON):", self.txt_sett_inv)
        hex_sidebar.addWidget(self.sett_group)
        hex_sidebar.addStretch()
        
        self.tabs.addTab(map_tab, "🗺️ World Map Editor")
        
        # --- TAB 2: FACTIONS & COAT-OF-ARMS ---
        faction_tab = QWidget()
        faction_layout = QHBoxLayout(faction_tab)
        
        list_group = QGroupBox("Factions List")
        list_layout = QVBoxLayout(list_group)
        self.faction_list = QListWidget()
        self.faction_list.currentRowChanged.connect(self.on_faction_list_selection)
        list_layout.addWidget(self.faction_list)
        
        btn_add_fac = QPushButton("➕ Add Faction")
        btn_add_fac.clicked.connect(self.add_new_faction)
        list_layout.addWidget(btn_add_fac)
        faction_layout.addWidget(list_group, 1)
        
        details_group = QGroupBox("Faction Attributes & Shield Editor")
        details_form = QFormLayout(details_group)
        
        self.txt_fac_name = QLineEdit()
        self.txt_fac_name.editingFinished.connect(self.on_faction_details_changed)
        details_form.addRow("Faction Name:", self.txt_fac_name)
        
        self.txt_fac_treasury = QLineEdit()
        self.txt_fac_treasury.editingFinished.connect(self.on_faction_details_changed)
        details_form.addRow("Treasury:", self.txt_fac_treasury)
        
        self.spin_fac_tech = QSpinBox()
        self.spin_fac_tech.setRange(1, 100)
        self.spin_fac_tech.valueChanged.connect(self.on_faction_details_changed)
        details_form.addRow("Tech Level:", self.spin_fac_tech)
        
        self.txt_fac_rule = QLineEdit()
        self.txt_fac_rule.editingFinished.connect(self.on_faction_details_changed)
        details_form.addRow("Special Rule:", self.txt_fac_rule)
        
        self.cb_coa_div = QComboBox()
        self.cb_coa_div.addItems(COA_DIVISIONS)
        self.cb_coa_div.currentIndexChanged.connect(self.on_coa_changed)
        details_form.addRow("Shield Division:", self.cb_coa_div)
        
        self.cb_coa_c1 = QComboBox()
        self.cb_coa_c1.addItems(list(COA_TINCTURES.keys()))
        self.cb_coa_c1.currentIndexChanged.connect(self.on_coa_changed)
        details_form.addRow("Primary Color:", self.cb_coa_c1)
        
        self.cb_coa_c2 = QComboBox()
        self.cb_coa_c2.addItems(list(COA_TINCTURES.keys()))
        self.cb_coa_c2.currentIndexChanged.connect(self.on_coa_changed)
        details_form.addRow("Secondary Color:", self.cb_coa_c2)
        
        self.cb_coa_charge = QComboBox()
        self.cb_coa_charge.addItems(COA_CHARGES)
        self.cb_coa_charge.currentIndexChanged.connect(self.on_coa_changed)
        details_form.addRow("Charge Motif:", self.cb_coa_charge)
        
        self.cb_coa_charge_color = QComboBox()
        self.cb_coa_charge_color.addItems(list(COA_TINCTURES.keys()))
        self.cb_coa_charge_color.currentIndexChanged.connect(self.on_coa_changed)
        details_form.addRow("Charge Color:", self.cb_coa_charge_color)
        faction_layout.addWidget(details_group, 1.5)
        
        visual_group = QGroupBox("Visual Shield & Diplomacy Matrix")
        visual_layout = QVBoxLayout(visual_group)
        self.coa_visual = CoatOfArmsWidget()
        visual_layout.addWidget(self.coa_visual, alignment=Qt.AlignmentFlag.AlignCenter)
        
        visual_layout.addWidget(QLabel("Diplomatic Relations (WAR, ALLIANCE, NEUTRAL)"))
        self.diplomacy_table = QTableWidget()
        self.diplomacy_table.setColumnCount(3)
        self.diplomacy_table.setHorizontalHeaderLabels(["Target Faction", "Status", "Trust Level"])
        self.diplomacy_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.diplomacy_table.cellChanged.connect(self.on_diplomacy_table_changed)
        visual_layout.addWidget(self.diplomacy_table)
        faction_layout.addWidget(visual_group, 2)
        
        self.tabs.addTab(faction_tab, "🛡️ Faction & CoA Editor")
        
        # --- TAB 3: PARAGONS & AGENTS EDITOR ---
        paragon_tab = QWidget()
        paragon_layout = QHBoxLayout(paragon_tab)
        
        plist_group = QGroupBox("Paragons in Settlement")
        plist_layout = QVBoxLayout(plist_group)
        self.lbl_paragon_sett = QLabel("No settlement selected")
        plist_layout.addWidget(self.lbl_paragon_sett)
        
        self.paragon_list = QListWidget()
        self.paragon_list.currentRowChanged.connect(self.on_paragon_list_selection)
        plist_layout.addWidget(self.paragon_list)
        
        btn_add_par = QPushButton("➕ Add Paragon / Merchant")
        btn_add_par.clicked.connect(self.add_new_paragon)
        plist_layout.addWidget(btn_add_par)
        
        btn_del_par = QPushButton("➖ Remove Paragon")
        btn_del_par.clicked.connect(self.delete_selected_paragon)
        plist_layout.addWidget(btn_del_par)
        paragon_layout.addWidget(plist_group, 1.2)
        
        peditor_group = QGroupBox("Paragon Attributes & Motivation")
        peditor_form = QFormLayout(peditor_group)
        self.txt_p_name = QLineEdit()
        self.txt_p_name.editingFinished.connect(self.on_paragon_form_changed)
        peditor_form.addRow("Name:", self.txt_p_name)
        
        self.cb_p_archetype = QComboBox()
        self.cb_p_archetype.addItems(["Commander", "Merchant", "Mage", "Scholar", "Rogue"])
        self.cb_p_archetype.currentIndexChanged.connect(self.on_paragon_form_changed)
        peditor_form.addRow("Archetype:", self.cb_p_archetype)
        
        self.spin_p_level = QSpinBox()
        self.spin_p_level.setRange(1, 100)
        self.spin_p_level.valueChanged.connect(self.on_paragon_form_changed)
        peditor_form.addRow("Level:", self.spin_p_level)
        
        self.txt_p_motivation = QLineEdit()
        self.txt_p_motivation.editingFinished.connect(self.on_paragon_form_changed)
        peditor_form.addRow("Motivation:", self.txt_p_motivation)
        
        self.txt_p_stats = QLineEdit()
        self.txt_p_stats.editingFinished.connect(self.on_paragon_form_changed)
        peditor_form.addRow("Stats (JSON):", self.txt_p_stats)
        
        self.txt_p_traits = QLineEdit()
        self.txt_p_traits.editingFinished.connect(self.on_paragon_form_changed)
        peditor_form.addRow("Traits (JSON Array):", self.txt_p_traits)
        paragon_layout.addWidget(peditor_group, 2)
        
        self.tabs.addTab(paragon_tab, "🧙 Paragons & Agents")
        
        # --- TAB 4: WORLD ENTITIES & MILITARY REGIMENTS ---
        entity_tab = QWidget()
        entity_layout = QHBoxLayout(entity_tab)
        
        elist_group = QGroupBox("Active Forces List")
        elist_layout = QVBoxLayout(elist_group)
        self.entity_list = QListWidget()
        self.entity_list.currentRowChanged.connect(self.on_entity_list_selection)
        elist_layout.addWidget(self.entity_list)
        
        btn_add_ent = QPushButton("➕ Deploy New Regiment / Force")
        btn_add_ent.clicked.connect(self.add_new_entity)
        elist_layout.addWidget(btn_add_ent)
        
        btn_del_ent = QPushButton("➖ Delete Selected Force")
        btn_del_ent.clicked.connect(self.delete_selected_entity)
        elist_layout.addWidget(btn_del_ent)
        entity_layout.addWidget(elist_group, 1.2)
        
        eeditor_group = QGroupBox("Regiment & Force Editor")
        eeditor_form = QFormLayout(eeditor_group)
        
        self.cb_ent_type = QComboBox()
        self.cb_ent_type.addItems(["Regiment", "Cult Monster", "Null Zealots", "Chaos Creature", "Hurricane", "Chaos Storm"])
        self.cb_ent_type.currentIndexChanged.connect(self.on_entity_form_changed)
        eeditor_form.addRow("Type:", self.cb_ent_type)
        
        coord_layout = QHBoxLayout()
        self.spin_ent_q = QSpinBox()
        self.spin_ent_q.setRange(-100, 100)
        self.spin_ent_q.valueChanged.connect(self.on_entity_form_changed)
        self.spin_ent_r = QSpinBox()
        self.spin_ent_r.setRange(-100, 100)
        self.spin_ent_r.valueChanged.connect(self.on_entity_form_changed)
        coord_layout.addWidget(QLabel("q:"))
        coord_layout.addWidget(self.spin_ent_q)
        coord_layout.addWidget(QLabel("r:"))
        coord_layout.addWidget(self.spin_ent_r)
        eeditor_form.addRow("Global Grid Coordinates:", coord_layout)
        
        btn_snap_coords = QPushButton("📍 Set Coordinates to Selected Map Hex")
        btn_snap_coords.clicked.connect(self.snap_entity_to_selected_hex)
        eeditor_form.addRow("", btn_snap_coords)
        
        micro_coord_layout = QHBoxLayout()
        self.spin_ent_mq = QSpinBox()
        self.spin_ent_mq.setRange(-5, 5)
        self.spin_ent_mq.valueChanged.connect(self.on_entity_form_changed)
        self.spin_ent_mr = QSpinBox()
        self.spin_ent_mr.setRange(-5, 5)
        self.spin_ent_mr.valueChanged.connect(self.on_entity_form_changed)
        micro_coord_layout.addWidget(QLabel("mq:"))
        micro_coord_layout.addWidget(self.spin_ent_mq)
        micro_coord_layout.addWidget(QLabel("mr:"))
        micro_coord_layout.addWidget(self.spin_ent_mr)
        eeditor_form.addRow("Nested Grid Coordinates:", micro_coord_layout)
        
        self.spin_ent_radius = QSpinBox()
        self.spin_ent_radius.setRange(1, 100)
        self.spin_ent_radius.valueChanged.connect(self.on_entity_form_changed)
        eeditor_form.addRow("Action Radius:", self.spin_ent_radius)
        
        self.spin_ent_duration = QSpinBox()
        self.spin_ent_duration.setRange(1, 1000)
        self.spin_ent_duration.valueChanged.connect(self.on_entity_form_changed)
        eeditor_form.addRow("Duration (Ticks):", self.spin_ent_duration)
        
        self.spin_ent_intensity = QDoubleSpinBox()
        self.spin_ent_intensity.setRange(0.1, 100.0)
        self.spin_ent_intensity.setValue(1.0)
        self.spin_ent_intensity.valueChanged.connect(self.on_entity_form_changed)
        eeditor_form.addRow("Intensity Scalar:", self.spin_ent_intensity)
        
        self.cb_ent_align = QComboBox()
        self.cb_ent_align.currentIndexChanged.connect(self.on_entity_form_changed)
        eeditor_form.addRow("Faction Alignment:", self.cb_ent_align)
        entity_layout.addWidget(eeditor_group, 2)
        
        self.tabs.addTab(entity_tab, "⚔️ Regiments & Active Forces")
        
        # --- TAB 5: TRADE ROUTES EDITOR ---
        route_tab = QWidget()
        route_layout = QHBoxLayout(route_tab)
        
        rlist_group = QGroupBox("Active Routes List")
        rlist_layout = QVBoxLayout(rlist_group)
        self.route_list = QListWidget()
        self.route_list.currentRowChanged.connect(self.on_route_list_selection)
        rlist_layout.addWidget(self.route_list)
        
        btn_add_rt = QPushButton("➕ Establish Trade Route")
        btn_add_rt.clicked.connect(self.add_new_route)
        rlist_layout.addWidget(btn_add_rt)
        
        btn_del_rt = QPushButton("➖ Dissolve Selected Route")
        btn_del_rt.clicked.connect(self.delete_selected_route)
        rlist_layout.addWidget(btn_del_rt)
        route_layout.addWidget(rlist_group, 1.2)
        
        reditor_group = QGroupBox("Trade Route Attributes")
        reditor_form = QFormLayout(reditor_group)
        self.cb_rt_sett_a = QComboBox()
        self.cb_rt_sett_a.currentIndexChanged.connect(self.on_route_form_changed)
        reditor_form.addRow("Settlement A:", self.cb_rt_sett_a)
        
        self.cb_rt_sett_b = QComboBox()
        self.cb_rt_sett_b.currentIndexChanged.connect(self.on_route_form_changed)
        reditor_form.addRow("Settlement B:", self.cb_rt_sett_b)
        
        self.spin_rt_bandwidth = QSpinBox()
        self.spin_rt_bandwidth.setRange(1, 1000)
        self.spin_rt_bandwidth.valueChanged.connect(self.on_route_form_changed)
        reditor_form.addRow("Bandwidth (Capacity):", self.spin_rt_bandwidth)
        
        self.cb_rt_type = QComboBox()
        self.cb_rt_type.addItems(["Land", "Sea", "Underground"])
        self.cb_rt_type.currentIndexChanged.connect(self.on_route_form_changed)
        reditor_form.addRow("Route Type:", self.cb_rt_type)
        
        self.cb_rt_faction = QComboBox()
        self.cb_rt_faction.currentIndexChanged.connect(self.on_route_form_changed)
        reditor_form.addRow("Owner Faction:", self.cb_rt_faction)
        route_layout.addWidget(reditor_group, 2)
        
        self.tabs.addTab(route_tab, "🛣️ Trade Routes")
        
        # --- TAB 6: RELIGIONS EDITOR ---
        rel_tab = QWidget()
        rel_layout = QHBoxLayout(rel_tab)
        
        rel_list_group = QGroupBox("Religions List")
        rel_list_layout = QVBoxLayout(rel_list_group)
        self.rel_list = QListWidget()
        self.rel_list.currentRowChanged.connect(self.on_rel_list_selection)
        rel_list_layout.addWidget(self.rel_list)
        
        btn_add_rel = QPushButton("➕ Add Religion")
        btn_add_rel.clicked.connect(self.add_new_religion)
        rel_list_layout.addWidget(btn_add_rel)
        rel_layout.addWidget(rel_list_group, 1)
        
        rel_editor_group = QGroupBox("Religion Settings")
        rel_editor_form = QFormLayout(rel_editor_group)
        self.txt_rel_name = QLineEdit()
        self.txt_rel_name.editingFinished.connect(self.on_religion_details_changed)
        rel_editor_form.addRow("Name:", self.txt_rel_name)
        
        self.cb_rel_type = QComboBox()
        self.cb_rel_type.addItems(["Polytheism", "Monotheism", "Animism", "Shamanism"])
        self.cb_rel_type.currentIndexChanged.connect(self.on_religion_details_changed)
        rel_editor_form.addRow("Type:", self.cb_rel_type)
        
        self.cb_rel_color = QComboBox()
        self.cb_rel_color.addItems(["#8E44AD", "#E74C3C", "#3498DB", "#2ECC71", "#F1C40F", "#E67E22", "#1ABC9C"])
        self.cb_rel_color.currentIndexChanged.connect(self.on_religion_details_changed)
        rel_editor_form.addRow("Theme Color:", self.cb_rel_color)
        rel_layout.addWidget(rel_editor_group, 2)
        
        self.tabs.addTab(rel_tab, "🕍 Religions")
        
        # --- TAB 7: CULTURES EDITOR ---
        cul_tab = QWidget()
        cul_layout = QHBoxLayout(cul_tab)
        
        cul_list_group = QGroupBox("Cultures List")
        cul_list_layout = QVBoxLayout(cul_list_group)
        self.cul_list = QListWidget()
        self.cul_list.currentRowChanged.connect(self.on_cul_list_selection)
        cul_list_layout.addWidget(self.cul_list)
        
        btn_add_cul = QPushButton("➕ Add Culture")
        btn_add_cul.clicked.connect(self.add_new_culture)
        cul_list_layout.addWidget(btn_add_cul)
        cul_layout.addWidget(cul_list_group, 1)
        
        cul_editor_group = QGroupBox("Culture Settings")
        cul_editor_form = QFormLayout(cul_editor_group)
        self.txt_cul_name = QLineEdit()
        self.txt_cul_name.editingFinished.connect(self.on_culture_details_changed)
        cul_editor_form.addRow("Name:", self.txt_cul_name)
        
        self.txt_cul_lang = QLineEdit()
        self.txt_cul_lang.editingFinished.connect(self.on_culture_details_changed)
        cul_editor_form.addRow("Language Base:", self.txt_cul_lang)
        
        self.cb_cul_color = QComboBox()
        self.cb_cul_color.addItems(["#E67E22", "#F1C40F", "#2ECC71", "#3498DB", "#9B59B6", "#1ABC9C", "#E74C3C"])
        self.cb_cul_color.currentIndexChanged.connect(self.on_culture_details_changed)
        cul_editor_form.addRow("Culture Color:", self.cb_cul_color)
        
        self.spin_cul_exp = QDoubleSpinBox()
        self.spin_cul_exp.setRange(0.1, 10.0)
        self.spin_cul_exp.setValue(1.0)
        self.spin_cul_exp.valueChanged.connect(self.on_culture_details_changed)
        cul_editor_form.addRow("Expansionism:", self.spin_cul_exp)
        cul_layout.addWidget(cul_editor_group, 2)
        
        self.tabs.addTab(cul_tab, "🎨 Cultures")
        
        # --- TAB 8: MARKERS (POINTS OF INTEREST) ---
        mark_tab = QWidget()
        mark_layout = QHBoxLayout(mark_tab)
        
        mark_list_group = QGroupBox("Markers List")
        mark_list_layout = QVBoxLayout(mark_list_group)
        self.mark_list = QListWidget()
        self.mark_list.currentRowChanged.connect(self.on_mark_list_selection)
        mark_list_layout.addWidget(self.mark_list)
        
        btn_add_mark = QPushButton("➕ Place New Marker / POI")
        btn_add_mark.clicked.connect(self.add_new_marker)
        mark_list_layout.addWidget(btn_add_mark)
        
        btn_del_mark = QPushButton("➖ Delete Selected Marker")
        btn_del_mark.clicked.connect(self.delete_selected_marker)
        mark_list_layout.addWidget(btn_del_mark)
        mark_layout.addWidget(mark_list_group, 1.2)
        
        mark_editor_group = QGroupBox("Marker Details")
        mark_editor_form = QFormLayout(mark_editor_group)
        self.cb_mark_type = QComboBox()
        self.cb_mark_type.addItems(["Ruins", "Dungeon", "Cave", "Portal", "Obelisk"])
        self.cb_mark_type.currentIndexChanged.connect(self.on_marker_details_changed)
        mark_editor_form.addRow("Marker Type:", self.cb_mark_type)
        
        self.txt_mark_desc = QLineEdit()
        self.txt_mark_desc.editingFinished.connect(self.on_marker_details_changed)
        mark_editor_form.addRow("Description:", self.txt_mark_desc)
        
        mark_coord_layout = QHBoxLayout()
        self.spin_mark_q = QSpinBox()
        self.spin_mark_q.setRange(-100, 100)
        self.spin_mark_q.valueChanged.connect(self.on_marker_details_changed)
        self.spin_mark_r = QSpinBox()
        self.spin_mark_r.setRange(-100, 100)
        self.spin_mark_r.valueChanged.connect(self.on_marker_details_changed)
        mark_coord_layout.addWidget(QLabel("q:"))
        mark_coord_layout.addWidget(self.spin_mark_q)
        mark_coord_layout.addWidget(QLabel("r:"))
        mark_coord_layout.addWidget(self.spin_mark_r)
        mark_editor_form.addRow("Coordinates:", mark_coord_layout)
        
        btn_snap_mark = QPushButton("📍 Set Coordinates to Selected Map Hex")
        btn_snap_mark.clicked.connect(self.snap_marker_to_selected_hex)
        mark_editor_form.addRow("", btn_snap_mark)
        mark_layout.addWidget(mark_editor_group, 2)
        
        self.tabs.addTab(mark_tab, "📍 Markers (POIs)")

        self.generate_new_world()
        
    def on_view_layer_changed(self):
        self.map_viewer.set_render_mode(self.cb_view_layer.currentText())
        
    def update_tool_mode(self):
        if self.radio_select.isChecked():
            self.map_viewer.set_tool_mode("Select")
        elif self.radio_paint_elev.isChecked():
            self.map_viewer.set_tool_mode("Paint Elevation", self.spin_elev_brush.value())
        elif self.radio_paint_biome.isChecked():
            self.map_viewer.set_tool_mode("Paint Biome", self.cb_biome_brush.currentData())
        elif self.radio_paint_rel.isChecked():
            self.map_viewer.set_tool_mode("Paint Religion", self.cb_rel_brush.currentData())
        elif self.radio_paint_cul.isChecked():
            self.map_viewer.set_tool_mode("Paint Culture", self.cb_cul_brush.currentData())
            
    def generate_new_world(self):
        seed, ok = QInputDialog.getInt(self, "Generate Map", "Enter Seed Value:", 100, 1, 999999)
        if ok:
            self.state = generate_world(R=57, elevation_seed=seed)
            self.map_viewer.load_map(self.state)
            self.update_factions_ui()
            self.update_entities_ui()
            self.update_routes_ui()
            self.update_religions_ui()
            self.update_cultures_ui()
            self.update_markers_ui()
            self.statusBar().showMessage("Generated new procedural map state.", 3000)
            self.radio_select.setChecked(True)
            
    def import_azgaar_map(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Azgaar .map / JSON", "", "JSON Files (*.json *.map)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.state = convert_azgaar_to_hex_grid(data, R=57)
                self.map_viewer.load_map(self.state)
                self.update_factions_ui()
                self.update_entities_ui()
                self.update_routes_ui()
                self.update_religions_ui()
                self.update_cultures_ui()
                self.update_markers_ui()
                self.statusBar().showMessage(f"Successfully converted and loaded map: {os.path.basename(path)}", 3000)
                self.radio_select.setChecked(True)
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
            self.update_entities_ui()
            self.update_routes_ui()
            self.update_religions_ui()
            self.update_cultures_ui()
            self.update_markers_ui()
            self.statusBar().showMessage("Successfully loaded map state from simulator DB.", 3000)
            self.radio_select.setChecked(True)
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
        
        self.faction_list.clear()
        for f_id, f in self.state.factions.items():
            self.cb_sett_faction.addItem(f.name, f_id)
            self.cb_ent_align.addItem(f.name)
            self.cb_rt_faction.addItem(f.name, f_id)
            self.faction_list.addItem(f"{f.name} (ID: {f_id})")
            
        self.cb_sett_faction.blockSignals(False)
        self.cb_ent_align.blockSignals(False)
        self.cb_rt_faction.blockSignals(False)
        
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
        self.tabs.setCurrentIndex(0)
        
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
            # Random color from presets
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
        
    def on_culture_details_changed(self):
        if self.selected_culture_id is None: return
        cul = self.state.cultures[self.selected_culture_id]
        cul.name = self.txt_cul_name.text()
        cul.language_base = self.txt_cul_lang.text()
        cul.color = self.cb_cul_color.currentText()
        cul.expansionism = self.spin_cul_exp.value()
        self.update_cultures_ui()
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
            
    def on_sett_name_changed(self):
        if not self.selected_coord: return
        hx = self.state.hexes.get(self.selected_coord)
        if hx and hx.settlement:
            hx.settlement.name = self.txt_sett_name.text()
            
    def on_sett_faction_changed(self, index):
        if not self.selected_coord: return
        hx = self.state.hexes.get(self.selected_coord)
        if hx and hx.settlement:
            hx.settlement.faction_id = self.cb_sett_faction.currentData()
            
    def on_sett_pop_changed(self):
        if not self.selected_coord: return
        hx = self.state.hexes.get(self.selected_coord)
        if hx and hx.settlement:
            try:
                hx.settlement.population = int(self.txt_sett_pop.text())
            except ValueError:
                self.txt_sett_pop.setText(str(hx.settlement.population))

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = FMGMainWindow()
    window.show()
    sys.exit(app.exec())
