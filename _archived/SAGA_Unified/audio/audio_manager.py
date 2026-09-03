import pyttsx3
import speech_recognition as sr
from PyQt6.QtCore import QThread, pyqtSignal
import numpy as np
from faster_whisper import WhisperModel

class TTSWorker(QThread):
    """
    Dedicated QThread for Text-to-Speech to prevent UI freezes.
    """
    finished_speaking = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._text_queue = []
        self._engine = None

    def _init_engine(self):
        if self._engine is None:
            try:
                self._engine = pyttsx3.init()
                self._engine.setProperty('rate', 150) # Slower, more dramatic pacing
            except Exception as e:
                self.error_occurred.emit(f"TTS Init Error: {str(e)}")

    def run(self):
        self._init_engine()
        if not self._engine:
            return
            
        while not self.isInterruptionRequested():
            if self._text_queue:
                text = self._text_queue.pop(0)
                try:
                    self._engine.say(text)
                    self._engine.runAndWait()
                    self.finished_speaking.emit()
                except Exception as e:
                    self.error_occurred.emit(str(e))
            self.msleep(100)
            
    def speak(self, text: str):
        self._text_queue.append(text)

class STTWorker(QThread):
    """
    Dedicated QThread for continuous Speech-to-Text listening.
    """
    speech_recognized = pyqtSignal(str)
    listening_status = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.recognizer = sr.Recognizer()
        # Force 16kHz sample rate for Whisper compatibility
        self.microphone = sr.Microphone(sample_rate=16000)
        self.model = None
        
        # Optimize recognizer for quicker responses
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
        self._active = False

    def run(self):
        try:
            # Strictly offline. Will check local cache only.
            self.model = WhisperModel("tiny.en", device="cpu", compute_type="int8", download_root="models/whisper", local_files_only=True)
        except Exception as e:
            self.error_occurred.emit(f"Failed to load STT model: {str(e)}")
            return
            
        self._active = True
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
        while self._active and not self.isInterruptionRequested():
            self.listening_status.emit(True)
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=10)
                
                self.listening_status.emit(False)
                # Attempt to transcribe locally
                raw_data = audio.get_raw_data(convert_rate=16000, convert_width=2)
                audio_np = np.frombuffer(raw_data, np.int16).astype(np.float32) / 32768.0
                
                segments, _ = self.model.transcribe(audio_np, beam_size=1)
                text = " ".join([segment.text for segment in segments]).strip()
                
                if text:
                    self.speech_recognized.emit(text)
                    
            except sr.WaitTimeoutError:
                pass # Expected, just loop again
            except sr.UnknownValueError:
                pass # Could not understand audio
            except Exception as e:
                self.error_occurred.emit(str(e))
                
    def stop_listening(self):
        self._active = False
