import sqlite3

db_path = r"C:\Users\krazy\Desktop\ttrpgsimulationprojects\TALEWEAVERSAGA\saga_director\saga_world.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in TALEWEAVERSAGA saga_world.db:")
    for table in tables:
        print(table[0])
    conn.close()
except Exception as e:
    print("Error:", e)
