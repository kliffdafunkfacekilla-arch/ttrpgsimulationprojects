# app.py
import os
import sqlite3
import json
from flask import Flask, jsonify, send_from_directory, request
from core_engine.engine import GlobalEngine
from core_engine.codec import unpack_micro_cluster, unpack_nano_cluster

app = Flask(__name__, static_folder='client_vtt/src', static_url_path='')
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "core_engine", "world_state.db")
engine = GlobalEngine(DB_PATH)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# --- UNIFIED FRONTEND WEB ASSET ROUTERS ---
@app.route('/')
def index():
    return send_from_directory('client_vtt/src', 'index.html')

@app.route('/<path:path>')
def serve_file(path):
    return send_from_directory('client_vtt/src', path)

# --- BACKEND SIMULATION API ENDPOINTS ---
@app.route('/api/map')
def get_map():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, q, r, pack_geo, pack_ecology, chaos_domain FROM global_hexes')
    hexes = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute('SELECT global_hex_id, name, population, wealth, faction_id FROM settlements')
    settlements = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute('SELECT global_hex_id, type FROM world_entities')
    entities = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute('SELECT id, type, global_q, global_r, is_chaos, chaos_domain FROM weather_systems')
    weather = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jsonify({"hexes": hexes, "settlements": settlements, "entities": entities, "weather": weather})

