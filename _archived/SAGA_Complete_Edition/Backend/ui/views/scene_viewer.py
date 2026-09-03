import sys
import json
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QGraphicsView, QGraphicsScene, 
                             QGraphicsPixmapItem, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
                             QPushButton, QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QGridLayout, QGroupBox)
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt, QTimer

from ui.components.asset_mapper import AssetMapper

class SceneViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SAGA - Tag-Driven UI Renderer")
        self.setGeometry(100, 100, 1024, 768)
        
        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # HUD Layout (Top)
        hud_layout = QHBoxLayout()
        hud_layout.setContentsMargins(15, 10, 15, 10)
        
        self.stamina_label = QLabel("STAMINA: 10 / 10")
        self.stamina_label.setStyleSheet("color: #ff4444; font-weight: bold; font-size: 16px;")
        
        self.focus_label = QLabel("FOCUS: 10 / 10")
        self.focus_label.setStyleSheet("color: #4444ff; font-weight: bold; font-size: 16px;")
        
        self.location_label = QLabel("LOCATION: Unknown")
        self.location_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 16px;")
        
        self.char_button = QPushButton("Character / Inventory")
        self.char_button.setStyleSheet("background-color: #4caf50; color: white; font-weight: bold; padding: 5px;")
        self.char_button.clicked.connect(self.open_character_sheet)
        
        hud_layout.addWidget(self.stamina_label)
        hud_layout.addStretch()
        hud_layout.addWidget(self.location_label)
        hud_layout.addStretch()
        hud_layout.addWidget(self.char_button)
        hud_layout.addSpacing(15)
        hud_layout.addWidget(self.focus_label)
        
        hud_widget = QWidget()
        hud_widget.setStyleSheet("background-color: #1a1a1a;")
        hud_widget.setLayout(hud_layout)
        main_layout.addWidget(hud_widget)
        
        # Graphics View (Middle)
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setStyleSheet("background-color: #000000; border: none;")
        main_layout.addWidget(self.view, stretch=1)
        
        # Subtitle Box (Bottom)
        self.subtitle_label = QLabel("Waiting for AI Director...")
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setStyleSheet("background-color: #1a1a1a; color: #dddddd; font-size: 18px; padding: 15px; border-top: 2px solid #333;")
        self.subtitle_label.setMinimumHeight(100)
        main_layout.addWidget(self.subtitle_label)
        
        # Asset Mapper and Items
        self.mapper = AssetMapper()
        
        self.bg_item = QGraphicsPixmapItem()
        self.scene.addItem(self.bg_item)
        
        self.structural_items = []
        self.prop_items = []
        self.entity_items = []
        
        # Polling setup
        self.last_state_mtime = 0
        self.state_file = "scene_state.json"
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll_state_file)
        self.timer.start(1000)
        
        self.current_tags = {}

    def open_character_sheet(self):
        char_data = self.current_tags.get("character")
        if char_data:
            dialog = CharacterSheetDialog(char_data, self)
            dialog.exec()
        else:
            print("No character data available yet.")

    def poll_state_file(self):
        if not os.path.exists(self.state_file):
            return
            
        mtime = os.path.getmtime(self.state_file)
        if mtime > self.last_state_mtime:
            self.last_state_mtime = mtime
            try:
                with open(self.state_file, "r") as f:
                    self.current_tags = json.load(f)
                self.update_scene(self.current_tags)
            except Exception as e:
                print(f"Error parsing scene_state.json: {e}")

    def update_scene(self, tags: dict):
        """
        Updates the UI overlays and the graphical layers.
        """
        # 1. Update HUD & Subtitles
        if "stamina" in tags:
            self.stamina_label.setText(f"STAMINA: {tags['stamina']} / {tags.get('max_stamina', 10)}")
        if "focus" in tags:
            self.focus_label.setText(f"FOCUS: {tags['focus']} / {tags.get('max_focus', 10)}")
        if "location" in tags:
            self.location_label.setText(f"LOCATION: {tags['location']}")
        if "narration_text" in tags:
            self.subtitle_label.setText(tags["narration_text"])

        # 2. Background (Layer 0)
        biome = tags.get("biome", "Default")
        bg_path = self.mapper.get_background(biome)
        if bg_path:
            # Scale background to current view size
            view_w = self.view.width() if self.view.width() > 0 else 1024
            view_h = self.view.height() if self.view.height() > 0 else 768
            pixmap = QPixmap(bg_path).scaled(view_w, view_h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation)
            self.bg_item.setPixmap(pixmap)
            
        # Clean up old layers
        for item in self.structural_items + self.prop_items + self.entity_items:
            self.scene.removeItem(item)
        self.structural_items.clear()
        self.prop_items.clear()
        self.entity_items.clear()

        def add_layered_item(path, x, y, scale_factor=4):
            if not path: return None
            pixmap = QPixmap(path).scaled(32 * scale_factor, 32 * scale_factor, Qt.AspectRatioMode.KeepAspectRatio)
            item = QGraphicsPixmapItem(pixmap)
            item.setPos(x, y)
            self.scene.addItem(item)
            return item
            
        # 3. Structural (Layer 1)
        offset_x = 100
        for struct_tag in tags.get("structural", []):
            path = self.mapper._verify_path(f"structural/{struct_tag}.png")
            if path:
                item = add_layered_item(path, offset_x, 150)
                if item: self.structural_items.append(item)
                offset_x += 150
                
        # 4. Props (Layer 2)
        offset_x = 200
        for prop_tag in tags.get("props", []):
            path = self.mapper.get_prop_asset(prop_tag)
            if path:
                item = add_layered_item(path, offset_x, 300)
                if item: self.prop_items.append(item)
                offset_x += 120
                
        # 5. Entities (Layer 3)
        offset_x = 350
        for entity_tag in tags.get("entities", []):
            path = self.mapper.get_entity_asset(entity_tag)
            if path:
                item = add_layered_item(path, offset_x, 250, scale_factor=5)
                if item: self.entity_items.append(item)
                offset_x += 150

