import json
import random

# Shape Costs: 
# Point: 1 Focus
# Line: 1 Focus, 1 Move
# Cone: 2 Focus
# Burst: 1 Focus, 1 Stamina
# Wall: 2 Focus, 1 Move
# Aura: 1 Focus, 1 Move
SHAPE_COSTS = {
    "point": {"focus": 1, "move": 0, "stamina": 0},
    "line": {"focus": 1, "move": 1, "stamina": 0},
    "cone": {"focus": 2, "move": 0, "stamina": 0},
    "burst": {"focus": 1, "move": 0, "stamina": 1},
    "wall": {"focus": 2, "move": 1, "stamina": 0},
    "aura": {"focus": 1, "move": 1, "stamina": 0}
}

class AnomalyParser:
    """
    Parses LLM-generated JSON for a spell and deducts the BRUTAL engine costs.
    """
    
    @staticmethod
    def parse_spell(actor, anomaly_json_str: str) -> dict:
        """
        Expects a JSON string resembling:
        {
            "shape": "Line",
            "school": "Mass",
            "effect_rank": 4,
            "power_scale": 5
        }
        """
        try:
            equation = json.loads(anomaly_json_str)
        except json.JSONDecodeError:
            return {"success": False, "error": "Invalid spell equation format."}
            
        shape = equation.get("shape", "").lower()
        school = equation.get("school", "Unknown")
        rank = equation.get("effect_rank", 1)
        scale = equation.get("power_scale", 1)
        
        # 1. Base Shape Cost (Action Beats)
        shape_cost = SHAPE_COSTS.get(shape, {"focus": 1, "move": 0, "stamina": 0})
        
        # 2. Total Costs
        total_focus = shape_cost["focus"] + rank    # Focus Beats + F-Die
        total_stamina = shape_cost["stamina"] + scale # Stamina Beats + S-Die
        total_move = shape_cost["move"]
        
        # 3. Check Battery
        if actor.active_focus < total_focus:
            return {"success": False, "error": f"Insufficient Focus. Need {total_focus}, have {actor.active_focus}."}
        if actor.active_stamina < total_stamina:
            return {"success": False, "error": f"Insufficient Stamina. Need {total_stamina}, have {actor.active_stamina}."}
            
        # Optional: Check Beats available this turn (we assume the action check happens beforehand, but we can check here)
        if hasattr(actor, "beats"):
            if actor.beats.get("focus", 0) < shape_cost["focus"]:
                return {"success": False, "error": "Not enough Focus beats remaining this turn."}
            if actor.beats.get("move", 0) < shape_cost["move"]:
                return {"success": False, "error": "Not enough Move beats remaining this turn."}
            if actor.beats.get("stamina", 0) < shape_cost["stamina"]:
                return {"success": False, "error": "Not enough Stamina beats remaining this turn."}
                
            actor.beats["focus"] -= shape_cost["focus"]
            actor.beats["move"] -= shape_cost["move"]
            actor.beats["stamina"] -= shape_cost["stamina"]
            
        # Deduct Pools
        actor.active_focus -= total_focus
        actor.active_stamina -= total_stamina
        
        return {
            "success": True,
            "school": school,
            "shape": shape,
            "rank": rank,
            "scale": scale,
            "cost_summary": f"Burned {total_focus} Focus and {total_stamina} Stamina.",
            "narrative_hint": f"[ANOMALY CAST] {actor.name} shapes a {rank}-Rank {school} {shape} at {scale}-Scale Power! (-{total_focus} Focus, -{total_stamina} Stamina)"
        }
