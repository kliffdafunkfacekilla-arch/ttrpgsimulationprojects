import os
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLabel, QLineEdit, QPushButton, QStackedWidget, QListWidget,
    QScrollArea, QGroupBox, QStatusBar
)
from PyQt6.QtCore import Qt

class WorldsmithMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Worldsmith Sandbox - Prompt-Driven Worldbuilder")
        self.resize(1400, 900)
        
        # Modern Dark-Mode Stylesheet
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #121214;
                color: #E1E1E6;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox {
                border: 1px solid #29292E;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                color: #04D361;
            }
            QPushButton {
                background-color: #202024;
                border: 1px solid #29292E;
                color: #E1E1E6;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #29292E;
                border-color: #04D361;
            }
            QLineEdit, QTextEdit, QListWidget {
                background-color: #1c1c21;
                border: 1px solid #29292E;
                border-radius: 4px;
                padding: 6px;
                color: #E1E1E6;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #04D361;
            }
        """)

        # Main Layout: 3 Docking/Splitter Sections
        # Left Panel: Map Canvas
        # Center Panel: Note Editor (Obsidian Style)
        # Right Panel: Integrated AI Prompt Assistant
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self.main_splitter)

        # 1. Map Panel Container
        self.map_container = QWidget()
        map_layout = QVBoxLayout(self.map_container)
        map_layout.setContentsMargins(0, 0, 0, 0)
        self.map_label = QLabel("d20 Icosahedral Map Viewport")
        self.map_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.map_label.setStyleSheet("background-color: #0d0d10; border: 1px solid #202024;")
        map_layout.addWidget(self.map_label)
        self.main_splitter.addWidget(self.map_container)

        # 2. Note Editor Panel Container
        self.note_container = QWidget()
        note_layout = QVBoxLayout(self.note_container)
        
        self.note_title_input = QLineEdit()
        self.note_title_input.setPlaceholderText("Note Title (e.g. Faction name, Settlement, character)")
        self.note_title_input.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        self.note_editor = QTextEdit()
        self.note_editor.setPlaceholderText("Write notes using [[WikiLinks]] or #tags. Press Ctrl+S to save.")
        
        self.note_action_layout = QHBoxLayout()
        self.btn_save_note = QPushButton("💾 Save Note")
        self.btn_delete_note = QPushButton("🗑️ Delete")
        self.note_action_layout.addWidget(self.btn_save_note)
        self.note_action_layout.addWidget(self.btn_delete_note)
        
        note_layout.addWidget(QLabel("<b>Obsidian-Style Notebook</b>"))
        note_layout.addWidget(self.note_title_input)
        note_layout.addWidget(self.note_editor)
        note_layout.addLayout(self.note_action_layout)
        self.main_splitter.addWidget(self.note_container)

        # 3. AI Assistant Prompt Panel
        self.ai_container = QWidget()
        ai_layout = QVBoxLayout(self.ai_container)
        
        self.ai_prompt_history = QTextEdit()
        self.ai_prompt_history.setReadOnly(True)
        self.ai_prompt_history.setPlaceholderText("The AI will ask questions and direct the generation process here...")
        
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("Answer prompts, ask to generate states, etc...")
        
        self.btn_send_prompt = QPushButton("⚡ Send Response")
        
        ai_layout.addWidget(QLabel("<b>Co-Author Assistant</b>"))
        ai_layout.addWidget(self.ai_prompt_history)
        ai_layout.addWidget(self.ai_input)
        ai_layout.addWidget(self.btn_send_prompt)
        self.main_splitter.addWidget(self.ai_container)

        # Set sizes (40% Map, 35% Note, 25% AI)
        self.main_splitter.setSizes([560, 490, 350])

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Clean Framework Ready.")

def main():
    app = QApplication(sys.argv)
    window = WorldsmithMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
