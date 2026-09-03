import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QFormLayout, QSpinBox, 
    QStackedWidget, QRadioButton, QButtonGroup, QCheckBox,
    QMessageBox, QScrollArea, QGridLayout, QFrame, QTextEdit
)
from PyQt6.QtCore import Qt
from beta_build.core.chassis_data import KINGDOMS, SUB_TYPES, BASE_STATS, ORIGINS
from core.models.skills_data import SKILL_TRACKS
from core.models.character_sheet import CharacterSheet

logger = logging.getLogger("CharForge")

class CharacterCreationScreen(QWidget):
    def __init__(self, bus):
        super().__init__()
        self.bus = bus
        self.setStyleSheet("background-color: #1a1e24; color: #d8d8d8;")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Title
        title = QLabel("CHARACTER FORGE")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #4CAF50; letter-spacing: 2px; margin: 10px;")
        self.layout.addWidget(title)
        
        # Wizard Stack
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)
        
        # State variables
        self.char_name = "Wanderer"
        self.selected_kingdom = KINGDOMS[0]
        self.selected_subtype = SUB_TYPES[0]
        self.selected_origin = "Unknown"
        self.size_shift = 0 # 0=Standard, -1=Down, 1=Up
        self.shift_stat = ""
        self.selected_paths = []
        self.final_stats = {}

        self._init_page_1()
        self._init_page_2()
        self._init_page_3()
        self._init_page_4()
        
        # Navigation
        nav_layout = QHBoxLayout()
        self.btn_prev = QPushButton("◄ Previous")
        self.btn_prev.clicked.connect(self.prev_step)
        
        self.step_label = QLabel("Step 1 of 4")
        self.step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.step_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #888;")
        
        self.btn_next = QPushButton("Next ►")
        self.btn_next.clicked.connect(self.next_step)
        
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.step_label)
        nav_layout.addWidget(self.btn_next)
        self.layout.addLayout(nav_layout)
        
        self.stack.setCurrentIndex(0)
        self.update_nav()

    # --- PAGE 1: GENUS SELECTION ---
    def _init_page_1(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        # Name
        name_layout = QHBoxLayout()
        name_label = QLabel("Subject Designation:")
        name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.name_input = QLineEdit("Wanderer")
        self.name_input.setStyleSheet("font-size: 18px; padding: 8px; background-color: #0f1115; border: 1px solid #4CAF50;")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        layout.addSpacing(20)
        
        # Kingdom Toggles
        k_label = QLabel("Select Biological Kingdom:")
        k_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #aaa;")
        layout.addWidget(k_label)
        
        self.kingdom_group = QButtonGroup(page)
        k_grid = QGridLayout()
        for i, k in enumerate(KINGDOMS):
            btn = QPushButton(k)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton { background-color: #2b323b; padding: 15px; font-size: 16px; border: 2px solid #3a414c; border-radius: 6px; }
                QPushButton:checked { background-color: #143314; border: 2px solid #4CAF50; color: #4CAF50; font-weight: bold; }
            """)
            if i == 0:
                btn.setChecked(True)
            self.kingdom_group.addButton(btn, i)
            k_grid.addWidget(btn, i // 2, i % 2)
            
        layout.addLayout(k_grid)
        layout.addSpacing(20)
        
        # Subtype Selection
        s_label = QLabel("Select Mechanical Sub-Type:")
        s_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #aaa;")
        layout.addWidget(s_label)
        
        self.subtype_combo = QComboBox()
        self.subtype_combo.addItems(SUB_TYPES)
        self.subtype_combo.setStyleSheet("font-size: 18px; padding: 8px; background-color: #0f1115; border: 1px solid #3a414c;")
        layout.addWidget(self.subtype_combo)
        
        layout.addStretch()
        page.setLayout(layout)
        self.stack.addWidget(page)

    # --- PAGE 2: BIOLOGICAL NICHE ---
    def _init_page_2(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        # Origin Select
        o_label = QLabel("Select Specific Origin:")
        o_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #aaa;")
        layout.addWidget(o_label)
        
        self.origin_combo = QComboBox()
        self.origin_combo.setStyleSheet("font-size: 18px; padding: 8px; background-color: #0f1115; border: 1px solid #3a414c;")
        layout.addWidget(self.origin_combo)
        
        layout.addSpacing(30)
        
        # Size Shift
        size_label = QLabel("Genetic Variation (Size Shift):")
        size_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #aaa;")
        layout.addWidget(size_label)
        
        self.size_group = QButtonGroup(page)
        
        self.btn_size_std = QRadioButton("Standard (No Stat Shift)")
        self.btn_size_std.setChecked(True)
        self.btn_size_down = QRadioButton("Shift Down (Small) - Requires +1 to Finesse or Reflex")
        self.btn_size_up = QRadioButton("Shift Up (Large) - Requires +1 to Might or Endurance")
        
        for btn, idx in [(self.btn_size_std, 0), (self.btn_size_down, -1), (self.btn_size_up, 1)]:
            btn.setStyleSheet("font-size: 16px; padding: 5px;")
            self.size_group.addButton(btn, idx)
            layout.addWidget(btn)
            
        layout.addSpacing(20)
        
        # Shift Stat Choice
        self.shift_choice = QComboBox()
        self.shift_choice.setStyleSheet("font-size: 16px; padding: 6px; background-color: #0f1115;")
        self.shift_choice.setEnabled(False)
        layout.addWidget(QLabel("Select Shift Bonus Target:"))
        layout.addWidget(self.shift_choice)
        
        self.size_group.idToggled.connect(self._on_size_toggled)
        
        layout.addStretch()
        page.setLayout(layout)
        self.stack.addWidget(page)
        
    def _on_size_toggled(self, id, checked):
        if not checked: return
        self.shift_choice.clear()
        if id == 0:
            self.shift_choice.setEnabled(False)
        elif id == -1:
            self.shift_choice.addItems(["finesse", "reflexes"])
            self.shift_choice.setEnabled(True)
        elif id == 1:
            self.shift_choice.addItems(["might", "endurance"])
            self.shift_choice.setEnabled(True)

    def refresh_page_2(self):
        self.selected_kingdom = self.kingdom_group.checkedButton().text()
        self.selected_subtype = self.subtype_combo.currentText()
        
        origins = ORIGINS.get(self.selected_kingdom, {}).get(self.selected_subtype, ["Standard"])
        self.origin_combo.clear()
        self.origin_combo.addItems(origins)

    # --- PAGE 3: THE PATH ---
    def _init_page_3(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        p_label = QLabel("Define Your Paths (1 Offense, 1 Defense, 2 Utility/Power):")
        p_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #4CAF50;")
        layout.addWidget(p_label)
        
        def format_track(k):
            t = SKILL_TRACKS[k]
            return f"{t['name']} ({t['category'].capitalize()})"

        # Categorize tracks
        offense_tracks = [k for k, v in SKILL_TRACKS.items() if v["category"].lower() == "offense"]
        defense_tracks = [k for k, v in SKILL_TRACKS.items() if v["category"].lower() == "defense"]
        utility_tracks = [k for k, v in SKILL_TRACKS.items() if v["category"].lower() in ["utility", "magic"]]
        
        self.path_1 = QComboBox()
        self.path_1.addItems([format_track(k) for k in offense_tracks])
        self.path_1.setProperty("keys", offense_tracks)
        
        self.path_2 = QComboBox()
        self.path_2.addItems([format_track(k) for k in defense_tracks])
        self.path_2.setProperty("keys", defense_tracks)
        
        self.path_3 = QComboBox()
        self.path_3.addItems([format_track(k) for k in utility_tracks])
        self.path_3.setProperty("keys", utility_tracks)
        if self.path_3.count() > 0: self.path_3.setCurrentIndex(0)
        
        self.path_4 = QComboBox()
        self.path_4.addItems([format_track(k) for k in utility_tracks])
        self.path_4.setProperty("keys", utility_tracks)
        if self.path_4.count() > 1: self.path_4.setCurrentIndex(1)
        
        form = QFormLayout()
        for label, widget in [
            ("Primary Offense:", self.path_1),
            ("Primary Defense:", self.path_2),
            ("Utility/Power 1:", self.path_3),
            ("Utility/Power 2:", self.path_4)
        ]:
            widget.setStyleSheet("font-size: 14px; padding: 6px; background-color: #0f1115; border: 1px solid #3a414c;")
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #aaa;")
            form.addRow(lbl, widget)
            
        layout.addLayout(form)
        layout.addStretch()
        page.setLayout(layout)
        self.stack.addWidget(page)

    def refresh_page_3(self):
        # Nothing strictly needs refreshing here based on page 2
        pass

    # --- PAGE 4: MANIFEST ---
    def _init_page_4(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("BIOLOGICAL & PATH MANIFEST")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #4CAF50;")
        layout.addWidget(title)
        
        self.manifest_text = QTextEdit()
        self.manifest_text.setReadOnly(True)
        self.manifest_text.setStyleSheet("font-size: 16px; font-family: monospace; background-color: #0a0c0f; border: 1px solid #3a414c; padding: 10px;")
        layout.addWidget(self.manifest_text)
        
        self.btn_finalize = QPushButton("FINALIZE & ENTER WORLD")
        self.btn_finalize.setStyleSheet("""
            QPushButton { background-color: #4CAF50; color: #0a0c0f; font-size: 20px; font-weight: bold; padding: 15px; border-radius: 8px; }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.btn_finalize.clicked.connect(self._finalize_character)
        layout.addWidget(self.btn_finalize)
        
        page.setLayout(layout)
        self.stack.addWidget(page)

    def refresh_page_4(self):
        """Calculate final stats and display manifest."""
        self.char_name = self.name_input.text() or "Wanderer"
        self.selected_origin = self.origin_combo.currentText()
        size_id = self.size_group.checkedId()
        shift_target = self.shift_choice.currentText() if size_id != 0 else None
        
        # Fetch chosen paths
        keys_1 = self.path_1.property("keys")
        keys_2 = self.path_2.property("keys")
        keys_3 = self.path_3.property("keys")
        keys_4 = self.path_4.property("keys")
        
        self.selected_paths = [
            keys_1[self.path_1.currentIndex()],
            keys_2[self.path_2.currentIndex()],
            keys_3[self.path_3.currentIndex()],
            keys_4[self.path_4.currentIndex()]
        ]
        
        # Load Base Stats
        base = BASE_STATS.get(self.selected_kingdom, {}).get(self.selected_subtype, {})
        self.final_stats = {
            "might": base.get("might", 5),
            "endurance": base.get("endurance", 5),
            "finesse": base.get("finesse", 5),
            "reflexes": base.get("reflex", 5),
            "vitality": base.get("vitality", 5),
            "fortitude": base.get("fortitude", 5),
            "knowledge": base.get("knowledge", 5),
            "logic": base.get("logic", 5),
            "awareness": base.get("awareness", 5),
            "intuition": base.get("intuition", 5),
            "charm": base.get("charm", 5),
            "willpower": base.get("willpower", 5),
        }
        
        # Apply Size Shift
        if size_id != 0 and shift_target:
            self.final_stats[shift_target] += 1
            
        # (Stat path modifiers removed as per skills_data.py structure)
            
        manifest = f"SUBJECT: {self.char_name}\n"
        manifest += f"KINGDOM: {self.selected_kingdom}\n"
        manifest += f"SUB-TYPE: {self.selected_subtype}\n"
        manifest += f"ORIGIN: {self.selected_origin}\n"
        manifest += "-"*30 + "\n"
        
        manifest += "CORE STATS (Post-Modifiers):\n"
        for stat, val in self.final_stats.items():
            manifest += f"  {stat.capitalize().ljust(12)}: {val}\n"
            
        manifest += "-"*30 + "\n"
        manifest += "SELECTED PATHS:\n"
        for path_key in self.selected_paths:
            track = SKILL_TRACKS[path_key]
            manifest += f"  - {track['name']} ({track['category']})\n"
            
        manifest += "\nBIOLOGICAL PASSIVES:\n"
        manifest += "  - Base Sub-Type Trait unlocked.\n"
        if size_id == 1: manifest += "  - Large Size Trait unlocked.\n"
        if size_id == -1: manifest += "  - Small Size Trait unlocked.\n"
        
        self.manifest_text.setText(manifest)

    def _finalize_character(self):
        """Instantiate Pydantic Model and Broadcast."""
        sheet = CharacterSheet(
            name=self.char_name,
            biological_origin=f"{self.selected_origin} ({self.selected_subtype})",
            stats=self.final_stats,
            skills=[SKILL_TRACKS[pk]["name"] for pk in self.selected_paths]
        )
        logger.info(f"Finalized Character: {self.char_name}")
        self.bus.publish("PLAYER_CREATED", sheet.model_dump())

    # --- NAVIGATION ---
    def prev_step(self):
        idx = self.stack.currentIndex()
        if idx > 0:
            self.stack.setCurrentIndex(idx - 1)
        self.update_nav()

    def next_step(self):
        idx = self.stack.currentIndex()
        if idx == 0:
            self.refresh_page_2()
            self.stack.setCurrentIndex(1)
        elif idx == 1:
            self.refresh_page_3()
            self.stack.setCurrentIndex(2)
        elif idx == 2:
            self.refresh_page_4()
            self.stack.setCurrentIndex(3)
        self.update_nav()

    def update_nav(self):
        idx = self.stack.currentIndex()
        self.step_label.setText(f"Step {idx + 1} of {self.stack.count()}")
        self.btn_prev.setEnabled(idx > 0)
        
        if idx == self.stack.count() - 1:
            self.btn_next.hide()
        else:
            self.btn_next.show()
