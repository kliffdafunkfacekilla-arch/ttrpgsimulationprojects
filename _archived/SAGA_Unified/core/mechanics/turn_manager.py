import logging
import random
from typing import Dict, Any, List

logger = logging.getLogger("TurnManager")

class TurnManager:
    def __init__(self, bus):
        self.bus = bus
        
        self.is_combat_active = False
        self.initiative_order = []
        self.current_turn_index = 0
        
        self.active_entity = None
        self.beats = {
            "move": False,
            "stamina": False,
            "focus": False
        }
        
    def start_combat(self, combatants: List[Dict[str, Any]]):
        """
        Initiates combat and sets up the turn order based on Awareness + Reflexes + Logic.
        combatants should be a list of dicts: {"uuid": "player_1", "stats": {"awareness": 5, "reflexes": 5, "logic": 5}}
        """
        self.is_combat_active = True
        
        # Roll initiative for all combatants
        rolls = []
        for c in combatants:
            stats = c.get("stats", {})
            score = stats.get("awareness", 0) + stats.get("reflexes", 0) + stats.get("logic", 0)
            roll = score + random.randint(1, 20)
            rolls.append({"uuid": c["uuid"], "roll": roll})
            
        # Sort descending
        rolls.sort(key=lambda x: x["roll"], reverse=True)
        
        self.initiative_order = [r["uuid"] for r in rolls]
        
        self.current_turn_index = 0
        self._start_turn(self.initiative_order[0])
        
    def _start_turn(self, entity_uuid: str):
        """Resets beats for the new turn."""
        self.active_entity = entity_uuid
        self.beats = {
            "move": True,
            "stamina": True,
            "focus": True
        }
        logger.info(f"Turn started for {entity_uuid}.")
        self.bus.publish("TURN_STARTED", {"uuid": entity_uuid})
        if entity_uuid == "player_1":
            self.bus.publish("BEAT_UPDATE", {"beats": self.beats})
        
    def end_turn(self, entity_uuid: str) -> bool:
        """Ends the turn for the given entity, passing to the next."""
        if not self.is_combat_active:
            return False
            
        if entity_uuid != self.active_entity:
            return False # Not their turn
            
        self.current_turn_index = (self.current_turn_index + 1) % len(self.initiative_order)
        next_entity = self.initiative_order[self.current_turn_index]
        
        self._start_turn(next_entity)
        return True
        
    def consume_beat(self, entity_uuid: str, beat_type: str) -> bool:
        """
        Attempts to consume a beat (move, stamina, focus).
        Returns True if successful, False if the beat is already used or it's not their turn.
        """
        # If combat isn't active, we might allow freeform actions, or we might auto-start combat.
        # For this prototype, if combat isn't active, actions are always allowed.
        if not self.is_combat_active:
            return True
            
        if entity_uuid != self.active_entity:
            return False
            
        if beat_type in self.beats and self.beats[beat_type]:
            self.beats[beat_type] = False
            if entity_uuid == "player_1":
                self.bus.publish("BEAT_UPDATE", {"beats": self.beats})
            return True
            
        return False

    def can_act(self, entity_uuid: str, beat_type: str) -> bool:
        if not self.is_combat_active:
            return True
        if entity_uuid != self.active_entity:
            return False
        return self.beats.get(beat_type, False)
