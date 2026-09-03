# database.py
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'ttrpg_world.db')

def get_db_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and creates the schema."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 1. Cells table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS cells (
            id INTEGER PRIMARY KEY,
            biome TEXT,
            elevation REAL,
            depth_elevation REAL DEFAULT 0.0,
            geom_wkt TEXT,
            food_supply REAL DEFAULT 0.5,
            chaos_saturation REAL DEFAULT 0.0,
            weather TEXT DEFAULT 'Clear',
            chaos_base_modifier REAL DEFAULT 0.0,
            controlling_burg_id INTEGER,
            cults_json TEXT,
            fringe_json TEXT,
            flora_json TEXT,
            fauna_json TEXT
        );
    ''')
    
    # 2. Cell edges table (for graph connectivity)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS cell_edges (
            cell_a INTEGER,
            cell_b INTEGER,
            PRIMARY KEY (cell_a, cell_b)
        );
    ''')
    
    # 3. Macro groups (factions/settlements) table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS macro_groups (
            id INTEGER PRIMARY KEY,
            cell_id INTEGER REFERENCES cells(id) ON DELETE CASCADE,
            faction_id INTEGER DEFAULT 0,
            faction_name TEXT,
            is_capital INTEGER DEFAULT 0,
            chaos_level REAL DEFAULT 0.0,
            population INTEGER DEFAULT 0,
            discontent REAL DEFAULT 0.0,
            crime_level REAL DEFAULT 0.0,
            food_supply REAL DEFAULT 0.5,
            physical_well_being REAL DEFAULT 1.0,
            mental_well_being REAL DEFAULT 1.0,
            safety_rating REAL DEFAULT 0.5,
            camps_count INTEGER DEFAULT 0,
            mines_count INTEGER DEFAULT 0,
            farms_count INTEGER DEFAULT 0,
            barracks_count INTEGER DEFAULT 0,
            watchtowers_count INTEGER DEFAULT 0,
            pressure REAL DEFAULT 0.0,
            magistar_id TEXT,
            is_active INTEGER DEFAULT 1,
            distance_to_chaos_structure REAL DEFAULT 0.0,
            distance_to_convergence REAL DEFAULT 0.0,
            docks_count INTEGER DEFAULT 0,
            walls_count INTEGER DEFAULT 0,
            kelp_farms_count INTEGER DEFAULT 0,
            underwater_domes_count INTEGER DEFAULT 0,
            coral_mines_count INTEGER DEFAULT 0,
            reef_walls_count INTEGER DEFAULT 0,
            cult_infiltration REAL DEFAULT 0.05,
            cult_population REAL DEFAULT 0.0,
            cult_devoted REAL DEFAULT 0.0,
            flora_ghost_flower REAL DEFAULT 100.0,
            flora_stone_root REAL DEFAULT 100.0,
            fauna_sky_grazer REAL DEFAULT 50.0,
            fauna_timber_wolf REAL DEFAULT 10.0,
            domestic_greenhouses INTEGER DEFAULT 0,
            domestic_orchards INTEGER DEFAULT 0,
            domestic_pens INTEGER DEFAULT 0,
            domestic_kennels INTEGER DEFAULT 0,
            churches_count INTEGER DEFAULT 0,
            theatres_count INTEGER DEFAULT 0,
            arenas_count INTEGER DEFAULT 0,
            gambling_dens_count INTEGER DEFAULT 0,
            black_markets_count INTEGER DEFAULT 0,
            workshops_count INTEGER DEFAULT 0,
            settlements_json TEXT,
            paragon_json TEXT,
            inventory_json TEXT,
            hub_wealth REAL DEFAULT 0.0,
            ruined_hub_penalty REAL DEFAULT 0.0
        );
    ''')
    
    # 4. Simulation logs table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS simulation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tick_number INTEGER,
            event_type TEXT,
            description TEXT,
            severity INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    
    # 5. Paragons table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS paragons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            macro_group_id INTEGER REFERENCES macro_groups(id),
            faction_id INTEGER,
            loyalty REAL DEFAULT 0.5,
            military_trait REAL DEFAULT 0.0,
            economic_trait REAL DEFAULT 0.0,
            chaos_corruption REAL DEFAULT 0.0
        );
    ''')
    
    # 6. Cell resources table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS cell_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cell_id INTEGER REFERENCES cells(id),
            iron REAL DEFAULT 0.0,
            kelp REAL DEFAULT 0.0,
            chaos_resin REAL DEFAULT 0.0
        );
    ''')
    
    # 7. Faction inventories table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS faction_inventories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            faction_id INTEGER,
            refined_metal REAL DEFAULT 0.0,
            advanced_units INTEGER DEFAULT 0
        );
    ''')
    
    # 8. Dragon prisons table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS dragon_prisons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cell_id INTEGER REFERENCES cells(id),
            x REAL,
            y REAL,
            seal_integrity REAL DEFAULT 1.0
        );
    ''')
    
    # 9. Global state table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS global_state (
            id INTEGER PRIMARY KEY,
            current_day INTEGER DEFAULT 150,
            warden_population REAL DEFAULT 1500.0,
            warden_recruits_accumulated REAL DEFAULT 0.0,
            diplomacy_json TEXT,
            fringe_groups_json TEXT,
            trade_routes_json TEXT
        );
    ''')
    
    # 10. Resource nodes table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS resource_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cell_id INTEGER REFERENCES cells(id),
            faction_id INTEGER,
            name TEXT,
            icon TEXT,
            description TEXT,
            yield_remaining REAL,
            is_discovered INTEGER DEFAULT 0
        );
    ''')
    
    conn.commit()
    cur.close()
    conn.close()
    print("Database initialized successfully.")

if __name__ == '__main__':
    init_db()
