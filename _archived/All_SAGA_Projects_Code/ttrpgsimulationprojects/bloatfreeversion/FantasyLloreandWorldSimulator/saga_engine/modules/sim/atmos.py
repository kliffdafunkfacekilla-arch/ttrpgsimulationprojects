import random
from typing import Dict
from saga_engine.core.simulation import SimulationOrgan
from saga_engine.core.bus import EventBus
from saga_engine.core.state import CampaignState
from saga_engine.core.chronicler import Chronicler
from saga_engine.core.world_loader import WorldLoader

class AetherFlow(SimulationOrgan):
    """
    Atmospheric and Aetheric Simulation.
    Manages regional moisture, winds, and magical (mana) saturation.
    """
    
    def __init__(self, bus: EventBus, state: CampaignState, chronicler: Chronicler, loader: WorldLoader):
        super().__init__(bus, state, chronicler, loader)
        self.biome_bases = {
            0: {"mana": 0.1, "moisture": 1.0},  # Ocean
            1: {"mana": 0.3, "moisture": 0.3},  # Tundra
            2: {"mana": 0.4, "moisture": 0.6},  # Grassland
            3: {"mana": 0.6, "moisture": 0.8},  # Forest
            4: {"mana": 0.2, "moisture": 0.1},  # Desert
            5: {"mana": 0.5, "moisture": 0.4},  # Mountains
            6: {"mana": 0.7, "moisture": 0.9},  # Swamp
            7: {"mana": 0.4, "moisture": 0.5},  # Hills
            8: {"mana": 0.9, "moisture": 0.1},  # Wasteland
            9: {"mana": 1.0, "moisture": 0.5},  # Zone: Mass
            10: {"mana": 1.0, "moisture": 0.5}, # Zone: Ordo
            11: {"mana": 1.0, "moisture": 0.5}, # Zone: Motus
            12: {"mana": 1.0, "moisture": 0.5}  # Zone: Flux
        }
        self.is_initialized = False

    def _initialize_hexes(self):
        """Sets initial values for all hexes if not present."""
        # Note: We need the hex data to know the biomes.
        # Since we don't have the loader, we assume the CampaignState has hexes or we wait for logic.
        # Actually, the WorldLoader syncs hexes to state.discovered_hexes? No, that's just strings.
        # Let's assume the SimulationDirector or Loader provides the hex list.
        # For now, we'll try to get it from the state's hex_metadata keys if populated, or wait for an init pulse.
        pass

    def run_hourly(self):
        """Simulates minor atmospheric drift."""
        meta = self.state.dynamic_world.hex_metadata
        
        # Simple drift for existing hexes
        for hex_id, data in meta.items():
            # Randomly drift variables
            data["mana"] = max(0.0, min(1.0, data.get("mana", 0.5) + random.uniform(-0.01, 0.01)))
            data["moisture"] = max(0.0, min(1.0, data.get("moisture", 0.5) + random.uniform(-0.01, 0.01)))

    def run_daily(self):
        """Major weather shifts or hazard generation."""
        # 5% chance of a local hazard in a high-mana zone
        meta = self.state.dynamic_world.hex_metadata
        for hex_id, data in meta.items():
            if data["mana"] > 0.9 and random.random() < 0.05:
                hazard = {
                    "hex": hex_id,
                    "type": "Mana Storm",
                    "severity": random.uniform(0.5, 1.0)
                }
                self.state.dynamic_world.active_hazards.append(hazard)
                self.chronicler.log_event("WORLD", "HAZARD_SPAWN", 
                                         f"A Mana Storm has ignited at hex {hex_id}", 
                                         game_time=str(self.state.time))

    def seed_hex(self, q: int, r: int, biome_id: int):
        """Called by the world loader or director to populate initial metadata."""
        hex_id = f"{q},{r}"
        base = self.biome_bases.get(biome_id, {"mana": 0.5, "moisture": 0.5})
        self.state.dynamic_world.hex_metadata[hex_id] = {
            "mana": base["mana"],
            "moisture": base["moisture"],
            "tension": 0.0
        }
