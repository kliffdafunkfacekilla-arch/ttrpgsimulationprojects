# fringe_system.py
# Full fringe group integration: population, wealth, influence, and unique operations.
# Fringe groups operate as parasitic overlays on faction economies.
import random

# ===========================
# FRINGE GROUP DEFINITIONS
# ===========================
FRINGE_DEFINITIONS = {
    "Obsidian Cartel and Sister Org": {
        "type": "criminal_syndicate",
        "preferred_hosts": ["Sump-Kin", "Iron Caladrea", "Vaneer Concord"],
        "recruit_from": "crime",  # Recruits from factions with high crime
        "base_population": 200.0,
        "base_wealth": 500.0,
    },
    "Freesky Barons": {
        "type": "sky_miners",
        "preferred_hosts": ["Canopy Clans", "Avians", "Flower Valwey"],
        "recruit_from": "adventurers",  # Recruits from frontier/low-pop factions
        "base_population": 150.0,
        "base_wealth": 300.0,
    },
    "Ghost Wind Raiders": {
        "type": "sky_pirates",
        "preferred_hosts": ["Meridian Chain", "River Folk", "Avians"],
        "recruit_from": "military",  # Recruits from disillusioned soldiers
        "base_population": 100.0,
        "base_wealth": 200.0,
    },
    "Gilded Compass": {
        "type": "financial_syndicate",
        "preferred_hosts": ["Vaneer Concord", "River Folk", "Iron Caladrea"],
        "recruit_from": "trade",  # Recruits from commercial hubs
        "base_population": 80.0,
        "base_wealth": 1000.0,
    },
    "Crimson Coursairs": {
        "type": "smuggler_fleet",
        "preferred_hosts": ["Meridian Chain", "River Folk", "Theocracy"],
        "recruit_from": "docks",  # Recruits from dockworker populations
        "base_population": 120.0,
        "base_wealth": 250.0,
    },
    "Silent Current": {
        "type": "deep_marine_syndicate",
        "preferred_hosts": ["Theocracy", "Meridian Chain", "River Folk"],
        "recruit_from": "aquatic",  # Recruits from aquatic-affiliated factions
        "base_population": 60.0,
        "base_wealth": 400.0,
    },
    "The Black Label": {
        "type": "mercenary_guild",
        "preferred_hosts": ["Iron Caladrea", "Ursine Hegemony", "East Hounds"],
        "recruit_from": "military",  # Recruits veteran soldiers
        "base_population": 100.0,
        "base_wealth": 350.0,
    },
    "The Otter Syndicate": {
        "type": "riverine_black_market",
        "preferred_hosts": ["River Folk", "Sump-Kin", "Guirrilla Clans"],
        "recruit_from": "crime",  # Recruits from criminal underclass
        "base_population": 90.0,
        "base_wealth": 300.0,
    },
    "The Spring Ghosts": {
        "type": "assassin_guild",
        "preferred_hosts": ["Prism Lizards", "Canopy Clans", "Sylvian"],
        "recruit_from": "chaos",  # Recruits during high-static weather
        "base_population": 40.0,
        "base_wealth": 600.0,
    },
}

def initialize_fringe_groups():
    """Creates all 9 fringe group state objects."""
    groups = {}
    for name, defn in FRINGE_DEFINITIONS.items():
        groups[name] = {
            "name": name,
            "type": defn["type"],
            "population": defn["base_population"],
            "wealth": defn["base_wealth"],
            "influence": 0.10,  # 0.0 to 1.0 how embedded in host faction
            "host_faction": random.choice(defn["preferred_hosts"]),
            "preferred_hosts": defn["preferred_hosts"],
            "recruit_from": defn["recruit_from"],
            "contracts": [],  # active mercenary/service contracts
            "heat": 0.0,  # law enforcement pressure (0-1)
        }
    return groups

