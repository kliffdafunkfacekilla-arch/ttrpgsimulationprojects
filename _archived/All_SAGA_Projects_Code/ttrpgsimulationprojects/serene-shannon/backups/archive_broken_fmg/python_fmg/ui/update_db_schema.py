import os
import sqlite3

def update_schema():
    db_path = r"c:\Users\krazy\Desktop\serene-shannon\lore_forge_world.db"
    if not os.path.exists(db_path):
        print(f"[-] Database not found at: {db_path}")
        return False
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Add valid_from / valid_until / z_layer to settlements
    try:
        cursor.execute("ALTER TABLE settlements ADD COLUMN valid_from INTEGER DEFAULT 0;")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE settlements ADD COLUMN valid_until INTEGER DEFAULT 9999;")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE settlements ADD COLUMN z_layer TEXT DEFAULT 'surface';")
    except sqlite3.OperationalError:
        pass
        
    # 2. Add valid_from / valid_until / z_layer to factions
    try:
        cursor.execute("ALTER TABLE factions ADD COLUMN valid_from INTEGER DEFAULT 0;")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE factions ADD COLUMN valid_until INTEGER DEFAULT 9999;")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE factions ADD COLUMN z_layer TEXT DEFAULT 'surface';")
    except sqlite3.OperationalError:
        pass
        
    # 3. Add z_layer to trade_routes
    try:
        cursor.execute("ALTER TABLE trade_routes ADD COLUMN z_layer TEXT DEFAULT 'surface';")
    except sqlite3.OperationalError:
        pass

    # 4. Create chronology_events table
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chronology_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER DEFAULT 0,
            name TEXT NOT NULL,
            description TEXT,
            global_q INTEGER,
            global_r INTEGER,
            end_year INTEGER,
            associated_entities_json TEXT DEFAULT '[]'
        );
        """)
    except Exception as e:
        print(f"[-] Failed to create chronology_events: {e}")
        
    conn.commit()
    conn.close()
    print("[+] SQLite Database Schema successfully updated!")
    return True

if __name__ == "__main__":
    update_schema()
