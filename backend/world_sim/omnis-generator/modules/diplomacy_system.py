# diplomacy_system.py
# Inter-faction diplomacy, war, trade agreements, and espionage for Ostraka.
import random

# ===========================
# CULTURAL SIMILARITY MATRIX
# ===========================
# Factions that share cultural kinship get a relations bonus
CULTURAL_KINSHIP = {
    ("Ursine Hegemony", "East Hounds"): 15,
    ("Ursine Hegemony", "Sylvian"): 10,
    ("River Folk", "Meridian Chain"): 20,
    ("River Folk", "Canopy Clans"): 5,
    ("Sump-Kin", "Guirrilla Clans"): 10,
    ("Iron Caladrea", "Sciute"): 15,
    ("Iron Caladrea", "Vaneer Concord"): 10,
    ("Vaneer Concord", "Hive Collective"): 10,
    ("Hive Collective", "Avians"): 5,
    ("Flower Valwey", "Sylvian"): 20,
    ("Canopy Clans", "Sylvian"): 15,
    ("Theocracy", "The Reliance"): -20,  # religious vs secular scholars
    ("Prism Lizards", "Meridian Chain"): 10,
    ("East Hounds", "Guirrilla Clans"): 10,
}

# ===========================
# ADJACENCY (from rules_engine)
# ===========================
FACTION_ADJACENCY = {
    "Ursine Hegemony": ["Sylvian", "East Hounds", "Flower Valwey", "Iron Caladrea"],
    "River Folk": ["Guirrilla Clans", "Vaneer Concord", "Meridian Chain", "Avians"],
    "Sump-Kin": ["Guirrilla Clans", "Iron Caladrea", "The Reliance", "Canopy Clans"],
    "Iron Caladrea": ["Ursine Hegemony", "Sump-Kin", "Vaneer Concord", "Sciute"],
    "Vaneer Concord": ["River Folk", "Iron Caladrea", "Hive Collective", "Prism Lizards"],
    "Hive Collective": ["Vaneer Concord", "Avians", "Prism Lizards", "Theocracy"],
    "Avians": ["River Folk", "Hive Collective", "Meridian Chain", "Theocracy"],
    "Flower Valwey": ["Ursine Hegemony", "Sylvian", "Sciute", "East Hounds"],
    "Sylvian": ["Ursine Hegemony", "Flower Valwey", "Sciute", "East Hounds"],
    "Sciute": ["Iron Caladrea", "Flower Valwey", "Sylvian", "Prism Lizards"],
    "Meridian Chain": ["River Folk", "Avians", "Prism Lizards", "Theocracy"],
    "Prism Lizards": ["Vaneer Concord", "Hive Collective", "Sciute", "Meridian Chain", "Canopy Clans"],
    "Canopy Clans": ["Sump-Kin", "Prism Lizards", "East Hounds", "Guirrilla Clans"],
    "East Hounds": ["Ursine Hegemony", "Flower Valwey", "Sylvian", "Canopy Clans"],
    "Guirrilla Clans": ["River Folk", "Sump-Kin", "Canopy Clans", "The Reliance"],
    "Theocracy": ["Hive Collective", "Avians", "Meridian Chain", "The Reliance"],
    "The Reliance": ["Sump-Kin", "Guirrilla Clans", "Theocracy"],
}

ALL_FACTIONS = list(FACTION_ADJACENCY.keys())

# ===========================
# DIPLOMATIC STATUS THRESHOLDS
# ===========================
def get_diplomatic_status(score):
    """Returns the diplomatic status string for a given relation score."""
    if score >= 70:
        return "Allied"
    elif score >= 30:
        return "Friendly"
    elif score >= -30:
        return "Neutral"
    elif score >= -70:
        return "Hostile"
    else:
        return "At War"

