import json
import sqlite3
import random
from core_engine.codec import unpack_micro_cluster, pack_micro_cluster
from core_engine.db_setup import apply_migrations

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

def process_population_phase(conn, cursor, s_id, pop, spark_born_pop, food_stockpile, wealth, sec, inventory, name, farm_production, farm_workers, f_rule, level, engine_tick, g_q, g_r):
    consume_rate = 1.0
    if f_rule == "Hearthless": consume_rate = 0.5
    elif f_rule == "Dust_Husk": consume_rate = 0.5

    general_pop = max(0, pop - farm_workers)
    baseline_food = (level - 1) * 5.0
    general_production = general_pop * 1.0
    food_stockpile += general_production + farm_production + baseline_food

    # Detailed refined food consumption and buffs
    refined_foods = ["Bread", "Steak", "Sausage", "Chuck", "Cake", "Pie", "Beer", "Wine"]
    refined_consumed = 0.0
    
    # Try to consume refined foods first for security/health/composure bonuses
    for rf in refined_foods:
        stock = inventory.setdefault("Survival", {}).get(rf, 0.0)
        if stock > 0.0:
            consume = min(stock, general_pop - refined_consumed)
            inventory["Survival"][rf] -= consume
            refined_consumed += consume
            # Refined foods buff composure and health
            inventory["Survival"]["Health"] = min(100.0, inventory["Survival"].get("Health", 100.0) + consume * 0.1)
            inventory["Survival"]["Composure"] = min(100.0, inventory["Survival"].get("Composure", 100.0) + consume * 0.1)

    # Fallback to standard/raw foods
    standard_foods = ["Grains", "Fruits", "Vegetables", "Roots", "Greens", "Red Meat", "White Meat", "Poultry"]
    standard_consumed = 0.0
    for sf in standard_foods:
        stock = inventory.setdefault("Survival", {}).get(sf, 0.0)
        if stock > 0.0:
            consume = min(stock, (general_pop - refined_consumed) - standard_consumed)
            inventory["Survival"][sf] -= consume
            standard_consumed += consume

    total_food_consumed = refined_consumed + standard_consumed
    food_needed = general_pop * consume_rate
    starvation_ticks = inventory["Survival"].get("StarvationTicks", 0)

    if total_food_consumed >= food_needed:
        if starvation_ticks > 0:
            starvation_ticks = max(0, starvation_ticks - 1)
            if starvation_ticks == 0:
                tags = inventory.setdefault("Tags", [])
                if "Rioting" in tags: tags.remove("Rioting")
                if "Anarchy" in tags: tags.remove("Anarchy")

        health = min(100.0, inventory["Survival"].get("Health", 100.0) + 2.0)
        composure = min(100.0, inventory["Survival"].get("Composure", 100.0) + 2.0)

        if inventory["Survival"].get("Health", 100.0) < 20.0 and random.random() < 0.1:
            pop = max(0, pop - 1)

        if f_rule != "Hearthless" and pop > 0:
            food_surplus = total_food_consumed - food_needed
            food_factor = max(0.0, min(1.0, food_surplus / (max(1, pop) * 0.5) + 0.1))
            wealth_factor = max(0.0, min(1.0, wealth / (max(1, pop) * 2.0)))
            security_factor = max(0.0, min(1.0, sec / 100.0))
            health_factor = max(0.0, min(1.0, health / 100.0))
            composure_factor = max(0.0, min(1.0, composure / 100.0))

            growth_mult = food_factor * wealth_factor * security_factor * health_factor * composure_factor
            pop_growth_fractional = (0.05 * pop + 0.1) * growth_mult
            
            accumulator = inventory["Survival"].setdefault("PopGrowthAccumulator", 0.0)
            accumulator += pop_growth_fractional
            new_growth = int(accumulator)
            if new_growth > 0:
                pop += new_growth
                accumulator -= new_growth
                if random.random() < 0.5:
                    spark_born_pop += new_growth
            inventory["Survival"]["PopGrowthAccumulator"] = accumulator

        wealth += 1.0
    else:
        starvation_ticks += 1
        starved = max(1, int(pop * 0.1))
        tags = inventory.setdefault("Tags", [])

        health = max(0.0, inventory["Survival"].get("Health", 100.0) - 10.0)
        composure = max(0.0, inventory["Survival"].get("Composure", 100.0) - 15.0)

        if starvation_ticks == 1:
            sec = max(0.0, sec - 10.0)
            cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)",
                           (engine_tick, "Starvation", f"{name} is experiencing critical food shortages!", g_q, g_r))
        elif starvation_ticks == 2:
            sec = max(0.0, sec - 20.0)
            wealth = max(0.0, wealth - 10.0)
            if "Rioting" not in tags:
                tags.append("Rioting")
            cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)",
                           (engine_tick, "Starvation", f"{name} is experiencing violent food riots due to famine!", g_q, g_r))
        else:
            sec = 0.0
            wealth = max(0.0, wealth - 20.0)
            if "Anarchy" not in tags:
                tags.append("Anarchy")
            if "Rioting" in tags:
                tags.remove("Rioting")
            
            pop = max(0, pop - starved)
            spark_born_pop = max(0, spark_born_pop - (starved // 2))
            cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)",
                           (engine_tick, "Starvation", f"{name} has collapsed into total anarchy! Starvation claims {starved} citizens.", g_q, g_r))

    inventory["Survival"]["Health"] = health
    inventory["Survival"]["Composure"] = composure
    inventory["Survival"]["StarvationTicks"] = starvation_ticks
    return pop, spark_born_pop, food_stockpile, wealth, sec, inventory

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
                    """, (hx.global_hex_id, target_hx.q, target_hx.r, s_id))
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
                    """, (hx.global_hex_id, target_hx.q, target_hx.r, s_id, struct_type))
                    struct_set.add((target_hx.q, target_hx.r))
                    cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, 'Construction', ?, ?, ?)", 
                                   (engine_tick, f"{name} built a new {struct_type}.", g_q, g_r))
                                   
    return wealth, inventory

def process_cluster_fidelity(engine_tick, global_hex_id, conn):
    cursor = conn.cursor()
    
    # Run active migrations to guarantee DB schema has integrity column, structure_costs, production_recipes
    apply_migrations(conn)
    
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
