import sqlite3
import os

DB_PATH = r'c:\Users\krazy\Desktop\serene-shannon\shatterlands_simulator\core_engine\world_state.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

columns = [
    ("global_q", "INTEGER"),
    ("global_r", "INTEGER"),
    ("energy", "REAL"),
    ("moisture", "REAL"),
    ("vorticity", "REAL"),
    ("is_chaos", "INTEGER DEFAULT 0"),
    ("chaos_domain", "TEXT")
]

for col_name, col_type in columns:
    try:
        cursor.execute(f"ALTER TABLE weather_systems ADD COLUMN {col_name} {col_type}")
        print(f"Added column {col_name}")
    except sqlite3.OperationalError as e:
        print(f"Could not add {col_name}: {e}")

conn.commit()
conn.close()
