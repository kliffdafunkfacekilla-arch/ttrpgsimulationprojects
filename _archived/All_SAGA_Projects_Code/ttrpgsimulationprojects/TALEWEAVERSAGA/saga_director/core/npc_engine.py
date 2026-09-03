from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from .models import NPCEntity, NPCSchedule, CampaignState

class NPCEngine:
    @staticmethod
    def resolve_npc_routines(db: Session, campaign_id: str, hex_id: int, current_time: float) -> List[Dict]:
        """
        Calculates the active positions and actions of all NPCs in a given hex
        based on their schedules and the current world clock.
        """
        npcs = db.query(NPCEntity).filter(
            NPCEntity.campaign_id == campaign_id,
            NPCEntity.hex_id == hex_id
        ).all()
        
        resolved_tokens = []
        
        for npc in npcs:
            if npc.hp <= 0:
                continue # NPC is dead
                
            token = {
                "id": npc.id,
                "name": npc.name,
                "x": npc.lx,
                "y": npc.ly,
                "hp": npc.hp,
                "max_hp": npc.max_hp,
                "disposition": npc.disposition,
                "action": "Idle"
            }
            
            # Apply schedule if it exists
            if npc.schedule_id:
                schedule = db.query(NPCSchedule).filter(NPCSchedule.id == npc.schedule_id).first()
                if schedule and schedule.routines:
                    # Find matching routine for current time
                    for r in schedule.routines:
                        start = r.get("start", 0.0)
                        end = r.get("end", 24.0)
                        
                        # Handle overnight schedules
                        if start <= end:
                            in_time = start <= current_time < end
                        else:
                            in_time = current_time >= start or current_time < end
                            
                        if in_time:
                            token["x"] = r.get("lx", token["x"])
                            token["y"] = r.get("ly", token["y"])
                            token["action"] = r.get("action", "Idle")
                            break
            
            resolved_tokens.append(token)
            
        return resolved_tokens

    @staticmethod
    def seed_default_npcs(db: Session, campaign_id: str, hex_id: int):
        """Seeds a few NPCs and schedules for the vertical slice demonstration."""
        # 1. Create Schedules
        blacksmith_sched = NPCSchedule(
            id="SCH_BLACKSMITH",
            name="Blacksmith Routine",
            routines=[
                {"start": 22.0, "end": 6.0, "lx": 42, "ly": 42, "action": "Sleeping"},
                {"start": 6.0, "end": 8.0, "lx": 45, "ly": 45, "action": "Pacing"},
                {"start": 8.0, "end": 18.0, "lx": 55, "ly": 55, "action": "Forging"},
                {"start": 18.0, "end": 22.0, "lx": 50, "ly": 40, "action": "Drinking"}
            ]
        )
        
        db.merge(blacksmith_sched)
        
        # 2. Create NPCs
        thorin = NPCEntity(
            id=f"NPC_{campaign_id}_thorin",
            campaign_id=campaign_id,
            name="Thorin Ironfoot",
            hex_id=hex_id,
            lx=55, ly=55,
            hp=25, max_hp=25,
            disposition="FRIENDLY",
            schedule_id="SCH_BLACKSMITH"
        )
        
        db.merge(thorin)
        db.commit()
