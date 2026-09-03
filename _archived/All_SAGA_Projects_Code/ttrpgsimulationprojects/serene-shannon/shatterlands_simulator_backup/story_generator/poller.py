# poller.py – periodically syncs region data (events + hex details) from the simulator DB into the narrative cache DB

import sqlite3
import os
import time
from datetime import datetime
from pathlib import Path

# Paths – adjust if the project layout changes
SIM_DB = Path(__file__).parents[1] / "world_state.db"
CACHE_DB = Path(__file__).parent / "narrative_cache.db"

# Ensure cache DB exists and has required schema
def init_cache_db():
    conn = sqlite3.connect(CACHE_DB)
    cur = conn.cursor()
    # Table for events within a region
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
    # Table for hex details (pack_ecology, river_volume, is_lake, chaos_seed)
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

# Simple hex‑distance (axial coordinates)
def hex_distance(a_q, a_r, b_q, b_r):
    return (abs(a_q - b_q) + abs(a_q + a_r - b_q - b_r) + abs(a_r - b_r)) // 2

# Pull recent events for a region (center q,r, radius)
def sync_region(center_q: int, center_r: int, radius: int = 5):
    sim_conn = sqlite3.connect(SIM_DB)
    cache_conn = sqlite3.connect(CACHE_DB)
    sim_cur = sim_conn.cursor()
    cache_cur = cache_conn.cursor()

    # --- Sync events ----------------------------------------------------
    sim_cur.execute("SELECT global_q, global_r, tick, category, message FROM event_log")
    for q, r, tick, category, message in sim_cur.fetchall():
        if hex_distance(center_q, center_r, q, r) <= radius:
            cache_cur.execute(
                "INSERT OR IGNORE INTO region_events (q, r, tick, category, message) VALUES (?,?,?,?,?)",
                (q, r, tick, category, message),
            )

    # --- Sync hex details ---------------------------------------------
    sim_cur.execute("SELECT q, r, pack_ecology, river_volume, is_lake, chaos_seed FROM global_hexes")
    for q, r, pack_ecology, river_volume, is_lake, chaos_seed in sim_cur.fetchall():
        if hex_distance(center_q, center_r, q, r) <= radius:
            cache_cur.execute(
                "INSERT OR REPLACE INTO hex_details (q, r, pack_ecology, river_volume, is_lake, chaos_seed) VALUES (?,?,?,?,?,?)",
                (q, r, pack_ecology, river_volume, is_lake, chaos_seed),
            )

    cache_conn.commit()
    sim_conn.close()
    cache_conn.close()

def main_loop(poll_interval_seconds: int = 30, centre_q: int = 0, centre_r: int = 0, radius: int = 5):
    init_cache_db()
    print(f"Narrative poller started – syncing every {poll_interval_seconds}s for radius {radius} around ({centre_q},{centre_r})")
    while True:
        sync_region(centre_q, centre_r, radius)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sync completed for region centred at ({centre_q},{centre_r})")
        time.sleep(poll_interval_seconds)

if __name__ == "__main__":
    # Example usage: python poller.py 12 -5 5  # centre at (12,-5), radius 5
    import sys
    if len(sys.argv) == 4:
        centre_q, centre_r, radius = map(int, sys.argv[1:4])
    else:
        centre_q, centre_r, radius = 0, 0, 5
    main_loop(centre_q=centre_q, centre_r=centre_r, radius=radius)
