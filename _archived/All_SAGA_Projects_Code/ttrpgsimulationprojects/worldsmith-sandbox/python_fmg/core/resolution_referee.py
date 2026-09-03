import sqlite3
import json
import random

class ResolutionReferee:
    def __init__(self, db_path):
        self.db_path = db_path

    def execute_command(self, entity_id, intent, target_id):
        """
        Applies the V12 Narrative Scale logic (Stat Tier vs. Difficulty).
        Returns a dictionary with success boolean and metadata.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT name, stat_json, location_id FROM entities WHERE id = ?", (entity_id,))
            entity_data = cursor.fetchone()
            if not entity_data:
                return {"success": False, "result": "Entity not found.", "metadata": {}}
                
            e_name, e_stats_raw, e_loc = entity_data
            
            try:
                e_stats = json.loads(e_stats_raw) if e_stats_raw else {}
            except json.JSONDecodeError:
                e_stats = {}
                
            # Action specific logic
            if intent == "Travel":
                cursor.execute("SELECT friction, name FROM regional_cells WHERE id = ?", (target_id,))
                target_data = cursor.fetchone()
                if not target_data:
                    return {"success": False, "result": "Target cell not found.", "metadata": {}}
                    
                t_friction, t_name = target_data
                difficulty = 6 + int(t_friction) # Base difficulty 6 + friction
                
                # Use Agility for Travel
                agility_bonus = e_stats.get("agility", 0)
                roll = random.randint(1, 12)
                total = roll + agility_bonus
                
                if total >= difficulty:
                    # Success
                    cursor.execute("UPDATE entities SET location_id = ? WHERE id = ?", (target_id, entity_id))
                    conn.commit()
                    return {
                        "success": True, 
                        "result": f"{e_name} successfully traveled to {t_name}.",
                        "metadata": {"roll": total, "difficulty": difficulty, "target": t_name}
                    }
                else:
                    return {
                        "success": False, 
                        "result": f"{e_name} failed to travel to {t_name} due to harsh conditions.",
                        "metadata": {"roll": total, "difficulty": difficulty, "target": t_name}
                    }
                    
            elif intent == "Attack":
                cursor.execute("SELECT name, stat_json FROM entities WHERE id = ?", (target_id,))
                target_data = cursor.fetchone()
                if not target_data:
                    return {"success": False, "result": "Target entity not found.", "metadata": {}}
                    
                t_name, t_stats_raw = target_data
                try:
                    t_stats = json.loads(t_stats_raw) if t_stats_raw else {}
                except json.JSONDecodeError:
                    t_stats = {}
                    
                # Use Defense stat for difficulty
                defense_bonus = t_stats.get("defense", 0)
                difficulty = 6 + defense_bonus
                
                # Use Might stat for attack
                might_bonus = e_stats.get("might", 0)
                roll = random.randint(1, 12)
                total = roll + might_bonus
                
                if total >= difficulty:
                    # In a real system, you might reduce target HP or eliminate them
                    return {
                        "success": True, 
                        "result": f"{e_name} defeated {t_name} in combat.",
                        "metadata": {"roll": total, "difficulty": difficulty, "target": t_name}
                    }
                else:
                    return {
                        "success": False, 
                        "result": f"{e_name} was repelled by {t_name}.",
                        "metadata": {"roll": total, "difficulty": difficulty, "target": t_name}
                    }
                    
            return {"success": False, "result": f"Unknown intent '{intent}'.", "metadata": {}}
