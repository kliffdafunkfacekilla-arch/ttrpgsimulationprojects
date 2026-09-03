import sqlite3

DB_PATH = r'c:\Users\krazy\Desktop\serene-shannon\shatterlands_simulator\core_engine\world_state.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='world_entities'")
row = cursor.fetchone()
if row:
    print(row[0])

# I'll also just add micro_q, micro_r directly to save time
try:
    cursor.execute("ALTER TABLE world_entities ADD COLUMN micro_q INTEGER")
    print("Added micro_q")
except Exception as e:
    print(e)
try:
    cursor.execute("ALTER TABLE world_entities ADD COLUMN micro_r INTEGER")
    print("Added micro_r")
except Exception as e:
    print(e)

conn.commit()
conn.close()
