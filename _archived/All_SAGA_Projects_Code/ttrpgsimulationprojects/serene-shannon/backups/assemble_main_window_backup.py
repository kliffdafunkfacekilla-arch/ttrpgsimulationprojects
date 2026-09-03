import os

main_path = "c:\\\\Users\\\\krazy\\\\Documents\\\\antigravity\\\\serene-shannon\\\\python_fmg\\\\ui\\\\main_window.py"

with open(main_path, "r", encoding="utf-8") as f:
    code = f.read()

# Let's write the definitions for our new/repurposed editor dialogs.
new_dialogs = """# ----------------------------------------------------
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
        for stat in ["Strength", "Dexterity", "Intelligence", "Wisdom", "Charisma"]:
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
"""

start_pos = code.find("class ElevationEditorDialog(FloatingEditorDialog):")
end_pos = code.find("class CellInspectorDialog(FloatingEditorDialog):")
if start_pos != -1 and end_pos != -1:
    code = code[:start_pos] + new_dialogs + "\n" + code[end_pos:]

# Replace FMGMainWindow init to define new dialogs
old_dialogs_init = """        self.dialog_settlements = None
        self.dialog_names = None"""

new_dialogs_init = """        self.dialog_settlements = None
        self.dialog_names = None
        self.dialog_trait_pool = None
        self.dialog_economy = None"""

code = code.replace(old_dialogs_init, new_dialogs_init)

# In FMGMainWindow.__init__, add menu/toolbar actions for Calendar, Trait Pool, Economy
old_editor_btns = """        self.btn_open_routes = QPushButton("🛣️ Trade Routes")
        self.btn_open_routes.clicked.connect(self.open_routes_editor)
        scroll_layout.addWidget(self.btn_open_routes)"""

new_editor_btns = """        self.btn_open_routes = QPushButton("🛣️ Trade Routes")
        self.btn_open_routes.clicked.connect(self.open_routes_editor)
        scroll_layout.addWidget(self.btn_open_routes)
        
        self.btn_open_trait_pool = QPushButton("🧬 Traits Pool")
        self.btn_open_trait_pool.clicked.connect(self.open_trait_pool_editor)
        scroll_layout.addWidget(self.btn_open_trait_pool)
        
        self.btn_open_calendar = QPushButton("📅 Calendar & Seasons")
        self.btn_open_calendar.clicked.connect(self.open_names_editor)
        scroll_layout.addWidget(self.btn_open_calendar)
        
        self.btn_open_economy = QPushButton("🪙 Economy & Goods")
        self.btn_open_economy.clicked.connect(self.open_economy_editor)
        scroll_layout.addWidget(self.btn_open_economy)"""

code = code.replace(old_editor_btns, new_editor_btns)

# Let's add open methods for the new dialogs on FMGMainWindow
open_methods = """    def open_trait_pool_editor(self):
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
        self.dialog_economy.activateWindow()"""

# Insert open methods and new helper methods
# We will insert them right after def open_routes_editor(self):
old_open_routes = """    def open_routes_editor(self):
        if not self.dialog_routes:
            self.dialog_routes = RoutesEditorDialog(self)
        self.dialog_routes.show()
        self.dialog_routes.raise_()
        self.dialog_routes.activateWindow()"""

# Helper methods on FMGMainWindow
helper_methods = """    # --- NEW SIMULATION TOOLS HELPERS ---
    
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
        all_goods = [{"name": g["name"], "cost": g["cost"], "effect": g["effect"], "type": "Refined"} for g in self.state.refined_goods] + \
                    [{"name": g["name"], "cost": g["cost"], "effect": g["effect"], "type": "Luxury"} for g in self.state.luxury_goods]
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
        new_state = generate_world(R=57, elevation_seed=random.randint(1, 9999))
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
"""

new_open_routes = old_open_routes + "\n\n" + open_methods + "\n\n" + helper_methods

code = code.replace(old_open_routes, new_open_routes)

# Let's fix the Factions Editor list update when selected
old_faction_selection_block = """        self.cb_coa_div.blockSignals(False)
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

        self.update_active_brush_mode()"""

new_faction_selection_block = """        self.cb_coa_div.blockSignals(False)
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

        self.update_active_brush_mode()"""

code = code.replace(old_faction_selection_block, new_faction_selection_block)

# Update on_faction_details_changed to read the new fields too!
old_fac_details_changed = """    def on_faction_details_changed(self):
        if self.selected_faction_id is None: return
        f = self.state.factions[self.selected_faction_id]
        f.name = self.txt_fac_name.text()
        try:
            f.treasury = float(self.txt_fac_treasury.text())
        except ValueError:
            self.txt_fac_treasury.setText(str(f.treasury))
        f.technology_level = self.spin_fac_tech.value()
        f.special_rule = self.txt_fac_rule.text()
        self.update_factions_ui()"""

