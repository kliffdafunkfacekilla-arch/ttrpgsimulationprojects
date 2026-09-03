import sqlite3
import json
import os
import math

def get_hex_vertices(q, r, size=12.0):
    # Standard flat-topped hexagon vertices projection
    # x = size * sqrt(3) * (q + r/2)
    # y = -1.5 * size * r
    cx = size * math.sqrt(3) * (q + r / 2.0)
    cy = -1.5 * size * r
    
    vertices = []
    for i in range(7): # 7 vertices to close the polygon loop
        angle_rad = (math.pi / 3.0) * i
        px = cx + size * math.cos(angle_rad)
        py = cy + size * math.sin(angle_rad)
        vertices.append([px, py])
    return vertices

def export_to_json(db_path, output_path):
    if not os.path.exists(db_path):
        return False, "Database not found."
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    data = {}
    
    # 1. Hexes
    cursor.execute("SELECT * FROM global_hexes")
    data["hexes"] = [dict(row) for row in cursor.fetchall()]
    
    # 2. Factions
    cursor.execute("SELECT * FROM factions")
    data["factions"] = [dict(row) for row in cursor.fetchall()]
    
    # 3. Settlements
    cursor.execute("SELECT * FROM settlements")
    data["settlements"] = [dict(row) for row in cursor.fetchall()]
    
    # 4. Entities
    cursor.execute("SELECT * FROM world_entities")
    data["entities"] = [dict(row) for row in cursor.fetchall()]
    
    # 5. Rivers
    try:
        cursor.execute("SELECT * FROM rivers")
        data["rivers"] = [dict(row) for row in cursor.fetchall()]
    except:
        pass
        
    conn.close()
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return True, f"JSON exported successfully to {output_path}"

def export_to_geojson(db_path, output_path):
    if not os.path.exists(db_path):
        return False, "Database not found."
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    features = []
    
    # 1. Hexes (represented as Polygon features)
    cursor.execute("SELECT id, q, r, pack_geo, pack_ecology, chaos_domain FROM global_hexes")
    hexes = cursor.fetchall()
    
    for h in hexes:
        vertices = get_hex_vertices(h["q"], h["r"])
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [vertices]
            },
            "properties": {
                "id": h["id"],
                "q": h["q"],
                "r": h["r"],
                "biome": h["pack_geo"] & 0xF,
                "elevation": (h["pack_geo"] >> 4) & 0xF,
                "chaos_domain": h["chaos_domain"]
            }
        })
        
    # 2. Settlements (represented as Point features)
    cursor.execute("""
        SELECT s.id, s.name, s.population, s.wealth, s.faction_id, g.q, g.r 
        FROM settlements s
        JOIN global_hexes g ON s.global_hex_id = g.id
    """)
    settlements = cursor.fetchall()
    for s in settlements:
        size = 12.0
        cx = size * math.sqrt(3) * (s["q"] + s["r"] / 2.0)
        cy = -1.5 * size * s["r"]
        
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [cx, cy]
            },
            "properties": {
                "id": s["id"],
                "name": s["name"],
                "population": s["population"],
                "wealth": s["wealth"],
                "faction_id": s["faction_id"],
                "q": s["q"],
                "r": s["r"]
            }
        })
        
    conn.close()
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    return True, f"GeoJSON exported successfully to {output_path}"
