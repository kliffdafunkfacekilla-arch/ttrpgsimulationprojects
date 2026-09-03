import sqlite3
import os

class WorldDB:
    def __init__(self, local_db_path: str = "world_state.db"):
        self.local_db_path = local_db_path
        self.omnis_db_path = r"C:\Users\krazy\Desktop\ttrpgsimulationprojects\worldsim\omnis-generator\ttrpg_world.db"
        self._initialize_local_tables()

    def _get_local_connection(self):
        return sqlite3.connect(self.local_db_path)
        
    def _get_omnis_connection(self):
        if not os.path.exists(self.omnis_db_path):
            print(f"WARNING: Omnis DB not found at {self.omnis_db_path}")
        return sqlite3.connect(self.omnis_db_path)

    def _initialize_local_tables(self):
        conn = self._get_local_connection()
        try:
            cursor = conn.cursor()
            
            # Reactive Seeds
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reactive_seeds (
                    seed_id TEXT PRIMARY KEY,
                    location_id TEXT,
                    origin_action TEXT,
                    subtle_description TEXT,
                    target_entity TEXT,
                    urgency_ticks INTEGER,
                    status TEXT
                )
            ''')
            
            # Campaign State
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS campaign_state (
                    id INTEGER PRIMARY KEY,
                    current_act INTEGER DEFAULT 1
                )
            ''')
            
            # Initialize Act 1 if not exists
            cursor.execute('INSERT OR IGNORE INTO campaign_state (id, current_act) VALUES (1, 1)')
            
            # Resolved Seeds History
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS resolved_seeds_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_title TEXT,
                    action_taken TEXT,
                    impact_vector TEXT
                )
            ''')
            
            # Escalated Threads (Unresolved Threats)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS escalated_threads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    threat_description TEXT
                )
            ''')
            
            conn.commit()
        finally:
            conn.close()

    def _get_connection(self):
        # Fallback for old code expecting _get_connection
        return self._get_local_connection()
        
    def reset_db(self):
        """Helper to clear local DB for testing."""
        if os.path.exists(self.local_db_path):
            os.remove(self.local_db_path)
            self._initialize_local_tables()

    def get_random_cell(self):
        """Fetches a random cell and its macro group from the Omnis DB."""
        conn = self._get_omnis_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, biome, food_supply, chaos_saturation FROM cells ORDER BY RANDOM() LIMIT 1")
            row = cursor.fetchone()
            if row:
                return self.get_cell_data(row[0])
            return None
        finally:
            conn.close()

    def get_cell_data(self, cell_id: int):
        """Gets full data for a given cell ID including faction control."""
        conn = self._get_omnis_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, biome, food_supply, chaos_saturation, weather FROM cells WHERE id = ?", (cell_id,))
            cell_row = cursor.fetchone()
            
            if not cell_row:
                return None
                
            cell_data = {
                "id": cell_row[0],
                "name": f"Sector {cell_row[0]}",
                "biome": cell_row[1],
                "food_supply": cell_row[2],
                "chaos": cell_row[3],
                "weather": cell_row[4],
                "faction": "Wilderness",
                "population": 0,
                "discontent": 0.0
            }
            
            # Check macro_groups to see who controls it
            cursor.execute("SELECT faction_name, population, discontent, is_capital FROM macro_groups WHERE cell_id = ? ORDER BY population DESC LIMIT 1", (cell_id,))
            mg_row = cursor.fetchone()
            if mg_row:
                cell_data["faction"] = mg_row[0]
                cell_data["population"] = mg_row[1]
                cell_data["discontent"] = mg_row[2]
                if mg_row[3]:
                    cell_data["name"] = f"{mg_row[0]} Capital"
                else:
                    cell_data["name"] = f"{mg_row[0]} Territory"
                    
            return cell_data
        finally:
            conn.close()
