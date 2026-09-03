from typing import List, Dict
from saga_engine.core.bus import EventBus
from saga_engine.core.state import CampaignState
from saga_engine.core.chronicler import Chronicler

from saga_engine.core.world_loader import WorldLoader

class SimulationOrgan:
    """Base class for world-simulation modules."""
    def __init__(self, bus: EventBus, state: CampaignState, chronicler: Chronicler, loader: WorldLoader):
        self.bus = bus
        self.state = state
        self.chronicler = chronicler
        self.loader = loader

    def run_hourly(self):
        pass

    def run_daily(self):
        pass

class SimulationDirector:
    """
    Coordinates world simulation pulses.
    Delegates work to various 'Organs' for atmosphere, factions, and ecology.
    """
    def __init__(self, bus: EventBus, state: CampaignState, chronicler: Chronicler, loader: WorldLoader):
        self.bus = bus
        self.state = state
        self.chronicler = chronicler
        self.loader = loader
        self.organs: List[SimulationOrgan] = []

        # Subscribe to Chronos beats
        self.bus.subscribe("CHRONOS_HOUR", self.on_hour_pulse)
        self.bus.subscribe("CHRONOS_DAY", self.on_day_pulse)

    def register_organ(self, organ: SimulationOrgan):
        self.organs.append(organ)

    def on_hour_pulse(self, payload: dict):
        """Triggers hourly logic for all registered organs."""
        if self.state.simulation_paused:
            return
            
        for organ in self.organs:
            organ.run_hourly()

    def on_day_pulse(self, payload: dict):
        """Triggers daily logic for all registered organs."""
        if self.state.simulation_paused:
            return

        summary = "Simulation Beat: Global state updated."
        self.chronicler.log_event("SYSTEM", "SIM_PULSE", summary, game_time=payload.get("time", "Unknown"))
        
        for organ in self.organs:
            organ.run_daily()
