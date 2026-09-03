import random

BIOME_RESOURCES = {
    0: { # Jungle
        "plants": ["Fruits", "Greens", "Spices"],
        "wood": "Hardwood",
        "stone": "Sandstone",
        "animals": {"meat": "Poultry", "mat": "Bones"}
    },
    1: { # Forest
        "plants": ["Fruits", "Greens"],
        "wood": "Hardwood",
        "stone": "River Rock",
        "animals": {"meat": "Red Meat", "mat": "Fur"}
    },
    2: { # Taiga
        "plants": ["Roots", "Greens"],
        "wood": "Softwood",
        "stone": "River Rock",
        "animals": {"meat": "Red Meat", "mat": "Fur"}
    },
    3: { # Desert
        "plants": ["Roots"],
        "wood": "Bamboo",
        "stone": "Sandstone",
        "animals": {"meat": "Red Meat", "mat": "Leather"}
    },
    4: { # Plains
        "plants": ["Grains", "Grass Fiber", "Vegetables"],
        "wood": "Softwood",
        "stone": "Flagstone",
        "animals": {"meat": "Red Meat", "mat": "Wool", "milk": 0.3, "eggs": 0.3}
    },
    5: { # Tundra
        "plants": ["Roots"],
        "wood": "Softwood",
        "stone": "Granite",
        "animals": {"meat": "White Meat", "mat": "Fur"}
    },
    6: { # Mountain
        "plants": ["Roots"],
        "wood": "Softwood",
        "stone": "Granite",
        "animals": {"meat": "Red Meat", "mat": "Wool"}
    },
    7: { # Volcano
        "plants": [],
        "wood": "Obsidian",
        "stone": "Granite",
        "animals": {"meat": "Red Meat", "mat": "Crystal"}
    },
    8: { # Arctic
        "plants": [],
        "wood": "Softwood",
        "stone": "Granite",
        "animals": {"meat": "White Meat", "mat": "Fur"}
    },
    9: { # Kelp Forest / Ocean
        "plants": ["Greens"],
        "wood": "Softwood",
        "stone": "River Rock",
        "animals": {"meat": "White Meat", "mat": "Bones"}
    },
    10: { # Coral Reef
        "plants": ["Greens"],
        "wood": "Softwood",
        "stone": "River Rock",
        "animals": {"meat": "White Meat", "mat": "Crystal"}
    },
    11: { # Arctic Ocean
        "plants": [],
        "wood": "Softwood",
        "stone": "River Rock",
        "animals": {"meat": "White Meat", "mat": "Bones"}
    },
    12: { # Abyssal Trench
        "plants": [],
        "wood": "Softwood",
        "stone": "Granite",
        "animals": {"meat": "White Meat", "mat": "Crystal"}
    },
    13: { # Waste
        "plants": ["Roots"],
        "wood": "Softwood",
        "stone": "Flagstone",
        "animals": {"meat": "Red Meat", "mat": "Bones"}
    }
}

def process_maintenance_phase(conn, cursor, s_id, wealth, inventory, name, engine_tick, g_q, g_r):
    # Iterate all structures owned by this settlement
    cursor.execute("SELECT id, structure_type, level, maintenance_cost, integrity FROM farms WHERE settlement_id=?", (s_id,))
    farms = cursor.fetchall()
    
    for f_id, s_type, s_level, base_maint, integrity in farms:
        if s_type is None:
            s_type = 'Farm'
        if integrity is None:
            integrity = 100.0
            
        # Get upkeep from structure_costs table
        cursor.execute("SELECT upkeep_wealth FROM structure_costs WHERE type=? AND level=?", (s_type, s_level))
        cost_row = cursor.fetchone()
        upkeep = cost_row[0] if cost_row else base_maint
        
        if wealth >= upkeep:
            wealth -= upkeep
            integrity = min(100.0, integrity + 5.0)
            cursor.execute("UPDATE farms SET integrity=? WHERE id=?", (integrity, f_id))
        else:
            integrity = max(0.0, integrity - 5.0)
            if integrity <= 0.0:
                cursor.execute("DELETE FROM farms WHERE id=?", (f_id,))
                cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, 'Construction', ?, ?, ?)",
                               (engine_tick, f"{name} demolished their {s_type} due to lack of maintenance.", g_q, g_r))
            else:
                cursor.execute("UPDATE farms SET integrity=? WHERE id=?", (integrity, f_id))
                
    return wealth, inventory

