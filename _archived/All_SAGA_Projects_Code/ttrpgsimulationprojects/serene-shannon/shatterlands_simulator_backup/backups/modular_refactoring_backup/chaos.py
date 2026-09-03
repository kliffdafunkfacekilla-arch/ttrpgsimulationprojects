import sqlite3
import random
import math
import json

def unpack_ecology(pack_val):
    p1 = pack_val & 0xFF
    p2 = (pack_val >> 8) & 0xFF
    p3 = (pack_val >> 16) & 0xFF
    res = (pack_val >> 24) & 0xFFFF
    return p1, p2, p3, res

def pack_ecology(p1, p2, p3, res):
    p1 = max(0, min(255, int(p1)))
    p2 = max(0, min(255, int(p2)))
    p3 = max(0, min(255, int(p3)))
    res = max(0, min(65535, int(res)))
    return p1 | (p2 << 8) | (p3 << 16) | (res << 24)

def get_neighbors(q, r):
    return [(q, r-1), (q+1, r-1), (q+1, r), (q, r+1), (q-1, r+1), (q-1, r)]

def wrap_hex(q, r, L=25):
    triangles = {}
    for i in range(5):
        triangles[i*4] = ('UP', (i+1)*L + i, -L)
        triangles[i*4 + 1] = ('DN', i*L + i + 1, L-1)
        triangles[i*4 + 2] = ('UP', i*L + i + 1 + L, 0)
        triangles[i*4 + 3] = ('DN', i*L + i + 1, 2*L - 1)

    connections = {}
    for i in range(5):
        t_top, t_mid_dn, t_mid_up, t_bot_dn = i*4, i*4+1, i*4+2, i*4+3
        connections[(t_top, 'B')] = (t_mid_dn, 'T')
        connections[(t_mid_dn, 'T')] = (t_top, 'B')
        connections[(t_mid_dn, 'R')] = (t_mid_up, 'L')
        connections[(t_mid_up, 'L')] = (t_mid_dn, 'R')
        connections[(t_mid_up, 'B')] = (t_bot_dn, 'T')
        connections[(t_bot_dn, 'T')] = (t_mid_up, 'B')

        prev_up = ((i-1)%5)*4+2
        connections[(t_mid_dn, 'L')] = (prev_up, 'R')
        connections[(prev_up, 'R')] = (t_mid_dn, 'L')

        prev_top, next_top = ((i-1)%5)*4, ((i+1)%5)*4
        connections[(t_top, 'L')] = (prev_top, 'R')
        connections[(t_top, 'R')] = (next_top, 'L')

        prev_bot, next_bot = ((i-1)%5)*4+3, ((i+1)%5)*4+3
        connections[(t_bot_dn, 'L')] = (prev_bot, 'R')
        connections[(t_bot_dn, 'R')] = (next_bot, 'L')

    best_t = -1
    best_dist = 999999
    best_b = None
    for t_id, (t_type, q0, r0) in triangles.items():
        if t_type == 'UP':
            b0, b1, b2 = r0 + L - 1 - r, q + r - (q0 + r0), q0 - q
        else:
            b0, b1, b2 = r - (r0 - L + 1), q - q0, q0 + r0 - (q + r)

        dist = 0
        if b0 < 0: dist -= b0
        if b1 < 0: dist -= b1
        if b2 < 0: dist -= b2
        if dist == 0: return q, r

        if dist < best_dist:
            best_dist, best_t, best_b = dist, t_id, (b0, b1, b2)

    if best_dist > 5: return q, r

    t_type = triangles[best_t][0]
    b0, b1, b2 = best_b
    edge = 'B' if t_type == 'UP' and b0 < 0 else 'T' if t_type == 'DN' and b0 < 0 else 'L' if b1 < 0 else 'R'

    conn = connections.get((best_t, edge))
    if not conn: return q, r
    nt_id, n_edge = conn
    nt_type, nq0, nr0 = triangles[nt_id]

    nb0, nb1, nb2 = b0, b1, b2
    if edge in ['L', 'R'] and n_edge in ['L', 'R']:
        nb0, nb1, nb2 = b0, b2, b1

    if nt_type == 'UP':
        return nq0 - nb2, nr0 + L - 1 - nb0
    else:
        return nq0 + nb1, nr0 - L + 1 + nb0

