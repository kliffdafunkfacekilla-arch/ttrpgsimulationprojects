# db_setup.py
# Initializes the SQLite database and schemas for the Shatterlands Simulator

import sqlite3
import os
import random
from codec import pack_micro_hex

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "world_state.db")

def init_database():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("Removed existing world_state.db")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create micro-hexes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS micro_hexes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        x INTEGER NOT NULL,
        y INTEGER NOT NULL,
        state_int INTEGER NOT NULL
    )
    """)

    # Create meso-hexes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meso_hexes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        center_x INTEGER NOT NULL,
        center_y INTEGER NOT NULL,
        archetype_int INTEGER NOT NULL,
        iron INTEGER NOT NULL DEFAULT 0,
        timber INTEGER NOT NULL DEFAULT 0,
        food INTEGER NOT NULL DEFAULT 0,
        development INTEGER NOT NULL DEFAULT 0
    )
    """)

    # Add indices on coordinates for high-performance snapshot queries
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_micro_coords ON micro_hexes (x, y)")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_meso_coords ON meso_hexes (center_x, center_y)")

    conn.commit()
    print("Database schema successfully created with indices.")
    return conn

def seed_initial_world(conn):
    cursor = conn.cursor()
    print("Seeding initial world state with Ostraka lore:")

    # Let's seed a 7x7 grid of Meso hexes, and each Meso hex maps to a cluster of Micro hexes
    # We will generate Micro-hexes spanning x from -15 to 15, y from -15 to 15
    micro_coords = []
    for x in range(-15, 16):
        for y in range(-15, 16):
            # Seed random biome (1 to 12)
            biome = random.randint(1, 12)
            # Seed random faction (0 to 15)
            faction = random.randint(0, 15)
            # Seed random resource (0 to 15)
            resource = random.randint(0, 15)
            # Seed development (0 to 5)
            dev_level = random.randint(0, 5) if faction != 0 else 0
            # Seed active overlay (0 for none initially, overlays will drift over time)
            overlay = 0
            # Spark (1 in 10 chance)
            spark = 1 if random.random() < 0.1 else 0

            state_int = pack_micro_hex(biome, faction, resource, dev_level, overlay, spark)
            micro_coords.append((x, y, state_int))

    cursor.executemany("INSERT INTO micro_hexes (x, y, state_int) VALUES (?, ?, ?)", micro_coords)

    # Let's seed Meso-hexes at interval centers of 5 units (e.g. x, y in [-10, -5, 0, 5, 10])
    meso_centers = [-10, -5, 0, 5, 10]
    meso_records = []
    for cx in meso_centers:
        for cy in meso_centers:
            # Archetype_int represents the folded 4-bit matrix or representation
            # Let's pack a simple number representing the dominant features of the surrounding cells
            archetype_int = random.randint(0, 15)
            iron = random.randint(10, 100)
            timber = random.randint(10, 200)
            food = random.randint(20, 300)
            dev = random.randint(0, 10)

            meso_records.append((cx, cy, archetype_int, iron, timber, food, dev))

    cursor.executemany("""
    INSERT INTO meso_hexes (center_x, center_y, archetype_int, iron, timber, food, development)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, meso_records)

    conn.commit()
    print(f"Successfully seeded {len(micro_coords)} micro-hexes and {len(meso_records)} meso-hexes.")

if __name__ == "__main__":
    conn = init_database()
    seed_initial_world(conn)
    conn.close()