@app.route('/api/cluster/<global_q>/<global_r>')
def get_cluster(global_q, global_r):
    global_q = int(global_q)
    global_r = int(global_r)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, pack_geo, pack_meso, pack_ecology, micro_data_json 
        FROM global_hexes 
        WHERE q = ? AND r = ?
    ''', (global_q, global_r))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Global hex not found"}), 404
        
    global_hex_id = row['id']
    pack_geo = row['pack_geo']
    pack_meso = row['pack_meso']
    pack_eco = row['pack_ecology']
    micro_data_json = row['micro_data_json']
    
    micro_hexes = unpack_micro_cluster(global_q, global_r, pack_geo, pack_meso, pack_eco, micro_data_json)
    
    # Query structures
    cursor.execute('SELECT micro_q, micro_r, name, settlement_level FROM settlements WHERE global_hex_id = ?', (global_hex_id,))
    settlements = {(s['micro_q'], s['micro_r']): s['name'] for s in cursor.fetchall()}
    
    cursor.execute('SELECT micro_q, micro_r, structure_type FROM farms WHERE global_hex_id = ?', (global_hex_id,))
    farms = {(f['micro_q'], f['micro_r']): f['structure_type'] for f in cursor.fetchall()}
    
    cursor.execute('SELECT micro_q, micro_r, type FROM world_entities WHERE global_hex_id = ?', (global_hex_id,))
    entities = {(e['micro_q'], e['micro_r']): e['type'] for e in cursor.fetchall()}
    
    hexes_list = []
    for (mq, mr), hx in micro_hexes.items():
        infrastructure = farms.get((mq, mr)) or entities.get((mq, mr))
        settlement_type = settlements.get((mq, mr))
        
        hexes_list.append({
            "micro_q": mq,
            "micro_r": mr,
            "ecology": {
                "plants": hx.p1, 
                "prey": hx.p2, 
                "predators": hx.p3, 
                "resources": hx.res,
                "biome_id": hx.biome_id,
                "elevation": hx.elevation,
                "res_plant": hx.res_plant,
                "res_special": hx.res_special
            },
            "settlement": settlement_type,
            "infrastructure": infrastructure,
        })
        
    conn.close()
    return jsonify({"global_q": global_q, "global_r": global_r, "hexes": hexes_list})

@app.route('/api/nano_cluster/<global_q>/<global_r>/<micro_q>/<micro_r>')
def get_nano_cluster(global_q, global_r, micro_q, micro_r):
    global_q = int(global_q)
    global_r = int(global_r)
    micro_q = int(micro_q)
    micro_r = int(micro_r)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, pack_geo, pack_meso, pack_ecology, micro_data_json 
        FROM global_hexes 
        WHERE q = ? AND r = ?
    ''', (global_q, global_r))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Global hex not found"}), 404
        
    global_hex_id = row['id']
    pack_geo = row['pack_geo']
    pack_meso = row['pack_meso']
    pack_eco = row['pack_ecology']
    micro_data_json = row['micro_data_json']
    
    # We need the micro hex properties to seed the nano generator
    micro_hexes = unpack_micro_cluster(global_q, global_r, pack_geo, pack_meso, pack_eco, micro_data_json)
    hx = micro_hexes.get((micro_q, micro_r))
    
    if not hx:
        conn.close()
        return jsonify({"error": "Micro hex not found"}), 404
        
    cursor.execute('SELECT name, settlement_level FROM settlements WHERE global_hex_id = ? AND micro_q = ? AND micro_r = ?', (global_hex_id, micro_q, micro_r))
    settlement = cursor.fetchone()
    
    cursor.execute('SELECT structure_type FROM farms WHERE global_hex_id = ? AND micro_q = ? AND micro_r = ?', (global_hex_id, micro_q, micro_r))
    farm = cursor.fetchone()
    
    cursor.execute('SELECT type FROM world_entities WHERE global_hex_id = ? AND micro_q = ? AND micro_r = ?', (global_hex_id, micro_q, micro_r))
    entity = cursor.fetchone()

    s_name = settlement['name'] if settlement else None
    s_level = settlement['settlement_level'] if settlement else 0
    infra_type = farm['structure_type'] if farm else (entity['type'] if entity else None)
    
    nano_hexes = unpack_nano_cluster(global_q, global_r, micro_q, micro_r, hx.biome_id, hx.elevation, hx.p1, hx.p2, hx.p3, hx.res, s_name, s_level, infra_type)
    
    hexes_list = []
    for (nq, nr), nhx in nano_hexes.items():
        infrastructure = None
        settlement_type = None
        if nhx.res_special in ["Town Center", "Market District", "Residential District", "Guard Barracks", "Temple", "Crafting District", "Outer Slums", "Granary", "Trading Post", "City Wall / Gatehouse"]:
            settlement_type = s_name
        elif nhx.res_special in ["Wheat Field", "Irrigation Canal", "Farmhouse", "Windmill", "Main Mine Shaft", "Miner Camp", "Smelting Furnace", "Slag Heap", "Outpost Keep", "Palisade Wall"]:
            infrastructure = infra_type
            
        hexes_list.append({
            "nano_q": nq,
            "nano_r": nr,
            "ecology": {
                "plants": nhx.p1, 
                "prey": nhx.p2, 
                "predators": nhx.p3, 
                "resources": nhx.res,
                "biome_id": nhx.biome_id,
                "elevation": nhx.elevation,
                "res_plant": nhx.res_plant,
                "res_special": nhx.res_special
            },
            "settlement": settlement_type,
            "infrastructure": infrastructure,
        })
        
    conn.close()
    return jsonify({
        "global_q": global_q, "global_r": global_r, 
        "micro_q": micro_q, "micro_r": micro_r, 
        "hexes": hexes_list
    })

@app.route('/api/status')
def get_status():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT SUM(population) as pop FROM settlements')
    row = cursor.fetchone()
    pop = row["pop"] if row and row["pop"] else 0
    conn.close()
    return jsonify({
        "tick": engine.tick,
        "season": getattr(engine, 'season', 'Unknown'),
        "day": getattr(engine, 'day', 0),
        "year": getattr(engine, 'year', 0),
        "global_population": pop
    })

@app.route('/api/tick', methods=['POST'])
def run_tick():
    data = request.json or {}
    ticks = data.get("ticks", 1)
    for _ in range(ticks):
        engine.trigger_tick()
    return jsonify({"status": "success", "tick": engine.tick})

@app.route('/api/logs')
def get_logs():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT tick, category, message, global_q, global_r FROM event_log ORDER BY id DESC LIMIT 15')
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(logs)

if __name__ == '__main__':
    app.run(port=5000, debug=True)