def process_global_chaos_flow(cursor, season):
    cursor.execute("SELECT id, pack_ecology, flow_target_id FROM global_hexes")
    all_hexes = cursor.fetchall()

    hex_dict = {h[0]: list(unpack_ecology(h[1])) for h in all_hexes}
    flow_targets = {h[0]: h[2] for h in all_hexes if h[2]}

    for h_id, target_id in flow_targets.items():
        if target_id in hex_dict:
            p1 = hex_dict[h_id][0]
            if p1 > 5:
                flow_amt = int(p1 * 0.15)
                hex_dict[h_id][0] -= flow_amt
                hex_dict[target_id][0] = min(255, hex_dict[target_id][0] + flow_amt)

    # Dynamic Chaos bleed / expansion into neighbors
    for h_id, vals in list(hex_dict.items()):
        p1, p2, p3, res = vals
        if p1 > 150 and random.random() < 0.1:
            cursor.execute("SELECT q, r FROM global_hexes WHERE id=?", (h_id,))
            row = cursor.fetchone()
            if row:
                q, r = row
                for nq, nr in get_neighbors(q, r):
                    cursor.execute("SELECT id, pack_ecology FROM global_hexes WHERE q=? AND r=?", (nq, nr))
                    nrow = cursor.fetchone()
                    if nrow:
                        nh_id, n_eco = nrow
                        np1, np2, np3, nres = unpack_ecology(n_eco)
                        if np1 < p1 - 20:
                            bleed = int((p1 - np1) * 0.1)
                            if bleed > 0:
                                hex_dict[h_id][0] -= bleed
                                if nh_id in hex_dict:
                                    hex_dict[nh_id][0] = min(255, hex_dict[nh_id][0] + bleed)

    for h_id, vals in hex_dict.items():
        p1, p2, p3, res = vals
        if season in ["Shadowburn", "Highreach"]:
            p1 = min(255, p1 + 1)
        elif season == "GreenSpan":
            p2 = min(255, p2 + 2)
        elif season == "Shadowfall":
            p1 = min(255, p1 + 5)
            p2 = max(0, p2 - 1)
        hex_dict[h_id] = (p1, p2, p3, res)

    cursor.executemany("UPDATE global_hexes SET pack_ecology=? WHERE id=?",
                       [(pack_ecology(*v), k) for k, v in hex_dict.items()])

def is_hex_in_chaos_flow(q, r, chaos_nodes, tick):
    lunar_offset = tick % 28
    drift = math.sin((lunar_offset / 28.0) * 2 * math.pi) * 0.05

    lon = (q / 50.0) * (2 * math.pi) - math.pi
    lat = (r / 50.0) * math.pi - (math.pi / 2)

    for node in chaos_nodes:
        n_lon, n_lat = node["lon"] + drift, node["lat"] + drift
        line_len_sq = n_lon**2 + n_lat**2
        if line_len_sq > 0:
            t = max(0, min(1, (lon * n_lon + lat * n_lat) / line_len_sq))
            proj_lon, proj_lat = t * n_lon, t * n_lat
            if math.sqrt((lon - proj_lon)**2 + (lat - proj_lat)**2) < 0.04:
                return True
    return False

