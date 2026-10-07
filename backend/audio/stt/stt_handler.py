import speech_recognition as sr
from PyQt6.QtCore import QThread, pyqtSignal

class STTHandler:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Adjust for ambient noise on init
        print("[SYSTEM]: Calibrating microphone for ambient noise...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        print("[SYSTEM]: Microphone ready.")

    def listen(self) -> str:
        """Blocks and listens to the microphone until speech is detected."""
        with self.microphone as source:
            print("\n[LISTENING...] (Speak now)")
            try:
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
                print("[PROCESSING AUDIO...]")
                # Using sphinx for offline capabilities, but fallback to google if needed
                try:
                    # Trying pocketsphinx offline first
                    text = self.recognizer.recognize_sphinx(audio)
                    return text
                except sr.UnknownValueError:
                    return ""
                except sr.RequestError:
                    # Sphinx might not be installed correctly, use Google as a fallback
                    text = self.recognizer.recognize_google(audio)
                    return text
            except sr.WaitTimeoutError:
                return ""
            except Exception as e:
                print(f"[STT Error]: {e}")
                return ""

class STTWorker(QThread):
    """QThread worker for non-blocking STT operations."""
    result_ready = pyqtSignal(str)

    def __init__(self, stt_handler):
        super().__init__()
        self.stt_handler = stt_handler

    def run(self):
        """Run STT in background thread."""
        result = self.stt_handler.listen()
        self.result_ready.emit(result)
