import random
from typing import Dict, List, Optional
from saga_engine.core.state import CampaignState
from saga_engine.core.bus import EventBus
from saga_engine.core.chronicler import Chronicler

class QuestWeaver:
    """
    The Master Narrator of the S.A.G.A. Brain.
    Manages the Quest Framework, Pacing, and JIT Story Seeds.
    """
    
    def __init__(self, bus: EventBus, state: CampaignState, chronicler: Chronicler):
        self.bus = bus
        self.state = state
        self.chronicler = chronicler
        
        # Pacing State: 0-100 (100 = Climax reached, needs resolution)
        self.tension_level = 0
        
        # Subscribe to events that build tension
        self.bus.subscribe("MAP_CLICK", self._on_player_move)
        self.bus.subscribe("CHRONOS_DAY", self._on_new_day)

    def generate_story_seed(self, local_context: Dict) -> Dict:
        """
        Builds a JIT story seed based on biome and local POIs.
        """
        biome = local_context.get("biome", "Wilderness")
        pois = local_context.get("pois", [])
        
        # Select a primary POI for the seed if available
        primary_poi = random.choice(pois) if pois else {"type": "Natural Feature"}
        
        # Seed themes
        hooks = {
            "Forest": ["Whispering Shadows", "The Lost Scout", "Ancient Resonance"],
            "Wasteland": ["Scavenger's Bounty", "The Corroded Gate", "Signal from the Fog"],
            "Mountains": ["The High Pass", "Stone Sentinel", "Echoes in the Cave"]
        }
        
        theme = random.choice(hooks.get(biome, ["Intriguing Discovery"]))
        
        seed = {
            "id": f"SEED_{random.randint(1000, 9999)}",
            "title": f"{theme} at {primary_poi['type']}",
            "biome_context": biome,
            "associated_poi": primary_poi,
            "status": "Available",
            "urgency": random.randint(1, 5)
        }
        
        self.chronicler.log_event("QUEST", "SEED_GENERATED", 
                                f"New Story Seed: {seed['title']}", 
                                payload=seed)
        
        return seed

    def update_pacing(self, tension_shift: int):
        """Adjusts the narrative tension and triggers 'Beats' accordingly."""
        self.tension_level = max(0, min(100, self.tension_level + tension_shift))
        
        if self.tension_level >= 80:
            self._trigger_climax_event()
        elif self.tension_level <= 20:
            self._trigger_rest_beat()

    def _on_player_move(self, payload: dict):
        """Movement gradually builds tension/fatigue."""
        self.update_pacing(random.randint(1, 3))

    def _on_new_day(self, payload: dict):
        """Resolution of a full day reduces tension naturally."""
        self.update_pacing(-10)

    def _trigger_climax_event(self):
        """Forces a high-stakes event based on current tension."""
        self.bus.publish("STATE_UPDATE", {
            "element": "LOG", 
            "text": "[DIRECTOR] Narrative Tension at Climax. Triggering high-stakes event."
        })
        self.tension_level = 50 # Reset to mid-tension

    def _trigger_rest_beat(self):
        """Triggers a low-tension moment for character development or recovery."""
        self.bus.publish("STATE_UPDATE", {
            "element": "LOG", 
            "text": "[DIRECTOR] Quiet moment. Opportunity for respite."
        })
