# python_fmg/core/db_sync.py
import sqlite3
import json
import os
from typing import Optional
from python_fmg.core.models import MapState, GlobalHex, Settlement, Faction, Paragon, WorldEntity, TradeRoute

def load_from_db(db_path: str) -> Optional[MapState]:
    if not os.path.exists(db_path):
        return None
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if coa_json column exists in factions, if not alter the table
    try:
        cursor.execute("SELECT coa_json FROM factions LIMIT 1")
    except sqlite3.OperationalError:
        try:
            cursor.execute("ALTER TABLE factions ADD COLUMN coa_json TEXT DEFAULT '{}'")
            conn.commit()
        except Exception:
            pass
            
    # Check if micro_q / micro_r exist in world_entities
    try:
        cursor.execute("SELECT micro_q, micro_r FROM world_entities LIMIT 1")
    except sqlite3.OperationalError:
        try:
            cursor.execute("ALTER TABLE world_entities ADD COLUMN micro_q INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE world_entities ADD COLUMN micro_r INTEGER DEFAULT 0")
            conn.commit()
        except Exception:
            pass
            
    # 1. Load Factions
    factions = {}
    try:
        cursor.execute("SELECT id, name, treasury, technology_level, special_rule, coa_json FROM factions")
        for f_id, name, treasury, tech, rule, coa in cursor.fetchall():
            factions[f_id] = Faction(
                id=f_id,
                name=name,
                treasury=treasury,
                technology_level=tech,
                special_rule=rule,
                coa_json=coa or "{}"
            )
            
        # Load Faction Relations
        cursor.execute("SELECT faction_a_id, faction_b_id, status, trust_level FROM faction_relations")
        for f_a, f_b, status, trust in cursor.fetchall():
            if f_a in factions:
                factions[f_a].relations[f_b] = (status, trust)
    except sqlite3.OperationalError:
        pass
        
    # 2. Load Paragons
    paragon_map = {}
    try:
        cursor.execute("SELECT id, settlement_id, name, archetype, level, stats_json, traits_json, motivation FROM paragons")
        for p_id, s_id, name, arch, lvl, stats, traits, mot in cursor.fetchall():
            p = Paragon(
                id=p_id,
                name=name,
                archetype=arch,
                level=lvl,
                stats_json=stats,
                traits_json=traits,
                motivation=mot
            )
            if s_id not in paragon_map:
                paragon_map[s_id] = []
            paragon_map[s_id].append(p)
    except sqlite3.OperationalError:
        pass

    # 3. Load Settlements
    settlements = {}
    try:
        cursor.execute("""
            SELECT s.id, s.faction_id, s.global_hex_id, s.name, s.settlement_level, 
                   s.population, s.wealth, s.security_points, s.inventory_json, 
                   s.hidden_cultists, s.magic_loadout, f.name
            FROM settlements s
            LEFT JOIN factions f ON s.faction_id = f.id
        """)
        for s_id, f_id, g_hex_id, name, lvl, pop, wealth, sec, inv, hidden, magic, f_name in cursor.fetchall():
            sett = Settlement(
                id=s_id,
                faction_id=f_id,
                faction_name=f_name or "Neutral",
                name=name,
                settlement_level=lvl,
                population=pop,
                wealth=wealth,
                security_points=sec,
                inventory_json=inv,
                hidden_cultists=hidden,
                magic_loadout=magic,
                paragons=paragon_map.get(s_id, [])
            )
            settlements[g_hex_id] = sett
    except sqlite3.OperationalError:
        pass

    # 4. Load Hexes
    hexes = {}
    hex_id_to_coords = {}
    try:
        cursor.execute("""
            SELECT id, q, r, pack_geo, pack_meso, pack_ecology, micro_data_json, 
                   flow_target_id, wind_direction, river_volume, is_lake, chaos_domain 
            FROM global_hexes
        """)
        for h_id, q, r, pack_geo, pack_meso, pack_eco, micro_json, flow_tgt, wind_dir, r_vol, is_lake, domain in cursor.fetchall():
            biome = pack_geo & 0xF
            elevation = (pack_geo >> 4) & 0xF
            
            p1 = pack_eco & 0xFF
            p2 = (pack_eco >> 8) & 0xFF
            p3 = (pack_eco >> 16) & 0xFF
            res = (pack_eco >> 24) & 0xFFFF
            
            hx = GlobalHex(
                id=h_id,
                q=q,
                r=r,
                biome=biome,
                elevation=elevation,
                p1=p1,
                p2=p2,
                p3=p3,
                res=res,
                wind_direction=wind_dir,
                river_volume=r_vol,
                is_lake=bool(is_lake),
                chaos_domain=domain,
                flow_target_id=flow_tgt,
                micro_data_json=micro_json
            )
            if h_id in settlements:
                hx.settlement = settlements[h_id]
            hexes[(q, r)] = hx
            hex_id_to_coords[h_id] = (q, r)
    except sqlite3.OperationalError:
        conn.close()
        return None
        
    # 5. Load World Entities (Military / Monsters)
    entities_list = []
    try:
        cursor.execute("""
            SELECT id, type, global_hex_id, radius, duration, intensity, alignment, micro_q, micro_r 
            FROM world_entities
        """)
        for e_id, e_type, g_hex_id, radius, duration, intensity, alignment, mq, mr in cursor.fetchall():
            g_coords = hex_id_to_coords.get(g_hex_id, (0, 0))
            entities_list.append(WorldEntity(
                id=e_id,
                type=e_type,
                global_hex_id=g_hex_id,
                global_q=g_coords[0],
                global_r=g_coords[1],
                radius=radius,
                duration=duration,
                intensity=intensity,
                alignment=alignment,
                micro_q=mq,
                micro_r=mr
            ))
    except sqlite3.OperationalError:
        pass
        
    # 6. Load Trade Routes
    routes_list = []
    try:
        cursor.execute("SELECT id, faction_id, settlement_a_id, settlement_b_id, bandwidth, route_type FROM trade_routes")
        for r_id, f_id, s_a, s_b, band, r_type in cursor.fetchall():
            routes_list.append(TradeRoute(
                id=r_id,
                faction_id=f_id,
                settlement_a_id=s_a,
                settlement_b_id=s_b,
                bandwidth=band,
                route_type=r_type
            ))
    except sqlite3.OperationalError:
        pass
        
    conn.close()
    return MapState(hexes=hexes, factions=factions, entities=entities_list, routes=routes_list)