new_fac_details_changed = """    def on_faction_details_changed(self):
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
            
        self.update_factions_ui()"""

code = code.replace(old_fac_details_changed, new_fac_details_changed)

# Replace NameStyleEditorDialog click handler with CalendarEditorDialog
old_names_init = """        if not self.dialog_names:
            self.dialog_names = NameStyleEditorDialog(self)
        self.dialog_names.show()"""

new_names_init = """        if not self.dialog_names:
            self.dialog_names = CalendarEditorDialog(self)
        self.update_calendar_ui()
        self.dialog_names.show()"""

code = code.replace(old_names_init, new_names_init)

# Hook up updates on load/new map to refresh our new editors
old_religions_ui_call = "        self.update_religions_ui()"
new_religions_ui_call = "        self.update_religions_ui()\n        self.update_chaos_paths_ui()\n        self.update_fringe_groups_ui()\n        self.update_paragons_list()"

code = code.replace(old_religions_ui_call, new_religions_ui_call)

# Constrain painting Paragon areas of influence to their own faction territory
old_province_paint_line = '            elif attr == "province_id": hx.province_id = val'
new_province_paint_line = """            elif attr == "province_id":
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
                        hx.province_id = val"""

code = code.replace(old_province_paint_line, new_province_paint_line)

# Let's fix the settlement linked paragon select in update and select callbacks:
old_sett_select_line = """        self.txt_inv.setText(s.inventory_json)"""
new_sett_select_line = """        self.txt_inv.setText(s.inventory_json)
        
        # Populate linked paragons
        if self.dialog_settlements:
            self.dialog_settlements.cb_linked_paragon.blockSignals(True)
            self.dialog_settlements.cb_linked_paragon.clear()
            self.dialog_settlements.cb_linked_paragon.addItem("None", 0)
            
            # Find all paragons in settlement list
            for hx_val in self.state.hexes.values():
                if hx_val.settlement:
                    for p in hx_val.settlement.paragons:
                        self.dialog_settlements.cb_linked_paragon.addItem(p.name, p.id)
                        if p.id == s.linked_paragon_id:
                            self.dialog_settlements.cb_linked_paragon.setCurrentIndex(self.dialog_settlements.cb_linked_paragon.count() - 1)
            self.dialog_settlements.cb_linked_paragon.blockSignals(False)"""

code = code.replace(old_sett_select_line, new_sett_select_line)

# When updating settlement, save linked paragon
old_sett_update_line = """        try:
            s.population = int(self.txt_pop.text())
        except ValueError:
            self.txt_pop.setText(str(s.population))"""

new_sett_update_line = """        try:
            s.population = int(self.txt_pop.text())
        except ValueError:
            self.txt_pop.setText(str(s.population))
            
        if self.dialog_settlements:
            s.linked_paragon_id = self.dialog_settlements.cb_linked_paragon.currentData() or None"""

code = code.replace(old_sett_update_line, new_sett_update_line)

# Update other combos in settlements:cb_faction
old_sett_fac_list = """        self.dialog_settlements.cb_faction.blockSignals(True)
        self.dialog_settlements.cb_faction.clear()
        for f_id, f in self.state.factions.items():
            self.dialog_settlements.cb_faction.addItem(f.name, f_id)
        self.dialog_settlements.cb_faction.blockSignals(False)"""

new_sett_fac_list = old_sett_fac_list + """
        
        # Populate linked paragons combobox
        self.dialog_settlements.cb_linked_paragon.blockSignals(True)
        self.dialog_settlements.cb_linked_paragon.clear()
        self.dialog_settlements.cb_linked_paragon.addItem("None", 0)
        for hx_val in self.state.hexes.values():
            if hx_val.settlement:
                for p in hx_val.settlement.paragons:
                    self.dialog_settlements.cb_linked_paragon.addItem(p.name, p.id)
        self.dialog_settlements.cb_linked_paragon.blockSignals(False)"""

code = code.replace(old_sett_fac_list, new_sett_fac_list)

# When selecting settlement, show building counts in table
old_sett_table_building_refresh = """        self.dialog_settlements.list_settlements.blockSignals(True)"""
new_sett_table_building_refresh = """        # Populate buildings table
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

        self.dialog_settlements.list_settlements.blockSignals(True)"""

code = code.replace(old_sett_table_building_refresh, new_sett_table_building_refresh)

with open(main_path, "w", encoding="utf-8") as f_out:
    f_out.write(code)

print("Assembly complete.")
