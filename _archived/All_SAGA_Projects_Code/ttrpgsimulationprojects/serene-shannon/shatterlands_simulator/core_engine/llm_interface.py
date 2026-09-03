import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "world_state.db")

def get_world_context(db_path=DB_PATH):
    """
    Extracts a concise, broad summary of the world state for an LLM prompt.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    context = {"calendar": {}, "settlements": [], "factions": [], "relations": [], "recent_events": []}
    
    # Time
    cursor.execute("SELECT key, value FROM metadata WHERE key IN ('current_tick', 'current_year', 'current_month', 'current_day', 'current_season')")
    for k, v in cursor.fetchall():
        context["calendar"][k] = v
        
    # Settlements and their Regional Data
    cursor.execute("""
        SELECT s.id, s.name, s.prosperity_level, s.military_strength, s.status_tags, g.regional_data_json 
        FROM settlements s
        LEFT JOIN global_hexes g ON s.global_hex_id = g.id
    """)
    for s_id, name, pros, mil, tags, regional_json in cursor.fetchall():
        try:
            parsed_tags = json.loads(tags)
        except:
            parsed_tags = tags
            
        regional_data = {}
        if regional_json:
            try:
                regional_data = json.loads(regional_json)
            except:
                pass
                
        context["settlements"].append({
            "id": s_id,
            "name": name,
            "prosperity": pros,
            "military": mil,
            "tags": parsed_tags,
            "regional_data": regional_data
        })
        
    # Factions
    cursor.execute("SELECT id, name, special_rule, wealth_status FROM factions")
    for f_id, name, rule, wealth in cursor.fetchall():
        context["factions"].append({
            "id": f_id,
            "name": name,
            "trait": rule,
            "wealth": wealth
        })
        
    # Relations
    cursor.execute("SELECT faction_a_id, faction_b_id, status, tension_level FROM faction_relations")
    for fa, fb, status, tension in cursor.fetchall():
        context["relations"].append({
            "faction_a": fa,
            "faction_b": fb,
            "status": status,
            "tension": tension
        })
        
    # Events
    cursor.execute("SELECT tick, event_type, description FROM story_events ORDER BY tick DESC LIMIT 10")
    for tick, etype, desc in cursor.fetchall():
        context["recent_events"].append({"tick": tick, "type": etype, "desc": desc})
        
    conn.close()
    return json.dumps(context, indent=2)

def apply_narrative_shift(shift_data, db_path=DB_PATH):
    """
    Takes an abstract JSON payload from the LLM and updates the database.
    Example shift_data:
    {
        "settlements": [{"id": 1, "prosperity_level": "Low", "status_tags": ["Starving"]}],
        "relations": [{"faction_a": 1, "faction_b": 2, "status": "Hostile", "tension": 8}],
        "events": [{"tick": 105, "region": "Global", "type": "Plague", "desc": "A terrible plague spreads."}]
    }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    if "settlements" in shift_data:
        for s in shift_data["settlements"]:
            s_id = s.get("id")
            if not s_id: continue
            
            updates = []
            params = []
            if "prosperity_level" in s:
                updates.append("prosperity_level = ?")
                params.append(s["prosperity_level"])
            if "military_strength" in s:
                updates.append("military_strength = ?")
                params.append(s["military_strength"])
            if "status_tags" in s:
                updates.append("status_tags = ?")
                params.append(json.dumps(s["status_tags"]))
                
            if updates:
                params.append(s_id)
                cursor.execute(f"UPDATE settlements SET {', '.join(updates)} WHERE id = ?", params)
                
    if "relations" in shift_data:
        for r in shift_data["relations"]:
            fa = r.get("faction_a")
            fb = r.get("faction_b")
            status = r.get("status")
            tension = r.get("tension")
            if fa is not None and fb is not None:
                cursor.execute("""
                    INSERT INTO faction_relations (faction_a_id, faction_b_id, status, tension_level)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(faction_a_id, faction_b_id) DO UPDATE SET
                    status=excluded.status, tension_level=excluded.tension_level
                """, (fa, fb, status, tension))
                
    if "events" in shift_data:
        for e in shift_data["events"]:
            cursor.execute("INSERT INTO story_events (tick, region, event_type, description) VALUES (?, ?, ?, ?)",
                           (e.get("tick", 0), e.get("region", "Global"), e.get("type", "Event"), e.get("desc", "")))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("Current Context:")
    print(get_world_context())
