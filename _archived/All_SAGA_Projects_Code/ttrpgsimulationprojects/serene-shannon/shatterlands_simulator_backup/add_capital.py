import sqlite3

DB_PATH = r'c:\Users\krazy\Desktop\serene-shannon\shatterlands_simulator\core_engine\world_state.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE settlements ADD COLUMN capital_id INTEGER")
    cursor.execute("ALTER TABLE settlements ADD COLUMN expansion_ring INTEGER DEFAULT 0")
    print("Added capital_id, expansion_ring to settlements.")
except Exception as e:
    print(f"Error: {e}")

conn.commit()
conn.close()
