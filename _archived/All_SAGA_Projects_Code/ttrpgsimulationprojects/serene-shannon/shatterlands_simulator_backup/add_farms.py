import sqlite3

DB_PATH = r'c:\Users\krazy\Desktop\serene-shannon\shatterlands_simulator\core_engine\world_state.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS farms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    global_hex_id INTEGER,
    micro_q INTEGER,
    micro_r INTEGER,
    settlement_id INTEGER,
    species_name TEXT,
    output_rate REAL DEFAULT 1.0,
    maintenance_cost REAL DEFAULT 5.0,
    level INTEGER DEFAULT 1
)
""")
conn.commit()
conn.close()
print("Created farms table.")