def manage_weather(cursor, conn, tick, season, log_event_fn):
    if random.random() < 0.2:
        cursor.execute("SELECT id, q, r FROM global_hexes WHERE (pack_geo & 15) >= 9 ORDER BY RANDOM() LIMIT 1")
        row = cursor.fetchone()
        if row:
            cursor.execute("INSERT INTO weather_systems (type, global_q, global_r, energy, moisture, vorticity) VALUES ('Hurricane', ?, ?, 0.8, 0.9, 0.1)", (row[1], row[2]))

    if random.random() < 0.1:
        cursor.execute("SELECT id, q, r FROM global_hexes WHERE (pack_geo & 15) <= 4 ORDER BY RANDOM() LIMIT 1")
        row = cursor.fetchone()
        if row:
            cursor.execute("INSERT INTO weather_systems (type, global_q, global_r, energy, moisture, vorticity) VALUES ('Tornado', ?, ?, 0.5, 0.2, 0.8)", (row[1], row[2]))

    cursor.execute("SELECT id, type, global_q, global_r, energy, moisture, vorticity, is_chaos, chaos_domain FROM weather_systems")
    storms = cursor.fetchall()

    updates = []
    deletes = []

    vecs = {'W': (-1, 0), 'E': (1, 0)}

    for w_id, w_type, q, r, energy, moisture, vorticity, is_chaos, domain in storms:
        cursor.execute("SELECT wind_direction, pack_geo, chaos_domain FROM global_hexes WHERE q=? AND r=?", (q, r))
        hex_data = cursor.fetchone()
        if not hex_data:
            deletes.append((w_id,))
            continue

        wind, p_geo, h_domain = hex_data
        wq, wr = vecs.get(wind, (1, 0))

        q, r = wrap_hex(q + wq, r + wr)

        energy -= 0.05
        moisture -= 0.02
        vorticity -= 0.01

        if energy <= 0 or moisture <= 0 or vorticity <= 0:
            deletes.append((w_id,))
        else:
            updates.append((w_type, q, r, energy, moisture, vorticity, is_chaos, domain, w_id))

    cursor.executemany("UPDATE weather_systems SET type=?, global_q=?, global_r=?, energy=?, moisture=?, vorticity=?, is_chaos=?, chaos_domain=? WHERE id=?", updates)
    cursor.executemany("DELETE FROM weather_systems WHERE id=?", deletes)

