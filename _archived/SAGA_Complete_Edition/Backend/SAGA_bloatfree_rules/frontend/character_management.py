from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QGridLayout, QFrame, QScrollArea,
                             QGroupBox, QTabWidget)
from PyQt6.QtCore import Qt

class StatRow(QWidget):
    def __init__(self, stat_name, stat_value, bus, can_upgrade):
        super().__init__()
        self.bus = bus
        self.stat_name = stat_name
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_name = QLabel(stat_name.capitalize() + ":")
        lbl_name.setStyleSheet("color: #AAA; font-size: 16px; font-weight: bold; width: 100px;")
        
        self.lbl_val = QLabel(str(stat_value))
        self.lbl_val.setStyleSheet("color: white; font-size: 16px;")
        
        self.btn_up = QPushButton("+")
        self.btn_up.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 2px 5px;")
        self.btn_up.setFixedWidth(30)
        self.btn_up.clicked.connect(self._on_upgrade)
        
        if not can_upgrade:
            self.btn_up.hide()
            
        layout.addWidget(lbl_name)
        layout.addWidget(self.lbl_val)
        layout.addWidget(self.btn_up)
        layout.addStretch()
        
        self.setLayout(layout)
        
    def _on_upgrade(self):
        self.bus.publish("UI_CHARACTER_UPGRADE_STAT", {"stat": self.stat_name})


class EquippedItemRow(QWidget):
    def __init__(self, slot_name, item_dict, bus):
        super().__init__()
        self.bus = bus
        self.slot_name = slot_name
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 5, 0, 5)
        
        lbl_slot = QLabel(slot_name.capitalize() + ":")
        lbl_slot.setStyleSheet("color: #AAA; font-size: 14px; font-weight: bold; width: 80px;")
        
        if item_dict:
            name = item_dict.get("name", "Unknown")
            mod = f"+{item_dict.get('modifier', 0)} {item_dict.get('stat_type', '')}"
            cost = item_dict.get("loadout_cost", 0)
            
            lbl_item = QLabel(f"{name} ({mod})")
            lbl_item.setStyleSheet("color: white; font-size: 14px; width: 180px;")
            
            lbl_cost = QLabel(f"Tax: {cost}")
            lbl_cost.setStyleSheet("color: #FF5555; font-size: 12px; width: 60px;")
            
            btn_unequip = QPushButton("Unequip")
            btn_unequip.setStyleSheet("background-color: #883333; color: white; padding: 2px 5px;")
            btn_unequip.clicked.connect(self._on_unequip)
            
            layout.addWidget(lbl_slot)
            layout.addWidget(lbl_item)
            layout.addWidget(lbl_cost)
            layout.addWidget(btn_unequip)
        else:
            lbl_item = QLabel("Empty")
            lbl_item.setStyleSheet("color: #555; font-size: 14px;")
            layout.addWidget(lbl_slot)
            layout.addWidget(lbl_item)
            layout.addStretch()
            
        self.setLayout(layout)
        
    def _on_unequip(self):
        self.bus.publish("UI_INVENTORY_UNEQUIP", {"slot": self.slot_name})


class BagItemRow(QWidget):
    def __init__(self, index, item_dict, bus):
        super().__init__()
        self.bus = bus
        self.index = index
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 5, 0, 5)
        
        name = item_dict.get("name", "Unknown")
        mod = f"+{item_dict.get('modifier', 0)} {item_dict.get('stat_type', '')}"
        cost = item_dict.get("loadout_cost", 0)
        
        lbl_item = QLabel(f"{name} ({mod}) [Tax: {cost}]")
        lbl_item.setStyleSheet("color: white; font-size: 14px;")
        
        btn_equip = QPushButton("Equip")
        btn_equip.setStyleSheet("background-color: #335588; color: white; padding: 2px 5px;")
        btn_equip.clicked.connect(self._on_equip)
        
        layout.addWidget(lbl_item)
        layout.addStretch()
        layout.addWidget(btn_equip)
        
        self.setLayout(layout)
        
    def _on_equip(self):
        self.bus.publish("UI_INVENTORY_EQUIP", {"index": self.index})


