from saga_engine.core.state import CampaignState
from saga_engine.core.bus import EventBus
from saga_engine.core.chronicler import Chronicler

class ChronosManager:
    """
    The heart of the simulation pulse. 
    Manages game time intervals and triggers world-event cycles.
    """
    
    def __init__(self, bus: EventBus, state: CampaignState, chronicler: Chronicler):
        self.bus = bus
        self.state = state
        self.chronicler = chronicler
        
        # Subscribe to manual time adjustments or heartbeats
        self.bus.subscribe("PULSE_START", self.on_pulse)

    def on_pulse(self, payload: dict):
        """Advances the simulation by a fixed increment (default: 1 hour)."""
        if self.state.simulation_paused:
            return
            
        minutes = payload.get("increment_minutes", 60)
        self.advance_time(minutes)

    def advance_time(self, minutes: int):
        """Core logic for rolling the simulation clock forward."""
        t = self.state.time
        t.minute += minutes
        
        # Overflow logic
        while t.minute >= 60:
            t.minute -= 60
            t.hour += 1
            self._on_hour_passed()
            
        while t.hour >= 24:
            t.hour -= 24
            t.day += 1
            self._on_day_passed()
            
        # Seasonal Logic (Simplified: 30 days per month, 3 months per season)
        if t.day > 30:
            t.day = 1
            t.month += 1
            self._update_season()
            
        if t.month > 12:
            t.month = 1
            t.year += 1
            
        # Log the heartbeat
        summary = f"Chronos: {str(t)}"
        self.chronicler.log_event("SYSTEM", "TIME_PULSE", summary, game_time=str(t))
        
        # Broadcast the new time to the engine
        self.bus.publish("STATE_UPDATE", {"element": "TIME", "value": str(t)})

    def _on_hour_passed(self):
        """Triggers minor world updates (weather shifts, stamina regen)."""
        self.bus.publish("CHRONOS_HOUR", {"time": str(self.state.time)})
        
    def _on_day_passed(self):
        """Triggers major world updates (faction influence, market shifts)."""
        self.bus.publish("CHRONOS_DAY", {"time": str(self.state.time)})
        
    def _update_season(self):
        """Updates the weather/biological context based on the month."""
        seasons = {
            (12, 1, 2): "Deep Winter",
            (3, 4, 5): "New Growth",
            (6, 7, 8): "High Sun",
            (9, 10, 11): "Harvest Moon"
        }
        for months, name in seasons.items():
            if self.state.time.month in months:
                self.state.time.season = name
                break