class CharacterSheetDialog(QDialog):
    def __init__(self, char_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Character Sheet - {char_data.get('name', 'Unknown')}")
        self.setGeometry(200, 200, 800, 600)
        self.setStyleSheet("background-color: #1e1e1e; color: #eeeeee; font-family: Segoe UI, sans-serif;")
        
        layout = QHBoxLayout(self)
        
        # Left Panel (Stats)
        left_panel = QVBoxLayout()
        
        header = QLabel(f"{char_data.get('name', 'Unknown')} - Level {char_data.get('level', 1)}")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #4caf50;")
        left_panel.addWidget(header)
        
        stats_group = QGroupBox("Core Attributes")
        stats_layout = QGridLayout()
        base_stats = char_data.get("base_stats", {})
        row, col = 0, 0
        for stat, val in base_stats.items():
            stats_layout.addWidget(QLabel(f"{stat.capitalize()}: {val}"), row, col)
            row += 1
            if row > 5:
                row = 0
                col += 1
        stats_group.setLayout(stats_layout)
        left_panel.addWidget(stats_group)
        
        skills_group = QGroupBox("Skills")
        skills_layout = QVBoxLayout()
        for skill in char_data.get("skills", []):
            skills_layout.addWidget(QLabel(f"- {skill}"))
        skills_group.setLayout(skills_layout)
        left_panel.addWidget(skills_group)
        
        left_panel.addStretch()
        layout.addLayout(left_panel, 1)
        
        # Right Panel (Inventory)
        right_panel = QVBoxLayout()
        inv_data = char_data.get("inventory", {})
        
        equip_group = QGroupBox("Equipped Gear")
        equip_layout = QVBoxLayout()
        slots = inv_data.get("slots", {})
        for slot_name, item in slots.items():
            if item:
                equip_layout.addWidget(QLabel(f"{slot_name.capitalize()}: {item.get('name')} (+{item.get('modifier')} {item.get('stat_type')})"))
            else:
                equip_layout.addWidget(QLabel(f"{slot_name.capitalize()}: Empty"))
        equip_group.setLayout(equip_layout)
        right_panel.addWidget(equip_group)
        
        pack_group = QGroupBox(f"Backpack (Gold: {inv_data.get('gold', 0)})")
        pack_layout = QVBoxLayout()
        pack = inv_data.get("bag", [])
        if pack:
            for item in pack:
                pack_layout.addWidget(QLabel(f"- {item.get('name')} (x{item.get('quantity', 1)})"))
        else:
            pack_layout.addWidget(QLabel("Backpack is empty."))
        pack_group.setLayout(pack_layout)
        right_panel.addWidget(pack_group)
        
        right_panel.addStretch()
        layout.addLayout(right_panel, 1)

# For standalone testing
if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = SceneViewer()
    viewer.show()
    sys.exit(app.exec())
