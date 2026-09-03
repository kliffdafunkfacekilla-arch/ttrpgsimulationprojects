import sqlite3
import json

db_path = r"C:\Users\krazy\Desktop\ttrpgsimulationprojects\worldsim\omnis-generator\ttrpg_world.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- 1 MACRO GROUP ---")
cursor.execute("SELECT id, faction_name, is_capital, population, settlements_json FROM macro_groups WHERE settlements_json IS NOT NULL LIMIT 1")
mg = cursor.fetchone()
if mg:
    print(f"Faction: {mg[1]}, Pop: {mg[3]}")
    try:
        print("Settlements:", json.loads(mg[4]))
    except:
        print("Settlements:", mg[4])
        
print("\n--- 1 CELL ---")
cursor.execute("SELECT id, biome, food_supply, controlling_burg_id FROM cells LIMIT 1")
cell = cursor.fetchone()
print(cell)

conn.close()
