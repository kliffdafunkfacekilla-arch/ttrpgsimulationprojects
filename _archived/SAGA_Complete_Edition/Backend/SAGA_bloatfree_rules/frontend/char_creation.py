from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QFormLayout, QSpinBox, 
    QStackedWidget, QRadioButton, QButtonGroup, QCheckBox,
    QMessageBox, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt
from rules_engine.chassis_data import KINGDOMS, SUB_TYPES, BASE_STATS, ORIGINS, SKILL_TRACKS

class CharacterCreationScreen(QWidget):
    def __init__(self, bus):
        super().__init__()
        self.bus = bus
        self.setStyleSheet("background-color: #222; color: white;")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        title = QLabel("Initialize Biological Chassis")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #44FF44;")
        self.layout.addWidget(title)
        
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)
        
        self.step_label = QLabel("Step 1 of 5")
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
        self._init_step5()
        
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
        
        info = QLabel("Life Experience Phase: Allocate exactly +3 Body points and +3 Mind points.\nBiological Ceiling is 8.")
        layout.addWidget(info)
        
        grid = QGridLayout()
        self.stat_spinboxes = {}
        
        self.body_stats = ["Might", "Endurance", "Finesse", "Reflex", "Vitality", "Fortitude"]
        self.mind_stats = ["Knowledge", "Logic", "Awareness", "Intuition", "Charm", "Willpower"]
        
        row = 0
        grid.addWidget(QLabel("Body Stats (+3)"), row, 0)
        grid.addWidget(QLabel("Mind Stats (+3)"), row, 2)
        row += 1
        
        for i in range(6):
            b_stat = self.body_stats[i]
            b_sb = QSpinBox()
            b_sb.setRange(0, 3)
            self.stat_spinboxes[b_stat.lower()] = b_sb
            grid.addWidget(QLabel(b_stat), row, 0)
            grid.addWidget(b_sb, row, 1)
            
            m_stat = self.mind_stats[i]
            m_sb = QSpinBox()
            m_sb.setRange(0, 3)
            self.stat_spinboxes[m_stat.lower()] = m_sb
            grid.addWidget(QLabel(m_stat), row, 2)
            grid.addWidget(m_sb, row, 3)
            
            row += 1
            
        layout.addLayout(grid)
        page.setLayout(layout)
        self.stack.addWidget(page)
        
    def _init_step4(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        info = QLabel("Professional Training: Select exactly 6 Skill Tracks.\nEach grants +2 to its governing attribute.")
        layout.addWidget(info)
        
        scroll = QScrollArea()
        scroll_w = QWidget()
        grid = QGridLayout()
        
        self.track_checkboxes = []
        row, col = 0, 0
        for track, stat in SKILL_TRACKS.items():
            cb = QCheckBox(f"{track} (+2 {stat.title()})")
            self.track_checkboxes.append((track, cb, stat))
            grid.addWidget(cb, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1
                
        scroll_w.setLayout(grid)
        scroll.setWidget(scroll_w)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        page.setLayout(layout)
        self.stack.addWidget(page)
        
    def _init_step5(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        self.summary_label = QLabel("Summary will appear here.")
        layout.addWidget(self.summary_label)
        
        btn_finalize = QPushButton("Finalize Party & Enter Drift")
        btn_finalize.setStyleSheet("padding: 10px; background-color: #550000; color: white; font-weight: bold;")
        btn_finalize.clicked.connect(self._on_finalize)
        layout.addWidget(btn_finalize)
        
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
            body_pts = sum(self.stat_spinboxes[s.lower()].value() for s in self.body_stats)
            mind_pts = sum(self.stat_spinboxes[s.lower()].value() for s in self.mind_stats)
            if body_pts != 3 or mind_pts != 3:
                QMessageBox.warning(self, "Error", f"Must allocate exactly 3 Body (current: {body_pts}) and 3 Mind (current: {mind_pts}).")
                return
        if idx == 3:
            selected = sum(1 for _, cb, _ in self.track_checkboxes if cb.isChecked())
            if selected != 6:
                QMessageBox.warning(self, "Error", f"Must select exactly 6 Skill Tracks. Currently selected: {selected}")
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
            
        # 3. Life Experience
        for stat, sb in self.stat_spinboxes.items():
            base[stat] += sb.value()
            
        # 4. Professional Training
        for track, cb, stat in self.track_checkboxes:
            if cb.isChecked():
                base[stat] += 2
                
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
        
    def _on_finalize(self):
        name = self.name_input.text().strip()
        kingdom = self.kingdom_combo.currentText()
        origin = self.origin_combo.currentText()
        
        payload = {
            "name": name,
            "origin": f"{kingdom}-{origin}",
            "stats": self.final_stats
        }
        self.bus.publish("UI_FINALIZE_PARTY", payload)
