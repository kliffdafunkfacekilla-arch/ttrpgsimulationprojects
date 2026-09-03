import sqlite3

db_path = r"C:\Users\krazy\Desktop\ttrpgsimulationprojects\worldsim\omnis-generator\ttrpg_world.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in ttrpg_world.db:")
    for table in tables:
        print(table[0])
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    conn.close()
except Exception as e:
    print("Error:", e)
