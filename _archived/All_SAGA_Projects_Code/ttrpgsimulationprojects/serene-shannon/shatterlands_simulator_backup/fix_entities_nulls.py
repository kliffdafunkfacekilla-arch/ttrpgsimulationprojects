import sqlite3

DB_PATH = r'c:\Users\krazy\Desktop\serene-shannon\shatterlands_simulator\core_engine\world_state.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("UPDATE world_entities SET micro_q = 0 WHERE micro_q IS NULL")
cursor.execute("UPDATE world_entities SET micro_r = 0 WHERE micro_r IS NULL")
conn.commit()
conn.close()
print("Fixed nulls in world_entities.")
