# story_generator DB utilities – used by the API and the poller

import sqlite3
from pathlib import Path

# Paths – relative to this package
SIM_DB = Path(__file__).parents[1] / "world_state.db"
CACHE_DB = Path(__file__) / "narrative_cache.db"

# Ensure the cache DB exists and has the correct schema
def init_cache_db():
    conn = sqlite3.connect(CACHE_DB)
    cur = conn.cursor()
    # Events table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS region_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            q INTEGER NOT NULL,
            r INTEGER NOT NULL,
            tick INTEGER NOT NULL,
            category TEXT NOT NULL,
            message TEXT NOT NULL,
            UNIQUE(q, r, tick, category, message)
        );
        """
    )
    # Hex details table (stores the packed ecology and other macro fields)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS hex_details (
            q INTEGER NOT NULL,
            r INTEGER NOT NULL,
            pack_ecology INTEGER NOT NULL,
            river_volume INTEGER NOT NULL,
            is_lake INTEGER NOT NULL,
            chaos_seed INTEGER NOT NULL,
            PRIMARY KEY (q, r)
        );
        """
    )
    conn.commit()
    conn.close()

# Simple axial hex distance
def hex_distance(a_q: int, a_r: int, b_q: int, b_r: int) -> int:
    return (abs(a_q - b_q) + abs(a_q + a_r - b_q - b_r) + abs(a_r - b_r)) // 2

# Pull recent events and hex details for a region (center + radius) and store them in the cache DB
def sync_region(center_q: int, center_r: int, radius: int = 5):
    sim_conn = sqlite3.connect(SIM_DB)
    cache_conn = sqlite3.connect(CACHE_DB)
    sim_cur = sim_conn.cursor()
    cache_cur = cache_conn.cursor()

    # ---- Events ----
    sim_cur.execute("SELECT global_q, global_r, tick, category, message FROM event_log")
    for q, r, tick, category, message in sim_cur.fetchall():
        if hex_distance(center_q, center_r, q, r) <= radius:
            cache_cur.execute(
                "INSERT OR IGNORE INTO region_events (q, r, tick, category, message) VALUES (?,?,?,?,?)",
                (q, r, tick, category, message),
            )

    # ---- Hex details ----
    sim_cur.execute(
        "SELECT q, r, pack_ecology, river_volume, is_lake, chaos_seed FROM global_hexes"
    )
    for q, r, pack_ecology, river_volume, is_lake, chaos_seed in sim_cur.fetchall():
        if hex_distance(center_q, center_r, q, r) <= radius:
            cache_cur.execute(
                "INSERT OR REPLACE INTO hex_details (q, r, pack_ecology, river_volume, is_lake, chaos_seed) VALUES (?,?,?,?,?,?)",
                (q, r, pack_ecology, river_volume, is_lake, chaos_seed),
            )

    cache_conn.commit()
    sim_conn.close()
    cache_conn.close()

# Helper to fetch cached data for a region (used by the API)
def fetch_region_data(center_q: int, center_r: int, radius: int = 5):
    conn = sqlite3.connect(CACHE_DB)
    cur = conn.cursor()
    # Events
    cur.execute(
        "SELECT q, r, tick, category, message FROM region_events"
    )
    events = [row for row in cur.fetchall() if hex_distance(center_q, center_r, row[0], row[1]) <= radius]
    # Hex details
    cur.execute(
        "SELECT q, r, pack_ecology, river_volume, is_lake, chaos_seed FROM hex_details"
    )
    hexes = [row for row in cur.fetchall() if hex_distance(center_q, center_r, row[0], row[1]) <= radius]
    conn.close()
    return events, hexes
