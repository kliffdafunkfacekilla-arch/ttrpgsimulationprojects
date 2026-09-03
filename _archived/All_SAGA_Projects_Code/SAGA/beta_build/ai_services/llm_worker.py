import os
import json
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

class LLMWorker(QThread):
    """
    Asynchronous LLM worker running in a dedicated QThread.
    Prevents the main PyQt event loop from freezing during long inference tasks.
    """
    token_generated = pyqtSignal(str)
    generation_complete = pyqtSignal(str, str) # tag, full_text
    error_occurred = pyqtSignal(str)

    def __init__(self, model_path: str = None, parent=None):
        super().__init__(parent)
        self.model_path = model_path
        self._llama = None
        self._is_ready = False
        
        # Request Queue
        self._current_request = None
        
        # Initialize model on MAIN THREAD to prevent QThread access violation crash
        self.initialize_model()

    def initialize_model(self):
        default_dir = Path(__file__).resolve().parents[2] / "models"
        path = Path(self.model_path) if self.model_path else None
        
        if path is None:
            candidates = list(default_dir.glob("*.gguf"))
            if candidates:
                path = candidates[0]
                
        if path and path.is_file() and Llama:
            try:
                self._llama = Llama(
                    model_path=str(path),
                    n_ctx=4096,
                    n_threads=2,
                    n_gpu_layers=0,  # Disabled GPU offloading to prevent access violation crashes
                    verbose=False,
                )
                self._is_ready = True
            except Exception as e:
                self.error_occurred.emit(f"Failed to load LLM: {str(e)}")
        else:
            self.error_occurred.emit("Model not found or llama_cpp not installed.")

    def run(self):
        """Main thread loop that processes inference requests."""
        if not self._is_ready:
            return
            
        while not self.isInterruptionRequested():
            if self._current_request:
                req = self._current_request
                self._current_request = None # Clear immediately to allow new requests
                
                prompt = req.get("prompt", "")
                tag = req.get("tag", "generic")
                max_tokens = req.get("max_tokens", 400)
                
                try:
                    # Stream tokens back to the UI
                    stream = self._llama(
                        prompt,
                        max_tokens=max_tokens,
                        temperature=0.72,
                        top_p=0.9,
                        stream=True
                    )
                    
                    full_text = ""
                    for chunk in stream:
                        if self.isInterruptionRequested():
                            break
                        token = chunk["choices"][0].get("text", "")
                        if token:
                            full_text += token
                            self.token_generated.emit(token)
                            
                    self.generation_complete.emit(tag, full_text.strip())
                except Exception as e:
                    self.error_occurred.emit(str(e))
            
            self.msleep(10) # Prevent CPU hogging

    def request_generation(self, prompt: str, tag: str = "narrative", max_tokens: int = 400):
        """Called by the main thread to queue a request."""
        self._current_request = {
            "prompt": prompt,
            "tag": tag,
            "max_tokens": max_tokens
        }
