import sqlite3

def setup_master_knowledge_db(db_path):
    try:
        conn = sqlite3.connect(db_path, timeout=15.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        cursor.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT UNIQUE NOT NULL, content TEXT NOT NULL, category TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        cursor.execute("CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(title, content, category, content=notes, content_rowid=id)")
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS notes_ai AFTER INSERT ON notes BEGIN
          INSERT INTO notes_fts(rowid, title, content, category) VALUES (new.id, new.title, new.content, new.category);
        END;
        """)
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS notes_ad AFTER DELETE ON notes BEGIN
          INSERT INTO notes_fts(notes_fts, rowid, title, content, category) VALUES('delete', old.id, old.title, old.content, old.category);
        END;
        """)
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS notes_au AFTER UPDATE ON notes BEGIN
          INSERT INTO notes_fts(notes_fts, rowid, title, content, category) VALUES('delete', old.id, old.title, old.content, old.category);
          INSERT INTO notes_fts(rowid, title, content, category) VALUES (new.id, new.title, new.content, new.category);
        END;
        """)
        cursor.execute("CREATE TABLE IF NOT EXISTS factions (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, color TEXT NOT NULL, gov_type TEXT DEFAULT 'Feudal Monarchy', dominant_cultures TEXT, dominant_religions TEXT, aggression_scale INTEGER DEFAULT 5, trade_scale INTEGER DEFAULT 5, explore_scale INTEGER DEFAULT 5, espionage_scale INTEGER DEFAULT 5, morale INTEGER DEFAULT 5, crime INTEGER DEFAULT 5, poverty INTEGER DEFAULT 5, freedom INTEGER DEFAULT 5, magic_stance TEXT DEFAULT 'Regulated', domain_type TEXT DEFAULT 'Both', treasury REAL DEFAULT 1000.0, capital_cell INTEGER, associated_note_id INTEGER, FOREIGN KEY(associated_note_id) REFERENCES notes(id) ON DELETE SET NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS provinces (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, color TEXT NOT NULL, state_id INTEGER NOT NULL, governor_name TEXT, tax_rate REAL DEFAULT 10.0, local_morale INTEGER DEFAULT 5, local_crime INTEGER DEFAULT 5, local_poverty INTEGER DEFAULT 5, local_freedom INTEGER DEFAULT 5, local_magic_handling TEXT DEFAULT 'Lax Enforcement', associated_note_id INTEGER, FOREIGN KEY(state_id) REFERENCES factions(id) ON DELETE CASCADE, FOREIGN KEY(associated_note_id) REFERENCES notes(id) ON DELETE SET NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS cultures (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, code TEXT NOT NULL, language_base TEXT DEFAULT 'Imperial', trait_type TEXT DEFAULT 'None', trait_modifier REAL DEFAULT 1.0, domain_type TEXT DEFAULT 'Both', associated_note_id INTEGER, FOREIGN KEY(associated_note_id) REFERENCES notes(id) ON DELETE SET NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS cell_cultures_overlap (cell_id INTEGER NOT NULL, culture_id INTEGER NOT NULL, density REAL DEFAULT 1.0, PRIMARY KEY (cell_id, culture_id), FOREIGN KEY(culture_id) REFERENCES cultures(id) ON DELETE CASCADE)")
        cursor.execute("CREATE TABLE IF NOT EXISTS religions (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, color TEXT NOT NULL, religion_type TEXT DEFAULT 'Deity-Centric', is_official INTEGER DEFAULT 0, devotion INTEGER DEFAULT 5, recruit_rate INTEGER DEFAULT 5, rival_religion_ids TEXT, leaders TEXT, supreme_deity TEXT DEFAULT 'Solis', domain_type TEXT DEFAULT 'Both', holy_site_cell INTEGER, associated_note_id INTEGER, FOREIGN KEY(associated_note_id) REFERENCES notes(id) ON DELETE SET NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS military (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, faction_id INTEGER, cell_idx INTEGER, troops_count INTEGER DEFAULT 1000, unit_type TEXT DEFAULT 'Infantry', tech_dependency_id INTEGER, associated_note_id INTEGER, FOREIGN KEY(faction_id) REFERENCES factions(id) ON DELETE SET NULL, FOREIGN KEY(associated_note_id) REFERENCES notes(id) ON DELETE SET NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS defensive_structures (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, structure_type TEXT DEFAULT 'Watchtower', cell_idx INTEGER NOT NULL, defense_value INTEGER DEFAULT 5, garrison_capacity INTEGER DEFAULT 500, associated_note_id INTEGER, FOREIGN KEY(associated_note_id) REFERENCES notes(id) ON DELETE SET NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS production_goods (cell_id INTEGER PRIMARY KEY, good TEXT NOT NULL, valuation REAL DEFAULT 1.0, is_finite INTEGER DEFAULT 0, max_capacity REAL DEFAULT 1000.0, current_capacity REAL DEFAULT 1000.0, is_market_center INTEGER DEFAULT 0, associated_note_id INTEGER, FOREIGN KEY(associated_note_id) REFERENCES notes(id) ON DELETE SET NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS trade_routes (id INTEGER PRIMARY KEY AUTOINCREMENT, origin_cell INTEGER NOT NULL, destination_cell INTEGER NOT NULL, route_type TEXT DEFAULT 'Cobbled Road', safety_index REAL DEFAULT 1.0)")
        cursor.execute("CREATE TABLE IF NOT EXISTS cells (id INTEGER PRIMARY KEY, centroid_x REAL NOT NULL, centroid_y REAL NOT NULL, elevation INTEGER DEFAULT 20, moisture INTEGER DEFAULT 10, temperature INTEGER DEFAULT 15, biome TEXT DEFAULT 'Marine', plant_value INTEGER DEFAULT 5, prey_value INTEGER DEFAULT 5, predator_value INTEGER DEFAULT 5, state_id INTEGER, province_id INTEGER, culture_id INTEGER, religion_id INTEGER, FOREIGN KEY(state_id) REFERENCES factions(id) ON DELETE SET NULL, FOREIGN KEY(province_id) REFERENCES provinces(id) ON DELETE SET NULL, FOREIGN KEY(culture_id) REFERENCES cultures(id) ON DELETE SET NULL, FOREIGN KEY(religion_id) REFERENCES religions(id) ON DELETE SET NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS settlements (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, population REAL DEFAULT 10.0, cell_idx INTEGER, faction_id INTEGER, culture_id INTEGER, has_port INTEGER DEFAULT 0, has_university INTEGER DEFAULT 0, notable_locations TEXT, leaders_links TEXT, associated_note_id INTEGER, FOREIGN KEY(faction_id) REFERENCES factions(id) ON DELETE SET NULL, FOREIGN KEY(culture_id) REFERENCES cultures(id) ON DELETE SET NULL, FOREIGN KEY(associated_note_id) REFERENCES notes(id) ON DELETE SET NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS geography_plates (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, movement_vector TEXT NOT NULL, volcanic_index REAL DEFAULT 1.0, associated_note_id INTEGER, FOREIGN KEY(associated_note_id) REFERENCES notes(id) ON DELETE SET NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS magic_layers (id INTEGER PRIMARY KEY AUTOINCREMENT, label TEXT NOT NULL, mode_type TEXT DEFAULT 'Point', origin_cell_idx INTEGER NOT NULL, termination_cell_idx INTEGER, radius_of_effect INTEGER DEFAULT 10, intensity REAL DEFAULT 1.0, effect_field_description TEXT, associated_note_id INTEGER, FOREIGN KEY(associated_note_id) REFERENCES notes(id) ON DELETE SET NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS tech_eras (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, description TEXT, year_range TEXT NOT NULL, buff_type TEXT DEFAULT 'Extraction Speed', buff_modifier REAL DEFAULT 1.0, associated_note_id INTEGER, FOREIGN KEY(associated_note_id) REFERENCES notes(id) ON DELETE SET NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS influence_factions (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, category TEXT DEFAULT 'Secret Society', leaders TEXT, headquarters_cell INTEGER, influence_effect_type TEXT DEFAULT 'Crime Catalyst', influence_intensity REAL DEFAULT 1.0, associated_note_id INTEGER, FOREIGN KEY(associated_note_id) REFERENCES notes(id) ON DELETE SET NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS cell_shadow_influence (cell_id INTEGER NOT NULL, influence_faction_id INTEGER NOT NULL, grip_strength REAL DEFAULT 0.5, PRIMARY KEY (cell_id, influence_faction_id), FOREIGN KEY(influence_faction_id) REFERENCES influence_factions(id) ON DELETE CASCADE)")
        
        cursor.execute("CREATE TABLE IF NOT EXISTS calendar_config (id INTEGER PRIMARY KEY AUTOINCREMENT, year_length INTEGER DEFAULT 360, months_json TEXT, seasons_json TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS moons (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, period INTEGER DEFAULT 30, size_multiplier REAL DEFAULT 1.0, gravitational_tide_mod REAL DEFAULT 1.0, arcane_flux_modifier REAL DEFAULT 1.0)")
        cursor.execute("CREATE TABLE IF NOT EXISTS timeline_events (id INTEGER PRIMARY KEY AUTOINCREMENT, year INTEGER NOT NULL, day INTEGER DEFAULT 1, title TEXT NOT NULL, description TEXT, faction_id INTEGER, cell_idx INTEGER, associated_note_id INTEGER, FOREIGN KEY(faction_id) REFERENCES factions(id) ON DELETE SET NULL, FOREIGN KEY(associated_note_id) REFERENCES notes(id) ON DELETE SET NULL)")
        
        cursor.execute("CREATE TABLE IF NOT EXISTS note_map_bindings (note_id INTEGER, cell_idx INTEGER, PRIMARY KEY (note_id, cell_idx))")
        cursor.execute("CREATE TABLE IF NOT EXISTS markdown_map_bindings (title TEXT PRIMARY KEY, bind_type TEXT, bind_target TEXT, cell_idx INTEGER)")
        cursor.execute("CREATE TABLE IF NOT EXISTS actors (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, faction_id INTEGER, current_cell_idx INTEGER, is_alive INTEGER DEFAULT 1, role TEXT, FOREIGN KEY(faction_id) REFERENCES factions(id))")
        cursor.execute("CREATE TABLE IF NOT EXISTS faction_relations (faction_a_id INTEGER, faction_b_id INTEGER, diplomacy_score INTEGER, treaty_status TEXT, UNIQUE(faction_a_id, faction_b_id), FOREIGN KEY(faction_a_id) REFERENCES factions(id), FOREIGN KEY(faction_b_id) REFERENCES factions(id))")
        cursor.execute("CREATE TABLE IF NOT EXISTS faction_economics (id INTEGER PRIMARY KEY AUTOINCREMENT, faction_id INTEGER, good_name TEXT, status TEXT, urgency_multiplier REAL, FOREIGN KEY(faction_id) REFERENCES factions(id))")
        cursor.execute("CREATE TABLE IF NOT EXISTS atomic_facts (id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT NOT NULL, relationship TEXT NOT NULL, target TEXT NOT NULL, context TEXT, associated_note_id INTEGER, FOREIGN KEY(associated_note_id) REFERENCES notes(id) ON DELETE SET NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS inconsistencies (id INTEGER PRIMARY KEY AUTOINCREMENT, subject_type TEXT, subject_id INTEGER, description TEXT, status TEXT DEFAULT 'Active')")
        cursor.execute("CREATE TABLE IF NOT EXISTS map_snapshots (year INTEGER PRIMARY KEY, engine_state_json BLOB)")
        cursor.execute("CREATE TABLE IF NOT EXISTS markers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, type TEXT NOT NULL, cell_idx INTEGER NOT NULL, associated_note_id INTEGER, FOREIGN KEY(associated_note_id) REFERENCES notes(id) ON DELETE SET NULL)")

        cursor.execute("SELECT COUNT(*) FROM factions")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT OR IGNORE INTO factions (id, name, color, gov_type, aggression_scale, trade_scale, morale, magic_stance, domain_type, treasury) VALUES (1, 'Vulfurn Magocracy', '#ef4444', 'Magocracy', 8, 4, 7, 'Ruling Class', 'Both', 5000.0)")
            cursor.execute("INSERT OR IGNORE INTO factions (id, name, color, gov_type, aggression_scale, trade_scale, morale, magic_stance, domain_type, treasury) VALUES (2, 'Chipis Union', '#3b82f6', 'Merchant Oligarchy', 3, 9, 6, 'Repressed', 'Land', 8500.0)")
            cursor.execute("INSERT OR IGNORE INTO provinces (id, name, color, state_id, governor_name, local_morale, local_crime, local_magic_handling) VALUES (10, 'Shattered Marches', '#fca5a5', 1, 'Inquisitor Vael', 4, 8, 'Strict Inquisition')")
            cursor.execute("INSERT OR IGNORE INTO provinces (id, name, color, state_id, governor_name, local_morale, local_crime, local_magic_handling) VALUES (20, 'Ostraka Coastline', '#93c5fd', 2, 'Prefect Vance', 8, 2, 'Sanctuary')")
            cursor.execute("INSERT OR IGNORE INTO cultures (id, name, code, language_base, trait_type, trait_modifier) VALUES (50, 'Boreal Elves', 'BE', 'Elven', 'Arcane Catalyst', 1.25)")
            cursor.execute("INSERT OR IGNORE INTO cultures (id, name, code, language_base, trait_type, trait_modifier) VALUES (51, 'Abyssal Gill-kin', 'AG', 'DeepSpeech', 'Resource Drain', 0.85)")
            cursor.execute("INSERT OR IGNORE INTO religions (id, name, color, religion_type, devotion, recruit_rate, supreme_deity, domain_type) VALUES (201, 'Eternal Sun Creed', '#eab308', 'Deity-Centric', 9, 7, 'Solis the Unconquered', 'Both')")
            cursor.execute("INSERT OR IGNORE INTO influence_factions (id, name, category, leaders, influence_effect_type, influence_intensity) VALUES (301, 'The Obsidian Cartel', 'Criminal Cartel', 'Enzo the Silk Finger', 'Crime Catalyst', 1.50)")
            cursor.execute("INSERT OR IGNORE INTO calendar_config (id, year_length, months_json, seasons_json) VALUES (1, 420, '[]', '[]')")
            cursor.execute("INSERT OR IGNORE INTO moons (id, name, period, size_multiplier, gravitational_tide_mod, arcane_flux_modifier) VALUES (1, 'Vespera', 30, 1.2, 1.3, 1.5)")
            cursor.execute("INSERT OR IGNORE INTO moons (id, name, period, size_multiplier, gravitational_tide_mod, arcane_flux_modifier) VALUES (2, 'Aetheris', 45, 0.8, 0.7, 2.0)")
            cursor.execute("INSERT OR IGNORE INTO timeline_events (year, day, title, description, faction_id) VALUES (100, 50, 'The Foundation Stone', 'Sovereigns lay down the boundaries of the capitol.', 1)")
            cursor.execute("INSERT OR IGNORE INTO timeline_events (year, day, title, description, faction_id) VALUES (200, 150, 'The Sunder War', 'Border margins shatter during the iron ore skirmish.', 2)")

        
        # Ostraka Systemic Engine Tables
        cursor.execute("CREATE TABLE IF NOT EXISTS regional_cells (id INTEGER PRIMARY KEY, name TEXT, biome TEXT, chaos_level REAL DEFAULT 0.0, friction REAL DEFAULT 1.0, prey_density REAL DEFAULT 1.0, wealth REAL DEFAULT 0.0, neighbors TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS entities (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, type TEXT NOT NULL, stat_json TEXT, location_id INTEGER, intent_data TEXT, FOREIGN KEY(location_id) REFERENCES regional_cells(id))")
        cursor.execute("CREATE TABLE IF NOT EXISTS world_history (tick INTEGER, category TEXT, event_summary TEXT)")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error establishing master knowledge database schema: {e}")

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        
    def init_tables(self):
        setup_master_knowledge_db(self.db_path)


