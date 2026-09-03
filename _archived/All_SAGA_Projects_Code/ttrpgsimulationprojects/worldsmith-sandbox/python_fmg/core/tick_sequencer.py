import sqlite3
import json

class WorldKernel:
    def __init__(self, db_path):
        self.db_path = db_path
        self.current_tick = 0
        self._load_current_tick()

    def _load_current_tick(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(tick) FROM world_history")
            res = cursor.fetchone()
            if res and res[0] is not None:
                self.current_tick = res[0]

    def process_tick(self):
        """Execute the dependency chain for a single systemic tick."""
        self.current_tick += 1
        print(f"--- Processing Tick {self.current_tick} ---")
        
        with sqlite3.connect(self.db_path) as conn:
            self._system_1_spatial(conn)
            self._system_2_ecological_economic(conn)
            self._system_3_political_military(conn)
            
            # Log tick end
            cursor = conn.cursor()
            cursor.execute("INSERT INTO world_history (tick, category, event_summary) VALUES (?, ?, ?)",
                           (self.current_tick, "System", f"Tick {self.current_tick} processed successfully."))
            conn.commit()

    def _system_1_spatial(self, conn):
        """
        System 1 (Spatial): Calculates environment (Weather, Chaos-bleed).
        Updates friction for all cells based on chaos_level.
        Dependency: Must run first to set difficulty for other systems.
        """
        cursor = conn.cursor()
        cursor.execute("SELECT id, chaos_level, friction FROM regional_cells")
        cells = cursor.fetchall()
        
        for cell_id, chaos_level, friction in cells:
            # Example logic: Chaos increases friction. Weather randomizes slightly.
            # Here we just apply a basic rule: Friction = base(1.0) + chaos_level
            new_friction = 1.0 + (chaos_level * 2.0)
            cursor.execute("UPDATE regional_cells SET friction = ? WHERE id = ?", (new_friction, cell_id))
            
            # Log significant chaos events
            if chaos_level > 0.8:
                cursor.execute("INSERT INTO world_history (tick, category, event_summary) VALUES (?, ?, ?)",
                               (self.current_tick, "Spatial", f"High chaos bleeding in region {cell_id}."))

    def _system_2_ecological_economic(self, conn):
        """
        System 2 (Ecological/Economic): Calculates resource growth and trade decay based on friction.
        """
        cursor = conn.cursor()
        cursor.execute("SELECT id, friction, prey_density, wealth FROM regional_cells")
        cells = cursor.fetchall()
        
        for cell_id, friction, prey, wealth in cells:
            # High friction reduces wealth (trade decay) and stunts prey growth
            wealth_change = -0.1 if friction > 2.0 else 0.1
            prey_change = -0.05 if friction > 2.5 else 0.05
            
            new_wealth = max(0.0, wealth + wealth_change)
            new_prey = max(0.0, min(1.0, prey + prey_change)) # Prey capped at 1.0
            
            cursor.execute("UPDATE regional_cells SET wealth = ?, prey_density = ? WHERE id = ?", 
                           (new_wealth, new_prey, cell_id))

    def _system_3_political_military(self, conn):
        """
        System 3 (Political/Military): Executes autonomous movement of Army entities based on intent and friction.
        """
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, location_id, intent_data FROM entities WHERE type = 'Army'")
        armies = cursor.fetchall()
        
        for army_id, name, loc_id, intent_data in armies:
            if not intent_data:
                continue
                
            try:
                intent = json.loads(intent_data)
                target_loc = intent.get("target_location_id")
                action = intent.get("action")
                
                if action == "Travel" and target_loc:
                    # Connectivity check
                    cursor.execute("SELECT neighbors FROM regional_cells WHERE id = ?", (loc_id,))
                    current_cell_res = cursor.fetchone()
                    
                    can_reach = False
                    if current_cell_res and current_cell_res[0]:
                        try:
                            neighbors = json.loads(current_cell_res[0])
                            if target_loc in neighbors:
                                can_reach = True
                        except json.JSONDecodeError:
                            pass
                            
                    if not can_reach:
                        cursor.execute("INSERT INTO world_history (tick, category, event_summary) VALUES (?, ?, ?)",
                                       (self.current_tick, "Military", f"Army '{name}' failed to travel to {target_loc} due to lack of connectivity."))
                        continue

                    # Check friction of target
                    cursor.execute("SELECT friction FROM regional_cells WHERE id = ?", (target_loc,))
                    res = cursor.fetchone()
                    if res:
                        friction = res[0]
                        if friction < 2.5: # Can travel
                            cursor.execute("UPDATE entities SET location_id = ? WHERE id = ?", (target_loc, army_id))
                            # Log movement
                            cursor.execute("INSERT INTO world_history (tick, category, event_summary) VALUES (?, ?, ?)",
                                           (self.current_tick, "Military", f"Army '{name}' traveled to region {target_loc}."))
                        else:
                            # Log failure due to friction
                            cursor.execute("INSERT INTO world_history (tick, category, event_summary) VALUES (?, ?, ?)",
                                           (self.current_tick, "Military", f"Army '{name}' failed to travel to {target_loc} due to high friction."))
            except json.JSONDecodeError:
                pass
