import sqlite3
import json

class WorldRenderer:
    def __init__(self, db_path):
        self.db_path = db_path
        
    def render_tactical_dashboard(self, cell_id):
        """Displays Tactical Dashboard for a region (Chaos, Wealth, Proximity)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, chaos_level, wealth, friction, prey_density FROM regional_cells WHERE id = ?", (cell_id,))
            cell = cursor.fetchone()
            
            if not cell:
                return "Region not found."
                
            name, chaos, wealth, friction, prey = cell
            
            cursor.execute("SELECT name, type FROM entities WHERE location_id = ?", (cell_id,))
            entities = cursor.fetchall()
            
            dashboard = f"=== TACTICAL DASHBOARD: {name} ===\n"
            dashboard += f"Chaos: {chaos:.2f} | Wealth: {wealth:.2f} | Friction: {friction:.2f} | Prey: {prey:.2f}\n"
            dashboard += "Entities in Proximity:\n"
            for e_name, e_type in entities:
                dashboard += f" - {e_name} ({e_type})\n"
            
            return dashboard

class InputParser:
    def __init__(self):
        pass
        
    def parse_input(self, user_text):
        """
        Uses LLM (simulated here) to extract Intent and Target.
        In a real scenario, we would pass user_text to an LLM like Gemini.
        """
        # Simulated LLM NLP extraction
        user_text = user_text.lower()
        if "travel to" in user_text:
            target_name = user_text.replace("travel to", "").strip().title()
            return {"intent": "Travel", "target_name": target_name}
        elif "attack" in user_text:
            target_name = user_text.replace("attack", "").strip().title()
            return {"intent": "Attack", "target_name": target_name}
            
        return {"intent": "Wait", "target_name": None}

class Narrator:
    def __init__(self):
        pass
        
    def narrate_resolution(self, resolution_dict, lore_context=""):
        """
        Takes the output from ResolutionReferee and passes it to an LLM.
        """
        success = resolution_dict.get("success", False)
        result_text = resolution_dict.get("result", "")
        
        # Simulated LLM Generation
        narration = f"[NARRATOR (Simulated)] The engine resolved the action: {result_text}\n"
        if lore_context:
            narration += f"Drawing upon the ancient lore: '{lore_context[:50]}...', the world reacts.\n"
            
        if success:
            narration += "The endeavor was a resounding success, shifting the tides of fate."
        else:
            narration += "Failure leaves a bitter taste as the entity struggles against insurmountable odds."
            
        return narration
