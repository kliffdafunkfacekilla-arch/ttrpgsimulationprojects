import sqlite3
import os

# Absolute path to the SQLite database file
db_path = r"C:/Users/krazy/Desktop/serene-shannon/shatterlands_simulator/world_state.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("DELETE FROM metadata WHERE key IN ('world_ended', 'world_end_cause', 'current_tick')")
cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('current_tick', '0')")
conn.commit()
conn.close()
print("Metadata reset successfully.")
