"""
Provides the main application window that orchestrates all UI screens and background workers.
"""
from PyQt6.QtWidgets import QMainWindow, QStackedWidget
from PyQt6.QtCore import pyqtSlot

# --- Beta Architecture ---
from beta_build.ui.event_bus import EventBus
from beta_build.ai_services.llm_worker import LLMWorker
from beta_build.audio.audio_manager import TTSWorker, STTWorker
from beta_build.core.models import CharacterSheet
from beta_build.ai_services.director import AIDirector

# --- Frontend Components ---
from beta_build.ui.char_creation import CharacterCreationScreen
from beta_build.ui.character_management import CharacterManagementScreen
from beta_build.ui.map_view import MapCanvas
from beta_build.ui.screens import StartMenu, VendorScreen

class SagaDesktopApp(QMainWindow):
    """
    The main window for the S.A.G.A Engine.
    Handles the initialization of background workers (LLM, Audio), the central EventBus,
    and the StackedWidget to navigate between UI views.
    """
    def __init__(self):
        super().__init__()
        self.bus = EventBus()
        self.setWindowTitle("S.A.G.A. Engine Beta")
        self.setGeometry(100, 100, 1200, 800)
        
        premium_css = """
        QMainWindow { background-color: #0f1115; }
        QWidget { color: #d8d8d8; font-family: 'Segoe UI', Arial, sans-serif; }
        QPushButton {
            background-color: #1c2026;
            border: 1px solid #3a414c;
            border-radius: 4px;
            color: #4CAF50;
            padding: 8px 16px;
            font-weight: bold;
            font-size: 14px;
        }
        QPushButton:hover { background-color: #2b323b; border: 1px solid #4CAF50; }
        QPushButton:pressed { background-color: #4CAF50; color: #0f1115; }
        QLabel { font-size: 14px; }
        QTextEdit, QLineEdit, QComboBox, QSpinBox {
            background-color: #14171c;
            border: 1px solid #2b323b;
            border-radius: 3px;
            color: #e0e0e0;
            padding: 6px;
        }
        QTextEdit:focus, QLineEdit:focus { border: 1px solid #4CAF50; }
        """
        self.setStyleSheet(premium_css)
        
        # UI Stack
        self.stack = QStackedWidget()
        
        # Initialize UI Screens
        self.start_menu = StartMenu(self.bus)
        self.char_creation = CharacterCreationScreen(self.bus)
        self.map_canvas = MapCanvas(self.bus)
        self.char_management = CharacterManagementScreen(self.bus)
        self.vendor_screen = VendorScreen(self.bus)
        
        self.stack.addWidget(self.start_menu)      # 0
        self.stack.addWidget(self.char_creation)   # 1
        self.stack.addWidget(self.map_canvas)      # 2
        self.stack.addWidget(self.char_management) # 3
        self.stack.addWidget(self.vendor_screen)   # 4
        
        self.setCentralWidget(self.stack)
        
        # Navigation Subs
        self.bus.subscribe("UI_START_NEW_GAME", lambda p: self.stack.setCurrentIndex(1))
        self.bus.subscribe("UI_LOAD_GAME", self._show_game)
        self.bus.subscribe("UI_FINALIZE_PARTY", self._show_game)
        
        self.bus.subscribe("UI_OPEN_CHAR_MANAGEMENT", lambda p: self.stack.setCurrentIndex(3))
        self.bus.subscribe("UI_CLOSE_CHAR_MANAGEMENT", lambda p: self.stack.setCurrentIndex(2))
        
        self.bus.subscribe("UI_OPEN_VENDOR", lambda p: self.stack.setCurrentIndex(4))
        self.bus.subscribe("UI_CLOSE_VENDOR", lambda p: self.stack.setCurrentIndex(2))

        # Intent Execution Sub
        self.bus.subscribe("EXECUTE_INTENT", self._handle_intent)
        self.bus.subscribe("UI_TOGGLE_MIC", self._handle_mic_toggle)

        # Background Workers Initialization
        self.init_workers()
        
        # Core State
        self.player_character = CharacterSheet(name="Wanderer")
        self.ai_director = AIDirector(load_model=False)

    def init_workers(self):
        """Initializes and connects QThreads for background AI and audio tasks."""
        # 1. LLM Worker
        self.llm_worker = LLMWorker(parent=self)
        self.llm_worker.token_generated.connect(self.map_canvas.on_token_received)
        self.llm_worker.generation_complete.connect(self.map_canvas.on_generation_complete)
        self.llm_worker.generation_complete.connect(self._on_llm_complete)
        self.llm_worker.error_occurred.connect(self.map_canvas.on_error)
        self.llm_worker.start()

        # 2. TTS Worker
        self.tts_worker = TTSWorker(parent=self)
        self.tts_worker.error_occurred.connect(self.map_canvas.on_error)
        self.tts_worker.start()

        # 3. STT Worker
        self.stt_worker = STTWorker(parent=self)
        self.stt_worker.speech_recognized.connect(self.map_canvas.on_speech_recognized)
        self.stt_worker.error_occurred.connect(self.map_canvas.on_error)
        
    def _show_game(self, payload=None):
        self.stack.setCurrentIndex(2)
        # Hook up the Pydantic character state to the UI HUD
        self.bus.publish("HUD_UPDATE", {"character": self.player_character.model_dump()})

    def _handle_intent(self, payload):
        intent = payload.get("intent", "")
        
        self.map_canvas.log_view.append("\n<i>Narrator is thinking...</i>\n")
        self.map_canvas.log_view.append("<font color='#a0a0ff'>[NARRATOR]:</font> ")
        
        # Use the actual AIDirector to generate a context-aware prompt
        # Using placeholder context values until world generation is hooked up
        prompt = self.ai_director.generate_llm_prompt(
            mechanical_result="The action resolves successfully.",
            context="The player is standing in a dusty, ruined town square.",
            intent_raw=intent
        )
        self.llm_worker.request_generation(prompt=prompt, tag="narrative")

    def _handle_mic_toggle(self, payload):
        if payload.get("active", False):
            if not self.stt_worker.isRunning():
                self.stt_worker.start()
        else:
            self.stt_worker.stop_listening()

    @pyqtSlot(str, str)
    def _on_llm_complete(self, tag: str, full_text: str):
        # Feed the fully generated text to the TTS worker
        if full_text:
            self.tts_worker.speak(full_text)

    def closeEvent(self, event):
        """Ensure threads are properly closed when shutting down."""
        self.llm_worker.requestInterruption()
        self.tts_worker.requestInterruption()
        self.stt_worker.requestInterruption()
        super().closeEvent(event)
