import sqlite3

def ensure_table(cursor, table_name, create_sql):
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    if not cursor.fetchone():
        cursor.execute(create_sql)

def ensure_columns(cursor, table_name, columns_info):
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = {row[1] for row in cursor.fetchall()}
    for col_name, col_def in columns_info.items():
        if col_name not in existing_columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}")

def apply_migrations(conn):
    cursor = conn.cursor()

    # global_hexes
    ensure_table(cursor, "global_hexes", """
        CREATE TABLE IF NOT EXISTS global_hexes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            q INTEGER, r INTEGER, d20_triangle_id INTEGER,
            pack_geo INTEGER DEFAULT 0, pack_meso INTEGER DEFAULT 0, pack_ecology INTEGER DEFAULT 0,
            micro_data_json TEXT, regional_data_json TEXT, flow_target_id INTEGER, wind_direction TEXT,
            chaos_domain TEXT
        )
    """)
    ensure_columns(cursor, "global_hexes", {
        "d20_triangle_id": "INTEGER",
        "pack_geo": "INTEGER DEFAULT 0",
        "pack_meso": "INTEGER DEFAULT 0",
        "pack_ecology": "INTEGER DEFAULT 0",
        "micro_data_json": "TEXT",
        "regional_data_json": "TEXT",
        "flow_target_id": "INTEGER",
        "wind_direction": "TEXT",
        "chaos_domain": "TEXT",
        "biome_name": "TEXT",
        "temperature": "REAL",
        "elevation": "INTEGER",
        "culture_id": "INTEGER",
        "religion_id": "INTEGER"
    })

    # weather_systems
    ensure_table(cursor, "weather_systems", """
        CREATE TABLE IF NOT EXISTS weather_systems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT, global_q INTEGER, global_r INTEGER,
            energy REAL, moisture REAL, vorticity REAL, global_hex_id INTEGER,
            is_chaos INTEGER DEFAULT 0, chaos_domain TEXT
        )
    """)
    ensure_columns(cursor, "weather_systems", {
        "global_q": "INTEGER",
        "global_r": "INTEGER",
        "global_hex_id": "INTEGER",
        "is_chaos": "INTEGER DEFAULT 0",
        "chaos_domain": "TEXT"
    })

    # world_entities
    ensure_table(cursor, "world_entities", """
        CREATE TABLE IF NOT EXISTS world_entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT, global_hex_id INTEGER, radius INTEGER, duration INTEGER,
            alignment TEXT, micro_q INTEGER DEFAULT 0, micro_r INTEGER DEFAULT 0,
            strength INTEGER DEFAULT 10
        )
    """)
    ensure_columns(cursor, "world_entities", {
        "alignment": "TEXT",
        "micro_q": "INTEGER DEFAULT 0",
        "micro_r": "INTEGER DEFAULT 0",
        "strength": "INTEGER DEFAULT 10"
    })
    cursor.execute("UPDATE world_entities SET micro_q = 0 WHERE micro_q IS NULL")
    cursor.execute("UPDATE world_entities SET micro_r = 0 WHERE micro_r IS NULL")

    # settlements (Simplified for Abstract Tracking)
    ensure_table(cursor, "settlements", """
        CREATE TABLE IF NOT EXISTS settlements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, global_hex_id INTEGER, faction_id INTEGER,
            capital_id INTEGER, settlement_level INTEGER DEFAULT 1,
            prosperity_level TEXT DEFAULT 'Medium', military_strength TEXT DEFAULT 'Moderate',
            status_tags TEXT DEFAULT '[]', expansion_ring INTEGER DEFAULT 0,
            micro_q INTEGER DEFAULT 0, micro_r INTEGER DEFAULT 0
        )
    """)
    ensure_columns(cursor, "settlements", {
        "prosperity_level": "TEXT DEFAULT 'Medium'",
        "military_strength": "TEXT DEFAULT 'Moderate'",
        "status_tags": "TEXT DEFAULT '[]'",
        "settlement_level": "INTEGER DEFAULT 1",
        "capital_id": "INTEGER",
        "expansion_ring": "INTEGER DEFAULT 0",
        "micro_q": "INTEGER DEFAULT 0",
        "micro_r": "INTEGER DEFAULT 0",
        "culture_id": "INTEGER",
        "treasury": "REAL DEFAULT 0.0"
    })

    # active_stages
    ensure_table(cursor, "active_stages", """
        CREATE TABLE IF NOT EXISTS active_stages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            settlement_id INTEGER NOT NULL, global_hex_id INTEGER NOT NULL,
            npcs_json TEXT NOT NULL, conflict_signal TEXT, last_updated_tick INTEGER NOT NULL
        )
    """)

    # story_events
    ensure_table(cursor, "global_events", """
        CREATE TABLE IF NOT EXISTS global_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tick INTEGER,
            region TEXT,
            event_type TEXT,
            description TEXT
        )
    """)

    # --- NEW RPG APP TABLES ---
    cursor.execute("DROP TABLE IF EXISTS characters")
    cursor.execute('''
        CREATE TABLE characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            kingdom TEXT,
            species TEXT,
            passive_trait TEXT,
            power_track TEXT,
            survival_track TEXT,
            crew_talent TEXT,
            background TEXT,
            might INTEGER DEFAULT 0,
            fortitude INTEGER DEFAULT 0,
            finesse INTEGER DEFAULT 0,
            vitality INTEGER DEFAULT 0,
            reflex INTEGER DEFAULT 0,
            endurance INTEGER DEFAULT 0,
            willpower INTEGER DEFAULT 0,
            intuition INTEGER DEFAULT 0,
            logic INTEGER DEFAULT 0,
            knowledge INTEGER DEFAULT 0,
            awareness INTEGER DEFAULT 0,
            charm INTEGER DEFAULT 0,
            current_hp INTEGER DEFAULT 20,
            max_hp INTEGER DEFAULT 20
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS npcs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            location_id INTEGER,
            personality TEXT,
            memory TEXT,
            FOREIGN KEY(location_id) REFERENCES settlements(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaign_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_framework TEXT,
            current_quest TEXT,
            current_location_id INTEGER,
            FOREIGN KEY(current_location_id) REFERENCES settlements(id)
        )
    ''')

    # Seed the campaign state if it's empty
    cursor.execute("SELECT COUNT(*) FROM campaign_state")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO campaign_state (story_framework, current_quest, current_location_id) VALUES ('', '', 1)")

    # metadata
    ensure_table(cursor, "metadata", """
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY, value TEXT
        )
    """)

    # event_log
    ensure_table(cursor, "event_log", """
        CREATE TABLE IF NOT EXISTS event_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tick INTEGER, category TEXT, message TEXT,
            global_q INTEGER, global_r INTEGER
        )
    """)
    ensure_columns(cursor, "event_log", {
        "global_q": "INTEGER",
        "global_r": "INTEGER"
    })

    # factions (Simplified)
    ensure_table(cursor, "factions", """
        CREATE TABLE IF NOT EXISTS factions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, special_rule TEXT, wealth_status TEXT DEFAULT 'Adequate',
            technology_level INTEGER DEFAULT 1
        )
    """)
    ensure_columns(cursor, "factions", {
        "special_rule": "TEXT",
        "wealth_status": "TEXT DEFAULT 'Adequate'",
        "technology_level": "INTEGER DEFAULT 1"
    })

    # faction_relations (Abstracted)
    ensure_table(cursor, "faction_relations", """
        CREATE TABLE IF NOT EXISTS faction_relations (
            faction_a_id INTEGER, faction_b_id INTEGER,
            status TEXT DEFAULT 'Neutral', tension_level INTEGER DEFAULT 5,
            PRIMARY KEY (faction_a_id, faction_b_id)
        )
    """)
    ensure_columns(cursor, "faction_relations", {
        "status": "TEXT DEFAULT 'Neutral'",
        "tension_level": "INTEGER DEFAULT 5"
    })

    # diplomacy_relations
    ensure_table(cursor, "diplomacy_relations", """
        CREATE TABLE IF NOT EXISTS diplomacy_relations (
            settlement_a_id INTEGER, settlement_b_id INTEGER,
            score INTEGER DEFAULT 0,
            PRIMARY KEY (settlement_a_id, settlement_b_id)
        )
    """)

    # trade_routes (Abstracted)
    ensure_table(cursor, "trade_routes", """
        CREATE TABLE IF NOT EXISTS trade_routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            faction_id INTEGER, settlement_a_id INTEGER, settlement_b_id INTEGER,
            route_type TEXT, status TEXT DEFAULT 'Active', tension_level INTEGER DEFAULT 1
        )
    """)
    ensure_columns(cursor, "trade_routes", {
        "status": "TEXT DEFAULT 'Active'",
        "tension_level": "INTEGER DEFAULT 1"
    })

    # cultures
    ensure_table(cursor, "cultures", """
        CREATE TABLE IF NOT EXISTS cultures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, type TEXT, expansionism REAL
        )
    """)

    # military_regiments
    ensure_table(cursor, "military_regiments", """
        CREATE TABLE IF NOT EXISTS military_regiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            faction_id INTEGER,
            name TEXT, icon TEXT,
            stationed_cell_id INTEGER,
            units_json TEXT
        )
    """)

    # religions
    ensure_table(cursor, "religions", """
        CREATE TABLE IF NOT EXISTS religions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, type TEXT, form TEXT, deity TEXT
        )
    """)

    # rivers
    ensure_table(cursor, "rivers", """
        CREATE TABLE IF NOT EXISTS rivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, type TEXT, source_hex_id INTEGER, mouth_hex_id INTEGER
        )
    """)

    # markers
    ensure_table(cursor, "markers", """
        CREATE TABLE IF NOT EXISTS markers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            icon TEXT, type TEXT, global_hex_id INTEGER
        )
    """)

    # zones
    ensure_table(cursor, "zones", """
        CREATE TABLE IF NOT EXISTS zones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, type TEXT
        )
    """)

    # zone_hexes
    ensure_table(cursor, "zone_hexes", """
        CREATE TABLE IF NOT EXISTS zone_hexes (
            zone_id INTEGER, global_hex_id INTEGER
        )
    """)

    # goods
    ensure_table(cursor, "goods", """
        CREATE TABLE IF NOT EXISTS goods (
            id INTEGER PRIMARY KEY,
            name TEXT, type TEXT, base_value REAL, unit TEXT
        )
    """)

    # markets
    ensure_table(cursor, "markets", """
        CREATE TABLE IF NOT EXISTS markets (
            id INTEGER PRIMARY KEY,
            settlement_id INTEGER
        )
    """)

    # market_goods
    ensure_table(cursor, "market_goods", """
        CREATE TABLE IF NOT EXISTS market_goods (
            market_id INTEGER, good_id INTEGER,
            stock REAL, price REAL
        )
    """)

    # deals
    ensure_table(cursor, "deals", """
        CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY,
            seller_id INTEGER, seller_type TEXT,
            buyer_id INTEGER, buyer_type TEXT,
            good_id INTEGER, units REAL, price REAL
        )
    """)

    # settlement_production
    ensure_table(cursor, "settlement_production", """
        CREATE TABLE IF NOT EXISTS settlement_production (
            settlement_id INTEGER, good_id INTEGER, units REAL
        )
    """)

    conn.commit()

if __name__ == "__main__":
    conn = sqlite3.connect("world_state.db")
    apply_migrations(conn)
    conn.close()
    print("Database schema updated for abstract tracking.")