def save_to_db(state: MapState, db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Save Factions
    faction_updates = []
    for f_id, f in state.factions.items():
        faction_updates.append((
            f.name,
            f.treasury,
            f.technology_level,
            f.special_rule,
            f.coa_json,
            f.id
        ))
    if faction_updates:
        try:
            cursor.executemany("""
                UPDATE factions 
                SET name=?, treasury=?, technology_level=?, special_rule=?, coa_json=?
                WHERE id=?
            """, faction_updates)
        except sqlite3.OperationalError:
            cursor.executemany("""
                UPDATE factions 
                SET name=?, treasury=?, technology_level=?, special_rule=?
                WHERE id=?
            """, [item[:-2] + (item[-1],) for item in faction_updates])
            
    # Save Faction Relations
    for f_id, f in state.factions.items():
        for target_id, (status, trust) in f.relations.items():
            cursor.execute("""
                INSERT OR REPLACE INTO faction_relations (faction_a_id, faction_b_id, status, trust_level)
                VALUES (?, ?, ?, ?)
            """, (f.id, target_id, status, trust))

    # 2. Save Hexes
    hex_updates = []
    for (q, r), hx in state.hexes.items():
        pack_geo = (hx.biome & 0xF) | ((hx.elevation & 0xF) << 4)
        pack_eco = hx.p1 | (hx.p2 << 8) | (hx.p3 << 16) | (hx.res << 24)
        hex_updates.append((
            pack_geo,
            pack_eco,
            hx.micro_data_json,
            hx.wind_direction,
            hx.river_volume,
            1 if hx.is_lake else 0,
            hx.chaos_domain,
            hx.flow_target_id,
            hx.id
        ))
        
    cursor.executemany("""
        UPDATE global_hexes 
        SET pack_geo=?, pack_ecology=?, micro_data_json=?, wind_direction=?, 
            river_volume=?, is_lake=?, chaos_domain=?, flow_target_id=?
        WHERE id=?
    """, hex_updates)
    
    # 3. Save Settlements & Paragons
    for (q, r), hx in state.hexes.items():
        if hx.settlement:
            s = hx.settlement
            if s.id is not None:
                cursor.execute("""
                    UPDATE settlements 
                    SET faction_id=?, name=?, settlement_level=?, population=?, 
                        wealth=?, security_points=?, inventory_json=?, hidden_cultists=?, magic_loadout=?
                    WHERE id=?
                """, (s.faction_id, s.name, s.settlement_level, s.population, s.wealth, s.security_points, s.inventory_json, s.hidden_cultists, s.magic_loadout, s.id))
            else:
                cursor.execute("""
                    INSERT INTO settlements 
                    (faction_id, global_hex_id, name, settlement_level, population, wealth, security_points, inventory_json, hidden_cultists, magic_loadout)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (s.faction_id, hx.id, s.name, s.settlement_level, s.population, s.wealth, s.security_points, s.inventory_json, s.hidden_cultists, s.magic_loadout))
                s.id = cursor.lastrowid
                
            cursor.execute("DELETE FROM paragons WHERE settlement_id=?", (s.id,))
            for p in s.paragons:
                cursor.execute("""
                    INSERT INTO paragons (settlement_id, name, archetype, level, stats_json, traits_json, motivation)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (s.id, p.name, p.archetype, p.level, p.stats_json, p.traits_json, p.motivation))
        else:
            cursor.execute("SELECT id FROM settlements WHERE global_hex_id=?", (hx.id,))
            sett_row = cursor.fetchone()
            if sett_row:
                s_id = sett_row[0]
                cursor.execute("DELETE FROM paragons WHERE settlement_id=?", (s_id,))
                cursor.execute("DELETE FROM settlements WHERE id=?", (s_id,))
                
    # 4. Save World Entities (Military Units / Storms)
    cursor.execute("DELETE FROM world_entities")
    for ent in state.entities:
        cursor.execute("""
            INSERT INTO world_entities (type, global_hex_id, radius, duration, intensity, alignment, micro_q, micro_r)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (ent.type, ent.global_hex_id, ent.radius, ent.duration, ent.intensity, ent.alignment, ent.micro_q, ent.micro_r))
        ent.id = cursor.lastrowid
        
    # 5. Save Trade Routes
    cursor.execute("DELETE FROM trade_routes")
    for route in state.routes:
        cursor.execute("""
            INSERT INTO trade_routes (faction_id, settlement_a_id, settlement_b_id, bandwidth, route_type)
            VALUES (?, ?, ?, ?, ?)
        """, (route.faction_id, route.settlement_a_id, route.settlement_b_id, route.bandwidth, route.route_type))
        route.id = cursor.lastrowid
            
    conn.commit()
    conn.close()