def process_fringe_tick(fringe_groups, faction_groups_by_name, diplomacy, logs):
    """
    Processes one tick of fringe group operations.
    fringe_groups: dict of fringe group state objects
    faction_groups_by_name: dict of faction name -> faction state dict
    diplomacy: the diplomacy state dict
    logs: list to append log messages to
    """
    for fg_name, fg in fringe_groups.items():
        host_name = fg["host_faction"]
        host = faction_groups_by_name.get(host_name)
        if not host:
            # Migrate to a random preferred host that exists
            available = [h for h in fg["preferred_hosts"] if h in faction_groups_by_name]
            if available:
                fg["host_faction"] = random.choice(available)
                host = faction_groups_by_name[fg["host_faction"]]
            else:
                continue
        
        host_inv = host.get("inventory", {})
        
        # =====================
        # RECRUITMENT
        # =====================
        recruit_rate = 0.0
        if fg["recruit_from"] == "crime":
            recruit_rate = host.get("crime_level", 0.0) * 0.005 * host.get("population", 1000.0)
        elif fg["recruit_from"] == "military":
            recruit_rate = host.get("discontent", 0.0) * 0.003 * host.get("population", 1000.0)
        elif fg["recruit_from"] == "trade":
            recruit_rate = 0.002 * host.get("population", 1000.0) * (1.0 if host_inv.get("Grain", 0.0) > 20.0 else 0.3)
        elif fg["recruit_from"] == "docks":
            recruit_rate = host.get("docks_count", 0) * 2.0
        elif fg["recruit_from"] == "aquatic":
            recruit_rate = (host.get("docks_count", 0) + 1) * 1.5
        elif fg["recruit_from"] == "adventurers":
            recruit_rate = max(0.0, (0.3 - host.get("crime_level", 0.0)) * 3.0 * host.get("population", 1000.0) / 1000.0)
        elif fg["recruit_from"] == "chaos":
            recruit_rate = host.get("chaos_level", 0.0) * 0.002 * host.get("population", 1000.0)
        
        # Recruitment drains from host population (parasitic overlay from underclass)
        actual_recruits = min(recruit_rate, host.get("population", 1000.0) * 0.001)
        fg["population"] = max(10.0, fg["population"] + actual_recruits)
        # Small population drain from host
        host["population"] = max(100.0, host.get("population", 1000.0) - actual_recruits * 0.5)
        
        # Natural attrition
        fg["population"] = max(10.0, fg["population"] * 0.98)
        
        # Law enforcement pressure reduces population
        if fg["heat"] > 0.5:
            arrested = fg["population"] * (fg["heat"] - 0.5) * 0.1
            fg["population"] = max(10.0, fg["population"] - arrested)
        
        # Heat decays naturally
        fg["heat"] = max(0.0, fg["heat"] - 0.05)
        
        # Influence grows with population and wealth relative to host
        fg["influence"] = min(1.0, (fg["population"] / max(100.0, host.get("population", 1000.0))) + (fg["wealth"] / max(500.0, sum(host_inv.values()))))
        
        # =====================
        # HOST MIGRATION
        # =====================
        # If heat gets too high or host is too dangerous, migrate
        if fg["heat"] > 0.8 or host.get("security_rating", 0.0) > 0.9:
            available = [h for h in fg["preferred_hosts"] if h in faction_groups_by_name and h != host_name]
            if available:
                new_host = random.choice(available)
                fg["host_faction"] = new_host
                fg["heat"] = 0.0
                logs.append(f"🏃 FRINGE: {fg_name} relocated operations from {host_name} to {new_host} to avoid law enforcement!")
                continue
        
        # =====================
        # UNIQUE OPERATIONS
        # =====================
        _process_fringe_operation(fg, host, host_inv, faction_groups_by_name, diplomacy, logs)

