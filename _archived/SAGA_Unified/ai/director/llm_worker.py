import json
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

SHARED_LLAMA_MODEL = None

def preload_shared_llama(model_path: str = None):
    """
    Pre-initializes the GGUF Llama model BEFORE QApplication is instantiated.
    Prevents Windows C++ OpenMP / Qt thread access violation crashes.
    """
    global SHARED_LLAMA_MODEL
    if SHARED_LLAMA_MODEL is not None:
        return SHARED_LLAMA_MODEL

    default_dir = Path(__file__).resolve().parents[2] / "models"
    path = Path(model_path) if model_path else None
    
    if path is None:
        candidates = list(default_dir.glob("*.gguf"))
        if candidates:
            path = candidates[0]
            
    if path and path.is_file() and Llama:
        for threads in [1, 2]:
            try:
                SHARED_LLAMA_MODEL = Llama(
                    model_path=str(path),
                    n_ctx=2048,
                    n_threads=threads,
                    n_gpu_layers=0,
                    verbose=False,
                )
                print(f"[LLMWorker] Shared Llama model pre-warmed successfully (threads={threads}).")
                break
            except Exception as e:
                print(f"[LLMWorker] Pre-warm failed with threads={threads}: {e}")
                
    return SHARED_LLAMA_MODEL

class LLMWorker(QThread):
    """
    Asynchronous LLM worker running in a dedicated QThread.
    Prevents the main PyQt event loop from freezing during long inference tasks.
    """
    token_generated = pyqtSignal(str)
    generation_complete = pyqtSignal(str, str) # tag, full_text
    error_occurred = pyqtSignal(str)

    def __init__(self, bus, model_path: str = None, parent=None):
        super().__init__(parent)
        self.bus = bus
        self.model_path = model_path
        self._llama = None
        self._is_ready = False
        
        # Request Queue
        self._request_queue = []
        
        self.init_error = None
        self.initialize_model()

    def initialize_model(self):
        global SHARED_LLAMA_MODEL
        if SHARED_LLAMA_MODEL is None:
            preload_shared_llama(self.model_path)
            
        if SHARED_LLAMA_MODEL is not None:
            self._llama = SHARED_LLAMA_MODEL
            self._is_ready = True
            self.init_error = None
        else:
            self.init_error = "Model not found or llama_cpp not installed."

    def run(self):
        """Main thread loop that processes inference requests."""
        if self.init_error:
            self.error_occurred.emit(self.init_error)
            return
            
        if not self._is_ready:
            return
            
        while not self.isInterruptionRequested():
            if self._request_queue:
                req = self._request_queue.pop(0)
                
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
                    in_prose = False
                    prose_started = False
                    
                    for chunk in stream:
                        if self.isInterruptionRequested():
                            break
                        token = chunk["choices"][0].get("text", "")
                        if token:
                            full_text += token
                            
                            # Parse out only the narrative_prose field for live streaming
                            if tag != "silent_setup":
                                if '"narrative_prose": "' in full_text and not prose_started:
                                    prose_started = True
                                    in_prose = True
                                    # Grab anything generated right after the starting quote
                                    start_idx = full_text.find('"narrative_prose": "') + len('"narrative_prose": "')
                                    new_text = full_text[start_idx:]
                                    if new_text:
                                        self.token_generated.emit(new_text.replace('\\n', '\n'))
                                elif in_prose:
                                    # We are inside the string. Stop if we hit the closing quote that leads to next JSON key.
                                    # A simple heuristic: if we see '",\n' or '",\r\n', we are done.
                                    if '",\n' in full_text[-10:] or '",\r\n' in full_text[-10:]:
                                        in_prose = False
                                    else:
                                        # Safe to emit
                                        self.token_generated.emit(token.replace('\\n', '\n').replace('\\"', '"'))
                                    
                    full_text = full_text.strip()
                    
                    # Try parsing as JSON
                    try:
                        # Clean up any potential markdown code blocks
                        clean_text = full_text.replace("```json", "").replace("```", "").strip()
                        data = json.loads(clean_text)
                        
                        prose = data.get("narrative_prose", full_text)
                        mechanics = data.get("mechanical_actions", [])
                        
                        self.bus.publish("AI_NARRATED", {"prose": prose, "tag": tag})
                        if mechanics:
                            self.bus.publish("MECHANICS_TRIGGERED", {"actions": mechanics})
                            
                        self.generation_complete.emit(tag, clean_text)
                        
                    except json.JSONDecodeError:
                        # Fallback for plain text
                        self.bus.publish("AI_NARRATED", {"prose": full_text, "tag": tag})
                        self.generation_complete.emit(tag, full_text)
                        
                except Exception as e:
                    self.error_occurred.emit(str(e))
            
            self.msleep(10) # Prevent CPU hogging

    def request_generation(self, prompt: str, tag: str = "narrative", max_tokens: int = 400):
        """Called by the main thread to queue a request."""
        self._request_queue.append({
            "prompt": prompt,
            "tag": tag,
            "max_tokens": max_tokens
        })
