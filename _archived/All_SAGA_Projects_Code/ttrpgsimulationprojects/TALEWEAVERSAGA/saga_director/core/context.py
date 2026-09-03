from typing import Dict, Any, List
from sqlalchemy.orm import Session
from core.models import CampaignState, NPCEntity, WorldDelta, ActiveQuest

class ContextAssembler:
    """
    Consolidates disparate game data into a single GameState dict for the LangGraph AI Director.
    """
    @staticmethod
    def assemble_game_state(db: Session, campaign_id: str, player_action: Dict[str, Any] = None) -> Dict[str, Any]:
        campaign = db.query(CampaignState).filter(CampaignState.campaign_id == campaign_id).first()
        if not campaign:
            return {}

        # 1. Basic Vitals & Location
        state = {
            "player_id": campaign.player_id,
            "action_type": player_action.get("type", "PULSE") if player_action else "PULSE",
            "action_target": player_action.get("target", "NONE") if player_action else "NONE",
            "raw_chat_text": player_action.get("text", "") if player_action else "",
            "stamina_burned": player_action.get("stamina_cost", 0) if player_action else 0,
            "focus_burned": player_action.get("focus_cost", 0) if player_action else 0,
            "current_location": f"HEX_{campaign.current_hex_id}",
            "current_layer": 5, # Default to tactical analysis
            "weather": campaign.weather,
            "tension": campaign.tension,
            "chaos_numbers": campaign.chaos_numbers if isinstance(campaign.chaos_numbers, list) else [campaign.chaos_numbers],
            "math_log": "",
            "vtt_commands": [],
            "ai_narration": "",
            "active_encounter": None # TODO: Link if active
        }

        # 2. Nearby NPCs
        npcs = db.query(NPCEntity).filter(NPCEntity.campaign_id == campaign_id).all()
        state["nearby_entities"] = [
            {
                "id": n.entity_id,
                "name": n.name,
                "hp": n.hp,
                "disposition": n.disposition,
                "activity": n.current_activity
            } for n in npcs
        ]

        # 3. Recent World Changes (Deltas)
        deltas = db.query(WorldDelta).filter(WorldDelta.campaign_id == campaign_id).order_by(WorldDelta.id.desc()).limit(5).all()
        state["recent_changes"] = [
            {"x": d.x, "y": d.y, "change": f"{d.original_value} -> {d.new_value}"} for d in deltas
        ]

        # 4. Active Quests
        quests = db.query(ActiveQuest).filter(ActiveQuest.campaign_id == campaign_id).all()
        state["active_quests"] = [
            {"title": q.title, "objectives": q.objectives} for q in quests
        ]

        return state
