from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QFormLayout, QSpinBox, 
    QStackedWidget, QRadioButton, QButtonGroup, QCheckBox,
    QMessageBox, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt
from rules_engine.chassis_data import (KINGDOMS, SUB_TYPES, BASE_STATS, ORIGINS, 
                                       OFFENSE_TRACKS, DEFENSE_TRACKS, POWER_TRACKS)

class CharacterCreationScreen(QWidget):
    def __init__(self, on_complete=None):
        super().__init__()
        self.on_complete = on_complete
        self.setStyleSheet("background-color: #222; color: white;")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        title = QLabel("Initialize Biological Chassis")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #44FF44;")
        self.layout.addWidget(title)
        
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)
        
        self.step_label = QLabel("Step 1 of 4")
        self.layout.addWidget(self.step_label)
        
        nav_layout = QHBoxLayout()
        self.btn_prev = QPushButton("Previous")
        self.btn_prev.clicked.connect(self.prev_step)
        self.btn_next = QPushButton("Next")
        self.btn_next.clicked.connect(self.next_step)
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.btn_next)
        self.layout.addLayout(nav_layout)
        
        self.current_stats = {}
        
        self._init_step1()
        self._init_step2()
        self._init_step3()
        self._init_step4()
        
        self.stack.setCurrentIndex(0)
        self.update_nav()
        
    def _init_step1(self):
        page = QWidget()
        layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.kingdom_combo = QComboBox()
        self.kingdom_combo.addItems(KINGDOMS)
        
        self.subtype_combo = QComboBox()
        self.subtype_combo.addItems(SUB_TYPES)
        
        self.kingdom_combo.currentTextChanged.connect(self._update_origins)
        self.subtype_combo.currentTextChanged.connect(self._update_origins)
        
        layout.addRow("Chassis Designation:", self.name_input)
        layout.addRow("Biological Kingdom:", self.kingdom_combo)
        layout.addRow("Mechanical Sub-Type:", self.subtype_combo)
        
        page.setLayout(layout)
        self.stack.addWidget(page)
        
    def _init_step2(self):
        page = QWidget()
        layout = QFormLayout()
        
        self.origin_combo = QComboBox()
        layout.addRow("Biological Origin:", self.origin_combo)
        
        self.size_group = QButtonGroup()
        self.size_standard = QRadioButton("Standard (No Stat Shift)")
        self.size_standard.setChecked(True)
        self.size_down = QRadioButton("Shift Down (+1 Finesse or +1 Reflex)")
        self.size_up = QRadioButton("Shift Up (+1 Might or +1 Endurance)")
        
        self.size_group.addButton(self.size_standard)
        self.size_group.addButton(self.size_down)
        self.size_group.addButton(self.size_up)
        
        layout.addRow(QLabel("Genetic Variation (Size Shift):"))
        layout.addRow(self.size_standard)
        layout.addRow(self.size_down)
        layout.addRow(self.size_up)
        
        self.shift_choice = QComboBox()
        self.shift_choice.addItems(["Might", "Endurance"]) # Will update based on radio
        self.shift_choice.setEnabled(False)
        layout.addRow("Shift Bonus to:", self.shift_choice)
        
        self.size_down.toggled.connect(self._update_shift_combo)
        self.size_up.toggled.connect(self._update_shift_combo)
        self.size_standard.toggled.connect(self._update_shift_combo)
        
        page.setLayout(layout)
        self.stack.addWidget(page)
        self._update_origins() # Populate initially
        
    def _update_shift_combo(self):
        if self.size_standard.isChecked():
            self.shift_choice.clear()
            self.shift_choice.setEnabled(False)
        elif self.size_down.isChecked():
            self.shift_choice.clear()
            self.shift_choice.addItems(["finesse", "reflex"])
            self.shift_choice.setEnabled(True)
        elif self.size_up.isChecked():
            self.shift_choice.clear()
            self.shift_choice.addItems(["might", "endurance"])
            self.shift_choice.setEnabled(True)
            
    def _update_origins(self):
        kingdom = self.kingdom_combo.currentText()
        subtype = self.subtype_combo.currentText()
        self.origin_combo.clear()
        origins = ORIGINS.get(kingdom, {}).get(subtype, [])
        self.origin_combo.addItems(origins)
        
    def _init_step3(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        info = QLabel("Professional Training: Choose 1 Offense, 1 Defense, and 2 Power tracks.\nEach grants +2 to its governing attribute.")
        layout.addWidget(info)
        
        scroll = QScrollArea()
        scroll_w = QWidget()
        grid = QGridLayout()
        
        self.offense_cbs = []
        self.defense_cbs = []
        self.power_cbs = []
        
        def populate(title, col, track_dict, cb_list):
            grid.addWidget(QLabel(f"<b>{title}</b>"), 0, col)
            r = 1
            for name, stat in track_dict.items():
                cb = QCheckBox(f"{name} (+2 {stat.title()})")
                cb_list.append((name, cb, stat))
                grid.addWidget(cb, r, col)
                r += 1

        populate("Offense (Pick 1)", 0, OFFENSE_TRACKS, self.offense_cbs)
        populate("Defense (Pick 1)", 1, DEFENSE_TRACKS, self.defense_cbs)
        populate("Power (Pick 2)", 2, POWER_TRACKS, self.power_cbs)
        
        scroll_w.setLayout(grid)
        scroll.setWidget(scroll_w)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        page.setLayout(layout)
        self.stack.addWidget(page)
        
    def _init_step4(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        self.summary_label = QLabel("Summary will appear here.")
        layout.addWidget(self.summary_label)
        
        # We rely on the parent window's LAUNCH ENGINE button now.
        
        page.setLayout(layout)
        self.stack.addWidget(page)
        
    def prev_step(self):
        idx = self.stack.currentIndex()
        if idx > 0:
            self.stack.setCurrentIndex(idx - 1)
        self.update_nav()
        
    def next_step(self):
        idx = self.stack.currentIndex()
        
        # Validation
        if idx == 0:
            if not self.name_input.text().strip():
                QMessageBox.warning(self, "Error", "Chassis Designation required.")
                return
        if idx == 2:
            num_off = sum(1 for _, cb, _ in self.offense_cbs if cb.isChecked())
            num_def = sum(1 for _, cb, _ in self.defense_cbs if cb.isChecked())
            num_pow = sum(1 for _, cb, _ in self.power_cbs if cb.isChecked())
            
            if num_off != 1:
                QMessageBox.warning(self, "Error", f"Must select exactly 1 Offense Track (You have {num_off}).")
                return
            if num_def != 1:
                QMessageBox.warning(self, "Error", f"Must select exactly 1 Defense Track (You have {num_def}).")
                return
            if num_pow != 2:
                QMessageBox.warning(self, "Error", f"Must select exactly 2 Power Tracks (You have {num_pow}).")
                return
                
            self._generate_summary()
            
        if idx < self.stack.count() - 1:
            self.stack.setCurrentIndex(idx + 1)
        self.update_nav()
        
    def update_nav(self):
        idx = self.stack.currentIndex()
        self.step_label.setText(f"Step {idx + 1} of {self.stack.count()}")
        self.btn_prev.setEnabled(idx > 0)
        self.btn_next.setEnabled(idx < self.stack.count() - 1)
        
    def _generate_summary(self):
        kingdom = self.kingdom_combo.currentText()
        subtype = self.subtype_combo.currentText()
        origin = self.origin_combo.currentText()
        
        # 1. Base Stats
        base = BASE_STATS[kingdom][subtype].copy()
        
        # 2. Size Shift
        if not self.size_standard.isChecked():
            shift_stat = self.shift_choice.currentText().lower()
            base[shift_stat] += 1
            
        # 3. Professional Training
        self.selected_tracks = []
        all_cbs = self.offense_cbs + self.defense_cbs + self.power_cbs
        for track, cb, stat in all_cbs:
            if cb.isChecked():
                base[stat] += 2
                self.selected_tracks.append((track, cb, stat))
                
        # 5. Biological Ceiling & Overflow
        body = ["might", "endurance", "finesse", "reflex", "vitality", "fortitude"]
        mind = ["knowledge", "logic", "awareness", "intuition", "charm", "willpower"]
        
        for category in [body, mind]:
            overflow = 0
            for stat in category:
                if base[stat] > 8:
                    overflow += (base[stat] - 8)
                    base[stat] = 8
            while overflow > 0:
                for stat in category:
                    if overflow > 0 and base[stat] < 8:
                        base[stat] += 1
                        overflow -= 1
                    if overflow == 0: break
                if all(base[s] == 8 for s in category):
                    break
                    
        self.final_stats = base
        
        hp = base['endurance'] + base['fortitude'] + base['vitality']
        composure = base['willpower'] + base['logic'] + base['charm']
        stam_cap = base['might'] + base['reflex'] + base['finesse']
        foc_cap = base['knowledge'] + base['awareness'] + base['intuition']
        
        summary = (
            f"Name: {self.name_input.text()}\n"
            f"Origin: {kingdom} - {subtype} ({origin})\n\n"
            f"Derived Stats:\n"
            f"HP: {hp} | Composure: {composure}\n"
            f"Stamina: {stam_cap} | Focus: {foc_cap}\n\n"
            f"Core Attributes:\n"
        )
        for k, v in base.items():
            summary += f"{k.title()}: {v} | "
        
        self.summary_label.setText(summary)
        
    def get_character_payload(self):
        name = self.name_input.text().strip()
        kingdom = self.kingdom_combo.currentText()
        origin = self.origin_combo.currentText()
        
        if not hasattr(self, 'final_stats'):
            return None
            
        payload = {
            "name": name,
            "origin": f"{kingdom}-{origin}",
            "stats": self.final_stats
        }
        return payload