def apply_chaos_event(domain, name, pop, sec, inventory, q, r, p_geo, cursor, conn, log_event_fn):
    local_farm = 1.0
    local_consume = 1.0
    is_effect_a = random.random() < 0.5

    if domain == "Mass":
        if is_effect_a:
            inventory.setdefault("Building", {})["Wood"] = 0
            log_event_fn("Chaos", f"Mass crushed {name}! Wood destroyed.", conn, q, r)
        else:
            float_pop = int(pop * 0.2)
            pop -= float_pop
            inventory.setdefault("Survival", {})["Base Food"] = 0
            log_event_fn("Chaos", f"Anti-gravity in {name} flung {float_pop} people into the sky!", conn, q, r)

    elif domain == "Ordo":
        if is_effect_a:
            local_farm = 0.0
            pop -= int(pop * 0.1)
            log_event_fn("Chaos", f"Absolute zero struck {name}, freezing ecology and killing citizens.", conn, q, r)
        else:
            inventory["Tags"] = inventory.get("Tags", []) + ["Rigid"]
            log_event_fn("Chaos", f"Ordo structured {name}, removing brittle tags.", conn, q, r)

    elif domain == "Motus":
        if is_effect_a:
            inventory.setdefault("Building", {})["Stone"] = 0
            sec = max(0, sec - 20)
            log_event_fn("Chaos", f"Sonic boom shattered stone and security in {name}!", conn, q, r)
        else:
            inventory["Building"] = {}
            log_event_fn("Chaos", f"Resources in {name} slid away frictionlessly across the map!", conn, q, r)

    elif domain == "Flux":
        if is_effect_a:
            wood = inventory.get("Building", {}).get("Wood", 0)
            inventory.setdefault("Survival", {})["Base Food"] = inventory.get("Survival", {}).get("Base Food", 0) + wood
            inventory.setdefault("Building", {})["Wood"] = 0
            log_event_fn("Chaos", f"Flux transmuted wood to food in {name}!", conn, q, r)
        else:
            neighbors = get_neighbors(q, r)
            swap_coord = random.choice(neighbors)
            cursor.execute("SELECT id, pack_geo FROM global_hexes WHERE q=? AND r=?", (swap_coord[0], swap_coord[1]))
            row = cursor.fetchone()
            if row:
                n_id, n_geo = row
                cursor.execute("UPDATE global_hexes SET pack_geo=? WHERE id=?", (p_geo, n_id))
                cursor.execute("UPDATE global_hexes SET pack_geo=? WHERE q=? AND r=?", (n_geo, q, r))
                p_geo = n_geo
            log_event_fn("Chaos", f"Flux swapped the geography of {name} with a neighboring hex!", conn, q, r)

    elif domain == "Vita":
        if is_effect_a:
            local_farm *= 5.0
            pop -= int(pop * 0.1)
            log_event_fn("Chaos", f"Hyper-evolution in {name} exploded crop yields but caused lethal cancers!", conn, q, r)
        else:
            p_geo = 3
            cursor.execute("UPDATE global_hexes SET pack_geo=?, pack_ecology=pack_ecology | 200 WHERE q=? AND r=?", (p_geo, q, r))
            log_event_fn("Chaos", f"Toxic overgrowth permanently mutated {name} into a deadly jungle!", conn, q, r)

    elif domain == "Nexus":
        if is_effect_a:
            inventory.setdefault("Building", {})["Wood"] = 0
            log_event_fn("Chaos", f"Fire storms burned all the wood in {name}!", conn, q, r)
        else:
            if inventory.get("Reagents", {}).get("Oils", 0) > 0:
                inventory["Reagents"]["Oils"] = 0
                sec = max(0, sec - 50)
                log_event_fn("Chaos", f"Volatile oils exploded violently in {name}!", conn, q, r)

    elif domain == "Ratio":
        if is_effect_a:
            inventory["Tags"] = inventory.get("Tags", []) + ["Logic Broken"]
            log_event_fn("Chaos", f"Logic broke in {name}, randomizing construction costs!", conn, q, r)
        else:
            sec = max(0, sec - 30)
            log_event_fn("Chaos", f"People logiced themselves into violence in {name}, triggering massive riots!", conn, q, r)

    elif domain == "Anumis":
        if is_effect_a:
            inventory["Tags"] = inventory.get("Tags", []) + ["Inverted Physics"]
            log_event_fn("Chaos", f"Anumis inverted physical properties in {name}!", conn, q, r)
        else:
            inventory.setdefault("Building", {})["Stone"] = 0
            inventory.setdefault("Survival", {})["Base Food"] = 0
            log_event_fn("Chaos", f"An arcane whirlwind shredded resources in {name}!", conn, q, r)

    elif domain == "Lux":
        if is_effect_a:
            local_farm *= 0.5
            pop -= int(pop * 0.05)
            log_event_fn("Chaos", f"Blinding light scorched {name}, causing sunburns and blindness!", conn, q, r)
        else:
            sec = 0
            log_event_fn("Chaos", f"Terrifying illusions tanked morale and security in {name}!", conn, q, r)

    elif domain == "Omen":
        if is_effect_a:
            inventory.setdefault("Survival", {})["Base Food"] = inventory.get("Survival", {}).get("Base Food", 0) + (pop * 5)
            log_event_fn("Chaos", f"Omen simulated ticks ahead for {name}, generating instant food!", conn, q, r)
        else:
            inventory.setdefault("Survival", {})["Base Food"] = 0
            pop -= int(pop * 0.1)
            log_event_fn("Chaos", f"Temporal rot instantly decayed food and aged citizens in {name}!", conn, q, r)

    elif domain == "Aura":
        if is_effect_a:
            sec = 100
            local_farm = 0.0
            log_event_fn("Chaos", f"Toxic euphoria paralyzed {name} in bliss. 0 production.", conn, q, r)
        else:
            sec = 0
            pop -= int(pop * 0.2)
            log_event_fn("Chaos", f"Bloody hate riots decimated {name}!", conn, q, r)

    elif domain == "Lex":
        if is_effect_a:
            sec = 100
            local_farm = 0.0
            local_consume = 0.0
            log_event_fn("Chaos", f"Lex locked {name} in an absolute void of stasis!", conn, q, r)
        else:
            local_farm = 0.0
            pop -= int(pop * 0.1)
            log_event_fn("Chaos", f"A violent theological war halted production in {name} with massive fatalities!", conn, q, r)

    return pop, sec, inventory, local_farm, local_consume, p_geo
