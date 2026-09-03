import csv
import sqlite3
import os

CSV_PATH = r"C:\Users\krazy\Desktop\Okasha\Okasha Burgs 2026-06-26-06-56.csv"
DB_PATH = r"C:\Users\krazy\Desktop\SAGA_Voice\okasha_world.db"

def run_migration():
    if not os.path.exists(CSV_PATH):
        print(f"Error: Could not find CSV at {CSV_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Clear existing locations to prevent duplicates during multiple runs
    cursor.execute("DELETE FROM locations")

    added = 0
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            loc_id = f"burg_{row['Id']}"
            name = row['Burg']
            state = row.get('State Full Name') or row.get('State') or "the Wildlands"
            culture = row.get('Culture', 'Unknown')
            religion = row.get('Religion', 'Unknown beliefs')
            population = row.get('Population', 'unknown')
            group = row.get('Group', 'settlement')
            
            lore = (f"A {culture} {group} belonging to {state}. "
                    f"It has a population of roughly {population} citizens. "
                    f"The dominant local faith revolves around {religion}.")
            
            if row.get('Capital'):
                lore += " It serves as a major capital."
            if row.get('Citadel'):
                lore += " A formidable citadel overlooks the area."
            if row.get('Port'):
                lore += " It is a bustling port settlement."
                
            cursor.execute(
                "INSERT INTO locations (id, name, base_lore, tension_level) VALUES (?, ?, ?, ?)",
                (loc_id, name, lore, 0)
            )
            added += 1

    conn.commit()
    conn.close()
    print(f"Migration complete. Inserted {added} locations into okasha_world.db.")

if __name__ == "__main__":
    run_migration()
