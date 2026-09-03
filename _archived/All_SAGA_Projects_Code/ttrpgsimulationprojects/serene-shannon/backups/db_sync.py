# python_fmg/core/db_sync.py
import sqlite3
import json
import os
from typing import Optional
from python_fmg.core.models import MapState, GlobalHex, Settlement, Faction

def load_from_db(db_path: str) -> Optional[MapState]:
    if not os.path.exists(db_path):
        return None
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Load Factions
    factions = {}
    try:
        cursor.execute("SELECT id, name, treasury, technology_level, special_rule FROM factions")
        for f_id, name, treasury, tech, rule in cursor.fetchall():
            factions[f_id] = Faction(
                id=f_id,
                name=name,
                treasury=treasury,
                technology_level=tech,
                special_rule=rule
            )
    except sqlite3.OperationalError:
        pass  # Factions table may not exist yet
        
    # 2. Load Settlements
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
            settlements[g_hex_id] = Settlement(
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
                magic_loadout=magic
            )
    except sqlite3.OperationalError:
        pass

    # 3. Load Hexes
    hexes = {}
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
    except sqlite3.OperationalError:
        conn.close()
        return None
        
    conn.close()
    return MapState(hexes=hexes, factions=factions)

def save_to_db(state: MapState, db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # We want to perform updates or replaces in transaction
    # First update global_hexes
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
    
    # Update or insert settlements if they changed
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
        else:
            # If a settlement was removed from this hex in GUI, delete it from database
            cursor.execute("DELETE FROM settlements WHERE global_hex_id=?", (hx.id,))
            
    conn.commit()
    conn.close()