# ===========================
# INITIALIZE RELATIONS
# ===========================
def initialize_diplomacy():
    """Creates the initial diplomatic relations matrix between all 17 factions."""
    relations = {}
    active_wars = []
    active_treaties = []
    trade_agreements = []
    alliances = []

    for i, f1 in enumerate(ALL_FACTIONS):
        for f2 in ALL_FACTIONS[i+1:]:
            # Base relation: 0 (neutral)
            base = 0

            # Adjacent factions start slightly wary
            if f2 in FACTION_ADJACENCY.get(f1, []):
                base = random.randint(-15, 15)

            # Apply cultural kinship
            kinship = CULTURAL_KINSHIP.get((f1, f2), CULTURAL_KINSHIP.get((f2, f1), 0))
            base += kinship

            # Clamp to range
            base = max(-100, min(100, base))

            key = tuple(sorted([f1, f2]))
            relations[key] = base

    return {
        "relations": relations,
        "active_wars": active_wars,
        "active_treaties": active_treaties,
        "trade_agreements": trade_agreements,
        "alliances": alliances,
        "war_exhaustion": {},  # faction_name -> exhaustion value
        "espionage_cooldowns": {},  # (attacker, target) -> cooldown ticks remaining
    }

def get_relation(diplomacy, f1, f2):
    """Get the relation score between two factions."""
    key = tuple(sorted([f1, f2]))
    return diplomacy["relations"].get(key, 0)

def modify_relation(diplomacy, f1, f2, delta):
    """Modify the relation between two factions."""
    key = tuple(sorted([f1, f2]))
    current = diplomacy["relations"].get(key, 0)
    diplomacy["relations"][key] = max(-100, min(100, current + delta))

# ===========================
# MILITARY STRENGTH CALCULATION
# ===========================
def calculate_military_strength(group):
    """Calculates a faction's total military strength from population, buildings, resources, and paragon."""
    pop = group.get("population", 1000.0)
    barracks = group.get("barracks_count", 0)
    walls = group.get("walls_count", 0)
    watchtowers = group.get("watchtowers_count", 0)

    # Get inventory from group or separate dict
    inv = group.get("inventory", {})
    weapons = inv.get("Basic Weapons", 0.0)
    steel = inv.get("Smelted Steel", 0.0)
    armor = inv.get("Leather Armor", 0.0)

    # Base military from population (soldiers are ~5% of pop)
    base_military = pop * 0.05

    # Building bonuses
    building_bonus = barracks * 50.0 + walls * 30.0 + watchtowers * 20.0

    # Equipment bonus
    equip_bonus = weapons * 5.0 + steel * 2.0 + armor * 3.0

    # Kennel (trained wolves) bonus
    kennel_bonus = group.get("domestic_kennels", 0) * 25.0
    horse_bonus = group.get("domestic_horse_stables", 0) * 40.0

    # Paragon leadership bonus
    paragon = group.get("paragon")
    leader_bonus = 0.0
    if paragon:
        stats = paragon.get("stats", {})
        leader_bonus = (stats.get("Might", 10) + stats.get("Endurance", 10) + stats.get("Fortitude", 10)) * 3.0
        alignment = paragon.get("alignment", "Pragmatic")
        if alignment == "Heroic":
            leader_bonus *= 1.3  # Heroic leaders inspire troops
        elif alignment == "Villainous":
            leader_bonus *= 1.1  # Villainous leaders are ruthless but demoralizing

    return base_military + building_bonus + equip_bonus + kennel_bonus + horse_bonus + leader_bonus

