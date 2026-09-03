import json
import sqlite3
import random
from core_engine.codec import unpack_micro_cluster, pack_micro_cluster

# Import modular sub-system phases
from core_engine.combat import process_guards_upkeep
from core_engine.industry import (
    process_maintenance_phase,
    process_production_phase,
    process_construction_ai_phase
)
from core_engine.metabolism import process_population_phase

def process_cluster_fidelity(engine_tick, global_hex_id, conn):
    cursor = conn.cursor()
    
    cursor.execute("SELECT q, r, pack_geo, pack_meso, pack_ecology, micro_data_json FROM global_hexes WHERE id=?", (global_hex_id,))
    row = cursor.fetchone()
    if not row: return
    g_q, g_r, p_geo, p_meso, p_eco, micro_json = row

    micro_hexes = unpack_micro_cluster(g_q, g_r, p_geo, p_meso, p_eco, micro_json)

    cursor.execute("SELECT id, faction_id, name, settlement_level, population, spark_born_population, inventory_json, wealth, security_points, micro_q, micro_r, capital_id, expansion_ring FROM settlements WHERE global_hex_id=?", (global_hex_id,))
    settlements = cursor.fetchall()

    # --- ECOLOGY LOOP (Plant -> Prey -> Predator) ---
    for hx in micro_hexes.values():
        cursor.execute("SELECT id FROM farms WHERE global_hex_id=? AND micro_q=? AND micro_r=?", (global_hex_id, hx.q, hx.r))
        has_structure = cursor.fetchone()

        if has_structure:
            pass
        else:
            if hx.p1 < 250: hx.p1 += 5

            if hx.p1 > 10 and hx.p2 < 100:
                hx.p1 -= 2
                hx.p2 += 1

            if hx.p2 > 10 and hx.p3 < 50:
                hx.p2 -= 2
                hx.p3 += 1

    # --- SETTLEMENT METABOLIC LOOP ---
    for s in settlements:
        s_id, f_id, name, level, pop, spark_born_pop, inv_str, wealth, sec, m_q, m_r, cap_id, exp_ring = s

        try:
            inventory = json.loads(inv_str)
        except:
            inventory = {"Survival": {"Food": 500.0}}
        food_stockpile = inventory.setdefault("Survival", {}).get("Food", 0.0)

        cursor.execute("SELECT name, special_rule FROM factions WHERE id=?", (f_id,))
        f_row = cursor.fetchone()
        f_rule = f_row[1] if f_row else ""

        # A. Guard deployment & Security Upkeep System
        pop, wealth, sec, inventory = process_guards_upkeep(s_id, pop, wealth, sec, inventory, engine_tick, g_q, g_r, cursor)

        # B. Structure Maintenance & Upkeep System
        wealth, inventory = process_maintenance_phase(conn, cursor, s_id, wealth, inventory, name, engine_tick, g_q, g_r)

        # Reachable hex calculation
        def get_dist(hq, hr):
            return (abs(hq - m_q) + abs(hr - m_r) + abs(-hq-hr - (-m_q-m_r))) // 2

        if cap_id is not None:
            reachable = [hx for hx in micro_hexes.values() if get_dist(hx.q, hx.r) <= 2]
        else:
            reachable = [hx for hx in micro_hexes.values() if get_dist(hx.q, hx.r) <= level + 2 + exp_ring]

        # Make sure that each micro hex references its global_hex_id correctly
        for hx in reachable:
            hx.global_hex_id = global_hex_id

        cursor.execute("SELECT micro_q, micro_r FROM farms WHERE global_hex_id=?", (global_hex_id,))
        struct_set = {(r_q, r_r) for r_q, r_r in cursor.fetchall()}

        def sort_key(hx):
            dist = get_dist(hx.q, hx.r)
            is_foot = False
            if cap_id is None:
                if dist <= 1:
                    is_foot = True
                elif exp_ring >= 3 and dist >= 3:
                    is_foot = True
            if is_foot:
                return (0, dist)
            elif (hx.q, hx.r) in struct_set:
                return (1, dist)
            else:
                return (2, dist)

        reachable = sorted(reachable, key=sort_key)

        # Load global overrides to check for rare resources
        cell_tags = []
        rule_overrides = {}
        if micro_json:
            try:
                micro_data = json.loads(micro_json)
                if isinstance(micro_data, dict):
                    cell_tags = micro_data.get("tags", [])
                    rule_overrides = micro_data.get("rule_overrides", {})
            except json.JSONDecodeError:
                pass

        rare_type = rule_overrides.get("rare_resource")

        # C. Resource Gathering & Recipe Production System
        food_stockpile, wealth, inventory, working_pop, farm_production, farm_workers = process_production_phase(
            conn, cursor, s_id, pop, food_stockpile, wealth, inventory, name, reachable, rare_type, f_rule, cap_id, exp_ring, struct_set
        )

        # D. Population Metabolism & Starvation System
        pop, spark_born_pop, food_stockpile, wealth, sec, inventory = process_population_phase(
            conn, cursor, s_id, pop, spark_born_pop, food_stockpile, wealth, sec, inventory, name, farm_production, farm_workers, f_rule, level, engine_tick, g_q, g_r
        )

        # --- RING EXPANSION & HUB LOGISTICS LOOP ---
        if cap_id is None:
            can_expand = pop >= len(reachable)
            mithril_stock = inventory.setdefault("Materials", {}).get("Mithril", 0.0)
            star_herb_stock = inventory.setdefault("Reagents", {}).get("Star-Herb", 0.0)
            has_rare_upgrade = (mithril_stock >= 10.0 or star_herb_stock >= 10.0)

            # Ring expansion requires 10 rare resources (Mithril or Star-Herb)
            if can_expand and pop >= 150 + (exp_ring * 50) and wealth >= 200 + (exp_ring * 100) and exp_ring < 4 and has_rare_upgrade:
                exp_ring += 1
                wealth -= 100
                if mithril_stock >= 10.0:
                    inventory["Materials"]["Mithril"] -= 10.0
                else:
                    inventory["Reagents"]["Star-Herb"] -= 10.0
                cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)",
                               (engine_tick, "Expansion", f"{name} expanded to Ring {exp_ring}!", g_q, g_r))

                if exp_ring >= 3 and pop >= 200:
                    outer_hexes = [hx for hx in micro_hexes.values() if get_dist(hx.q, hx.r) == exp_ring + 2 and hx.biome_id in [3, 4]]
                    if outer_hexes:
                        hub_hex = random.choice(outer_hexes)
                        pop -= 20
                        wealth -= 50
                        hub_name = f"{name} Hub-Village"
                        cursor.execute("""
                            INSERT INTO settlements (faction_id, global_hex_id, name, settlement_level, capital_id, population, spark_born_population, wealth, security_points, micro_q, micro_r)
                            VALUES (?, ?, ?, 1, ?, 20, 10, 50.0, 10.0, ?, ?)
                        """, (f_id, global_hex_id, hub_name, s_id, hub_hex.q, hub_hex.r))

                        cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)",
                                       (engine_tick, "Expansion", f"{name} founded a relay Hub-Village to secure outer nodes!", g_q, g_r))
        else:
            if wealth > 20:
                tribute = wealth - 20
                wealth = 20
                cursor.execute("UPDATE settlements SET wealth = wealth + ? WHERE id=?", (tribute, cap_id))
            if food_stockpile > pop * 2:
                food_trib = food_stockpile - (pop * 2)
                food_stockpile -= food_trib
                cursor.execute("SELECT inventory_json FROM settlements WHERE id=?", (cap_id,))
                c_row = cursor.fetchone()
                if c_row:
                    try: c_inv = json.loads(c_row[0])
                    except: c_inv = {}
                    c_inv.setdefault("Survival", {})["Food"] = c_inv.setdefault("Survival", {}).get("Food", 0) + food_trib
                    cursor.execute("UPDATE settlements SET inventory_json=? WHERE id=?", (json.dumps(c_inv), cap_id))

        # --- LUNAR CHAOS EFFECTS ---
        import math
        chaos_nodes = []
        random.seed(12345)
        for i in range(12):
            lat = math.asin(2 * random.random() - 1)
            lon = 2 * math.pi * random.random()
            chaos_nodes.append({"lon": lon, "lat": lat})
        random.seed()

        lunar_offset = (engine_tick // 24) % 28
        drift = math.sin((lunar_offset / 28.0) * 2 * math.pi) * 0.05

        lon = (g_q / 50.0) * (2 * math.pi) - math.pi
        lat = (g_r / 50.0) * math.pi - (math.pi / 2)

        is_awakened = False
        for node in chaos_nodes:
            n_lon, n_lat = node["lon"] + drift, node["lat"] + drift
            line_len_sq = n_lon**2 + n_lat**2
            if line_len_sq > 0:
                t = max(0, min(1, (lon * n_lon + lat * n_lat) / line_len_sq))
                proj_lon, proj_lat = t * n_lon, t * n_lat
                if math.sqrt((lon - proj_lon)**2 + (lat - proj_lat)**2) < 0.04:
                    is_awakened = True
                    break

        if is_awakened:
            cursor.execute("SELECT chaos_domain FROM global_hexes WHERE q=? AND r=?", (g_q, g_r))
            row = cursor.fetchone()
            if row[0]:
                domain = row[0]
                effect_roll = random.random()
                if domain == "Mass":
                    if effect_roll < 0.5:
                        wealth = max(0, wealth - 20)
                        cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (engine_tick, "Chaos", f"{name} crushed by Mass gravity!", g_q, g_r))
                    else:
                        pop = max(1, pop - 10)
                        cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (engine_tick, "Chaos", f"People flung into the air at {name}!", g_q, g_r))
                elif domain == "Ordo":
                    if effect_roll < 0.5:
                        pop = max(1, pop - 5)
                        for hx in micro_hexes.values(): hx.p1 = 0; hx.p2 = 0
                        cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (engine_tick, "Chaos", f"Ordo froze {name}'s ecology!", g_q, g_r))
                    else:
                        sec += 20
                        cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (engine_tick, "Chaos", f"Ordo rigidly structured {name}!", g_q, g_r))
                elif domain == "Motus":
                    if effect_roll < 0.5:
                        wealth = max(0, wealth - 50)
                    else:
                        pop = max(1, pop - 5); wealth = max(0, wealth - 10)
                        cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (engine_tick, "Chaos", f"Motus sonic gale ripped through {name}!", g_q, g_r))
                elif domain == "Flux":
                    if effect_roll < 0.5:
                        for hx in micro_hexes.values(): hx.res = random.randint(1, 12)
                    cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (engine_tick, "Chaos", f"Flux transmuted the land around {name}!", g_q, g_r))
                elif domain == "Vita":
                    for hx in micro_hexes.values(): hx.p1 = 255
                    if effect_roll < 0.5:
                        pop = max(1, pop - 15)
                        cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (engine_tick, "Chaos", f"Vita cancerous overgrowth killed people at {name}!", g_q, g_r))
                    else:
                        sec = max(0, sec - 10)
                        cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (engine_tick, "Chaos", f"Vita toxic hazards formed at {name}!", g_q, g_r))
                elif domain == "Nexus":
                    if effect_roll < 0.5:
                        pop = max(1, pop - 10)
                        for hx in micro_hexes.values(): hx.p1 = 0
                        cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (engine_tick, "Chaos", f"Nexus fire storm burned {name}!", g_q, g_r))
                    else:
                        wealth = max(0, wealth - 30)
                        cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (engine_tick, "Chaos", f"Nexus explosive reactions wrecked {name}!", g_q, g_r))
                elif domain == "Ratio":
                    if effect_roll < 0.5:
                        wealth = random.randint(0, 100)
                    else:
                        sec = max(0, sec - 20)
                    cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (engine_tick, "Chaos", f"Ratio logic-riots disrupted {name}!", g_q, g_r))
                elif domain == "Anumis":
                    if effect_roll < 0.5:
                        temp = wealth; wealth = sec; sec = temp
                    else:
                        wealth = 0
                    cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (engine_tick, "Chaos", f"Anumis warped reality at {name}!", g_q, g_r))
                elif domain == "Lux":
                    if effect_roll < 0.5:
                        pop = max(1, pop - 2)
                    else:
                        sec = max(0, sec - 20)
                    cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (engine_tick, "Chaos", f"Lux blinded and panicked {name}!", g_q, g_r))
                elif domain == "Omen":
                    if effect_roll < 0.5:
                        pop += 5; wealth += 10
                    else:
                        pop = max(1, pop - 5); wealth = max(0, wealth - 20)
                    cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (engine_tick, "Chaos", f"Omen shifted time at {name}!", g_q, g_r))
                elif domain == "Aura":
                    if effect_roll < 0.5:
                        sec = 100; wealth = max(0, wealth - 10)
                    else:
                        sec = max(0, sec - 30); pop = max(1, pop - 5)
                    cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (engine_tick, "Chaos", f"Aura emotional spikes hit {name}!", g_q, g_r))
                elif domain == "Lex":
                    if effect_roll < 0.5:
                        sec = 100
                    else:
                        sec = 0
                    cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (engine_tick, "Chaos", f"Lex mandates rewrote {name}!", g_q, g_r))

        # --- UNDERWORLD & CRIME LOOP ---
        cursor.execute("SELECT sum(bandwidth) FROM trade_routes WHERE settlement_a_id=? OR settlement_b_id=?", (s_id, s_id))
        route_data = cursor.fetchone()
        trade_vol = route_data[0] if route_data and route_data[0] else 0

        if trade_vol > 0:
            theft_rate = max(0.01, 0.10 - (sec * 0.01))
            stolen_wealth = wealth * theft_rate
            stolen_food = food_stockpile * theft_rate

            wealth -= stolen_wealth
            food_stockpile -= stolen_food

            cursor.execute("SELECT id, wealth FROM criminal_hideouts WHERE global_hex_id=?", (global_hex_id,))
            hideout = cursor.fetchone()
            if hideout:
                h_id, h_wealth = hideout
                cursor.execute("UPDATE criminal_hideouts SET wealth=wealth+? WHERE id=?", (stolen_wealth, h_id))

                if sec < 10 and h_wealth > 20:
                    cursor.execute("UPDATE criminal_hideouts SET wealth=wealth-20 WHERE id=?", (h_id,))
                    inventory["Survival"]["Health"] = max(0.0, inventory["Survival"].get("Health", 100.0) - 10.0)
                    sec -= 2
                    cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (engine_tick, "Crime", f"Narcotics smuggled into {name}!", g_q, g_r))
                elif sec < 0 and h_wealth > 50:
                    cursor.execute("UPDATE criminal_hideouts SET wealth=wealth-50 WHERE id=?", (h_id,))
                    pop -= max(5, int(pop * 0.1))
                    sec -= 10
                    cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (engine_tick, "Crime", f"Terrorist explosion in {name}!", g_q, g_r))

        # E. AI Construction/Expansion/Upgrades Phase
        wealth, inventory = process_construction_ai_phase(
            conn, cursor, s_id, pop, wealth, exp_ring, inventory, name, reachable, struct_set, cap_id, engine_tick, g_q, g_r
        )

        inventory["Survival"]["Food"] = food_stockpile
        cursor.execute("UPDATE settlements SET population=?, spark_born_population=?, inventory_json=?, wealth=?, security_points=?, expansion_ring=? WHERE id=?", (pop, spark_born_pop, json.dumps(inventory), wealth, sec, exp_ring, s_id))

    # --- CHAOS AGENTS LOOP ---
    cursor.execute("SELECT id, type, strength, micro_q, micro_r FROM chaos_agents WHERE global_hex_id=? AND is_active=1", (global_hex_id,))
    for agent in cursor.fetchall():
        a_id, a_type, a_str, a_q, a_r = agent
        if a_type == "Cultist":
            cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (engine_tick, "Chaos", f"Cultists are increasing Latent Chaos at {a_q},{a_r}!", g_q, g_r))
        elif a_type == "Warden":
            cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (engine_tick, "Chaos", f"Wardens are purging Latent Chaos at {a_q},{a_r}!", g_q, g_r))

    new_json = pack_micro_cluster(micro_hexes)

    avg_p1 = sum(hx.p1 for hx in micro_hexes.values()) // 91
    avg_p2 = sum(hx.p2 for hx in micro_hexes.values()) // 91
    avg_p3 = sum(hx.p3 for hx in micro_hexes.values()) // 91
    avg_res = sum(hx.res for hx in micro_hexes.values()) // 91

    g_p1 = max(0, min(255, int(avg_p1)))
    g_p2 = max(0, min(255, int(avg_p2)))
    g_p3 = max(0, min(255, int(avg_p3)))
    g_res = max(0, min(65535, int(avg_res)))
    new_eco = g_p1 | (g_p2 << 8) | (g_p3 << 16) | (g_res << 24)

    cursor.execute("UPDATE global_hexes SET pack_ecology=?, micro_data_json=? WHERE id=?", (new_eco, new_json, global_hex_id))