def process_production_phase(conn, cursor, s_id, working_pop, food_stockpile, wealth, inventory, name, reachable, rare_type, f_rule, cap_id, exp_ring, struct_set):
    farm_workers = 0
    farm_production = 0.0
    
    def get_dist(hq, hr):
        return (abs(hq) + abs(hr) + abs(-hq-hr)) // 2

    # Gather Phase
    for hx in reachable:
        if working_pop <= 0: break

        is_footprint = False
        if cap_id is None:
            dist_center = get_dist(hx.q, hx.r)
            if dist_center <= 1:
                is_footprint = True
            elif exp_ring >= 3 and dist_center >= 3:
                is_footprint = True

        if is_footprint:
            working_pop -= 1
            # Basic wild gathering yields dynamic biomes plants/water
            biome_id = hx.biome_id if hx.biome_id is not None else 13
            b_info = BIOME_RESOURCES.get(biome_id, BIOME_RESOURCES[13])
            
            p_opts = b_info["plants"]
            if p_opts:
                p_res = random.choice(p_opts)
                inventory.setdefault("Survival", {})[p_res] = inventory.setdefault("Survival", {}).get(p_res, 0.0) + 1.0
            else:
                inventory.setdefault("Survival", {})["Water"] = inventory.setdefault("Survival", {}).get("Water", 0.0) + 1.0
            wealth += 1.0
            continue

        cursor.execute("SELECT id, output_rate, level, structure_type, integrity FROM farms WHERE global_hex_id=? AND micro_q=? AND micro_r=?", (hx.global_hex_id, hx.q, hx.r))
        farm = cursor.fetchone()

        assign = min(50, working_pop)

        if farm:
            f_id, out_rate, s_level, s_type, integrity = farm
            if s_type is None:
                s_type = 'Farm'
            if integrity is None:
                integrity = 100.0

            efficiency_mult = s_level * 2.0
            cost_mult = 0.5
            output = assign * out_rate * efficiency_mult * (integrity / 100.0)

            biome_id = hx.biome_id if hx.biome_id is not None else 13
            b_info = BIOME_RESOURCES.get(biome_id, BIOME_RESOURCES[13])

            if s_type == 'Farm':
                working_pop -= assign
                farm_workers += assign
                
                if f_rule == "Heartland_Alliance" and hx.biome_id == 4:
                    out_rate *= 3.0
                    output = assign * out_rate * efficiency_mult * (integrity / 100.0)

                # Farms produce specific crops depending on biome
                p_opts = b_info["plants"]
                if p_opts:
                    p_res = random.choice(p_opts)
                    inventory.setdefault("Survival", {})[p_res] = inventory.setdefault("Survival", {}).get(p_res, 0.0) + output
                else:
                    inventory.setdefault("Survival", {})["Grains"] = inventory.setdefault("Survival", {}).get("Grains", 0.0) + output
                
                # Animals in Plains can produce Milk or Eggs
                if biome_id == 4:
                    if random.random() < 0.3:
                        inventory.setdefault("Survival", {})["Milk"] = inventory.setdefault("Survival", {}).get("Milk", 0.0) + assign * 0.2
                    if random.random() < 0.3:
                        inventory.setdefault("Survival", {})["Eggs"] = inventory.setdefault("Survival", {}).get("Eggs", 0.0) + assign * 0.2

                depletion_cost = assign * out_rate * cost_mult
                if hx.p1 >= depletion_cost:
                    hx.p1 -= depletion_cost
                elif hx.p2 >= depletion_cost:
                    hx.p2 -= depletion_cost
                else:
                    hx.p3 = max(0, hx.p3 - depletion_cost)
            else:
                working_pop -= assign

                if hx.res <= 0:
                    hx.res = 100

                # Harvest rare resource if present in the deposit
                if rare_type and random.random() < 0.3:
                    if rare_type == "Mithril":
                        inventory.setdefault("Materials", {})["Mithril"] = inventory.setdefault("Materials", {}).get("Mithril", 0.0) + assign * 0.2
                    elif rare_type == "Star-Herb":
                        inventory.setdefault("Reagents", {})["Star-Herb"] = inventory.setdefault("Reagents", {}).get("Star-Herb", 0.0) + assign * 0.2

                if s_type == 'ReagentFarm':
                    depletion_cost = min(hx.p1, assign * out_rate * cost_mult)
                    hx.p1 -= depletion_cost
                    inventory.setdefault("Reagents", {})["Herbs"] = inventory.setdefault("Reagents", {}).get("Herbs", 0.0) + output
                elif s_type == 'MaterialFarm':
                    depletion_cost = assign * out_rate * cost_mult
                    if hx.p2 >= depletion_cost:
                        hx.p2 -= depletion_cost
                    elif hx.p3 >= depletion_cost:
                        hx.p3 -= depletion_cost
                    else:
                        tot = hx.p2 + hx.p3
                        hx.p2 = 0
                        hx.p3 = max(0, hx.p3 - (depletion_cost - tot))
                        
                    mat_type = b_info["animals"]["mat"]
                    inventory.setdefault("Materials", {})[mat_type] = inventory.setdefault("Materials", {}).get(mat_type, 0.0) + output
                elif s_type == 'Quarry':
                    harvest_cost = min(hx.res, assign * out_rate * cost_mult)
                    hx.res -= harvest_cost
                    stone_type = b_info["stone"]
                    inventory.setdefault("Building", {})[stone_type] = inventory.setdefault("Building", {}).get(stone_type, 0.0) + output
                elif s_type == 'LoggingCamp':
                    harvest_cost = min(hx.res, assign * out_rate * cost_mult)
                    hx.res -= harvest_cost
                    wood_type = b_info["wood"]
                    inventory.setdefault("Building", {})[wood_type] = inventory.setdefault("Building", {}).get(wood_type, 0.0) + output
                elif s_type == 'Mine':
                    harvest_cost = min(hx.res, assign * out_rate * cost_mult)
                    hx.res -= harvest_cost
                    inventory.setdefault("Materials", {})["Ore"] = inventory.setdefault("Materials", {}).get("Ore", 0.0) + output

        if not farm:
            assign = min(50, working_pop)
            working_pop -= assign

            if assign <= 0:
                working_pop += assign
                continue

            cursor.execute("SELECT goal, stat_vita, stat_motus, stat_lex, stat_flux FROM paragons WHERE settlement_id=?", (s_id,))
            paragon = cursor.fetchone()
            goal = paragon[0] if paragon else "Survive"
            s_vita = paragon[1] if paragon else 1
            s_motus = paragon[2] if paragon else 1
            s_flux = paragon[4] if paragon else 1

            biome_id = hx.biome_id if hx.biome_id is not None else 13
            b_info = BIOME_RESOURCES.get(biome_id, BIOME_RESOURCES[13])

            # Harvest rare resource if present on undeveloped hexes
            if rare_type and random.random() < 0.15:
                if rare_type == "Mithril":
                    inventory.setdefault("Materials", {})["Mithril"] = inventory.setdefault("Materials", {}).get("Mithril", 0.0) + assign * 0.1
                elif rare_type == "Star-Herb":
                    inventory.setdefault("Reagents", {})["Star-Herb"] = inventory.setdefault("Reagents", {}).get("Star-Herb", 0.0) + assign * 0.1

            if goal == "Survive" or s_vita > 5:
                priorities = [("Plant", hx.p1), ("Prey", hx.p2), ("Predator", hx.p3)]
                harvested = False
                for p_type, amount in priorities:
                    if amount >= 1:
                        harvest = min(amount, assign)
                        if p_type in ["Predator", "Prey"]:
                            if p_type == "Prey": hx.p2 -= harvest
                            else: hx.p3 -= harvest
                            meat_type = b_info["animals"]["meat"]
                            inventory.setdefault("Survival", {})[meat_type] = inventory.setdefault("Survival", {}).get(meat_type, 0.0) + harvest * 0.8
                            wealth += harvest * 0.2
                        elif p_type == "Plant":
                            hx.p1 -= harvest
                            p_opts = b_info["plants"]
                            if p_opts:
                                p_res = random.choice(p_opts)
                                inventory.setdefault("Survival", {})[p_res] = inventory.setdefault("Survival", {}).get(p_res, 0.0) + harvest * 0.9
                            else:
                                inventory.setdefault("Survival", {})["Water"] = inventory.setdefault("Survival", {}).get("Water", 0.0) + harvest * 0.9
                            wealth += harvest * 0.1
                        harvested = True
                        break
            elif goal == "Hoard Wealth" or s_flux > 5:
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
                            mat_type = b_info["animals"]["mat"]
                            inventory.setdefault("Materials", {})[mat_type] = inventory.setdefault("Materials", {}).get(mat_type, 0.0) + harvest * 0.5
                            wealth += harvest * 0.2
                        harvested = True
                        break
            else:
                if hx.res <= 0:
                    hx.res = 50
                
                harvest = min(hx.res, assign)
                if harvest > 0:
                    hx.res -= harvest
                    if hx.biome_id in [6, 7]:
                        stone_type = b_info["stone"]
                        inventory.setdefault("Building", {})[stone_type] = inventory.setdefault("Building", {}).get(stone_type, 0.0) + harvest * 1.0
                        hx.elevation -= 0.01 * harvest
                        wealth += harvest * 0.2
                    elif hx.biome_id in [1, 2]:
                        wood_type = b_info["wood"]
                        inventory.setdefault("Building", {})[wood_type] = inventory.setdefault("Building", {}).get(wood_type, 0.0) + harvest * 1.0
                        hx.biome_id = 3
                        wealth += harvest * 0.2
                    else:
                        inventory.setdefault("Building", {})["Clay"] = inventory.setdefault("Building", {}).get("Clay", 0.0) + harvest * 1.0
                        wealth += harvest * 0.1
                inventory.setdefault("Survival", {})["Water"] = inventory.setdefault("Survival", {}).get("Water", 0.0) + assign * 0.2

        if f_rule == "River_Folk" and hx.biome_id in [9, 11]:
            inventory.setdefault("Survival", {})["White Meat"] = inventory.setdefault("Survival", {}).get("White Meat", 0.0) + assign * 0.5
            wealth += assign * 0.5

    # Process internal production buildings inside the settlement/farms
    cursor.execute("SELECT type, level, associated_farm_id FROM buildings WHERE settlement_id=?", (s_id,))
    buildings = cursor.fetchall()
    
    for b_type, b_level, assoc_farm in buildings:
        # 1. Mill processing
        if b_type == 'Mill':
            grains = inventory.setdefault("Survival", {}).get("Grains", 0.0)
            if grains >= 1.0:
                take = int(grains)
                inventory["Survival"]["Grains"] -= take
                inventory.setdefault("Survival", {})["Flour"] = inventory.setdefault("Survival", {}).get("Flour", 0.0) + (take * 2.0 * b_level)
            
            veg = inventory.setdefault("Survival", {}).get("Vegetables", 0.0)
            if veg >= 2.0:
                take_v = int(veg // 2) * 2
                inventory["Survival"]["Vegetables"] -= take_v
                inventory.setdefault("Survival", {})["Oil"] = inventory.setdefault("Survival", {}).get("Oil", 0.0) + (take_v * 0.5 * b_level)

        # 2. Brewery processing
        elif b_type == 'Brewery':
            flour = inventory.setdefault("Survival", {}).get("Flour", 0.0)
            water = inventory.setdefault("Survival", {}).get("Water", 0.0)
            if flour >= 1.0 and water >= 1.0:
                take = int(min(flour, water))
                inventory["Survival"]["Flour"] -= take
                inventory["Survival"]["Water"] -= take
                inventory.setdefault("Survival", {})["Beer"] = inventory.setdefault("Survival", {}).get("Beer", 0.0) + (take * 2.0 * b_level)

            fruits = inventory.setdefault("Survival", {}).get("Fruits", 0.0)
            if fruits >= 1.0:
                take = int(fruits)
                inventory["Survival"]["Fruits"] -= take
                inventory.setdefault("Survival", {})["Wine"] = inventory.setdefault("Survival", {}).get("Wine", 0.0) + (take * 2.0 * b_level)

        # 3. Butcher processing
        elif b_type == 'Butcher':
            red = inventory.setdefault("Survival", {}).get("Red Meat", 0.0)
            if red >= 1.0:
                take = int(red)
                inventory["Survival"]["Red Meat"] -= take
                # Produce Steaks and Chucks
                inventory.setdefault("Survival", {})["Steak"] = inventory.setdefault("Survival", {}).get("Steak", 0.0) + (take * 1.0 * b_level)
                inventory.setdefault("Survival", {})["Chuck"] = inventory.setdefault("Survival", {}).get("Chuck", 0.0) + (take * 1.0 * b_level)

            white = inventory.setdefault("Survival", {}).get("White Meat", 0.0)
            if white >= 1.0:
                take = int(white)
                inventory["Survival"]["White Meat"] -= take
                inventory.setdefault("Survival", {})["Sausage"] = inventory.setdefault("Survival", {}).get("Sausage", 0.0) + (take * 2.0 * b_level)

        # 4. Bakery processing
        elif b_type == 'Bakery':
            flour = inventory.setdefault("Survival", {}).get("Flour", 0.0)
            eggs = inventory.setdefault("Survival", {}).get("Eggs", 0.0)
            milk = inventory.setdefault("Survival", {}).get("Milk", 0.0)
            spices = inventory.setdefault("Survival", {}).get("Spices", 0.0)
            if flour >= 1.0 and eggs >= 1.0 and milk >= 1.0 and spices >= 1.0:
                take = int(min(flour, eggs, milk, spices))
                inventory["Survival"]["Flour"] -= take
                inventory["Survival"]["Eggs"] -= take
                inventory["Survival"]["Milk"] -= take
                inventory["Survival"]["Spices"] -= take
                inventory.setdefault("Survival", {})["Bread"] = inventory.setdefault("Survival", {}).get("Bread", 0.0) + (take * 4.0 * b_level)

        # 5. Smelter processing
        elif b_type == 'Smelter':
            ore = inventory.setdefault("Materials", {}).get("Ore", 0.0)
            if ore >= 2.0:
                take = int(ore // 2) * 2
                inventory["Materials"]["Ore"] -= take
                inventory.setdefault("Materials", {})["Ingot"] = inventory.setdefault("Materials", {}).get("Ingot", 0.0) + (take * 0.5 * b_level)

        # 6. Forge processing
        elif b_type == 'Forge':
            ingots = inventory.setdefault("Materials", {}).get("Ingot", 0.0)
            if ingots >= 2.0:
                take = int(ingots // 2) * 2
                inventory["Materials"]["Ingot"] -= take
                inventory.setdefault("Equipment", {})["Tools"] = inventory.setdefault("Equipment", {}).get("Tools", 0.0) + (take * 0.5 * b_level)

        # 7. Workshop processing (Planks, Bricks, Paving Stone)
        elif b_type == 'Workshop':
            hardwood = inventory.setdefault("Building", {}).get("Hardwood", 0.0)
            softwood = inventory.setdefault("Building", {}).get("Softwood", 0.0)
            wood = hardwood + softwood
            if wood >= 1.0:
                take = int(wood)
                if hardwood >= take:
                    inventory["Building"]["Hardwood"] -= take
                else:
                    inventory["Building"]["Softwood"] -= take
                inventory.setdefault("Building", {})["Planks"] = inventory.setdefault("Building", {}).get("Planks", 0.0) + (take * 2.0 * b_level)

            clay = inventory.setdefault("Building", {}).get("Clay", 0.0)
            if clay >= 1.0:
                take = int(clay)
                inventory["Building"]["Clay"] -= take
                inventory.setdefault("Building", {})["Bricks"] = inventory.setdefault("Building", {}).get("Bricks", 0.0) + (take * 2.0 * b_level)

            granite = inventory.setdefault("Building", {}).get("Granite", 0.0)
            sandstone = inventory.setdefault("Building", {}).get("Sandstone", 0.0)
            stone = granite + sandstone
            if stone >= 1.0:
                take = int(stone)
                if granite >= take:
                    inventory["Building"]["Granite"] -= take
                else:
                    inventory["Building"]["Sandstone"] -= take
                inventory.setdefault("Building", {})["Paving Stone"] = inventory.setdefault("Building", {}).get("Paving Stone", 0.0) + (take * 2.0 * b_level)

        # 8. Apothecary processing
        elif b_type == 'Apothecary':
            herbs = inventory.setdefault("Reagents", {}).get("Herbs", 0.0)
            star = inventory.setdefault("Reagents", {}).get("Star-Herb", 0.0)
            if herbs >= 2.0 and star >= 0.5:
                take_h = int(herbs // 2) * 2
                take_s = take_h * 0.25
                if star >= take_s:
                    inventory["Reagents"]["Herbs"] -= take_h
                    inventory["Reagents"]["Star-Herb"] -= take_s
                    inventory.setdefault("Consumables", {})["Potions"] = inventory.setdefault("Consumables", {}).get("Potions", 0.0) + (take_h * b_level)

    return food_stockpile, wealth, inventory, working_pop, farm_production, farm_workers

def process_construction_ai_phase(conn, cursor, s_id, pop, wealth, exp_ring, inventory, name, reachable, struct_set, cap_id, engine_tick, g_q, g_r):
    cursor.execute("SELECT COUNT(*) FROM farms WHERE settlement_id=?", (s_id,))
    num_structures = cursor.fetchone()[0]

    wood_stock = inventory.setdefault("Building", {}).get("Wood", 0.0)
    clay_stock = inventory.setdefault("Building", {}).get("Clay", 0.0)

    # 30% chance to build or upgrade an internal production sub-structure instead of a raw node
    if num_structures > 0 and random.random() < 0.3:
        # Check internal structures count inside the settlement
        cursor.execute("SELECT COUNT(*) FROM buildings WHERE settlement_id=? AND associated_farm_id IS NULL", (s_id,))
        settlement_b_count = cursor.fetchone()[0]
        
        # Limit checking
        # Capitals/villages have 2 per level, Hubs have 1 per level
        is_hub = (cap_id is not None)
        limit = (1 if is_hub else 2) * exp_ring # Using exp_ring as settlement level proxy
        if limit <= 0: limit = 1
        
        if settlement_b_count < limit:
            # Build an internal building (Bakery, Brewery, Butcher, etc.)
            possible_b = ['Bakery', 'Brewery', 'Butcher', 'Mill', 'Smelter', 'Forge', 'Workshop', 'Apothecary']
            target_b = random.choice(possible_b)
            
            cursor.execute("SELECT wood_cost, clay_cost FROM structure_costs WHERE type=? AND level=1", (target_b,))
            cost_row = cursor.fetchone()
            w_cost, c_cost = cost_row if cost_row else (150, 150)
            
            if wood_stock >= w_cost and clay_stock >= c_cost and wealth >= 100:
                inventory["Building"]["Wood"] -= w_cost
                inventory["Building"]["Clay"] -= c_cost
                wealth -= 100
                cursor.execute("""
                    INSERT INTO buildings (settlement_id, type, level, associated_farm_id)
                    VALUES (?, ?, 1, NULL)
                """, (s_id, target_b))
                cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, 'Construction', ?, ?, ?)", 
                               (engine_tick, f"{name} built a new internal {target_b} sub-structure.", g_q, g_r))

    elif pop >= (num_structures + 1) * 15:
        undeveloped = []
        
        def get_dist(hq, hr):
            return (abs(hq) + abs(hr) + abs(-hq-hr)) // 2

        for hx in reachable:
            is_footprint = False
            if cap_id is None:
                dist_center = get_dist(hx.q, hx.r)
                if dist_center <= 1:
                    is_footprint = True
                elif exp_ring >= 3 and dist_center >= 3:
                    is_footprint = True
            if not is_footprint and (hx.q, hx.r) not in struct_set:
                undeveloped.append(hx)

        if undeveloped:
            target_hx = undeveloped[0]
            food_stockpile = inventory.setdefault("Survival", {}).get("Food", 0.0)

            if food_stockpile < pop * 5:
                # Lookup cost to build Farm lvl 1
                cursor.execute("SELECT wood_cost, clay_cost FROM structure_costs WHERE type='Farm' AND level=1")
                cost_row = cursor.fetchone()
                w_cost, c_cost = cost_row if cost_row else (50, 50)
                
                if wood_stock >= w_cost and clay_stock >= c_cost and wealth >= 50:
                    inventory["Building"]["Wood"] -= w_cost
                    inventory["Building"]["Clay"] -= c_cost
                    wealth -= 50
                    cursor.execute("""
                        INSERT INTO farms (global_hex_id, micro_q, micro_r, settlement_id, output_rate, maintenance_cost, level, structure_type, integrity)
                        VALUES (?, ?, ?, ?, 3.0, 1.0, 1, 'Farm', 100.0)
                    """, (target_hx.global_hex_id, target_hx.q, target_hx.r, s_id))
                    struct_set.add((target_hx.q, target_hx.r))
                    cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, 'Construction', ?, ?, ?)", 
                                   (engine_tick, f"{name} built a new Farm.", g_q, g_r))
            else:
                if target_hx.biome_id in [6, 7]:
                    struct_type = 'Quarry'
                elif target_hx.biome_id in [1, 2]:
                    struct_type = 'LoggingCamp'
                else:
                    struct_type = 'Mine'
                    
                # Lookup cost to build Quarry/Mine/LoggingCamp lvl 1
                cursor.execute("SELECT wood_cost, clay_cost FROM structure_costs WHERE type=? AND level=1", (struct_type,))
                cost_row = cursor.fetchone()
                w_cost, c_cost = cost_row if cost_row else (100, 100)

                if wood_stock >= w_cost and clay_stock >= c_cost and wealth >= 100:
                    inventory["Building"]["Wood"] -= w_cost
                    inventory["Building"]["Clay"] -= c_cost
                    wealth -= 100

                    cursor.execute("""
                        INSERT INTO farms (global_hex_id, micro_q, micro_r, settlement_id, output_rate, maintenance_cost, level, structure_type, integrity)
                        VALUES (?, ?, ?, ?, 2.0, 2.0, 1, ?, 100.0)
                    """, (target_hx.global_hex_id, target_hx.q, target_hx.r, s_id, struct_type))
                    struct_set.add((target_hx.q, target_hx.r))
                    cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, 'Construction', ?, ?, ?)", 
                                   (engine_tick, f"{name} built a new {struct_type}.", g_q, g_r))
                                   
    return wealth, inventory