class CharacterManagementScreen(QWidget):
    def __init__(self, bus):
        super().__init__()
        self.bus = bus
        
        self.current_stats = {}
        
        main_layout = QVBoxLayout()
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Character Management")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #44FF44;")
        
        self.btn_back = QPushButton("Back to World")
        self.btn_back.setStyleSheet("padding: 10px; background-color: #555; color: white; font-size: 16px;")
        self.btn_back.clicked.connect(lambda: self.bus.publish("UI_CLOSE_CHAR_MANAGEMENT"))
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.btn_back)
        main_layout.addLayout(header)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabBar::tab { background: #333; color: white; padding: 10px 20px; font-size: 16px; border: 1px solid #555; }
            QTabBar::tab:selected { background: #44FF44; color: black; font-weight: bold; }
            QTabWidget::pane { border: 2px solid #44FF44; }
        """)
        
        # TAB 1: Biological Chassis
        self.tab_stats = QWidget()
        self._build_stats_tab()
        
        # TAB 2: Loadout & Bag
        self.tab_inventory = QWidget()
        self._build_inventory_tab()
        
        self.tabs.addTab(self.tab_stats, "Biological Chassis")
        self.tabs.addTab(self.tab_inventory, "Loadout & Bag")
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
        
        self.bus.subscribe("HUD_UPDATE", self._on_hud_update)
        
    def _build_stats_tab(self):
        content_layout = QHBoxLayout(self.tab_stats)
        
        # Left Panel (Progression & Stats)
        left_panel = QGroupBox("Biological Chassis (Stats)")
        left_panel.setStyleSheet("QGroupBox { color: #44FF44; font-weight: bold; font-size: 16px; border: 2px solid #555; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }")
        self.left_layout = QVBoxLayout()
        
        self.lbl_level = QLabel("Level: 1 | XP: 0")
        self.lbl_level.setStyleSheet("font-size: 18px; color: white; margin-bottom: 10px;")
        self.left_layout.addWidget(self.lbl_level)
        
        self.lbl_unspent = QLabel("Unspent Points: 0")
        self.lbl_unspent.setStyleSheet("font-size: 16px; color: #FFD700; margin-bottom: 10px;")
        self.left_layout.addWidget(self.lbl_unspent)
        
        self.stats_container = QWidget()
        self.stats_layout = QVBoxLayout(self.stats_container)
        self.left_layout.addWidget(self.stats_container)
        self.left_layout.addStretch()
        
        left_panel.setLayout(self.left_layout)
        
        # Right Panel (Vitals & Reserves)
        right_panel = QGroupBox("Vitals & Logistics")
        right_panel.setStyleSheet("QGroupBox { color: #44FF44; font-weight: bold; font-size: 16px; border: 2px solid #555; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }")
        self.right_layout = QVBoxLayout()
        
        self.lbl_hp = QLabel("HP: 0/0")
        self.lbl_stamina = QLabel("Stamina: 0/0")
        self.lbl_focus = QLabel("Focus: 0/0")
        self.lbl_reserve = QLabel("Reserve Pool: 0")
        
        style = "font-size: 20px; color: white; margin-bottom: 15px;"
        self.lbl_hp.setStyleSheet(style)
        self.lbl_stamina.setStyleSheet(style)
        self.lbl_focus.setStyleSheet(style)
        self.lbl_reserve.setStyleSheet("font-size: 20px; color: #FFAA00; margin-bottom: 15px;")
        
        self.right_layout.addWidget(self.lbl_hp)
        self.right_layout.addWidget(self.lbl_stamina)
        self.right_layout.addWidget(self.lbl_focus)
        self.right_layout.addWidget(self.lbl_reserve)
        
        self.btn_rest = QPushButton("Rest (Burn Reserves)")
        self.btn_rest.setStyleSheet("QPushButton { background-color: #AA5500; color: white; font-weight: bold; font-size: 18px; padding: 15px; border-radius: 5px; } QPushButton:hover { background-color: #CC6600; }")
        self.btn_rest.clicked.connect(lambda: self.bus.publish("UI_CHARACTER_REST"))
        
        self.right_layout.addStretch()
        self.right_layout.addWidget(self.btn_rest)
        
        right_panel.setLayout(self.right_layout)
        
        content_layout.addWidget(left_panel)
        content_layout.addWidget(right_panel)

    def _build_inventory_tab(self):
        content_layout = QHBoxLayout(self.tab_inventory)
        
        # Left Panel (Slots)
        slots_panel = QGroupBox("Equipped Gear")
        slots_panel.setStyleSheet("QGroupBox { color: #44FF44; font-weight: bold; font-size: 16px; border: 2px solid #555; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }")
        
        slots_scroll = QScrollArea()
        slots_scroll.setWidgetResizable(True)
        slots_scroll.setStyleSheet("border: none; background-color: transparent;")
        self.slots_container = QWidget()
        self.slots_layout = QVBoxLayout(self.slots_container)
        self.slots_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        slots_scroll.setWidget(self.slots_container)
        
        slots_panel_layout = QVBoxLayout()
        slots_panel_layout.addWidget(slots_scroll)
        
        self.lbl_gear_tax = QLabel("Gear Tax (Physical: 0 | Mental: 0)")
        self.lbl_gear_tax.setStyleSheet("font-size: 18px; color: #FF5555; font-weight: bold; padding: 10px;")
        slots_panel_layout.addWidget(self.lbl_gear_tax)
        
        slots_panel.setLayout(slots_panel_layout)
        
        # Right Panel (Bag)
        bag_panel = QGroupBox("Bag Inventory")
        bag_panel.setStyleSheet("QGroupBox { color: #44FF44; font-weight: bold; font-size: 16px; border: 2px solid #555; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }")
        
        bag_scroll = QScrollArea()
        bag_scroll.setWidgetResizable(True)
        bag_scroll.setStyleSheet("border: none; background-color: transparent;")
        self.bag_container = QWidget()
        self.bag_layout = QVBoxLayout(self.bag_container)
        self.bag_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        bag_scroll.setWidget(self.bag_container)
        
        bag_panel_layout = QVBoxLayout()
        bag_panel_layout.addWidget(bag_scroll)
        bag_panel.setLayout(bag_panel_layout)
        
        content_layout.addWidget(slots_panel, stretch=1)
        content_layout.addWidget(bag_panel, stretch=1)

    def _on_hud_update(self, payload):
        self.current_stats = payload
        
        # Update Right Panel (Vitals)
        self.lbl_hp.setText(f"HP: {payload.get('hp', 0)} / {payload.get('max_hp', 0)}")
        self.lbl_stamina.setText(f"Stamina: {payload.get('stamina', 0)} / {payload.get('max_stamina', 0)}")
        self.lbl_focus.setText(f"Focus: {payload.get('focus', 0)} / {payload.get('max_focus', 0)}")
        self.lbl_reserve.setText(f"Reserve Pool: {payload.get('reserve_pool', 0)}")
        
        # Update Left Panel (Progression)
        lvl = payload.get('level', 1)
        xp = payload.get('xp', 0)
        unspent = payload.get('unspent_stat', 0)
        
        self.lbl_level.setText(f"Level: {lvl} | XP: {xp}")
        self.lbl_unspent.setText(f"Unspent Points: {unspent}")
        
        # Rebuild Stats List
        while self.stats_layout.count():
            child = self.stats_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        stats_dict = payload.get('stats', {})
        can_upgrade = unspent > 0
        
        for s_name, s_val in stats_dict.items():
            row = StatRow(s_name, s_val, self.bus, can_upgrade)
            self.stats_layout.addWidget(row)
            
        # Rebuild Inventory UI
        inv = payload.get('inventory')
        if inv:
            # Rebuild Slots
            while self.slots_layout.count():
                child = self.slots_layout.takeAt(0)
                if child.widget(): child.widget().deleteLater()
            
            slots_data = inv.get('slots', {})
            for slot_name, item_dict in slots_data.items():
                row = EquippedItemRow(slot_name, item_dict, self.bus)
                self.slots_layout.addWidget(row)
                
            p_tax = payload.get('physical_tax', 0)
            m_tax = payload.get('mental_tax', 0)
            self.lbl_gear_tax.setText(f"Gear Tax (Physical: {p_tax} | Mental: {m_tax})")
                
            # Rebuild Bag
            while self.bag_layout.count():
                child = self.bag_layout.takeAt(0)
                if child.widget(): child.widget().deleteLater()
                
            bag_data = inv.get('bag', [])
            for idx, item_dict in enumerate(bag_data):
                row = BagItemRow(idx, item_dict, self.bus)
                self.bag_layout.addWidget(row)
