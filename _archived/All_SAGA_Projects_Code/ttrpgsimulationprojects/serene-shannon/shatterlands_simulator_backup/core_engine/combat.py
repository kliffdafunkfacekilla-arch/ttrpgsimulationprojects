import sqlite3
import random
import math
from core_engine.codec import unpack_micro_cluster, pack_micro_cluster
from core_engine.chaos import get_neighbors, step_towards, wrap_hex

def process_world_entities(cursor, conn, tick, prison_coords, log_event_fn, is_hex_in_chaos_flow_fn, chaos_nodes):
    cursor.execute("SELECT id, q, r FROM global_hexes ORDER BY RANDOM() LIMIT 20")
    for row in cursor.fetchall():
        if is_hex_in_chaos_flow_fn(row[1], row[2], chaos_nodes, tick):
            if random.random() < 0.2:
                 cursor.execute("INSERT INTO world_entities (type, global_hex_id, radius, duration, micro_q, micro_r) VALUES ('Chaos Creature', ?, 1, 20, 0, 0)", (row[0],))
                 log_event_fn("Chaos", "A wild Chaos Creature spawned on a Chaos Path!", conn)

    # Balanced Null Zealot Spawns
    cursor.execute("SELECT COUNT(*) FROM world_entities WHERE type='Null Zealots'")
    num_nulls = cursor.fetchone()[0]
    if num_nulls < 5 and random.random() < 0.05:
        cursor.execute("SELECT id FROM global_hexes ORDER BY RANDOM() LIMIT 1")
        g_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO world_entities (type, global_hex_id, radius, duration, micro_q, micro_r) VALUES ('Null Zealots', ?, 1, 50, 0, 0)", (g_id,))
        log_event_fn("Mandate", "A crusade of Null Zealots has mobilized!", conn)

    # Warden Patrol Spawns
    cursor.execute("SELECT COUNT(*) FROM world_entities WHERE type='Warden Patrol'")
    num_wardens = cursor.fetchone()[0]
    if num_wardens < 3 and random.random() < 0.15:
        cursor.execute("SELECT global_hex_id FROM settlements WHERE name='The Warden Spire'")
        ws_row = cursor.fetchone()
        if ws_row:
            ws_hex = ws_row[0]
            cursor.execute("INSERT INTO world_entities (type, global_hex_id, radius, duration, micro_q, micro_r) VALUES ('Warden Patrol', ?, 2, 40, 0, 0)", (ws_hex,))
            log_event_fn("Mandate", "A Warden Patrol has departed from the Spire to hunt chaos!", conn)

    cursor.execute("SELECT id, type, global_hex_id, radius, duration, alignment, micro_q, micro_r FROM world_entities")
    entities = cursor.fetchall()

    vecs = {'W': (-1, 0), 'E': (1, 0)}
    alive_entities = []

    for e_id, e_type, g_id, e_rad, e_dur, e_align, m_q, m_r in entities:
        e_dur -= 1
        if e_dur <= 0:
            cursor.execute("DELETE FROM world_entities WHERE id=?", (e_id,))
            continue

        cursor.execute("SELECT q, r, wind_direction, pack_ecology, chaos_domain, pack_geo, pack_meso, micro_data_json FROM global_hexes WHERE id=?", (g_id,))
        hex_data = cursor.fetchone()
        if not hex_data:
            cursor.execute("DELETE FROM world_entities WHERE id=?", (e_id,))
            continue

        q, r, wind, p_eco, domain, p_geo, p_meso, micro_data_json = hex_data
        p1 = p_eco & 255

        if e_type in ["Hurricane", "Tornado", "Overcast", "Clear Skies"]:
            if p1 > 100 and random.random() < 0.25:
                e_type = "Chaos Storm"
                e_dur = 20
                e_align = domain
                log_event_fn("Chaos", f"A {e_type} has mutated into a Chaos Storm of {e_align}!", conn)

        nm_q, nm_r = m_q, m_r
        intended_global_q, intended_global_r = q, r

        if e_type == "Chaos Storm":
            nm_q, nm_r = random.choice(get_neighbors(m_q, m_r))
            micro_hexes = unpack_micro_cluster(q, r, p_geo, p_meso, p_eco, micro_data_json)
            if (nm_q, nm_r) in micro_hexes:
                micro_hexes[(nm_q, nm_r)].p1 = 255
                cursor.execute("UPDATE global_hexes SET micro_data_json=? WHERE id=?", (pack_micro_cluster(micro_hexes), g_id))
        elif e_type == "Chaos Creature":
            nm_q, nm_r = random.choice(get_neighbors(m_q, m_r))
            micro_hexes = unpack_micro_cluster(q, r, p_geo, p_meso, p_eco, micro_data_json)
            if (nm_q, nm_r) in micro_hexes:
                micro_hexes[(nm_q, nm_r)].p2 = 255
                micro_hexes[(nm_q, nm_r)].p3 = 255
                cursor.execute("UPDATE global_hexes SET micro_data_json=? WHERE id=?", (pack_micro_cluster(micro_hexes), g_id))
        elif e_type == "Null Zealots":
            if prison_coords:
                pq, pr = random.choice(list(prison_coords.values()))
                if (q, r) != (pq, pr): intended_global_q, intended_global_r = step_towards(q, r, pq, pr)
                nm_q, nm_r = random.choice(get_neighbors(m_q, m_r))
            else:
                nm_q, nm_r = random.choice(get_neighbors(m_q, m_r))
        elif e_type == "Warden Patrol":
            # Seek the closest hostile chaos creature, cult monster, or zealots
            cursor.execute("SELECT global_hex_id FROM world_entities WHERE type IN ('Chaos Creature', 'Cult Monster', 'Null Zealots')")
            targets = cursor.fetchall()
            if targets:
                t_hexes = [t[0] for t in targets]
                cursor.execute(f"SELECT q, r FROM global_hexes WHERE id IN ({','.join('?'*len(t_hexes))})", t_hexes)
                coords = cursor.fetchall()
                if coords:
                    closest_pq, closest_pr = coords[0]
                    min_dist = 999999
                    for cq, cr in coords:
                        dist_c = (abs(q - cq) + abs(r - cr) + abs(-q-r - (-cq-cr))) // 2
                        if dist_c < min_dist:
                            min_dist = dist_c
                            closest_pq, closest_pr = cq, cr
                    if (q, r) != (closest_pq, closest_pr):
                        intended_global_q, intended_global_r = step_towards(q, r, closest_pq, closest_pr)
            nm_q, nm_r = random.choice(get_neighbors(m_q, m_r))
        elif e_type == "Cult Monster" and e_align in prison_coords:
            pq, pr = prison_coords[e_align]
            if (q, r) != (pq, pr): intended_global_q, intended_global_r = step_towards(q, r, pq, pr)
            nm_q, nm_r = random.choice(get_neighbors(m_q, m_r))
            micro_hexes = unpack_micro_cluster(q, r, p_geo, p_meso, p_eco, micro_data_json)
            if (nm_q, nm_r) in micro_hexes:
                micro_hexes[(nm_q, nm_r)].p1 = 255
                micro_hexes[(nm_q, nm_r)].p3 = 255
                cursor.execute("UPDATE global_hexes SET micro_data_json=? WHERE id=?", (pack_micro_cluster(micro_hexes), g_id))
        else:
            wq, wr = vecs.get(wind, (1, 0))
            nm_q, nm_r = m_q + wq, m_r + wr
            intended_global_q, intended_global_r = q + wq, r + wr

        dist = (abs(nm_q) + abs(nm_r) + abs(-nm_q - nm_r)) // 2

        if dist > 4:
            nq, nr = intended_global_q, intended_global_r
            if nq == q and nr == r:
                nq, nr = random.choice(get_neighbors(q, r))

            nq, nr = wrap_hex(nq, nr)

            cursor.execute("SELECT id FROM global_hexes WHERE q=? AND r=?", (nq, nr))
            new_g_id_row = cursor.fetchone()

            if new_g_id_row:
                new_g_id = new_g_id_row[0]
                cursor.execute("UPDATE world_entities SET global_hex_id=?, duration=?, type=?, alignment=?, micro_q=?, micro_r=? WHERE id=?",
                               (new_g_id, e_dur, e_type, e_align, 0, 0, e_id))
                alive_entities.append((e_id, e_type, new_g_id, e_rad, 0, 0, e_align))
            else:
                cursor.execute("DELETE FROM world_entities WHERE id=?", (e_id,))
        else:
            cursor.execute("UPDATE world_entities SET duration=?, type=?, alignment=?, micro_q=?, micro_r=? WHERE id=?",
                           (e_dur, e_type, e_align, nm_q, nm_r, e_id))
            alive_entities.append((e_id, e_type, g_id, e_rad, nm_q, nm_r, e_align))

    # Warden Patrol Combat Collision Clashing
    cursor.execute("SELECT id, global_hex_id FROM world_entities WHERE type='Warden Patrol'")
    patrols = cursor.fetchall()
    for p_id, p_g_id in patrols:
        cursor.execute("SELECT id, type FROM world_entities WHERE global_hex_id=? AND type IN ('Chaos Creature', 'Cult Monster', 'Null Zealots')", (p_g_id,))
        hostile = cursor.fetchone()
        if hostile:
            h_id, h_type = hostile
            cursor.execute("DELETE FROM world_entities WHERE id=?", (p_id,))
            cursor.execute("DELETE FROM world_entities WHERE id=?", (h_id,))
            log_event_fn("Mandate", f"A Warden Patrol clashed with a {h_type} and destroyed it!", conn)

    return alive_entities