# ===========================
# WAR PROCESSING
# ===========================
def process_war_tick(diplomacy, groups_by_name, logs):
    """Processes active wars: resource drain, casualties, morale damage."""
    wars_to_end = []

    for war in diplomacy["active_wars"]:
        f1_name = war["attacker"]
        f2_name = war["defender"]

        g1 = groups_by_name.get(f1_name)
        g2 = groups_by_name.get(f2_name)
        if not g1 or not g2:
            wars_to_end.append(war)
            continue

        # Calculate military strengths
        str1 = calculate_military_strength(g1)
        str2 = calculate_military_strength(g2)

        # Determine battle outcome (probabilistic)
        total = str1 + str2
        if total == 0:
            continue

        win_chance_1 = str1 / total
        attacker_wins = random.random() < win_chance_1

        # Both sides suffer casualties and resource drain regardless
        # Population casualties (2-5% of military force)
        cas_rate_1 = random.uniform(0.02, 0.05) * (1.0 if attacker_wins else 1.5)
        cas_rate_2 = random.uniform(0.02, 0.05) * (1.5 if attacker_wins else 1.0)

        cas_1 = int(g1["population"] * cas_rate_1 * 0.05)
        cas_2 = int(g2["population"] * cas_rate_2 * 0.05)

        g1["population"] = max(100.0, g1["population"] - cas_1)
        g2["population"] = max(100.0, g2["population"] - cas_2)

        # Resource drain (war supplies)
        for g in [g1, g2]:
            inv = g.get("inventory", {})
            inv["Grain"] = max(0.0, inv.get("Grain", 0.0) - 10.0)
            inv["Lumber"] = max(0.0, inv.get("Lumber", 0.0) - 5.0)
            inv["Smelted Steel"] = max(0.0, inv.get("Smelted Steel", 0.0) - 2.0)

        # Morale damage
        g1["discontent"] = min(1.0, g1.get("discontent", 0.0) + 0.05)
        g2["discontent"] = min(1.0, g2.get("discontent", 0.0) + 0.05)

        # War exhaustion
        diplomacy["war_exhaustion"][f1_name] = diplomacy["war_exhaustion"].get(f1_name, 0.0) + 0.15
        diplomacy["war_exhaustion"][f2_name] = diplomacy["war_exhaustion"].get(f2_name, 0.0) + 0.15

        if attacker_wins:
            logs.append(f"⚔️ WAR BATTLE: {f1_name} won a battle against {f2_name}! ({f1_name} lost {cas_1}, {f2_name} lost {cas_2} soldiers)")
            modify_relation(diplomacy, f1_name, f2_name, -5)
        else:
            logs.append(f"⚔️ WAR BATTLE: {f2_name} repelled an attack from {f1_name}! ({f1_name} lost {cas_1}, {f2_name} lost {cas_2} soldiers)")
            modify_relation(diplomacy, f1_name, f2_name, -3)

        # Check for peace due to exhaustion
        exh1 = diplomacy["war_exhaustion"].get(f1_name, 0.0)
        exh2 = diplomacy["war_exhaustion"].get(f2_name, 0.0)

        if exh1 > 1.0 or exh2 > 1.0:
            # War exhaustion triggers peace negotiations
            if random.random() < 0.40:
                # Peace treaty: loser pays reparations
                loser = f1_name if exh1 > exh2 else f2_name
                winner = f2_name if loser == f1_name else f1_name
                g_loser = groups_by_name[loser]
                g_winner = groups_by_name[winner]

                # Reparations
                for res in ["Grain", "Lumber", "Stone", "Smelted Steel"]:
                    transfer = min(g_loser.get("inventory", {}).get(res, 0.0) * 0.2, 20.0)
                    g_loser["inventory"][res] = max(0.0, g_loser["inventory"].get(res, 0.0) - transfer)
                    g_winner["inventory"][res] = g_winner["inventory"].get(res, 0.0) + transfer

                wars_to_end.append(war)
                diplomacy["war_exhaustion"][f1_name] = 0.0
                diplomacy["war_exhaustion"][f2_name] = 0.0
                modify_relation(diplomacy, f1_name, f2_name, 30)  # Peace brings relations back up

                logs.append(f"🕊️ PEACE TREATY: {winner} and {loser} signed a peace treaty! {loser} pays reparations to {winner}.")
                diplomacy["active_treaties"].append({"parties": [f1_name, f2_name], "type": "peace", "duration": 10})

    # Remove ended wars
    for war in wars_to_end:
        if war in diplomacy["active_wars"]:
            diplomacy["active_wars"].remove(war)

