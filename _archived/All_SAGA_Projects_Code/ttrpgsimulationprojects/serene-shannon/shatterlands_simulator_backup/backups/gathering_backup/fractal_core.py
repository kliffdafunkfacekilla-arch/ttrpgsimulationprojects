import json
import sqlite3
import random
from core_engine.codec import unpack_micro_cluster, pack_micro_cluster

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
            # Building removes the 3 part cycle by mechanics
            pass
        else:
            # Baseline plant growth
            if hx.p1 < 250: hx.p1 += 5

            # Prey eat plants
            if hx.p1 > 10 and hx.p2 < 100:
                hx.p1 -= 2
                hx.p2 += 1

            # Predators eat prey
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

        # Calculate working population
        working_pop = max(1, pop)

        def get_dist(hq, hr):
            return (abs(hq - m_q) + abs(hr - m_r) + abs(-hq-hr - (-m_q-m_r))) // 2

        if cap_id is not None:
            # Hub Village manages anything within 2 spaces of it
            reachable = [hx for hx in micro_hexes.values() if get_dist(hx.q, hx.r) <= 2]
        else:
            # Capital City manages its rings
            reachable = [hx for hx in micro_hexes.values() if get_dist(hx.q, hx.r) <= level + 2 + exp_ring]

        # Sort reachable hexes to prioritize:
        # 1. City footprint (Rings 0 & 1, and outer footprint Rings 3 & 4 if expanded)
        # 2. Developed structures (from the farms table)
        # 3. Undeveloped spaces (hand-gathering)
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

        farm_workers = 0
        farm_production = 0.0

        # Gather Phase
        for hx in reachable:
            if working_pop <= 0: break

            # 1. Core/Outer Footprint Check: Rings 0 and 1 + Outer rings (3 and 4 when exp_ring >= 3)
            is_footprint = False
            if cap_id is None: # Only for Capital City
                dist_center = get_dist(hx.q, hx.r)
                if dist_center <= 1:
                    is_footprint = True
                elif exp_ring >= 3 and dist_center >= 3:
                    is_footprint = True

            if is_footprint:
                # Allocates exactly 1 worker, produces 1 food and 1 wealth, bypasses farm/gathering
                working_pop -= 1
                food_stockpile += 1.0
                wealth += 1.0
                continue

            # 2. Structure Check
            cursor.execute("SELECT output_rate, maintenance_cost, level, structure_type FROM farms WHERE global_hex_id=? AND micro_q=? AND micro_r=?", (global_hex_id, hx.q, hx.r))
            farm = cursor.fetchone()

            assign = min(50, working_pop)

            if farm:
                out_rate, maint, s_level, s_type = farm
                if s_type is None:
                    s_type = 'Farm'

                # Double output efficiency and half resource cost
                efficiency_mult = s_level * 2.0
                cost_mult = 0.5

                if s_type == 'Farm':
                    # Farm workers are self-sufficient and automatically fed by the farm.
                    working_pop -= assign
                    farm_workers += assign
                    
                    if f_rule == "Heartland_Alliance" and hx.biome_id == 4:
                        out_rate *= 3.0

                    if wealth >= maint:
                        wealth -= maint
                        farm_production += assign * out_rate * efficiency_mult
                        
                        # Halved ecology depletion
                        depletion_cost = assign * out_rate * cost_mult
                        if hx.p1 >= depletion_cost:
                            hx.p1 -= depletion_cost
                        elif hx.p2 >= depletion_cost:
                            hx.p2 -= depletion_cost
                        else:
                            hx.p3 = max(0, hx.p3 - depletion_cost)
                    else:
                        # Farm fails due to maintenance
                        pass
                else:
                    # Non-food structures require food, so they consume food from the stockpile
                    if wealth >= maint:
                        wealth -= maint
                        working_pop -= assign

                        desperate_foragers = min(5, working_pop + assign)
                        if food_stockpile < assign:
                            if food_stockpile > 0:
                                assign = max(int(food_stockpile), desperate_foragers)
                            else:
                                assign = desperate_foragers
                        
                        food_cost = max(0, assign - desperate_foragers)
                        if food_stockpile >= food_cost:
                            food_stockpile -= food_cost
                        else:
                            food_stockpile = 0.0

                        if hx.res <= 0:
                            hx.res = 100 # Initialize finite count for structures

                        if s_type == 'ReagentFarm':
                            # Halved plant depletion
                            depletion_cost = min(hx.p1, assign * out_rate * cost_mult)
                            hx.p1 -= depletion_cost
                            inventory.setdefault("Reagents", {})["Herbs"] = inventory.setdefault("Reagents", {}).get("Herbs", 0.0) + assign * out_rate * efficiency_mult
                        elif s_type == 'MaterialFarm':
                            # Halved animal depletion
                            depletion_cost = assign * out_rate * cost_mult
                            if hx.p2 >= depletion_cost:
                                hx.p2 -= depletion_cost
                            elif hx.p3 >= depletion_cost:
                                hx.p3 -= depletion_cost
                            else:
                                tot = hx.p2 + hx.p3
                                hx.p2 = 0
                                hx.p3 = max(0, hx.p3 - (depletion_cost - tot))
                            inventory.setdefault("Materials", {})["Leather"] = inventory.setdefault("Materials", {}).get("Leather", 0.0) + assign * out_rate * efficiency_mult
                        elif s_type == 'Quarry':
                            harvest_cost = min(hx.res, assign * out_rate * cost_mult)
                            hx.res -= harvest_cost
                            inventory.setdefault("Building", {})["Stone"] = inventory.setdefault("Building", {}).get("Stone", 0.0) + assign * out_rate * efficiency_mult
                        elif s_type == 'LoggingCamp':
                            harvest_cost = min(hx.res, assign * out_rate * cost_mult)
                            hx.res -= harvest_cost
                            inventory.setdefault("Building", {})["Wood"] = inventory.setdefault("Building", {}).get("Wood", 0.0) + assign * out_rate * efficiency_mult
                        elif s_type == 'Mine':
                            harvest_cost = min(hx.res, assign * out_rate * cost_mult)
                            hx.res -= harvest_cost
                            inventory.setdefault("Materials", {})["Ore"] = inventory.setdefault("Materials", {}).get("Ore", 0.0) + assign * out_rate * efficiency_mult

            if not farm:
                # Manual workers need food to operate.
                assign = min(50, working_pop)
                working_pop -= assign

                desperate_foragers = min(5, working_pop + assign)
                if food_stockpile < assign:
                    if food_stockpile > 0:
                        assign = max(int(food_stockpile), desperate_foragers)
                    else:
                        assign = desperate_foragers
                
                food_cost = max(0, assign - desperate_foragers)
                if food_stockpile >= food_cost:
                    food_stockpile -= food_cost
                else:
                    food_stockpile = 0.0

                if assign <= 0:
                    # Put back working_pop
                    working_pop += assign
                    continue

                # Paragon dictates priorities!
                cursor.execute("SELECT goal, stat_vita, stat_motus, stat_lex, stat_flux FROM paragons WHERE settlement_id=?", (s_id,))
                paragon = cursor.fetchone()
                goal = paragon[0] if paragon else "Survive"
                s_vita = paragon[1] if paragon else 1
                s_motus = paragon[2] if paragon else 1
                s_flux = paragon[4] if paragon else 1

                # 3. Undeveloped space gathering logic based on Paragon goal
                if goal == "Survive" or s_vita > 5:
                    priorities = [("Predator", hx.p3), ("Prey", hx.p2), ("Plant", hx.p1)]
                    harvested = False
                    for p_type, amount in priorities:
                        if amount >= 1:
                            harvest = min(amount, assign)
                            if p_type == "Predator":
                                hx.p3 -= harvest; food_stockpile += harvest * 0.5; wealth += harvest * 0.5
                            elif p_type == "Prey":
                                hx.p2 -= harvest; food_stockpile += harvest * 0.8; wealth += harvest * 0.2
                            elif p_type == "Plant":
                                hx.p1 -= harvest;
                                food_yield = harvest * 0.9
                                # Canopy Clans: Double food production in Jungle
                                if f_rule == "Canopy_Clans" and hx.biome_id == 3: food_yield *= 2.0
                                food_stockpile += food_yield
                                wealth += harvest * 0.1
                            harvested = True
                            break
                elif goal == "Hoard Wealth" or s_flux > 5:
                    # Prioritize Reagents from plants or Materials from prey/predators
                    priorities = [("Plant", hx.p1), ("Prey", hx.p2), ("Predator", hx.p3)]
                    harvested = False
                    for p_type, amount in priorities:
                        if amount >= 1:
                            harvest = min(amount, assign)
                            if p_type == "Plant":
                                hx.p1 -= harvest
                                inventory.setdefault("Reagents", {})["Herbs"] = inventory.setdefault("Reagents", {}).get("Herbs", 0.0) + harvest * 0.5
                                wealth += harvest * 0.2
                            else:
                                if p_type == "Prey": hx.p2 -= harvest
                                else: hx.p3 -= harvest
                                inventory.setdefault("Materials", {})["Leather"] = inventory.setdefault("Materials", {}).get("Leather", 0.0) + harvest * 0.5
                                wealth += harvest * 0.2
                            harvested = True
                            break
                else:
                    # Prioritize Sustainable but finite construction resources
                    if hx.res <= 0:
                        hx.res = 50 # Default starting count for undeveloped spaces
                    
                    harvest = min(hx.res, assign)
                    if harvest > 0:
                        hx.res -= harvest
                        if hx.biome_id in [6, 7]: # Mountains/Volcano (Stone)
                            inventory.setdefault("Building", {})["Stone"] = inventory.setdefault("Building", {}).get("Stone", 0.0) + harvest * 1.0
                            hx.elevation -= 0.01 * harvest
                            wealth += harvest * 0.2
                        elif hx.biome_id in [1, 2]: # Forest/Taiga (Wood)
                            inventory.setdefault("Building", {})["Wood"] = inventory.setdefault("Building", {}).get("Wood", 0.0) + harvest * 1.0
                            hx.biome_id = 3 # Deforests to Plains
                            wealth += harvest * 0.2
                        else: # Desert/Plains/Tundra (Clay)
                            inventory.setdefault("Building", {})["Clay"] = inventory.setdefault("Building", {}).get("Clay", 0.0) + harvest * 1.0
                            wealth += harvest * 0.1
                    food_stockpile += assign * 0.2 # Starvation rations

            # River Folk passive bonus near water
            if f_rule == "River_Folk" and hx.biome_id in [9, 11]: # Ocean/Lake
                food_stockpile += assign * 0.5
                wealth += assign * 0.5

        # Consumption Phase
        # Hive Commonwealth wealth boost from textiles/honey exports
        if f_rule == "Hive_Commonwealth": wealth += pop * 0.5

        consume_rate = 1.0
        if f_rule == "Hearthless": consume_rate = 0.5 # Less food consumed due to Hearth boost
        elif f_rule == "Dust_Husk": consume_rate = 0.5 # Consume 50% less food globally

        # Calculate general population (who are not farm workers and consume food from stockpile)
        general_pop = max(0, pop - farm_workers)

        # Baseline food production from settlement tier (Level 1 has 0, Level 2 has 5.0, etc.)
        baseline_food = (level - 1) * 5.0

        # General population generates 1.0 food each, maintaining themselves
        general_production = general_pop * 1.0

        # Add food production to stockpile
        food_stockpile += general_production + farm_production + baseline_food

        # Consume food from stockpile for general population
        food_consumption = general_pop * consume_rate

        # Get or initialize StarvationTicks
        starvation_ticks = inventory["Survival"].get("StarvationTicks", 0)

        if food_stockpile > food_consumption:
            # Consume the food
            food_stockpile -= food_consumption

            # Surplus -> Growth & Recovery
            if starvation_ticks > 0:
                starvation_ticks = max(0, starvation_ticks - 1)
                # Clear unrest/anarchy tags if starvation is fully recovered
                if starvation_ticks == 0:
                    tags = inventory.setdefault("Tags", [])
                    if "Rioting" in tags: tags.remove("Rioting")
                    if "Anarchy" in tags: tags.remove("Anarchy")

            # Hearthless don't naturally grow
            if f_rule != "Hearthless" and pop > 0:
                pop += 1
                if random.random() < 0.5: spark_born_pop += 1
            wealth += 1.0
        else:
            # Settlement has run out of food
            food_stockpile = 0.0
            
            # Starvation progression
            starvation_ticks += 1
            starved = max(1, int(pop * 0.1))

            tags = inventory.setdefault("Tags", [])

            if starvation_ticks == 1:
                # Stage 1: Shortage
                sec = max(0.0, sec - 10.0)
                cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)",
                               (engine_tick, "Starvation", f"{name} is experiencing critical food shortages!", g_q, g_r))
            elif starvation_ticks == 2:
                # Stage 2: Food Riots
                sec = max(0.0, sec - 20.0)
                wealth = max(0.0, wealth - 10.0)
                if "Rioting" not in tags:
                    tags.append("Rioting")
                cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)",
                               (engine_tick, "Starvation", f"{name} is experiencing violent food riots due to famine!", g_q, g_r))
            else:
                # Stage 3+: Total Anarchy & Deaths
                sec = 0.0
                wealth = max(0.0, wealth - 20.0)
                if "Anarchy" not in tags:
                    tags.append("Anarchy")
                if "Rioting" in tags:
                    tags.remove("Rioting")
                
                # People actually start dying only here
                pop = max(0, pop - starved)
                spark_born_pop = max(0, spark_born_pop - (starved // 2))
                cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)",
                               (engine_tick, "Starvation", f"{name} has collapsed into total anarchy! Starvation claims {starved} citizens.", g_q, g_r))

        inventory["Survival"]["StarvationTicks"] = starvation_ticks

        # --- RING EXPANSION & HUB LOGISTICS LOOP ---
        if cap_id is None: # Capital City
            # Gating beyond Ring 1: must be using all of current ring
            can_expand = True
            if exp_ring >= 1:
                if pop < len(reachable):
                    can_expand = False

            if can_expand and pop >= 150 + (exp_ring * 50) and wealth >= 200 + (exp_ring * 100) and exp_ring < 4:
                # Expand Territory!
                exp_ring += 1
                wealth -= 100
                cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)",
                               (engine_tick, "Expansion", f"{name} expanded to Ring {exp_ring}!", g_q, g_r))

                # Check for Hub Spawning if reaching deep rings
                if exp_ring >= 3 and pop >= 200:
                    outer_hexes = [hx for hx in micro_hexes.values() if get_dist(hx.q, hx.r) == exp_ring + 2 and hx.biome_id in [3, 4]] # Plains/Savanna for clear building
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
            # Hub Village Logistics: Send excess up the chain
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

        # Bandits skim trade routes based on low security
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

                # Smuggling & Consumption
                if sec < 10 and h_wealth > 20: # Narcotics
                    cursor.execute("UPDATE criminal_hideouts SET wealth=wealth-20 WHERE id=?", (h_id,))
                    pop -= 1 # Health debuff
                    sec -= 2 # Crime increase
                    cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (engine_tick, "Crime", f"Narcotics smuggled into {name}!", g_q, g_r))
                elif sec < 0 and h_wealth > 50: # Terrorist Weapons
                    cursor.execute("UPDATE criminal_hideouts SET wealth=wealth-50 WHERE id=?", (h_id,))
                    pop -= max(5, int(pop * 0.1))
                    sec -= 10
                    cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (engine_tick, "Crime", f"Terrorist explosion in {name}!", g_q, g_r))

        inventory["Survival"]["Food"] = food_stockpile
        cursor.execute("UPDATE settlements SET population=?, spark_born_population=?, inventory_json=?, wealth=?, security_points=?, expansion_ring=? WHERE id=?", (pop, spark_born_pop, json.dumps(inventory), wealth, sec, exp_ring, s_id))

    # --- CHAOS AGENTS LOOP ---
    cursor.execute("SELECT id, type, strength, micro_q, micro_r FROM chaos_agents WHERE global_hex_id=? AND is_active=1", (global_hex_id,))
    for agent in cursor.fetchall():
        a_id, a_type, a_str, a_q, a_r = agent
        if a_type == "Cultist":
            # Just log since latent_chaos doesn't exist explicitly in micro_hexes table structure
            cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (engine_tick, "Chaos", f"Cultists are increasing Latent Chaos at {a_q},{a_r}!", g_q, g_r))
        elif a_type == "Warden":
            cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (engine_tick, "Chaos", f"Wardens are purging Latent Chaos at {a_q},{a_r}!", g_q, g_r))

    # Save micro hexes back to JSON
    new_json = pack_micro_cluster(micro_hexes)

    # Update global pack_ecology
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
