import sqlite3

try:
    conn = sqlite3.connect(r'c:\Users\krazy\Desktop\serene-shannon\shatterlands_simulator\core_engine\world_state.db')
    cursor = conn.cursor()
    cursor.execute("SELECT spark_born_population FROM settlements LIMIT 1")
    print("Success: DB has spark_born_population")
except Exception as e:
    print(e)
