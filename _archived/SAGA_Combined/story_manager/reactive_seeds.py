import uuid
from contextlib import closing
from story_manager.world_db import WorldDB

class ReactiveSeed:
    def __init__(self, seed_id: str, location_id: str, origin_action: str, subtle_description: str, target_entity: str, urgency: int, status: str = "Subtle"):
        self.seed_id = seed_id
        self.location_id = location_id
        self.origin_action = origin_action              # What the player did to cause this
        self.subtle_description = subtle_description    # How it appears naturally in the scene
        self.target_entity = target_entity              # The person or object changed by the action
        self.urgency_ticks = urgency                    # Turns before this seed mutates if ignored
        self.status = status                            # Subtle, Escalated, Resolved, Faded

    def mutate(self):
        """Changes the seed if the player leaves or ignores it too long."""
        if self.status == "Subtle":
            self.status = "Escalated"
            self.subtle_description = f"The aftermath of {self.origin_action} has drawn quiet, watchful attention to the area. Things are tense."
        elif self.status == "Escalated":
            self.status = "Resolved" # Could be resolved violently by the world itself
            self.subtle_description = f"The situation involving {self.target_entity} has boiled over and concluded without you. Traces of the conflict remain."

class SeedManager:
    def __init__(self, db: WorldDB):
        self.db = db

    def create_seed(self, location_id: str, origin_action: str, subtle_description: str, target_entity: str, urgency: int = 3) -> str:
        seed_id = str(uuid.uuid4())
        
        with closing(self.db._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO reactive_seeds (seed_id, location_id, origin_action, subtle_description, target_entity, urgency_ticks, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (seed_id, location_id, origin_action, subtle_description, target_entity, urgency, "Subtle")
            )
            conn.commit()
            
        return seed_id
        
    def get_active_seeds(self, location_id: str) -> list[ReactiveSeed]:
        seeds = []
        with closing(self.db._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT seed_id, location_id, origin_action, subtle_description, target_entity, urgency_ticks, status FROM reactive_seeds WHERE location_id = ? AND status IN ('Subtle', 'Escalated')", (location_id,))
            rows = cursor.fetchall()
            for r in rows:
                seeds.append(ReactiveSeed(*r))
        return seeds
        
    def tick_simulation(self):
        """Advances time. Drops urgency. Mutates if urgency hits 0."""
        with closing(self.db._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT seed_id, location_id, origin_action, subtle_description, target_entity, urgency_ticks, status FROM reactive_seeds WHERE status IN ('Subtle', 'Escalated')")
            rows = cursor.fetchall()
            
            for r in rows:
                seed = ReactiveSeed(*r)
                seed.urgency_ticks -= 1
                
                if seed.urgency_ticks <= 0:
                    seed.mutate()
                    if seed.status == "Escalated":
                        seed.urgency_ticks = 3
                        
                cursor.execute(
                    "UPDATE reactive_seeds SET subtle_description = ?, urgency_ticks = ?, status = ? WHERE seed_id = ?",
                    (seed.subtle_description, seed.urgency_ticks, seed.status, seed.seed_id)
                )
            conn.commit()