def _process_fringe_operation(fg, host, host_inv, all_factions, diplomacy, logs):
    """Execute the unique operation for this fringe group type."""
    fg_name = fg["name"]
    host_name = fg["host_faction"]
    pop_scale = fg["population"] / 100.0
    
    # =====================
    # OBSIDIAN CARTEL AND SISTER ORG
    # =====================
    if fg["type"] == "criminal_syndicate":
        # Runs gambling dens and black markets. Drains resources, increases crime.
        host["crime_level"] = min(1.0, host.get("crime_level", 0.0) + 0.02 * fg["influence"])
        
        # Skim resources
        for res in ["Lumber", "Smelted Steel", "Dragonstone"]:
            skim = min(host_inv.get(res, 0.0) * 0.03, 3.0 * pop_scale)
            if skim > 0.5:
                host_inv[res] = max(0.0, host_inv[res] - skim)
                fg["wealth"] += skim * 10.0
        
        # Build gambling dens if influence high enough
        if fg["influence"] > 0.3 and host.get("gambling_dens_count", 0) < 3 and random.random() < 0.10:
            host["gambling_dens_count"] = host.get("gambling_dens_count", 0) + 1
            logs.append(f"🎲 CARTEL: {fg_name} established a new Gambling Den in {host_name}!")
        
        # Drug trade (generates wealth, increases discontent)
        if random.random() < 0.20:
            host["discontent"] = min(1.0, host.get("discontent", 0.0) + 0.01)
            fg["wealth"] += 50.0
            logs.append(f"💊 CARTEL: {fg_name} ran a drug operation in {host_name}, generating wealth but breeding discontent.")
        
        # Security crackdown chance
        if host.get("security_rating", 0.0) > 0.6:
            fg["heat"] = min(1.0, fg["heat"] + 0.1)
    
    # =====================
    # FREESKY BARONS
    # =====================
    elif fg["type"] == "sky_miners":
        # Mine Dragonstone from chaos zones. Sell to factions at premium.
        chaos = host.get("chaos_level", 0.0)
        if chaos > 0.3:
            mined = float(random.randint(1, 3)) * pop_scale * chaos
            host_inv["Dragonstone"] = host_inv.get("Dragonstone", 0.0) + mined
            fg["wealth"] += mined * 20.0
            if random.random() < 0.30:
                logs.append(f"⛏️ FREESKY: {fg_name} mined {mined:.0f} Dragonstone from chaos zones near {host_name}!")
        
        # Risk: chaos exposure causes casualties
        if chaos > 0.5 and random.random() < 0.15:
            casualties = fg["population"] * 0.05
            fg["population"] = max(10.0, fg["population"] - casualties)
            logs.append(f"💀 FREESKY: {fg_name} lost {casualties:.0f} miners to chaos exposure near {host_name}!")
        
        # Trade Dragonstone to other factions
        if fg["wealth"] > 200.0 and random.random() < 0.20:
            buyer_names = [n for n in all_factions.keys() if n != host_name]
            if buyer_names:
                buyer_name = random.choice(buyer_names)
                buyer = all_factions[buyer_name]
                buyer["inventory"]["Dragonstone"] = buyer["inventory"].get("Dragonstone", 0.0) + 1.0
                fg["wealth"] -= 50.0
                logs.append(f"💎 FREESKY: {fg_name} sold Dragonstone to {buyer_name}.")
    
    # =====================
    # GHOST WIND RAIDERS
    # =====================
    elif fg["type"] == "sky_pirates":
        # Raid trade routes, steal cargo. Funded secretly by Meridian Chain.
        if random.random() < 0.15 * pop_scale:
            target_names = [n for n in all_factions.keys() if n != host_name and n != "Meridian Chain"]
            if target_names:
                target_name = random.choice(target_names)
                target = all_factions.get(target_name)
                if target:
                    target_inv = target.get("inventory", {})
                    stolen_res = random.choice(["Grain", "Lumber", "Stone", "Smelted Steel"])
                    stolen_amt = min(target_inv.get(stolen_res, 0.0) * 0.08, 8.0 * pop_scale)
                    if stolen_amt > 1.0:
                        target_inv[stolen_res] = max(0.0, target_inv[stolen_res] - stolen_amt)
                        fg["wealth"] += stolen_amt * 8.0
                        logs.append(f"🏴‍☠️ RAIDERS: {fg_name} raided {target_name}'s trade routes, stealing {stolen_amt:.0f} {stolen_res}!")
                        
                        # Meridian Chain secretly benefits
                        mc = all_factions.get("Meridian Chain")
                        if mc:
                            mc["inventory"][stolen_res] = mc["inventory"].get(stolen_res, 0.0) + stolen_amt * 0.3
                        
                        fg["heat"] = min(1.0, fg["heat"] + 0.15)
    
    # =====================
    # GILDED COMPASS
    # =====================
    elif fg["type"] == "financial_syndicate":
        # Financial manipulation. Controls trade prices. Takes a cut of all trade.
        # Stabilizes host economy but enriches themselves
        host["discontent"] = max(0.0, host.get("discontent", 0.0) - 0.02 * fg["influence"])
        
        # Take a cut of trade
        trade_cut = sum(host_inv.get(r, 0.0) for r in ["Grain", "Lumber", "Stone"]) * 0.01 * fg["influence"]
        for res in ["Grain", "Lumber", "Stone"]:
            skim = host_inv.get(res, 0.0) * 0.01 * fg["influence"]
            host_inv[res] = max(0.0, host_inv[res] - skim)
        fg["wealth"] += trade_cut * 5.0
        
        # Audit manipulation: occasionally boost host economy
        if random.random() < 0.15:
            host_inv["Stone"] = host_inv.get("Stone", 0.0) + 5.0
            logs.append(f"📊 COMPASS: {fg_name} audited and redirected resources in {host_name}, granting 5 Stone.")
        
        # Loan sharking: if host is poor, offer loans (increase influence)
        if sum(host_inv.values()) < 100.0:
            fg["influence"] = min(1.0, fg["influence"] + 0.05)
            host_inv["Grain"] = host_inv.get("Grain", 0.0) + 10.0
            host_inv["Lumber"] = host_inv.get("Lumber", 0.0) + 10.0
            fg["wealth"] -= 30.0
            logs.append(f"💰 COMPASS: {fg_name} loaned resources to struggling {host_name}, deepening their influence.")
    
    # =====================
    # CRIMSON COURSAIRS
    # =====================
    elif fg["type"] == "smuggler_fleet":
        # Smuggle contraband between factions. Bypass embargoes.
        if random.random() < 0.20 * pop_scale:
            source_names = [n for n in all_factions.keys() if n != host_name]
            if source_names:
                source_name = random.choice(source_names)
                source = all_factions.get(source_name)
                if source:
                    source_inv = source.get("inventory", {})
                    contraband = random.choice(["Dragonstone", "Night-Nectar", "Smelted Steel", "Ghost Flower"])
                    amount = min(source_inv.get(contraband, 0.0) * 0.05, 3.0 * pop_scale)
                    if amount > 0.5:
                        source_inv[contraband] = max(0.0, source_inv[contraband] - amount)
                        host_inv[contraband] = host_inv.get(contraband, 0.0) + amount
                        fg["wealth"] += amount * 15.0
                        logs.append(f"🚢 CORSAIRS: {fg_name} smuggled {amount:.0f} {contraband} from {source_name} to {host_name}!")
                        fg["heat"] = min(1.0, fg["heat"] + 0.08)
    
    # =====================
    # SILENT CURRENT
    # =====================
    elif fg["type"] == "deep_marine_syndicate":
        # Underwater smuggling. Completely undetectable.
        if random.random() < 0.15 * pop_scale:
            target_names = [n for n in all_factions.keys() if n != host_name]
            if target_names:
                target_name = random.choice(target_names)
                target = all_factions.get(target_name)
                if target:
                    target_inv = target.get("inventory", {})
                    res = random.choice(["Dragonstone", "Refined Aether Battery", "Silk-Steel Thread"])
                    amount = min(target_inv.get(res, 0.0) * 0.04, 2.0 * pop_scale)
                    if amount > 0.3:
                        target_inv[res] = max(0.0, target_inv[res] - amount)
                        fg["wealth"] += amount * 20.0
                        # No heat increase - undetectable!
                        if random.random() < 0.40:
                            logs.append(f"🌊 SILENT: {fg_name} moved {amount:.0f} {res} through deep trenches undetected.")
    
    # =====================
    # THE BLACK LABEL
    # =====================
    elif fg["type"] == "mercenary_guild":
        # Hired by factions for protection. Expensive but effective.
        # Look for factions at war that need help
        if diplomacy:
            for war in diplomacy.get("active_wars", []):
                # Offer services to the weaker side
                att = all_factions.get(war["attacker"])
                dfn = all_factions.get(war["defender"])
                if att and dfn:
                    from diplomacy_system import calculate_military_strength
                    str_att = calculate_military_strength(att)
                    str_dfn = calculate_military_strength(dfn)
                    weaker = war["defender"] if str_att > str_dfn else war["attacker"]
                    g_weaker = all_factions[weaker]
                    
                    if g_weaker["inventory"].get("Grain", 0.0) > 20.0 and random.random() < 0.25:
                        # Hire mercenaries: costs resources, boosts military
                        g_weaker["inventory"]["Grain"] = max(0.0, g_weaker["inventory"]["Grain"] - 15.0)
                        g_weaker["barracks_count"] = g_weaker.get("barracks_count", 0) + 1  # temp military boost
                        fg["wealth"] += 200.0
                        logs.append(f"⚔️ MERCENARY: {fg_name} hired by {weaker} for military support! Cost: 15 Grain.")
                        break
        
        # VIP protection contracts
        if random.random() < 0.10:
            client_name = random.choice(list(all_factions.keys()))
            client = all_factions[client_name]
            if client.get("crime_level", 0.0) > 0.3:
                client["crime_level"] = max(0.0, client["crime_level"] - 0.05)
                client["inventory"]["Grain"] = max(0.0, client["inventory"].get("Grain", 0.0) - 5.0)
                fg["wealth"] += 80.0
                logs.append(f"🛡️ MERCENARY: {fg_name} provided security services to {client_name}, reducing crime.")
    
    # =====================
    # THE OTTER SYNDICATE
    # =====================
    elif fg["type"] == "riverine_black_market":
        # Bypass taxes, move illegal goods through sewers.
        host["crime_level"] = min(1.0, host.get("crime_level", 0.0) + 0.015 * fg["influence"])
        
        # Black market trade
        if random.random() < 0.20 * pop_scale:
            # Buy low from one faction, sell high to host
            source_names = [n for n in all_factions.keys() if n != host_name]
            if source_names:
                source_name = random.choice(source_names)
                source = all_factions.get(source_name)
                if source:
                    res = random.choice(["Grain", "Leather", "Coal", "Copper Ore"])
                    amount = min(source["inventory"].get(res, 0.0) * 0.05, 5.0 * pop_scale)
                    if amount > 1.0:
                        source["inventory"][res] = max(0.0, source["inventory"][res] - amount)
                        host_inv[res] = host_inv.get(res, 0.0) + amount * 0.8  # middleman cut
                        fg["wealth"] += amount * 5.0
                        logs.append(f"🦦 SYNDICATE: {fg_name} moved {amount:.0f} {res} through underground channels to {host_name}.")
        
        # Build black markets
        if fg["influence"] > 0.25 and host.get("black_markets_count", 0) < 3 and random.random() < 0.08:
            host["black_markets_count"] = host.get("black_markets_count", 0) + 1
            logs.append(f"🕶️ SYNDICATE: {fg_name} opened a Black Market in {host_name}!")
        
        fg["heat"] = min(1.0, fg["heat"] + 0.03)
    
    # =====================
    # THE SPRING GHOSTS
    # =====================
    elif fg["type"] == "assassin_guild":
        # Assassins and spies. Execute political sabotage during high-static weather.
        chaos = host.get("chaos_level", 0.0)
        
        # More active during high chaos (high-static phases)
        if chaos > 0.4 and random.random() < 0.12 * pop_scale:
            # Target a random faction's paragon
            target_names = [n for n in all_factions.keys() if n != host_name]
            if target_names:
                target_name = random.choice(target_names)
                target = all_factions.get(target_name)
                if target:
                    paragon = target.get("paragon")
                    if paragon and random.random() < 0.15:
                        # Assassination attempt
                        target_will = paragon.get("stats", {}).get("Willpower", 10)
                        if random.random() > target_will / 25.0:
                            paragon["stats"]["Vitality"] = max(0, paragon["stats"].get("Vitality", 10) - random.randint(3, 8))
                            fg["wealth"] += 300.0
                            logs.append(f"🗡️ GHOST STRIKE: {fg_name} wounded {target_name}'s leader {paragon['name']} during a high-static phase!")
                        else:
                            logs.append(f"🛡️ GHOST FOILED: {target_name}'s leader {paragon['name']} survived a {fg_name} assassination attempt!")
                            fg["heat"] = min(1.0, fg["heat"] + 0.20)
        
        # Political sabotage: increase discontent in a target
        if random.random() < 0.10:
            target_names = [n for n in all_factions.keys() if n != host_name]
            if target_names:
                target_name = random.choice(target_names)
                target = all_factions[target_name]
                target["discontent"] = min(1.0, target.get("discontent", 0.0) + 0.05)
                fg["wealth"] += 100.0
                logs.append(f"👻 GHOST OPS: {fg_name} spread propaganda and unrest in {target_name}!")
    
    # =====================
    # WEALTH DECAY
    # =====================
    # Fringe groups have operational costs
    fg["wealth"] = max(0.0, fg["wealth"] - fg["population"] * 0.5)
