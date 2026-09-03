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
            micro_data_json TEXT, flow_target_id INTEGER, wind_direction TEXT,
            chaos_domain TEXT
        )
    """)
    ensure_columns(cursor, "global_hexes", {
        "d20_triangle_id": "INTEGER",
        "pack_geo": "INTEGER DEFAULT 0",
        "pack_meso": "INTEGER DEFAULT 0",
        "pack_ecology": "INTEGER DEFAULT 0",
        "micro_data_json": "TEXT",
        "flow_target_id": "INTEGER",
        "wind_direction": "TEXT",
        "chaos_domain": "TEXT"
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
    # Update null micro_q/r
    cursor.execute("UPDATE world_entities SET micro_q = 0 WHERE micro_q IS NULL")
    cursor.execute("UPDATE world_entities SET micro_r = 0 WHERE micro_r IS NULL")

    # settlements
    ensure_table(cursor, "settlements", """
        CREATE TABLE IF NOT EXISTS settlements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, population INTEGER DEFAULT 100, wealth REAL DEFAULT 0,
            global_hex_id INTEGER, faction_id INTEGER, security_points REAL DEFAULT 0,
            hidden_cultists INTEGER DEFAULT 0, spark_born_population INTEGER DEFAULT 0,
            inventory_json TEXT DEFAULT '{}', settlement_level INTEGER DEFAULT 1,
            capital_id INTEGER, expansion_ring INTEGER DEFAULT 0,
            micro_q INTEGER DEFAULT 0, micro_r INTEGER DEFAULT 0
        )
    """)
    ensure_columns(cursor, "settlements", {
        "security_points": "REAL DEFAULT 0",
        "hidden_cultists": "INTEGER DEFAULT 0",
        "spark_born_population": "INTEGER DEFAULT 0",
        "inventory_json": "TEXT DEFAULT '{}'",
        "settlement_level": "INTEGER DEFAULT 1",
        "capital_id": "INTEGER",
        "expansion_ring": "INTEGER DEFAULT 0",
        "micro_q": "INTEGER DEFAULT 0",
        "micro_r": "INTEGER DEFAULT 0"
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
    ensure_table(cursor, "story_events", """
        CREATE TABLE IF NOT EXISTS story_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tick INTEGER NOT NULL, region TEXT NOT NULL,
            event_type TEXT NOT NULL, description TEXT NOT NULL, resolved INTEGER DEFAULT 0
        )
    """)

    # farms
    ensure_table(cursor, "farms", """
        CREATE TABLE IF NOT EXISTS farms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            global_hex_id INTEGER, micro_q INTEGER, micro_r INTEGER,
            settlement_id INTEGER, output_rate REAL DEFAULT 1.0,
            level INTEGER DEFAULT 1, structure_type TEXT,
            integrity REAL DEFAULT 100.0, maintenance_cost REAL DEFAULT 1.0
        )
    """)
    ensure_columns(cursor, "farms", {
        "global_hex_id": "INTEGER",
        "micro_q": "INTEGER",
        "micro_r": "INTEGER",
        "structure_type": "TEXT",
        "integrity": "REAL DEFAULT 100.0",
        "maintenance_cost": "REAL DEFAULT 1.0"
    })

    # buildings
    ensure_table(cursor, "buildings", """
        CREATE TABLE IF NOT EXISTS buildings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            settlement_id INTEGER, type TEXT, level INTEGER DEFAULT 1,
            associated_farm_id INTEGER
        )
    """)
    ensure_columns(cursor, "buildings", {
        "associated_farm_id": "INTEGER"
    })

    # paragons
    ensure_table(cursor, "paragons", """
        CREATE TABLE IF NOT EXISTS paragons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            settlement_id INTEGER, name TEXT, descriptor TEXT, goal TEXT,
            stat_vita INTEGER DEFAULT 5, stat_motus INTEGER DEFAULT 5,
            stat_lex INTEGER DEFAULT 5, stat_flux INTEGER DEFAULT 5
        )
    """)
    ensure_columns(cursor, "paragons", {
        "goal": "TEXT",
        "stat_vita": "INTEGER DEFAULT 5",
        "stat_motus": "INTEGER DEFAULT 5",
        "stat_lex": "INTEGER DEFAULT 5",
        "stat_flux": "INTEGER DEFAULT 5"
    })

    # structure_costs
    ensure_table(cursor, "structure_costs", """
        CREATE TABLE IF NOT EXISTS structure_costs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT, level INTEGER, upkeep_wealth REAL,
            wood_cost INTEGER, clay_cost INTEGER
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM structure_costs")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO structure_costs (type, level, upkeep_wealth, wood_cost, clay_cost) VALUES ('Farm', 1, 1.0, 10, 5)")
        cursor.execute("INSERT INTO structure_costs (type, level, upkeep_wealth, wood_cost, clay_cost) VALUES ('Mine', 1, 2.0, 20, 10)")
        cursor.execute("INSERT INTO structure_costs (type, level, upkeep_wealth, wood_cost, clay_cost) VALUES ('Lumber Camp', 1, 1.0, 5, 0)")

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

    # factions
    ensure_table(cursor, "factions", """
        CREATE TABLE IF NOT EXISTS factions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, special_rule TEXT, treasury REAL DEFAULT 1000.0,
            technology_level INTEGER DEFAULT 1
        )
    """)
    ensure_columns(cursor, "factions", {
        "special_rule": "TEXT",
        "treasury": "REAL DEFAULT 1000.0",
        "technology_level": "INTEGER DEFAULT 1"
    })

    # faction_relations
    ensure_table(cursor, "faction_relations", """
        CREATE TABLE IF NOT EXISTS faction_relations (
            faction_a_id INTEGER, faction_b_id INTEGER,
            status TEXT DEFAULT 'Neutral', trust_level INTEGER DEFAULT 0,
            PRIMARY KEY (faction_a_id, faction_b_id)
        )
    """)

    # diplomacy_relations
    ensure_table(cursor, "diplomacy_relations", """
        CREATE TABLE IF NOT EXISTS diplomacy_relations (
            settlement_a_id INTEGER, settlement_b_id INTEGER,
            score INTEGER DEFAULT 0,
            PRIMARY KEY (settlement_a_id, settlement_b_id)
        )
    """)

    # crimes
    ensure_table(cursor, "crimes", """
        CREATE TABLE IF NOT EXISTS crimes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            settlement_id INTEGER, type TEXT, severity INTEGER
        )
    """)

    # trade_routes
    ensure_table(cursor, "trade_routes", """
        CREATE TABLE IF NOT EXISTS trade_routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            faction_id INTEGER, settlement_a_id INTEGER, settlement_b_id INTEGER,
            route_type TEXT, bandwidth INTEGER DEFAULT 10
        )
    """)

    # criminal_hideouts
    ensure_table(cursor, "criminal_hideouts", """
        CREATE TABLE IF NOT EXISTS criminal_hideouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            global_hex_id INTEGER, type TEXT, wealth REAL DEFAULT 0,
            food_stockpile REAL DEFAULT 0, is_hidden INTEGER DEFAULT 1
        )
    """)

    # chaos_agents
    ensure_table(cursor, "chaos_agents", """
        CREATE TABLE IF NOT EXISTS chaos_agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT, global_hex_id INTEGER, is_active INTEGER DEFAULT 1,
            strength INTEGER DEFAULT 10, micro_q INTEGER DEFAULT 0, micro_r INTEGER DEFAULT 0
        )
    """)

    conn.commit()
