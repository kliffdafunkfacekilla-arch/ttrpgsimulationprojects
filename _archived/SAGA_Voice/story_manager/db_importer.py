import os
import glob
import csv
from contextlib import closing
from story_manager.world_db import WorldDB

def import_okasha_data(db_path: str, okasha_folder: str):
    db = WorldDB(db_path)
    
    # Optional: Add a world_lore table if it doesn't exist
    with closing(db._get_connection()) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS world_lore (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter_title TEXT,
                content TEXT
            )
        ''')
        conn.commit()

    print("Importing States (Factions)...")
    state_files = glob.glob(os.path.join(okasha_folder, "Okasha States*.csv"))
    if state_files:
        with open(state_files[0], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            with closing(db._get_connection()) as conn:
                for row in reader:
                    faction_id = f"faction_{row['Id']}"
                    name = row['Full Name'] if row['Full Name'] else row['State']
                    # Skip empty state names (e.g., Neutrals sometimes have blank names)
                    if not name:
                        name = row['State']
                    if not name: continue
                    
                    ideology = f"Culture: {row['Culture']}. Expansionism: {row['Expansionism']}"
                    
                    conn.execute(
                        "INSERT OR REPLACE INTO factions (id, name, ideology, current_status) VALUES (?, ?, ?, ?)",
                        (faction_id, name, ideology, "Active")
                    )
                conn.commit()

    print("Importing Burgs (Locations)...")
    burg_files = glob.glob(os.path.join(okasha_folder, "Okasha Burgs*.csv"))
    if burg_files:
        with open(burg_files[0], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            with closing(db._get_connection()) as conn:
                for row in reader:
                    loc_id = f"loc_{row['Id']}"
                    name = row['Burg']
                    
                    # Build some base lore from the CSV stats
                    lore = []
                    if row['State Full Name'] and row['State Full Name'] != 'undefined':
                        lore.append(f"Located in {row['State Full Name']}.")
                    if row['Culture']:
                        lore.append(f"Predominantly {row['Culture']} culture.")
                    if row['Religion']:
                        lore.append(f"Followers of {row['Religion']}.")
                    if row['Population']:
                        lore.append(f"Population roughly {row['Population']}k.")
                        
                    base_lore = " ".join(lore)
                    
                    conn.execute(
                        "INSERT OR REPLACE INTO locations (id, name, base_lore, tension_level) VALUES (?, ?, ?, ?)",
                        (loc_id, name, base_lore, 0)
                    )
                conn.commit()

    print("Importing Lore (Chapters)...")
    chapter_files = glob.glob(os.path.join(okasha_folder, "Chapter_*.md"))
    with closing(db._get_connection()) as conn:
        for filepath in chapter_files:
            filename = os.path.basename(filepath)
            title = filename.replace("_v1.6.md", "").replace("_", " ")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                conn.execute(
                    "INSERT OR REPLACE INTO world_lore (chapter_title, content) VALUES (?, ?)",
                    (title, content)
                )
            except Exception as e:
                print(f"Failed to read {filename}: {e}")
        conn.commit()

    print("Okasha data import complete!")

if __name__ == "__main__":
    db_path = "C:\\Users\\krazy\\Desktop\\SAGA_Voice\\okasha_world.db"
    okasha_folder = "C:\\Users\\krazy\\Desktop\\Okasha"
    import_okasha_data(db_path, okasha_folder)