# ===========================
# DIPLOMACY TICK
# ===========================
def process_diplomacy_tick(diplomacy, groups_by_name, logs):
    """
    Main diplomacy processing per world tick.
    Handles relation drift, trade, alliances, war declarations, espionage.
    """
    faction_names = list(groups_by_name.keys())

    # =====================
    # 1. NATURAL RELATION DRIFT
    # =====================
    for i, f1 in enumerate(faction_names):
        for f2 in faction_names[i+1:]:
            key = tuple(sorted([f1, f2]))
            current = diplomacy["relations"].get(key, 0)

            # Relations drift toward 0 (neutral) slowly
            if current > 0:
                diplomacy["relations"][key] = max(0, current - 1)
            elif current < 0:
                diplomacy["relations"][key] = min(0, current + 1)

    # =====================
    # 2. TRADE AGREEMENTS
    # =====================
    for agreement in list(diplomacy["trade_agreements"]):
        f1, f2 = agreement["parties"]
        g1 = groups_by_name.get(f1)
        g2 = groups_by_name.get(f2)
        if not g1 or not g2:
            continue

        # Trade generates small mutual resource benefit
        for res in ["Grain", "Lumber", "Stone"]:
            g1_inv = g1.get("inventory", {})
            g2_inv = g2.get("inventory", {})
            if g1_inv.get(res, 0.0) > 20.0 and g2_inv.get(res, 0.0) < 15.0:
                transfer = min(5.0, g1_inv[res] * 0.05)
                g1_inv[res] -= transfer
                g2_inv[res] = g2_inv.get(res, 0.0) + transfer
            elif g2_inv.get(res, 0.0) > 20.0 and g1_inv.get(res, 0.0) < 15.0:
                transfer = min(5.0, g2_inv[res] * 0.05)
                g2_inv[res] -= transfer
                g1_inv[res] = g1_inv.get(res, 0.0) + transfer

        # Trade boosts relations slightly
        modify_relation(diplomacy, f1, f2, 1)

        # Duration countdown
        agreement["duration"] = agreement.get("duration", 10) - 1
        if agreement["duration"] <= 0:
            diplomacy["trade_agreements"].remove(agreement)
            logs.append(f"📜 DIPLOMACY: Trade agreement between {f1} and {f2} expired.")

    # =====================
    # 3. ALLIANCE BENEFITS
    # =====================
    for alliance in list(diplomacy["alliances"]):
        f1, f2 = alliance["parties"]
        g1 = groups_by_name.get(f1)
        g2 = groups_by_name.get(f2)
        if not g1 or not g2:
            continue

        # Allies share military patrol coverage
        g1["crime_level"] = max(0.0, g1.get("crime_level", 0.0) - 0.02)
        g2["crime_level"] = max(0.0, g2.get("crime_level", 0.0) - 0.02)

        # Alliance boosts relations
        modify_relation(diplomacy, f1, f2, 2)

        # Break alliance if relations drop too low
        if get_relation(diplomacy, f1, f2) < 20:
            diplomacy["alliances"].remove(alliance)
            logs.append(f"💔 DIPLOMACY: Alliance between {f1} and {f2} dissolved due to deteriorating relations.")

    # =====================
    # 4. NEW DIPLOMATIC ACTIONS (random events per tick)
    # =====================
    if random.random() < 0.25:
        # Pick two adjacent factions
        f1 = random.choice(faction_names)
        adj = FACTION_ADJACENCY.get(f1, [])
        if adj:
            f2 = random.choice(adj)
            relation = get_relation(diplomacy, f1, f2)
            status = get_diplomatic_status(relation)

            g1 = groups_by_name.get(f1)
            g2 = groups_by_name.get(f2)
            if not g1 or not g2:
                pass
            else:
                # Paragon-driven diplomacy
                p1 = g1.get("paragon")
                p1_align = p1.get("alignment", "Pragmatic") if p1 else "Pragmatic"
                p1_charm = p1.get("stats", {}).get("Charm", 10) if p1 else 10

                # --- TRADE AGREEMENT ---
                if status in ["Friendly", "Neutral"] and relation > 10:
                    existing = [a for a in diplomacy["trade_agreements"]
                               if set(a["parties"]) == {f1, f2}]
                    if not existing and random.random() < 0.30:
                        diplomacy["trade_agreements"].append({"parties": [f1, f2], "type": "trade", "duration": 8})
                        modify_relation(diplomacy, f1, f2, 10)
                        logs.append(f"🤝 DIPLOMACY: {f1} and {f2} established a Trade Agreement!")

                # --- ALLIANCE ---
                elif status == "Allied" and relation >= 70:
                    existing = [a for a in diplomacy["alliances"]
                               if set(a["parties"]) == {f1, f2}]
                    if not existing and random.random() < 0.20:
                        diplomacy["alliances"].append({"parties": [f1, f2], "type": "alliance"})
                        logs.append(f"🛡️ DIPLOMACY: {f1} and {f2} formed a Military Alliance!")

                # --- WAR DECLARATION ---
                elif status == "Hostile" and relation < -50:
                    # Check not already at war
                    at_war = any(w for w in diplomacy["active_wars"]
                               if set([w["attacker"], w["defender"]]) == {f1, f2})
                    in_treaty = any(t for t in diplomacy["active_treaties"]
                                  if set(t["parties"]) == {f1, f2} and t["type"] == "peace")

                    if not at_war and not in_treaty and random.random() < 0.15:
                        # Villainous leaders more likely to declare war
                        war_chance = 0.60 if p1_align == "Villainous" else 0.30
                        if random.random() < war_chance:
                            diplomacy["active_wars"].append({"attacker": f1, "defender": f2})
                            modify_relation(diplomacy, f1, f2, -20)
                            logs.append(f"⚔️ WAR DECLARED: {f1} has declared war on {f2}!")

                # --- EMBARGO ---
                elif status == "Hostile" and relation < -30:
                    # Cancel existing trade agreements
                    for agreement in list(diplomacy["trade_agreements"]):
                        if set(agreement["parties"]) == {f1, f2}:
                            diplomacy["trade_agreements"].remove(agreement)
                            logs.append(f"🚫 EMBARGO: {f1} severed trade routes with {f2}!")

                # --- BORDER TENSION ---
                elif status == "Neutral" and random.random() < 0.15:
                    # Border incidents can shift relations
                    incident = random.choice(["border_dispute", "trade_insult", "refugee_crisis", "resource_claim"])
                    if incident == "border_dispute":
                        modify_relation(diplomacy, f1, f2, -8)
                        logs.append(f"⚠️ DIPLOMACY: Border dispute between {f1} and {f2} strained relations!")
                    elif incident == "trade_insult":
                        modify_relation(diplomacy, f1, f2, -5)
                        logs.append(f"⚠️ DIPLOMACY: A trade insult from {f1} offended {f2}!")
                    elif incident == "refugee_crisis":
                        modify_relation(diplomacy, f1, f2, random.choice([-5, 5]))
                        logs.append(f"⚠️ DIPLOMACY: Refugees fleeing chaos crossed from {f1} into {f2}!")
                    elif incident == "resource_claim":
                        modify_relation(diplomacy, f1, f2, -10)
                        logs.append(f"⚠️ DIPLOMACY: {f1} and {f2} dispute ownership of border resources!")

    # =====================
    # 5. ESPIONAGE
    # =====================
    if random.random() < 0.12:
        spy_faction = random.choice(faction_names)
        adj = FACTION_ADJACENCY.get(spy_faction, [])
        if adj:
            target_faction = random.choice(adj)
            relation = get_relation(diplomacy, spy_faction, target_faction)

            # Only spy on hostile or neutral factions
            if relation < 20:
                g_spy = groups_by_name.get(spy_faction)
                g_target = groups_by_name.get(target_faction)

                if g_spy and g_target:
                    # Check cooldown
                    cooldown_key = (spy_faction, target_faction)
                    if diplomacy["espionage_cooldowns"].get(cooldown_key, 0) > 0:
                        diplomacy["espionage_cooldowns"][cooldown_key] -= 1
                    else:
                        p_spy = g_spy.get("paragon")
                        p_target = g_target.get("paragon")

                        # Spy effectiveness
                        spy_skill = 50.0
                        if p_spy:
                            spy_stats = p_spy.get("stats", {})
                            spy_skill += spy_stats.get("Awareness", 10) + spy_stats.get("Intuition", 10) + spy_stats.get("Finesse", 10)

                        # Counter-espionage
                        counter_skill = 30.0 + g_target.get("security_rating", 0.0) * 50.0
                        if p_target:
                            t_stats = p_target.get("stats", {})
                            counter_skill += t_stats.get("Logic", 10) + t_stats.get("Awareness", 10)

                        # Add messenger birds bonus to counter
                        counter_skill += g_target.get("tool_messenger_bonus", 0) * 15.0

                        success_chance = spy_skill / (spy_skill + counter_skill)

                        if random.random() < success_chance:
                            # Espionage succeeds
                            action = random.choice(["steal_resources", "sabotage", "plant_cultists", "assassinate"])

                            if action == "steal_resources":
                                res = random.choice(["Grain", "Lumber", "Stone", "Smelted Steel", "Dragonstone"])
                                amount = min(g_target["inventory"].get(res, 0.0) * 0.1, 10.0)
                                if amount > 0:
                                    g_target["inventory"][res] = max(0.0, g_target["inventory"][res] - amount)
                                    g_spy["inventory"][res] = g_spy["inventory"].get(res, 0.0) + amount
                                    logs.append(f"🕵️ ESPIONAGE: {spy_faction} agents stole {amount:.0f} {res} from {target_faction}!")
                                    modify_relation(diplomacy, spy_faction, target_faction, -8)

                            elif action == "sabotage":
                                targets = ["farms_count", "watchtowers_count", "mines_count", "docks_count"]
                                for bld in targets:
                                    if g_target.get(bld, 0) > 0:
                                        g_target[bld] = max(0, g_target[bld] - 1)
                                        bld_name = bld.replace("_count", "").title()
                                        logs.append(f"🕵️ ESPIONAGE: {spy_faction} agents sabotaged a {bld_name} in {target_faction}!")
                                        modify_relation(diplomacy, spy_faction, target_faction, -12)
                                        break

                            elif action == "plant_cultists":
                                planted = int(g_target.get("population", 1000.0) * 0.005)
                                g_target["cult_population"] = g_target.get("cult_population", 0.0) + planted
                                g_target["cult_infiltration"] = g_target["cult_population"] / max(1.0, g_target.get("population", 1000.0))
                                logs.append(f"🕵️ ESPIONAGE: {spy_faction} agents planted {planted} chaos cultist cells in {target_faction}!")
                                modify_relation(diplomacy, spy_faction, target_faction, -15)

                            elif action == "assassinate":
                                if p_target and random.random() < 0.25:
                                    # Assassination attempt
                                    target_fort = p_target.get("stats", {}).get("Fortitude", 10)
                                    if random.random() > target_fort / 20.0:
                                        p_target["stats"]["Vitality"] = max(0, p_target["stats"].get("Vitality", 10) - random.randint(5, 10))
                                        logs.append(f"🗡️ ASSASSINATION: {spy_faction} agents wounded {target_faction}'s leader {p_target['name']}!")
                                        modify_relation(diplomacy, spy_faction, target_faction, -25)
                                    else:
                                        logs.append(f"🛡️ ESPIONAGE FOILED: {target_faction}'s leader {p_target['name']} survived an assassination attempt from {spy_faction}!")
                                        modify_relation(diplomacy, spy_faction, target_faction, -15)

                        else:
                            # Espionage detected/foiled
                            if random.random() < 0.5:
                                logs.append(f"🛡️ COUNTER-INTEL: {target_faction} intercepted spies from {spy_faction}!")
                                modify_relation(diplomacy, spy_faction, target_faction, -10)

                        # Set cooldown
                        diplomacy["espionage_cooldowns"][cooldown_key] = random.randint(3, 8)

    # =====================
    # 6. PROCESS ACTIVE WARS
    # =====================
    process_war_tick(diplomacy, groups_by_name, logs)

    # =====================
    # 7. PEACE TREATY DURATION
    # =====================
    for treaty in list(diplomacy["active_treaties"]):
        treaty["duration"] = treaty.get("duration", 10) - 1
        if treaty["duration"] <= 0:
            diplomacy["active_treaties"].remove(treaty)
            f1, f2 = treaty["parties"]
            logs.append(f"📜 DIPLOMACY: Peace treaty between {f1} and {f2} expired.")
