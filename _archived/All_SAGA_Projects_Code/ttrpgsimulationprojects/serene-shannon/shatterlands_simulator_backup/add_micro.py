import sqlite3

DB_PATH = r'c:\Users\krazy\Desktop\serene-shannon\shatterlands_simulator\core_engine\world_state.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE settlements ADD COLUMN micro_q INTEGER DEFAULT 0")
    cursor.execute("ALTER TABLE settlements ADD COLUMN micro_r INTEGER DEFAULT 0")
    print("Added micro_q, micro_r to settlements.")
except Exception as e:
    print(f"Error: {e}")

conn.commit()
conn.close()
