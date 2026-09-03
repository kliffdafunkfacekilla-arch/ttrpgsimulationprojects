"""
Provides the CharacterHUD and StoryTracker components for the right-hand panel of the VTT.
"""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QTextEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

class CharacterHUD(QFrame):
    """
    Displays the character's core stats (HP, Stamina, Focus) using graphical elements.
    Listens for 'HUD_UPDATE' events to refresh data from the Pydantic CharacterSheet.
    """
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 2px solid #555;
                border-radius: 5px;
                padding: 10px;
            }
            QLabel { color: #ddd; font-weight: bold; font-family: monospace; font-size: 14px; border: none; }
        """)
        self.setFixedWidth(250)
        
        layout = QVBoxLayout()
        
        # UI Polish: Asset injection
        self.portrait_label = QLabel()
        portrait_pixmap = QPixmap("assets/gui/Fantasy Minimal Pixel Art GUI by eta-commercial-free/UI/CharacterBox_56x57.png")
        if not portrait_pixmap.isNull():
            self.portrait_label.setPixmap(portrait_pixmap)
            self.portrait_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.portrait_label)
        
        self.name_label = QLabel("Player Name")
        self.name_label.setStyleSheet("font-size: 18px; color: #44FF44; margin-bottom: 10px;")
        
        # Use HealthBarPanel background if possible
        bar_bg = QPixmap("assets/gui/Fantasy Minimal Pixel Art GUI by eta-commercial-free/UI/HealthBarPanel_160x41.png")
        
        self.hp_label = QLabel("HP: --/--")
        if not bar_bg.isNull():
            self.hp_label.setStyleSheet("color: #FF5555; background-image: url('assets/gui/Fantasy Minimal Pixel Art GUI by eta-commercial-free/UI/HealthBarPanel_160x41.png'); padding: 5px;")
        
        self.stamina_label = QLabel("Stamina: --/--")
        self.focus_label = QLabel("Focus: --/--")
        if not bar_bg.isNull():
            self.focus_label.setStyleSheet("color: #5555FF; background-image: url('assets/gui/Fantasy Minimal Pixel Art GUI by eta-commercial-free/UI/HealthBarPanel_160x41.png'); padding: 5px;")
            
        self.trauma_label = QLabel("Trauma Tokens: 0")
        
        layout.addWidget(self.name_label)
        layout.addWidget(self.hp_label)
        layout.addWidget(self.stamina_label)
        layout.addWidget(self.focus_label)
        layout.addWidget(self.trauma_label)
        layout.addStretch()
        
        self.setLayout(layout)
        
    def update_stats(self, stats: dict):
        """
        Updates the HUD labels based on a serialized CharacterSheet dict.
        
        Args:
            stats (dict): The serialized Pydantic model representation of the character.
        """
        self.name_label.setText(stats.get("name", "Player"))
        self.hp_label.setText(f"HP: {stats.get('current_hp', 0)} / {stats.get('max_hp', 0)}")
        self.stamina_label.setText(f"Stamina: {stats.get('active_stamina', 0)} / {stats.get('max_stamina', 0)}")
        self.focus_label.setText(f"Focus: {stats.get('active_focus', 0)} / {stats.get('max_focus', 0)}")
        self.trauma_label.setText(f"Trauma Tokens: {stats.get('trauma_tokens', 0)}")


class StoryTracker(QFrame):
    """
    Displays the current story slot/quest and any active Reactive Seeds.
    Helps the player keep track of looming consequences and narrative goals.
    """
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 2px solid #3a414c;
                border-radius: 5px;
                padding: 10px;
                margin-top: 10px;
            }
            QLabel { color: #ddd; font-family: 'Segoe UI', sans-serif; border: none; }
        """)
        self.setFixedWidth(250)
        
        layout = QVBoxLayout()
        
        self.title_label = QLabel("Plot Directives")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50; margin-bottom: 5px;")
        
        self.quest_label = QTextEdit("Explore the world...")
        self.quest_label.setReadOnly(True)
        self.quest_label.setStyleSheet("background-color: #222; color: #aaa; font-style: italic; border: none; max-height: 80px;")
        
        self.seeds_title = QLabel("Looming Consequences")
        self.seeds_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ff5555; margin-top: 10px;")
        
        self.seeds_log = QTextEdit("None.")
        self.seeds_log.setReadOnly(True)
        self.seeds_log.setStyleSheet("background-color: #222; color: #ff9999; border: none; max-height: 120px;")
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.quest_label)
        layout.addWidget(self.seeds_title)
        layout.addWidget(self.seeds_log)
        layout.addStretch()
        
        self.setLayout(layout)
        
    def update_story(self, quest: str, active_seeds: list):
        """
        Updates the quest tracker and active seeds log.
        
        Args:
            quest (str): The current narrative directive.
            active_seeds (list): A list of dictionaries representing unresolved Reactive Seeds.
        """
        self.quest_label.setText(quest if quest else "Survive the Drift.")
        if not active_seeds:
            self.seeds_log.setText("The world is quiet... for now.")
        else:
            seed_text = ""
            for seed in active_seeds:
                desc = seed.get('subtle_description', '')
                urgency = seed.get('urgency_ticks', 0)
                seed_text += f"[{urgency} Ticks] {desc}\n\n"
            self.seeds_log.setText(seed_text.strip())
