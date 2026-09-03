import sqlite3

DB_PATH = r'c:\Users\krazy\Desktop\serene-shannon\shatterlands_simulator\core_engine\world_state.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE event_log ADD COLUMN global_q INTEGER")
    cursor.execute("ALTER TABLE event_log ADD COLUMN global_r INTEGER")
    print("Added global_q, global_r to event_log.")
except Exception as e:
    print(f"Error: {e}")

conn.commit()
conn.close()
