import sqlite3
import random
import os
import json

def random_micro_coord():
    while True:
        mq = random.randint(-4, 4)
        mr = random.randint(-4, 4)
        if abs(mq) + abs(mr) + abs(-mq-mr) <= 8:
            return mq, mr

def generate_traits(stats):
    TRAITS_DB = {
        "Good": [
            {"name": "Brute", "req_stat": "might", "req_val": 7},
            {"name": "Genius", "req_stat": "knowledge", "req_val": 7},
            {"name": "Charismatic", "req_stat": "charm", "req_val": 7},
            {"name": "Iron Will", "req_stat": "willpower", "req_val": 7},
            {"name": "Vigilant", "req_stat": "awareness", "req_val": 7},
            {"name": "Agile", "req_stat": "reflex", "req_val": 7},
            {"name": "Stalwart", "req_stat": "endurance", "req_val": 7},
            {"name": "Nimble", "req_stat": "finesse", "req_val": 7},
            {"name": "Hardy", "req_stat": "fortitude", "req_val": 7},
            {"name": "Feral", "req_stat": "instinct", "req_val": 7},
            {"name": "Logical", "req_stat": "logic", "req_val": 7},
            {"name": "Vigorous", "req_stat": "vitality", "req_val": 7},
            {"name": "Brave", "req_stat": "willpower", "req_val": 6},
            {"name": "Kind", "req_stat": "charm", "req_val": 6},
            {"name": "Generous", "req_stat": "finesse", "req_val": 6}
        ],
        "Bad": [
            {"name": "Weak", "req_stat": "might", "req_val": 4},
            {"name": "Ignorant", "req_stat": "knowledge", "req_val": 4},
            {"name": "Abrasive", "req_stat": "charm", "req_val": 4},
            {"name": "Cowardly", "req_stat": "willpower", "req_val": 4},
            {"name": "Oblivious", "req_stat": "awareness", "req_val": 4},
            {"name": "Sluggish", "req_stat": "reflex", "req_val": 4},
            {"name": "Frail", "req_stat": "endurance", "req_val": 4},
            {"name": "Clumsy", "req_stat": "finesse", "req_val": 4},
            {"name": "Delicate", "req_stat": "fortitude", "req_val": 4},
            {"name": "Overthinker", "req_stat": "instinct", "req_val": 4},
            {"name": "Irrational", "req_stat": "logic", "req_val": 4},
            {"name": "Sickly", "req_stat": "vitality", "req_val": 4},
            {"name": "Greedy", "req_stat": "charm", "req_val": 5},
            {"name": "Vengeful", "req_stat": "willpower", "req_val": 5},
            {"name": "Paranoid", "req_stat": "awareness", "req_val": 6}
        ],
        "Neutral": [
            {"name": "Traditionalist", "req_stat": "knowledge", "req_val": 5},
            {"name": "Pragmatic", "req_stat": "logic", "req_val": 5},
            {"name": "Suspicious", "req_stat": "awareness", "req_val": 5},
            {"name": "Stubborn", "req_stat": "willpower", "req_val": 5},
            {"name": "Restless", "req_stat": "vitality", "req_val": 5},
            {"name": "Proud", "req_stat": "charm", "req_val": 5},
            {"name": "Cautious", "req_stat": "instinct", "req_val": 5},
            {"name": "Stoic", "req_stat": "fortitude", "req_val": 5},
            {"name": "Reader", "req_stat": "knowledge", "req_val": 4},
            {"name": "Insomniac", "req_stat": "endurance", "req_val": 5},
            {"name": "Pacing", "req_stat": "reflex", "req_val": 5}
        ]
    }

    assigned = {"Good": None, "Bad": None, "Neutral": []}
    
    valid_good = [t["name"] for t in TRAITS_DB["Good"] if stats[t["req_stat"]] >= t["req_val"]]
    if valid_good: assigned["Good"] = random.choice(valid_good)
    else: assigned["Good"] = "Lucky"
    
    valid_bad = [t["name"] for t in TRAITS_DB["Bad"] if stats.get(t["req_stat"], 5) <= t.get("req_val", 4)]
    if valid_bad: assigned["Bad"] = random.choice(valid_bad)
    else: assigned["Bad"] = "Unlucky"
    
    valid_neutral = [t["name"] for t in TRAITS_DB["Neutral"] if stats[t["req_stat"]] >= t["req_val"]]
    if len(valid_neutral) >= 2:
        assigned["Neutral"] = random.sample(valid_neutral, 2)
    elif len(valid_neutral) == 1:
        assigned["Neutral"] = [valid_neutral[0], "Observer"]
    else:
        assigned["Neutral"] = ["Observer", "Drifter"]
        
    return assigned

