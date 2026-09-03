import json
import sqlite3
import os

JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "okasha", "Okasha Full 2026-06-26-06-52.json")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "world_state.db")

def seed_map():
    print(f"Loading map data from {JSON_PATH}...")
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            raw_text = f.read()
            if raw_text.startswith("Azgaar's"):
                print("Detected native .map format instead of strict JSON. Please use Azgaar's 'Save as JSON' option instead.")
                return
            else:
                data = json.loads(raw_text)
    except Exception as e:
        print(f"Failed to load JSON: {e}")
        return

    if data is None:
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    pack = data.get("pack", {}) if "pack" in data else data
    states = pack.get("states", [])
    burgs = pack.get("burgs", [])
    routes = pack.get("routes", [])
    cultures = pack.get("cultures", [])
    cells = pack.get("cells", [])
    rivers = pack.get("rivers", [])
    markers = pack.get("markers", [])
    zones = pack.get("zones", [])
    biomes_data = data.get("biomesData", {})
    
    goods = pack.get("goods", [])
    markets = pack.get("markets", [])
    deals = pack.get("deals", [])
    religions = pack.get("religions", [])

    print(f"Found {len(states)} factions, {len(burgs)} settlements, {len(routes)} routes, {len(cells)} cells, {len(goods)} goods, {len(deals)} deals, {len(religions)} religions.")

    # Parse biomes mapping
    biome_map = {}
    if "i" in biomes_data and "name" in biomes_data:
        for b_i, b_name in zip(biomes_data["i"], biomes_data["name"]):
            biome_map[b_i] = b_name

    # 1. Insert Cultures
    cursor.execute("DELETE FROM cultures")
    culture_map = {}
    for c in cultures:
        if not c or not c.get("name"): continue
        c_i = c.get("i", 0)
        cursor.execute("INSERT INTO cultures (name, type, expansionism) VALUES (?, ?, ?)",
                       (c.get("name"), c.get("type", "Generic"), c.get("expansionism", 1.0)))
        culture_map[c_i] = cursor.lastrowid

    # 2. Insert Factions
    cursor.execute("DELETE FROM factions")
    faction_map = {}
    for i, state in enumerate(states):
        if not state or not state.get("name"): continue
        cursor.execute("INSERT INTO factions (name, wealth_status) VALUES (?, ?)", (state.get("name"), "Adequate"))
        faction_map[state.get("i", i)] = cursor.lastrowid

    # 2.5 Insert Religions
    cursor.execute("DELETE FROM religions")
    religion_map = {}
    for r in religions:
        if not r or not r.get("name") or r.get("name") == "No religion": continue
        r_i = r.get("i", 0)
        cursor.execute("INSERT INTO religions (name, type, form, deity) VALUES (?, ?, ?, ?)",
                       (r.get("name"), r.get("type", "Unknown"), r.get("form", "Unknown"), r.get("deity", "Unknown")))
        religion_map[r_i] = cursor.lastrowid

    # 3. Insert Hexes (Cells)
    cursor.execute("DELETE FROM global_hexes")
    cell_id_to_db_id = {}
    
    if isinstance(cells, dict):
        print("Error: cells is dict, unexpected format.")
        return

    for c in cells:
        cell_idx = c.get("i", -1)
        if cell_idx == -1: continue
        q = (cell_idx % 100) - 50
        r = (cell_idx // 100) - 50
        
        b_idx = c.get("biome", 0)
        biome_name = biome_map.get(b_idx, "Unknown")
        t = c.get("t", 0.0)
        h = c.get("h", 0)
        cult_idx = c.get("culture", 0)
        db_cult_id = culture_map.get(cult_idx)
        rel_idx = c.get("religion", 0)
        db_rel_id = religion_map.get(rel_idx)

        cursor.execute("""
            INSERT INTO global_hexes (q, r, biome_name, temperature, elevation, culture_id, religion_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (q, r, biome_name, t, h, db_cult_id, db_rel_id))
        cell_id_to_db_id[cell_idx] = cursor.lastrowid

    print(f"Inserted {len(cell_id_to_db_id)} global hexes.")

    # 3.5 Insert Military & Diplomacy
    cursor.execute("DELETE FROM faction_relations")
    cursor.execute("DELETE FROM military_regiments")
    for i, state in enumerate(states):
        if not state or not state.get("name"): continue
        state_i = state.get("i", i)
        fac_a_db = faction_map.get(state_i)
        
        # Diplomacy
        diplomacy = state.get("diplomacy", [])
        for j, status in enumerate(diplomacy):
            if status not in ("x", ""):
                fac_b_db = faction_map.get(j)
                if fac_a_db and fac_b_db:
                    status_str = status[0] if isinstance(status, list) and len(status) > 0 else str(status)
                    cursor.execute("INSERT OR IGNORE INTO faction_relations (faction_a_id, faction_b_id, status) VALUES (?, ?, ?)",
                                   (fac_a_db, fac_b_db, status_str))
                                   
        # Military
        military = state.get("military", [])
        for reg in military:
            if not reg: continue
            cell_idx = reg.get("cell", -1)
            db_hex_id = cell_id_to_db_id.get(cell_idx)
            units_json = json.dumps(reg.get("u", {}))
            if fac_a_db:
                cursor.execute("INSERT INTO military_regiments (faction_id, name, icon, stationed_cell_id, units_json) VALUES (?, ?, ?, ?, ?)",
                               (fac_a_db, reg.get("name", "Regiment"), reg.get("icon", "⚔️"), db_hex_id, units_json))

    # 4. Insert Settlements
    cursor.execute("DELETE FROM settlements")
    burg_cell_to_db_id = {} 
    burg_i_to_db_id = {}
    
    for b in burgs:
        if not b or not b.get("name"): continue
        state_i = b.get("state", 0)
        cell_idx = b.get("cell", -1)
        cult_idx = b.get("culture", 0)
        treasury = b.get("treasury", 0.0)

        db_hex_id = cell_id_to_db_id.get(cell_idx)
        db_fac_id = faction_map.get(state_i)
        db_cult_id = culture_map.get(cult_idx)
        
        cursor.execute("""
            INSERT INTO settlements (name, global_hex_id, faction_id, culture_id, treasury, prosperity_level, military_strength) 
            VALUES (?, ?, ?, ?, ?, 'Medium', 'Moderate')
        """, (b.get("name"), db_hex_id, db_fac_id, db_cult_id, treasury))
        
        db_id = cursor.lastrowid
        burg_cell_to_db_id[cell_idx] = db_id
        burg_i_to_db_id[b.get("i")] = db_id

    # 5. Insert Trade Routes
    cursor.execute("DELETE FROM trade_routes")
    routes_added = 0
    for route in routes:
        if not route or "points" not in route: continue
        route_cells = [pt[2] for pt in route["points"] if len(pt) >= 3]
        
        route_settlements = []
        for cell_idx in route_cells:
            if cell_idx in burg_cell_to_db_id:
                if not route_settlements or route_settlements[-1] != burg_cell_to_db_id[cell_idx]:
                    route_settlements.append(burg_cell_to_db_id[cell_idx])
        
        group_name = route.get("group", "roads")
        for i in range(len(route_settlements) - 1):
            settlement_a = route_settlements[i]
            settlement_b = route_settlements[i+1]
            route_type = "Road"
            if "trail" in group_name.lower(): route_type = "Trail"
            if "searoute" in group_name.lower(): route_type = "Sea Route"
            
            cursor.execute("""
                INSERT INTO trade_routes (faction_id, settlement_a_id, settlement_b_id, route_type, status)
                VALUES (0, ?, ?, ?, 'Active')
            """, (settlement_a, settlement_b, route_type))
            routes_added += 1

    # 6. Insert Rivers
    cursor.execute("DELETE FROM rivers")
    for r in rivers:
        if not r or not r.get("name"): continue
        source_cell = r.get("source")
        mouth_cell = r.get("mouth")
        db_source = cell_id_to_db_id.get(source_cell)
        db_mouth = cell_id_to_db_id.get(mouth_cell)
        
        cursor.execute("""
            INSERT INTO rivers (name, type, source_hex_id, mouth_hex_id)
            VALUES (?, ?, ?, ?)
        """, (r.get("name"), r.get("type", "River"), db_source, db_mouth))

    # 7. Insert Markers
    cursor.execute("DELETE FROM markers")
    for m in markers:
        if not m: continue
        cell_idx = m.get("cell")
        db_hex_id = cell_id_to_db_id.get(cell_idx)
        cursor.execute("""
            INSERT INTO markers (icon, type, global_hex_id)
            VALUES (?, ?, ?)
        """, (m.get("icon", ""), m.get("type", "unknown"), db_hex_id))

    # 8. Insert Zones
    cursor.execute("DELETE FROM zones")
    cursor.execute("DELETE FROM zone_hexes")
    for z in zones:
        if not z or not z.get("name"): continue
        cursor.execute("INSERT INTO zones (name, type) VALUES (?, ?)", (z.get("name"), z.get("type", "Zone")))
        z_id = cursor.lastrowid
        z_cells = z.get("cells", [])
        for zc in z_cells:
            db_hex_id = cell_id_to_db_id.get(zc)
            if db_hex_id:
                cursor.execute("INSERT INTO zone_hexes (zone_id, global_hex_id) VALUES (?, ?)", (z_id, db_hex_id))

    # 9. Insert Goods
    cursor.execute("DELETE FROM goods")
    for g in goods:
        if not g: continue
        tags = g.get("tags", [])
        g_type = tags[0] if tags else "commodity"
        cursor.execute("INSERT INTO goods (id, name, type, base_value, unit) VALUES (?, ?, ?, ?, ?)",
                       (g.get("i"), g.get("name"), g_type, g.get("value", 1.0), g.get("unit", "unit")))

    # 10. Insert Markets & Market Goods
    cursor.execute("DELETE FROM markets")
    cursor.execute("DELETE FROM market_goods")
    for m in markets:
        if not m: continue
        m_id = m.get("i")
        burg_id = m.get("centerBurgId")
        db_settlement_id = burg_i_to_db_id.get(burg_id)
        
        cursor.execute("INSERT INTO markets (id, settlement_id) VALUES (?, ?)", (m_id, db_settlement_id))
        
        m_goods = m.get("goods", {})
        for g_id_str, g_data in m_goods.items():
            g_id = int(g_id_str)
            stock = g_data.get("stock", 0)
            price = g_data.get("price", 0)
            cursor.execute("INSERT INTO market_goods (market_id, good_id, stock, price) VALUES (?, ?, ?, ?)",
                           (m_id, g_id, stock, price))

    # 11. Insert Deals
    cursor.execute("DELETE FROM deals")
    for d in deals:
        if not d: continue
        s_id = d.get("seller")
        b_id = d.get("buyer")
        s_type = d.get("sellerType")
        b_type = d.get("buyerType")
        
        # We store them as they are in Azgaar. The engine can resolve market_id or burg_id later, 
        # or we map burg_id to db_settlement_id.
        if s_type == "burg":
            s_id = burg_i_to_db_id.get(s_id, s_id)
        if b_type == "burg":
            b_id = burg_i_to_db_id.get(b_id, b_id)
            
        cursor.execute("""
            INSERT INTO deals (id, seller_id, seller_type, buyer_id, buyer_type, good_id, units, price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (d.get("i"), s_id, s_type, b_id, b_type, d.get("good"), d.get("units"), d.get("price")))

    # 12. Settlement Production
    cursor.execute("DELETE FROM settlement_production")
    for b in burgs:
        if not b or not b.get("name"): continue
        b_i = b.get("i")
        db_id = burg_i_to_db_id.get(b_i)
        if not db_id: continue
        
        production = b.get("production", [])
        for p in production:
            if "goodId" in p and "units" in p:
                cursor.execute("INSERT INTO settlement_production (settlement_id, good_id, units) VALUES (?, ?, ?)",
                               (db_id, p["goodId"], p["units"]))

    conn.commit()
    conn.close()
    print("Database fully seeded with all Azgaar details including the economy.")

if __name__ == "__main__":
    seed_map()
