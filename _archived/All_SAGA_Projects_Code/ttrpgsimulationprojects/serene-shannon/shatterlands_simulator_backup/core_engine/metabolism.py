import random
import json

def process_population_phase(conn, cursor, s_id, pop, spark_born_pop, food_stockpile, wealth, sec, inventory, name, farm_production, farm_workers, f_rule, level, engine_tick, g_q, g_r):
    consume_rate = 1.0
    if f_rule == "Hearthless": consume_rate = 0.5
    elif f_rule == "Dust_Husk": consume_rate = 0.5

    # Farm workers are no longer exempt, they must consume food too.
    general_pop = pop
    baseline_food = (level - 1) * 5.0
    # Remove automatic food generation by the general population.
    general_production = 0.0
    
    # Update food stockpile from baseline, farm production, and ensure it is non-negative.
    food_stockpile = max(0.0, food_stockpile + general_production + farm_production + baseline_food)

    # Store current food_stockpile in inventory so "Food" is available for consumption
    inventory.setdefault("Survival", {})["Food"] = food_stockpile

    # Detailed refined food consumption and buffs
    refined_foods = ["Bread", "Steak", "Sausage", "Chuck", "Cake", "Pie", "Beer", "Wine"]
    refined_consumed = 0.0
    
    # Try to consume refined foods first for security/health/composure bonuses
    for rf in refined_foods:
        stock = inventory.setdefault("Survival", {}).get(rf, 0.0)
        if stock > 0.0:
            consume = min(stock, general_pop - refined_consumed)
            inventory["Survival"][rf] = max(0.0, stock - consume)
            refined_consumed += consume
            # Refined foods buff composure and health
            inventory["Survival"]["Health"] = min(100.0, inventory["Survival"].get("Health", 100.0) + consume * 0.1)
            inventory["Survival"]["Composure"] = min(100.0, inventory["Survival"].get("Composure", 100.0) + consume * 0.1)

    # Fallback to standard/raw foods
    standard_foods = ["Grains", "Fruits", "Vegetables", "Roots", "Greens", "Red Meat", "White Meat", "Poultry", "Food"]
    standard_consumed = 0.0
    for sf in standard_foods:
        stock = inventory.setdefault("Survival", {}).get(sf, 0.0)
        if stock > 0.0:
            consume = min(stock, (general_pop - refined_consumed) - standard_consumed)
            inventory["Survival"][sf] = max(0.0, stock - consume)
            standard_consumed += consume

    total_food_consumed = refined_consumed + standard_consumed
    food_needed = general_pop * consume_rate
    starvation_ticks = inventory["Survival"].get("StarvationTicks", 0)

    # Update food_stockpile to match the remaining generic Food and ensure it is non-negative
    food_stockpile = max(0.0, inventory["Survival"].get("Food", 0.0))

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

        # Enforce level-based population caps
        cap = 150 if level == 1 else 500 if level == 2 else 1500 if level == 3 else 5000

        if f_rule != "Hearthless" and pop > 0:
            if pop < cap:
                food_surplus = total_food_consumed - food_needed
                food_factor = max(0.0, min(1.0, food_surplus / (max(1, pop) * 0.5) + 0.1))
                wealth_factor = max(0.0, min(1.0, wealth / (max(1, pop) * 2.0)))
                security_factor = max(0.0, min(1.0, sec / 100.0))
                health_factor = max(0.0, min(1.0, health / 100.0))
                composure_factor = max(0.0, min(1.0, composure / 100.0))

                growth_mult = food_factor * wealth_factor * security_factor * health_factor * composure_factor
                # Slower population growth: settlement takes approx 100 years (53,900 ticks) to max level
                pop_growth_fractional = (0.001 * pop + 0.01) * growth_mult
                
                accumulator = inventory["Survival"].setdefault("PopGrowthAccumulator", 0.0)
                accumulator += pop_growth_fractional
                new_growth = int(accumulator)
                if new_growth > 0:
                    pop = min(cap, pop + new_growth)
                    accumulator -= new_growth
                    if random.random() < 0.5:
                        spark_born_pop = min(cap, spark_born_pop + new_growth)
                inventory["Survival"]["PopGrowthAccumulator"] = accumulator
            else:
                pop = cap

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

def process_crimes(cursor):
    cursor.execute("SELECT id, name, faction_id, security_points, wealth FROM settlements")
    for row in cursor.fetchall():
        s_id, name, s_faction, sec, wealth = row[0], row[1], row[2], row[3], row[4]
        # Active crime infiltration: base 5% chance, reduced by security
        infilt_chance = 0.05 * (1.0 - (sec / 100.0))
        if random.random() < infilt_chance:
            crime_type = random.choice(["Theft", "Smuggling", "Assault"])
            severity = random.choice([1, 2, 3])
            cursor.execute(
                "INSERT INTO crimes (settlement_id, type, severity) VALUES (?,?,?)",
                (s_id, crime_type, severity)
            )
            cursor.execute(
                "UPDATE settlements SET security_points = max(0.0, security_points - 2.0) WHERE id=?",
                (s_id,)
            )
            # Smuggle siphoned wealth
            loot = min(wealth, severity * 20.0)
            cursor.execute(
                "UPDATE settlements SET wealth = max(0.0, wealth - ?) WHERE id=?",
                (loot, s_id)
            )
