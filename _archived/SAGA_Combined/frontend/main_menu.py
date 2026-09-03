import sys
import json
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QComboBox, QCheckBox, QGroupBox, QTextEdit, 
                             QTabWidget, QSpinBox, QGridLayout)
from PyQt6.QtCore import Qt

# Import rules engine models to serialize the character
# Ensure SAGA_Voice directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rules_engine.character_sheet import CharacterSheet
from rules_engine.inventory import Item
from frontend.char_creation import CharacterCreationScreen

class SagaLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("S.A.G.A. - Campaign Launcher")
        self.setGeometry(200, 200, 600, 700)
        self.setStyleSheet("background-color: #1e1e1e; color: #eeeeee; font-family: Segoe UI, sans-serif;")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Header
        header = QLabel("PROJECT S.A.G.A.")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #4caf50; padding: 10px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabBar::tab { background: #333; color: white; padding: 10px; }
            QTabBar::tab:selected { background: #4caf50; }
        """)
        main_layout.addWidget(self.tabs)
        
        # --- TAB 1: CAMPAIGN SETTINGS ---
        self.campaign_tab = QWidget()
        self.build_campaign_tab()
        self.tabs.addTab(self.campaign_tab, "Campaign Settings")
        
        # --- TAB 2: CHARACTER CREATION ---
        self.character_tab = QWidget()
        self.build_character_tab()
        self.tabs.addTab(self.character_tab, "Character Creator")
        
        # Start Button
        self.start_btn = QPushButton("LAUNCH ENGINE")
        self.start_btn.setStyleSheet("background-color: #4caf50; color: white; font-weight: bold; font-size: 16px; padding: 15px; margin-top: 10px;")
        self.start_btn.clicked.connect(self.start_game)
        main_layout.addWidget(self.start_btn)

    def build_campaign_tab(self):
        layout = QVBoxLayout(self.campaign_tab)
        
        # Game Mode
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Game Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["New Game", "Load Game"])
        self.mode_combo.setStyleSheet("background-color: #333; padding: 5px;")
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(self.mode_combo)
        layout.addLayout(mode_layout)

        # Settings Group
        settings_group = QGroupBox("Campaign Settings")
        settings_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #555; margin-top: 10px; }")
        settings_layout = QVBoxLayout()
        
        # Difficulty & Frequency
        diff_layout = QHBoxLayout()
        diff_layout.addWidget(QLabel("Difficulty:"))
        self.diff_combo = QComboBox()
        self.diff_combo.addItems(["Story", "Normal", "Hardcore"])
        self.diff_combo.setCurrentText("Normal")
        self.diff_combo.setStyleSheet("background-color: #333;")
        diff_layout.addWidget(self.diff_combo)
        
        diff_layout.addWidget(QLabel("  Combat Frequency:"))
        self.freq_combo = QComboBox()
        self.freq_combo.addItems(["Low", "Medium", "High"])
        self.freq_combo.setCurrentText("Medium")
        self.freq_combo.setStyleSheet("background-color: #333;")
        diff_layout.addWidget(self.freq_combo)
        settings_layout.addLayout(diff_layout)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Content Filters Group
        filters_group = QGroupBox("Content Filters (Safety Toggles)")
        filters_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #555; margin-top: 10px; }")
        filters_layout = QHBoxLayout()
        
        self.chk_alcohol = QCheckBox("No Alcohol/Drugs")
        self.chk_gore = QCheckBox("No Gore/Gruesome Death")
        self.chk_spiders = QCheckBox("Arachnophobia (No Spiders)")
        
        filters_layout.addWidget(self.chk_alcohol)
        filters_layout.addWidget(self.chk_gore)
        filters_layout.addWidget(self.chk_spiders)
        
        filters_group.setLayout(filters_layout)
        layout.addWidget(filters_group)
        
        # Starting Plot
        plot_group = QGroupBox("Starting Location & Plot")
        plot_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #555; margin-top: 10px; }")
        plot_layout = QVBoxLayout()
        self.plot_input = QTextEdit()
        self.plot_input.setPlaceholderText("Leave blank for random settlement, or describe your own start (e.g., I am in the Canopy trying to find a missing merchant...)")
        self.plot_input.setStyleSheet("background-color: #333; border: 1px solid #555;")
        plot_layout.addWidget(self.plot_input)
        plot_group.setLayout(plot_layout)
        layout.addWidget(plot_group)

    def build_character_tab(self):
        layout = QVBoxLayout(self.character_tab)
        
        self.char_creator = CharacterCreationScreen()
        layout.addWidget(self.char_creator)

    def on_mode_changed(self, mode):
        self.character_tab.setEnabled(mode == "New Game")

    def create_and_save_character(self):
        payload = self.char_creator.get_character_payload()
        if not payload:
            print("No finalized character data found. Please complete the Character Creator steps to the end.")
            return False
            
        name = payload["name"]
        stats = payload["stats"]
        origin = payload["origin"]
        
        player = CharacterSheet(name=name, stats=stats)
        player.origin = origin
        
        # Rebuild skills from payload if needed
        selected_tracks = [track for track, cb, stat in self.char_creator.selected_tracks]
        player.skills = selected_tracks
        
        # Give some basic gear based on the first track
        if selected_tracks:
            primary_track = selected_tracks[0]
            if "Mercenary" in primary_track or "Wrangler" in primary_track or "Bulwark" in primary_track:
                player.inventory.add_item(Item("Iron Claymore", "weapon", "might", 2, 2))
                player.inventory.add_item(Item("Heavy Plate", "body", "endurance", 3, 3))
            elif "Scholar" in primary_track or "Anomaly" in primary_track or "Surgeon" in primary_track:
                player.inventory.add_item(Item("Scalpel", "weapon", "finesse", 1, 1))
                player.inventory.add_item(Item("Medical Kit", "hand", "logic", 2, 1))
            else:
                player.inventory.add_item(Item("Rusty Dagger", "weapon", "finesse", 1, 1))
                player.inventory.add_item(Item("Leather Scrap", "body", "endurance", 1, 1))
                
        with open("player_save.json", "w") as f:
            json.dump(player.to_dict(), f, indent=4)
            
        print(f"Saved character {name} to player_save.json")
        return True

    def start_game(self):
        if self.mode_combo.currentText() == "New Game":
            if not self.create_and_save_character():
                return
            
        filters = []
        if self.chk_alcohol.isChecked():
            filters.append("alcohol, drugs, substance abuse")
        if self.chk_gore.isChecked():
            filters.append("extreme gore, gruesome death, torture")
        if self.chk_spiders.isChecked():
            filters.append("spiders, arachnids, webs")
            
        settings = {
            "mode": self.mode_combo.currentText(),
            "character_name": self.char_creator.name_input.text() if hasattr(self, 'char_creator') else "Unknown",
            "difficulty": self.diff_combo.currentText(),
            "combat_frequency": self.freq_combo.currentText(),
            "filters": filters,
            "starting_plot": self.plot_input.toPlainText().strip()
        }
        
        with open("campaign_settings.json", "w") as f:
            json.dump(settings, f, indent=4)
            
        print("Settings saved. Launching engine...")
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = SagaLauncher()
    launcher.show()
    sys.exit(app.exec())