def seed_world_society(db_path=None):
    if db_path is None:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "core_engine", "world_state.db")
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create Lore Factions
    FACTIONS = [
        ("Vaneer Concord", "Vaneer_Concord"),
        ("Meridian Chain", "Meridian_Chain"),
        ("Ursine Hegemony", "Ursine_Hegemony"),
        ("Guerrilla Clans", "Guerrilla_Clans"),
        ("Canopy Clans", "Canopy_Clans"),
        ("Dust-Husk Riders", "Dust_Husk"),
        ("Eastern Hounds", "Eastern_Hounds"),
        ("Flower Valley Folk", "Flower_Valley"),
        ("Hive Commonwealth", "Hive_Commonwealth"),
        ("Prism-Scale Collective", "Prism_Scale"),
        ("Iron Caldera", "Iron_Caldera"),
        ("River Folk", "River_Folk"),
        ("Heartland Alliance", "Heartland_Alliance"),
        ("Sylvan Empire", "Sylvan_Empire"),
        ("Sumpkin", "Sumpkin"),
        ("Fulcrum Academy", "Fulcrum_Academy"),
        ("Fulcrum Bank", "Fulcrum_Bank"),
        ("Chaos Corps", "Chaos_Corps"),
        ("Storm-Lancers", "Storm_Lancers"),
        ("Cloud-Harriers", "Cloud_Harriers"),
        ("Hearthless", "Hearthless"),
        ("Seahorse Courier", "Seahorse_Courier"),
        ("Crimson Corsairs", "Crimson_Corsairs"),
        ("Free Sky-Baronies", "Sky_Baronies"),
        ("Ghostwind Raiders", "Ghostwind_Raiders"),
        ("Ghost Flotilla", "Ghost_Flotilla"),
        ("Golden Warren", "Golden_Warren"),
        ("Spring Ghosts", "Spring_Ghosts"),
        ("Reliance", "Reliance"),
        ("Scute Confederacy", "Scute_Confederacy"),
        ("Guilded Compass", "Guilded_Compass"),
        ("Obsidian Syndicate", "Obsidian_Syndicate"),
        ("Silk Syndicate", "Silk_Syndicate"),
        ("Silent Current", "Silent_Current"),
        ("Black Label", "Black_Label")
    ]
    faction_ids = []
    for fname, frule in FACTIONS:
        cursor.execute("INSERT INTO factions (name, treasury, technology_level, special_rule) VALUES (?, ?, ?, ?)", 
                       (fname, 1000.0, 5 if fname == "Order of the Clockwork" else 1, frule))
        faction_ids.append(cursor.lastrowid)

    # Create The Grey Wardens
    cursor.execute("INSERT INTO factions (name, treasury, technology_level, special_rule) VALUES (?, ?, ?, ?)", ("The Grey Wardens", 5000.0, 5, "Grey_Wardens"))
    warden_faction_id = cursor.lastrowid
    
    # Order of the Clockwork and Mandate of the Chain
    cursor.execute("INSERT INTO factions (name, treasury, technology_level, special_rule) VALUES (?, ?, ?, ?)", ("Order of the Clockwork", 5000.0, 5, "Clockwork"))
    cursor.execute("INSERT INTO factions (name, treasury, technology_level, special_rule) VALUES (?, ?, ?, ?)", ("Mandate of the Chain", 1000.0, 1, "Mandate_Chain"))

    # Create The 12 Worm Cults
    domains = ["Mass", "Ordo", "Motus", "Flux", "Vita", "Nexus", "Ratio", "Anumis", "Lux", "Omen", "Aura", "Lex"]
    cult_faction_ids = {}
    for d in domains:
        cursor.execute("INSERT INTO factions (name, treasury, special_rule) VALUES (?, ?, ?)", (f"Cult of {d}", 2000.0, "Cult"))
        cult_faction_ids[d] = cursor.lastrowid

    # Fetch Hexes
    R = 57
    inner_R = R // 2
    prisons = [
        (0, -R), (R, -R), (R, 0), (0, R), (-R, R), (-R, 0),
        (0, -inner_R), (inner_R, -inner_R), (inner_R, 0), (0, inner_R), (-inner_R, inner_R), (-inner_R, 0)
    ]
    prison_domains = {prisons[i]: domains[i] for i in range(12)}

    # Place Wardens at the Spire (0, 0)
    cursor.execute("SELECT id FROM global_hexes WHERE q=0 AND r=0")
    row = cursor.fetchone()
    if row:
        spire_hex_id = row[0]
        warden_inv = {
            "Survival": {"Food": 5000.0, "Water": 5000.0},
            "Building": {"Wood": 1000.0, "Stone": 1000.0, "Blackstone": 100.0},
            "Materials": {
                "Leather": 200.0,
                "Iron Ore": 200.0,
                "Copper Ore": 200.0,
                "Nickel Ore": 100.0,
                "Iron Ingot": 100.0,
                "Copper Ingot": 100.0,
                "Nickel Ingot": 50.0
            },
            "Equipment": {"Weapons": 50, "Sturdy Tools": 50},
            "Magic": {"Dragonstone": 100.0},
            "Warden Ranks": {"Rank 1": 100, "Rank 2": 50, "Rank 3": 20, "Rank 4": 5}
        }
        mq, mr = random_micro_coord()
        cursor.execute("""
            INSERT INTO settlements (faction_id, global_hex_id, name, population, spark_born_population, wealth, security_points, inventory_json, magic_loadout, micro_q, micro_r)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (warden_faction_id, spire_hex_id, "The Warden Spire", 175, 87, 5000.0, 100.0, json.dumps(warden_inv), json.dumps(["Ordo", "Nexus", "Lex"]), mq, mr))

    # Place the 12 Cult Prisons
    for p_coord, domain in prison_domains.items():
        cursor.execute("SELECT id FROM global_hexes WHERE q=? AND r=?", (p_coord[0], p_coord[1]))
        row = cursor.fetchone()
        if row:
            hex_id = row[0]
            faction_id = cult_faction_ids[domain]
            cult_inv = {
                "Survival": {"Food": 1000.0},
                "Building": {
                    "Wood": 300.0,
                    "Stone": 200.0,
                    "Clay": 200.0,
                    "Blackstone": 10.0
                },
                "Materials": {
                    "Leather": 20.0,
                    "Bone": 20.0,
                    "Iron Ore": 50.0,
                    "Copper Ore": 50.0,
                    "Iron Ingot": 20.0,
                    "Copper Ingot": 20.0
                },
                "Equipment": {"Weapons": 10},
                "Magic": {"Dragonstone": 5.0}
            }
            mq, mr = random_micro_coord()
            cursor.execute("""
                INSERT INTO settlements (faction_id, global_hex_id, name, population, spark_born_population, wealth, security_points, inventory_json, magic_loadout, micro_q, micro_r)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (faction_id, hex_id, f"Prison of {domain}", 50, 25, 1000.0, 50.0, json.dumps(cult_inv), json.dumps([domain, domain, domain]), mq, mr))

    # Normal Settlements
    cursor.execute("""
        SELECT id, q, r, pack_ecology FROM global_hexes 
        WHERE (pack_geo & 0xF) NOT IN (10, 11, 9)
        ORDER BY RANDOM() LIMIT 300
    """)
    habitable_hexes = cursor.fetchall()

    for i, (hex_id, q, r, pack_ecology) in enumerate(habitable_hexes):
        faction_id = faction_ids[i % len(faction_ids)]
        
        # When a settlement is built on a hex, the natural ecology is eradicated
        new_ecology = pack_ecology & 0xFF000000 
        cursor.execute("UPDATE global_hexes SET pack_ecology=? WHERE id=?", (new_ecology, hex_id))
        
        pop = random.randint(50, 200)
        
        # Modular Inventory Initial Seed - Bootstrapping budget
        inventory = {
            "Survival": {
                "Food": float(random.randint(100, 500)),
                "Water": float(random.randint(100, 500))
            },
            "Building": {
                "Wood": 300.0,
                "Stone": 200.0,
                "Clay": 200.0,
                "Blackstone": float(random.randint(0, 5))
            },
            "Materials": {
                "Leather": 20.0,
                "Bone": 20.0,
                "Iron Ore": float(random.randint(10, 50)),
                "Copper Ore": float(random.randint(10, 50)),
                "Nickel Ore": float(random.randint(5, 25)),
                "Iron Ingot": float(random.randint(5, 20)),
                "Copper Ingot": float(random.randint(5, 20)),
                "Nickel Ingot": float(random.randint(2, 10))
            },
            "Reagents": {"Oils": 5.0},
            "Magic": {
                "Dragonstone": float(random.randint(0, 2))
            }
        }
        # Calculate magic_loadout
        dists = []
        for p_coord, domain_name in prison_domains.items():
            pq, pr = p_coord
            dist = abs(q - pq) + abs(r - pr) + abs(-q-r - (-pq-pr))
            dists.append((dist, domain_name))
        dists.sort()
        magic_loadout = json.dumps([d[1] for d in dists[:3]])
        
        pop = random.randint(50, 200)
        spark_born = pop // 2
        name = f"{random.choice(['New', 'Old', 'Fort', 'Port', 'Camp', 'Lake', 'Mount', 'Deep'])} {random.choice(['Hope', 'Despair', 'Grasp', 'Reach', 'Hold', 'Fall', 'Peak', 'Water'])}"
        
        mq, mr = random_micro_coord()
        cursor.execute("""
            INSERT INTO settlements (faction_id, global_hex_id, name, settlement_level, population, spark_born_population, wealth, security_points, inventory_json, magic_loadout, micro_q, micro_r)
            VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (faction_id, hex_id, name, pop, spark_born, random.uniform(50, 500), random.uniform(0, 100), json.dumps(inventory), magic_loadout, mq, mr))
        
        s_id = cursor.lastrowid
        
        # Base 12 Domain Stats (1 to 10)
        p_stats = {d: random.randint(1, 5) for d in domains}
        
        # Boost stats based on proximity to prisons (magic_loadout)
        for dom in json.loads(magic_loadout):
            p_stats[dom] = min(10, p_stats[dom] + random.randint(2, 5))
            
        p_name = random.choice(["Kael", "Vorn", "Lyra", "Sera", "Tarn", "Rhys", "Jorn", "Mara", "Vane"])
        p_desc = random.choice(["The Iron-Fisted", "The Builder", "The Glutton", "The Zealot", "The Visionary", "The Ruthless", "The Merciful"])
        p_goal = random.choice(["Expand Borders", "Hoard Wealth", "Build an Army", "Survive", "Worship Chaos"])
        
        cursor.execute("""
            INSERT INTO paragons (settlement_id, name, descriptor, goal, 
                stat_mass, stat_ordo, stat_motus, stat_flux, stat_vita, stat_nexus, 
                stat_ratio, stat_anumis, stat_lux, stat_omen, stat_aura, stat_lex,
                blessing, flaw, quirk1, quirk2)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (s_id, p_name, p_desc, p_goal, 
              p_stats["Mass"], p_stats["Ordo"], p_stats["Motus"], p_stats["Flux"], 
              p_stats["Vita"], p_stats["Nexus"], p_stats["Ratio"], p_stats["Anumis"], 
              p_stats["Lux"], p_stats["Omen"], p_stats["Aura"], p_stats["Lex"],
              "Strong", "Greedy", "Paranoid", "Meticulous"))

    # --- POST-SEED: Zero out chaos power on all Prison hexes -----------------
    # The geology system fills pack_ecology p1 with large values for wilderness
    # hexes. Prison hexes must start with their seals fully intact (p1 = 0).
    # Wardens must then fight to keep them there. Left unchecked, natural seal
    # decay will bring p1 toward 250 over many hundreds of ticks.
    cursor.execute("SELECT id FROM global_hexes WHERE chaos_domain IS NOT NULL")
    chaos_hex_ids = cursor.fetchall()
    for (ch_id,) in chaos_hex_ids:
        # Clear p1 (bits 0-7) while preserving p2/p3/res in the packed int
        cursor.execute(
            "UPDATE global_hexes SET pack_ecology = (pack_ecology & 0xFFFFFF00) WHERE id=?",
            (ch_id,)
        )
    if chaos_hex_ids:
        print(f"Prison hex chaos power (p1) zeroed for {len(chaos_hex_ids)} prison hexes.")

    conn.commit()
    conn.close()
    print("Cults, Wardens, Factions, and Paragons seeded successfully.")

if __name__ == "__main__":
    seed_world_society()