def process_guards_upkeep(s_id, pop, wealth, sec, inventory, engine_tick, g_q, g_r, cursor):
    # Base security decay
    sec = max(0.0, sec - 1.0)
    
    # 5% of population are assigned as guards (max 50)
    num_guards = min(50, max(1, int(pop * 0.05)))
    guard_wealth_cost = num_guards * 0.5
    
    wood_stock = inventory.setdefault("Building", {}).get("Wood", 0.0)
    clay_stock = inventory.setdefault("Building", {}).get("Clay", 0.0)
    stone_stock = inventory.setdefault("Building", {}).get("Stone", 0.0)
    
    resource_available = wood_stock + clay_stock + stone_stock
    
    if wealth >= guard_wealth_cost and resource_available >= num_guards:
        wealth -= guard_wealth_cost
        rem = num_guards
        for res_group in ["Wood", "Clay", "Stone"]:
            avail = inventory["Building"].setdefault(res_group, 0.0)
            take = min(avail, rem)
            inventory["Building"][res_group] = avail - take
            rem -= take
            if rem <= 0: break
        
        # Gain security based on equipped guards
        sec = min(100.0, sec + (num_guards * 0.5))
    else:
        # Failed to equip guards - security decays and soldiers desert
        sec = max(0.0, sec - 2.0)
        if random.random() < 0.2:
            deserted = int(num_guards * 0.1)
            pop = max(1, pop - deserted)
            cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, 'Security', ?, ?, ?)",
                           (engine_tick, f"Guards deserted and security decayed due to lack of upkeep.", g_q, g_r))
    return pop, wealth, sec, inventory
