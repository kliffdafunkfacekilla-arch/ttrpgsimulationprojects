import sqlite3

DB_PATH = r'c:\Users\krazy\Desktop\serene-shannon\shatterlands_simulator\core_engine\world_state.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE settlements ADD COLUMN spark_born_population INTEGER DEFAULT 0")
    cursor.execute("UPDATE settlements SET spark_born_population = population / 2")
    print("Added spark_born_population to settlements.")
except Exception as e:
    print(f"Error: {e}")

conn.commit()
conn.close()
