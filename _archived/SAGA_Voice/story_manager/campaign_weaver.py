from contextlib import closing
from story_manager.world_db import WorldDB

class CampaignWeaver:
    def __init__(self, db: WorldDB):
        self.db = db

    def get_campaign_act(self) -> int:
        with closing(self.db._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT current_act FROM campaign_state WHERE id = 1")
            return cursor.fetchone()[0]

    def set_campaign_act(self, act: int):
        with closing(self.db._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE campaign_state SET current_act = ? WHERE id = 1", (act,))
            conn.commit()

    def get_resolved_history(self, limit: int = 5) -> list[dict]:
        history = []
        with closing(self.db._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT node_title, action_taken, impact_vector FROM resolved_seeds_history ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            for r in rows:
                history.append({
                    "node": r[0],
                    "action_taken": r[1],
                    "impact_vector": r[2]
                })
        return history[::-1] # Return in chronological order

    def get_escalated_threads(self) -> list[str]:
        threads = []
        with closing(self.db._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT threat_description FROM escalated_threads")
            rows = cursor.fetchall()
            for r in rows:
                threads.append(r[0])
        return threads

    def ingest_seed_resolution(self, seed_data: dict, player_choice_outcome: str):
        """Takes a resolved seed and weaves it into the grand framework."""
        with closing(self.db._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO resolved_seeds_history (node_title, action_taken, impact_vector) VALUES (?, ?, ?)",
                (seed_data.get("title", "Unknown Event"), player_choice_outcome, seed_data.get("category", "General"))
            )
            conn.commit()
            
        self._evaluate_campaign_shift()

    def escalate_ignored_seed(self, threat_description: str):
        """Promotes a localized seed that went unaddressed into a macro threat."""
        with closing(self.db._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO escalated_threads (threat_description) VALUES (?)",
                (threat_description,)
            )
            conn.commit()

    def _evaluate_campaign_shift(self):
        """Shifts the logical shape of the campaign based on accumulated choices."""
        with closing(self.db._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM resolved_seeds_history")
            count = cursor.fetchone()[0]
            
        current_act = self.get_campaign_act()
        if count >= 5 and current_act == 1:
            self.set_campaign_act(2)
            # Logically we would trigger an event here, or add a macro threat
            print(">>> CAMPAIGN SHIFT: Act II Begins! <<<")
