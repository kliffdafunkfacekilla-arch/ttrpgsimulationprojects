import sqlite3
conn = sqlite3.connect(r'c:\Users\krazy\Desktop\serene-shannon\shatterlands_simulator\core_engine\world_state.db')
cursor = conn.cursor()
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='weather_systems'")
row = cursor.fetchone()
if row:
    print(row[0])
else:
    print("Table weather_systems does not exist.")
