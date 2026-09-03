"""
Provides the StartMenu, VendorScreen, and other full-screen UI views.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QLineEdit
from PyQt6.QtCore import Qt

class StartMenu(QWidget):
    """
    The initial landing screen of the game.
    """
    def __init__(self, bus):
        super().__init__()
        self.bus = bus
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("S.A.G.A. ENGINE V1 (BETA)")
        title.setStyleSheet("font-size: 36px; font-weight: bold; color: #44FF44; margin-bottom: 30px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        btn_new = QPushButton("New Game (Create Party)")
        btn_new.setStyleSheet("padding: 15px; font-size: 18px; background-color: #333; color: white; width: 300px;")
        btn_new.clicked.connect(lambda: self.bus.publish("UI_START_NEW_GAME"))
        
        btn_load = QPushButton("Load Saved Game")
        btn_load.setStyleSheet("padding: 15px; font-size: 18px; background-color: #333; color: white; width: 300px; margin-top: 10px;")
        btn_load.clicked.connect(lambda: self.bus.publish("UI_LOAD_GAME"))
        
        btn_dm = QPushButton("LAUNCH DM DASHBOARD")
        btn_dm.setStyleSheet("padding: 10px; font-size: 16px; background-color: #551111; color: #ff5555; width: 300px; margin-top: 10px; border: 1px solid #ff5555;")
        btn_dm.clicked.connect(lambda: self.bus.publish("OPEN_DM_DASHBOARD"))
        
        layout.addWidget(title)
        layout.addWidget(btn_new)
        layout.addWidget(btn_load)
        layout.addWidget(btn_dm)
        
        self.setLayout(layout)

class VendorScreen(QWidget):
    """
    A screen for interacting with merchants.
    """
    def __init__(self, bus):
        super().__init__()
        self.bus = bus
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.title = QLabel("Vendor Shop")
        self.title.setStyleSheet("font-size: 24px; font-weight: bold; color: gold;")
        
        self.gold_label = QLabel("Gold: 0")
        self.gold_label.setStyleSheet("font-size: 18px; color: white;")
        
        self.item_list = QTextEdit()
        self.item_list.setReadOnly(True)
        self.item_list.setStyleSheet("background-color: #222; color: #ddd; font-family: monospace; font-size: 14px;")
        self.item_list.setMinimumHeight(400)
        
        self.buy_input = QLineEdit()
        self.buy_input.setPlaceholderText("Type item name to buy...")
        self.buy_input.setStyleSheet("padding: 5px; font-size: 16px; background-color: #333; color: white; border: 1px solid #555;")
        self.buy_input.returnPressed.connect(self._on_buy)
        
        btn_leave = QPushButton("Leave Shop")
        btn_leave.setStyleSheet("padding: 10px; background-color: #552222; color: white;")
        btn_leave.clicked.connect(lambda: self.bus.publish("UI_CLOSE_VENDOR"))
        
        self.layout.addWidget(self.title)
        self.layout.addWidget(self.gold_label)
        self.layout.addWidget(self.item_list)
        self.layout.addWidget(self.buy_input)
        self.layout.addWidget(btn_leave)
        self.setLayout(self.layout)
        
        self.bus.subscribe("VENDOR_DATA_UPDATE", self._on_vendor_update)
        
    def _on_vendor_update(self, payload):
        """Update shop inventory when new vendor data arrives."""
        self.title.setText(f"Trading with: {payload.get('vendor_name', 'Merchant')}")
        self.gold_label.setText(f"Gold: {payload.get('player_gold', 0)}")
        
        items = payload.get("items", [])
        text = "Items for Sale:\n\n"
        for i in items:
            text += f"- {i['name']} ({i['cost']} Gold) : {i['desc']}\n"
            
        self.item_list.setText(text)
        
    def _on_buy(self):
        """Send intent to buy an item."""
        item_name = self.buy_input.text().strip()
        if item_name:
            self.bus.publish("VENDOR_BUY_ITEM", {"item_name": item_name})
            self.buy_input.clear()
