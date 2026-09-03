"""
combat_manager.py
Manages the Combat State Machine, Initiative, and autonomous NPC turns.
"""
import logging
import random
from typing import Dict, Any

logger = logging.getLogger("CombatManager")

class CombatManager:
    def __init__(self, bus):
        self.bus = bus
        self.bus.subscribe("COMBAT_START", self._on_combat_start)
        self.bus.subscribe("END_TURN", self._on_end_turn)
        
        self.initiative_queue = []
        self.active_index = -1
        self.in_combat = False
        
    def _on_combat_start(self, payload: Dict[str, Any]):
        self.in_combat = True
        entities = payload.get("entities", [])
        player_stats = payload.get("player_stats", {})
        
        # Roll initiative
        queue = []
        
        p_ref = player_stats.get("reflexes", 5)
        p_roll = random.randint(1, 20) + p_ref
        queue.append({"uuid": "player_1", "name": "Player", "roll": p_roll, "is_player": True})
        
        for ent in entities:
            e_roll = random.randint(1, 20) + 4
            queue.append({
                "uuid": ent.get("uuid"), 
                "name": ent.get("name", "Unknown"), 
                "roll": e_roll, 
                "is_player": False,
                "tags": ent.get("tags", [])
            })
            
        # Sort descending
        queue.sort(key=lambda x: x["roll"], reverse=True)
        self.initiative_queue = queue
        self.active_index = -1
        
        log_str = "\n".join([f"{i+1}. {q['name']} ({q['roll']})" for i, q in enumerate(queue)])
        logger.info(f"Combat Started! Initiative Order:\n{log_str}")
        self.bus.publish("SYSTEM_LOG", {"message": f"<br><font color='orange'><b>COMBAT INITIATIVE:</b></font><br>{log_str.replace(chr(10), '<br>')}"})
        
        self._advance_turn()
        
    def _on_end_turn(self, payload):
        if self.in_combat:
            self._advance_turn()
            
    def _advance_turn(self):
        if not self.initiative_queue: return
        
        self.active_index = (self.active_index + 1) % len(self.initiative_queue)
        active_ent = self.initiative_queue[self.active_index]
        
        self.bus.publish("SYSTEM_LOG", {"message": f"<br><font color='#FF5555'><b>Turn: {active_ent['name']}</b></font>"})
        
        if active_ent["is_player"]:
            self.bus.publish("SYSTEM_LOG", {"message": "<i>Awaiting player command...</i>"})
        else:
            self._generate_ai_turn(active_ent)
            
    def _generate_ai_turn(self, entity):
        name = entity["name"]
        tags = entity.get("tags", [])
        
        prompt = (
            f"[SYSTEM OVERRIDE]: It is the NPC's turn in combat. "
            f"NPC Name: {name}. Tags: {tags}. "
            f"Target: Player. "
            f"Generate a short, brutal action intent for this NPC (e.g., 'The bandit swings his rusty pipe at the Wanderer!'). "
            f"Do not write player actions, only the NPC's attack."
        )
        
        self.bus.publish("EXECUTE_AI_INTENT", {"intent": prompt, "source_uuid": entity["uuid"], "source_name": name})
