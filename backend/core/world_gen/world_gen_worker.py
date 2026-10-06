import time
import logging
from PyQt6.QtCore import QThread, pyqtSignal

from core.world_gen.world_gen import WorldGenerator

logger = logging.getLogger("WorldGenWorker")

class WorldGenWorker(QThread):
    """
    Background worker for procedurally generating battle maps without freezing the UI.
    """
    map_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.world_gen = WorldGenerator()
        self._is_running = True
        self._pending_location = None
        self._pending_ambush = False
        self._pending_dynamic_entities = None

    def request_generation(self, location_name: str, is_ambush: bool = False, dynamic_entities: list = None):
        """Queue a location for map generation."""
        self._pending_location = location_name
        self._pending_ambush = is_ambush
        self._pending_dynamic_entities = dynamic_entities

    def run(self):
        """Main loop of the worker thread."""
        logger.info("WorldGenWorker thread started.")
        while self._is_running:
            if self._pending_location:
                loc = self._pending_location
                is_ambush = self._pending_ambush
                dynamic_entities = self._pending_dynamic_entities
                self._pending_location = None
                self._pending_ambush = False
                self._pending_dynamic_entities = None

                try:
                    logger.info(f"Generating map for {loc} (Ambush: {is_ambush})...")
                    payload = self.world_gen.generate_local_map(loc, is_ambush=is_ambush, dynamic_entities=dynamic_entities)
                    self.map_ready.emit(payload)
                except Exception as e:
                    logger.error(f"Error generating map: {e}")
                    self.error_occurred.emit(str(e))

            time.sleep(0.1)

    def requestInterruption(self):
        self._is_running = False
        super().requestInterruption()
