# rules_engine.py
# Calculates town size scores, unlocks, population well-being stats,
# resource gathering, production/crafting, dynamic construction, trading,
# wildlife encounters, alchemical lore events, Cult Infiltration, and Prison/Warden physics.

import sys
import os
import random

# Ensure project root is in path to import constants
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from constants import (
    TOWN_TIERS, TRANSPORT_UNLOCKS, BUILDING_UNLOCKS,
    WELLBEING_DECAY_RATE, FOOD_PER_FARM, FOOD_PER_DOCK,
    SAFETY_PER_TOWER, SAFETY_PER_WALL, SECURITY_PER_BARRACKS,
    RIOT_DISCONTENT_LIMIT, RIOT_CRIME_LIMIT,
    REVOLUTION_DISCONTENT_LIMIT, REVOLUTION_CRIME_LIMIT,
    TRADE_ABUNDANCE_LEVEL
)

# Cost of constructing buildings in Ostraka
BUILDING_COSTS = {
    "farms": {"Lumber": 50, "Stone": 50},
    "docks": {"Lumber": 70, "Stone": 30},
    "mines": {"Lumber": 30, "Stone": 80},
    "watchtowers": {"Lumber": 40, "Stone": 60},
    "walls": {"Lumber": 20, "Stone": 120},
    "barracks": {"Lumber": 60, "Stone": 100, "Smelted Steel": 20},
    "camps": {"Lumber": 40, "Stone": 20},
    "greenhouse": {"Lumber": 30, "Stone": 30},
    "orchard": {"Lumber": 30, "Stone": 30},
    "pen": {"Lumber": 30, "Stone": 30},
    "kennel": {"Lumber": 30, "Stone": 30},
    "church": {"Lumber": 40, "Stone": 60},
    "theatre": {"Lumber": 50, "Stone": 30},
    "arena": {"Lumber": 60, "Stone": 80}
}

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
    "The Reliance": ["Sump-Kin", "Guirrilla Clans", "Theocracy"]
}

def calculate_alignment(stats, traits):
    """Determines whether a leader is Heroic, Pragmatic (Neutral), or Villainous based on stats and traits."""
    if (stats.get("Charm", 10) >= 12 or stats.get("Willpower", 10) >= 12) and "Corrupt" not in traits and "Cowardly" not in traits:
        return "Heroic"
    elif "Corrupt" in traits or (stats.get("Might", 10) >= 12 and stats.get("Charm", 10) < 8 and stats.get("Willpower", 10) < 8) or ("Prejudiced" in traits and "Short-tempered" in traits):
        return "Villainous"
    else:
        return "Pragmatic"

def generate_paragon(faction_name=None, history_logs=None):
    """Generates a Paragon leader (mayor or guard captain) with 12 stats and Good/Bad traits based on lore/history."""
    cultures = ["Beavers", "Hippos", "Owls", "Horses", "Wolves", "Bears", "Sloths", "Toads", "Mice", "Bats", "Porcupines", "Otters", "Deer", "Mongooses", "Cactus-Kin", "Mushroom-Kin"]
    
    # Try to map faction name to a fitting starter culture, or pick at random
    culture = "Bears" # default
    if faction_name:
        if "Ursine" in faction_name:
            culture = "Bears"
        elif "River" in faction_name or "Otter" in faction_name:
            culture = "Otters"
        elif "Sump" in faction_name or "Toad" in faction_name:
            culture = "Toads"
        elif "Iron" in faction_name:
            culture = "Beavers"
        elif "Vaneer" in faction_name:
            culture = "Mice"
        elif "Hive" in faction_name:
            culture = "Sloths"
        elif "Avian" in faction_name:
            culture = "Owls"
        elif "Flower" in faction_name or "Sylvian" in faction_name:
            culture = "Deer"
        elif "Sciute" in faction_name:
            culture = "Porcupines"
        elif "Meridian" in faction_name:
            culture = "Hippos"
        elif "Lizards" in faction_name:
            culture = "Mongooses"
        elif "Canopy" in faction_name:
            culture = "Bats"
        elif "Hounds" in faction_name:
            culture = "Wolves"
        elif "Theocracy" in faction_name:
            culture = "Mushroom-Kin"
        elif "Reliance" in faction_name:
            culture = "Cactus-Kin"
        else:
            culture = random.choice(cultures)
    else:
        culture = random.choice(cultures)

    names_by_culture = {
        "Beavers": {
            "firsts": ["Castor", "Chisel", "Bramble", "Flattail", "Timber", "Damian"],
            "titles": ["the Builder", "the Mason", "the Constructer", "the Steady", "the Diligent", "the Sharp-toothed"],
            "lasts": ["Oakfeller", "Stonetail", "Riverblock", "Clayweaver", "Mudbar", "Pondkeep"]
        },
        "Hippos": {
            "firsts": ["Goliath", "Maw", "Riverton", "Heavyhoof", "Bari", "Brutus"],
            "titles": ["the Deep-Diver", "the Crushing", "the River-King", "the Wide-Mouthed", "the Unyielding", "the Sun-Baked"],
            "lasts": ["Mudstride", "Siltcrush", "Deltabreaker", "Bottomtreader", "Bayguard", "Gorgeforce"]
        },
        "Owls": {
            "firsts": ["Hoot", "Screech", "Archimedes", "Featherstone", "Barny", "Strix"],
            "titles": ["the Wise", "the Silent-Winged", "the Truth-Teller", "the All-Seeing", "the Nightwatch", "the Logic-Seeker"],
            "lasts": ["Screechowl", "Sagefeather", "Moonhollow", "Skygazer", "Talonstrike", "Aetherwing"]
        },
        "Horses": {
            "firsts": ["Gallop", "Steed", "Saddle", "Ironhoof", "Cavalier", "Destrier"],
            "titles": ["the Swift", "the Stalwart", "the Noble", "the Unbroken", "the Grid-Watcher", "the Shield-Bearer"],
            "lasts": ["Highstride", "Stormhoof", "Plainsrunner", "Shieldheart", "Ironclad", "Maneguard"]
        },
        "Wolves": {
            "firsts": ["Fang", "Lupine", "Greyback", "Packward", "Kael", "Lycaon"],
            "titles": ["the Boundary-Keeper", "the Pack-Leader", "the Fierce", "the Howler", "the Shadow-Stalker", "the Wild"],
            "lasts": ["Bloodtooth", "Winterfang", "Packweaver", "Frostclaw", "Wildrun", "Silentpaw"]
        },
        "Bears": {
            "firsts": ["Ursus", "Kodiak", "Grizzly", "Snowpaw", "Beowulf", "Arthur"],
            "titles": ["the Stasis-Keeper", "the Mountain", "the Ice-Walker", "the Sleeping", "the Mighty", "the Guardian"],
            "lasts": ["Stoneclaw", "Winterhide", "Frostbite", "Cavewall", "Honeylick", "Grizzlycoat"]
        },
        "Sloths": {
            "firsts": ["Slowmo", "Hang", "Cables", "Lazytoe", "Bradypod", "Mossy"],
            "titles": ["the Unhurried", "the Silk-Weaver", "the Calm", "the Canopy-Climber", "the Immune", "the Steady-Claw"],
            "lasts": ["Branchhang", "Silkspinner", "Slowglide", "Mossback", "Lazybranch", "Tensionline"]
        },
        "Toads": {
            "firsts": ["Croak", "Wart", "Bog", "Siltmouth", "Bufo", "Sludge"],
            "titles": ["the Mud-Born", "the Immune", "the Alchemy-Proof", "the Poison-Skin", "the Deep-Croaker", "the Swamp-Guide"],
            "lasts": ["Mucktreader", "Pondweed", "Sludgewalker", "Fenbound", "Wartskin", "Siltmouth"]
        },
        "Mice": {
            "firsts": ["Squeak", "Booker", "Pip", "Nibble", "Cecil", "Rattus"],
            "titles": ["the Auditor", "the Clerk", "the Detail-Finder", "the Quick-Pawed", "the Ledger-Keeper", "the Sharp-Eyed"],
            "lasts": ["Inkwell", "Bookbinder", "Nibblesworth", "Squeakley", "Grainhoard", "Auditspire"]
        },
        "Bats": {
            "firsts": ["Vamp", "Sonar", "Pipistrelle", "Echo", "Noctilio", "Flit"],
            "titles": ["the Echolocator", "the Sonic-Scout", "the Winged-Sentry", "the Sky-Mapper", "the Night-Singer", "the Blind-Seer"],
            "lasts": ["Cavesonic", "Echolash", "Flitwing", "Shadowbat", "Sonarstrike", "Guanoearth"]
        },
        "Porcupines": {
            "firsts": ["Needle", "Spike", "Quill", "Scalpel", "Ereth", "Quillan"],
            "titles": ["the Surgeon", "the Sharp-Quilled", "the Molt-Weaver", "the Prickly", "the Precise", "the Needle-Caster"],
            "lasts": ["Quillsharp", "Spikeweaver", "Scalpelhand", "Bristlecoat", "Pierceguard", "Needlework"]
        },
        "Otters": {
            "firsts": ["River", "Slick", "Smuggler", "Deltan", "Lutra", "Mustel"],
            "titles": ["the Smuggler", "the Swimmer", "the Lock-Breaker", "the Agile", "the River-Runner", "the Delta-Master"],
            "lasts": ["Slipstream", "Waterlock", "Deltanrun", "Smugglercreek", "Riverglide", "Quickdive"]
        },
        "Deer": {
            "firsts": ["Buck", "Doe", "Antler", "Meadow", "Cervus", "Fawn"],
            "titles": ["the Grower", "the Storm-Harvester", "the Fleet-Footed", "the Antlered", "the Meadow-Watcher", "the Greenwood-Sage"],
            "lasts": ["Meadowbound", "Antlercrown", "Stormcrop", "Greenwood", "Fawnrun", "Harvestfield"]
        },
        "Mongooses": {
            "firsts": ["Swift", "Riki", "Cobra", "Dodge", "Herpest", "Vermin"],
            "titles": ["the Bodyguard", "the Flux-Dodger", "the Cobra-Slayer", "the Quick", "the Gravity-Defier", "the Reflex-Master"],
            "lasts": ["Dodgeclaw", "Swiftstrike", "Viperfoil", "Reflexwind", "Gravityleap", "Quickstrike"]
        },
        "Cactus-Kin": {
            "firsts": ["Prickly", "Spike", "Needles", "Saguaro", "Succulent", "Cacta"],
            "titles": ["the Dry-Endurer", "the Spine-Shield", "the Ballast-Master", "the Desert-Born", "the Water-Hoarder", "the Green-Tower"],
            "lasts": ["Saguaroheart", "Spinespot", "Desertbloom", "Dryroot", "Cactusspire", "Needlehide"]
        },
        "Mushroom-Kin": {
            "firsts": ["Spore", "Cap", "Shroom", "Mycelium", "Agaric", "Fungus"],
            "titles": ["the Archivist", "the Mind-Shielded", "the Decay-Feeder", "the Spore-Scatterer", "the Deep-Rooted", "the Fungal-Sage"],
            "lasts": ["Sporecap", "Myceliumrun", "Agaricwood", "Shroomgrowth", "Fungalroot", "Archiviststem"]
        }
    }
    
    culture_pools = names_by_culture.get(culture, {
        "firsts": ["Leader"],
        "titles": ["the Ruler"],
        "lasts": ["of the Land"]
    })
    first_part = random.choice(culture_pools["firsts"])
    second_part = random.choice(culture_pools["titles"])
    third_part = random.choice(culture_pools["lasts"])
    name = f"{first_part} {second_part} {third_part}"
    role = random.choice(["Mayor", "Guard Captain"])

    # Base attributes 3 to 18
    stats = {
        "Might": random.randint(5, 15),
        "Endurance": random.randint(5, 15),
        "Finesse": random.randint(5, 15),
        "Reflex": random.randint(5, 15),
        "Vitality": random.randint(5, 15),
        "Fortitude": random.randint(5, 15),
        "Knowledge": random.randint(5, 15),
        "Logic": random.randint(5, 15),
        "Awareness": random.randint(5, 15),
        "Intuition": random.randint(5, 15),
        "Charm": random.randint(5, 15),
        "Willpower": random.randint(5, 15)
    }

    # Cultural adjustments
    if culture == "Bears":
        stats["Might"] += 3
        stats["Endurance"] += 2
    elif culture == "Mice":
        stats["Logic"] += 3
        stats["Knowledge"] += 2
    elif culture == "Bats":
        stats["Awareness"] += 3
        stats["Reflex"] += 2
    elif culture == "Mongooses":
        stats["Reflex"] += 3
        stats["Finesse"] += 2
    elif culture == "Horses":
        stats["Fortitude"] += 3
        stats["Endurance"] += 2
    elif culture == "Owls":
        stats["Intuition"] += 3
        stats["Willpower"] += 2

    # Good, Bad, and Neutral Traits Pools
    good_pool = ["War Survivor", "Diplomat", "Vigilant", "Sage", "Indomitable", "Highly Spiritual", "Zealous", "Generous", "Just", "Valiant"]
    bad_pool = ["Prejudiced", "Cowardly", "Short-tempered", "Corrupt", "Paranoid", "Dogmatic", "Cruel", "Greedy", "Suspicious", "Spiteful"]
    neutral_pool = ["Stoic", "Ambitious", "Eccentric", "Traditionalist", "Cautious", "Struggler", "Pragmatist", "Curious", "Secretive", "Stubborn", "Nostalgic", "Skeptical"]

    # Incorporate history logs to shape/influence traits
    history_good = None
    history_bad = None
    if history_logs:
        log_str = " ".join(history_logs).upper()
        if ("BANDIT" in log_str or "WILDLIFE" in log_str or "DAMAGE" in log_str) and random.random() < 0.6:
            history_good = "War Survivor"
        elif ("CULT" in log_str or "SABOTAGE" in log_str or "CHAOS" in log_str) and random.random() < 0.6:
            history_good = "Highly Spiritual"
        elif ("TRADE" in log_str or "GOLD" in log_str) and random.random() < 0.5:
            history_good = "Diplomat"
            
        if ("BANDIT" in log_str or "WILDLIFE" in log_str or "DAMAGE" in log_str) and random.random() < 0.4:
            history_bad = "Paranoid"
        elif ("CULT" in log_str or "SABOTAGE" in log_str or "CHAOS" in log_str) and random.random() < 0.5:
            history_bad = "Dogmatic"

    selected_good = history_good if (history_good and history_good in good_pool) else random.choice(good_pool)
    selected_bad = history_bad if (history_bad and history_bad in bad_pool) else random.choice(bad_pool)

    num_neutral = random.randint(1, 3)
    selected_neutrals = random.sample(neutral_pool, num_neutral)

    traits = [selected_good, selected_bad] + selected_neutrals

    # Small chance (15%) of getting a 2nd good or evil (bad) trait
    if random.random() < 0.15:
        remaining_good = [t for t in good_pool if t not in traits]
        if remaining_good:
            traits.append(random.choice(remaining_good))
    if random.random() < 0.15:
        remaining_bad = [t for t in bad_pool if t not in traits]
        if remaining_bad:
            traits.append(random.choice(remaining_bad))

    traits = list(set(traits))
    alignment = calculate_alignment(stats, traits)

    # 50/50 magic affinity split
    if random.random() < 0.5:
        magic_affinity = "Null"
    else:
        roll = random.random()
        if roll < 0.35:
            magic_affinity = "Sparkborn - Sensitive"
        elif roll < 0.65:
            magic_affinity = "Sparkborn - Attuned"
        elif roll < 0.85:
            magic_affinity = "Sparkborn - Adept"
        elif roll < 0.95:
            magic_affinity = "Sparkborn - Wielder"
        elif roll < 0.99:
            magic_affinity = "Sparkborn - Master"
        else:
            magic_affinity = "Sparkborn - Epic"

    return {
        "name": name,
        "culture": culture,
        "role": role,
        "stats": stats,
        "traits": traits,
        "alignment": alignment,
        "magic_affinity": magic_affinity,
        "recent_decisions": []
    }

def get_town_details(population):
    """Returns the matching town tier dictionary for a given population."""
    for tier in TOWN_TIERS:
        if tier["min_pop"] <= population <= tier["max_pop"]:
            return tier
    return TOWN_TIERS[0]

def calculate_tech_level(town_populations):
    """
    Calculates the Tech Level as the sum of Town Size Scores of all towns.
    town_populations: list of floats representing populations of all settlements in a group.
    """
    tech_level = 0
    for pop in town_populations:
        tier = get_town_details(pop)
        tech_level += tier["score"]
    return tech_level

def get_unlocked_transport(tech_level):
    """Returns list of unlocked transport names for a tech level."""
    unlocked = []
    for trans in TRANSPORT_UNLOCKS:
        if tech_level >= trans["min_tech"]:
            unlocked.append(trans["name"])
    return unlocked

def get_unlocked_buildings(tech_level):
    """Returns list of unlocked building names for a tech level."""
    unlocked = []
    for bld in BUILDING_UNLOCKS:
        if tech_level >= bld["min_tech"]:
            unlocked.append(bld["name"])
    return unlocked

def process_well_being_tick(stats, buildings, chaos_level):
    """
    Calculates physical/mental well-being, crime, discontent, and returns the updated values.
    stats: dict containing 'physical_well_being', 'mental_well_being', 'crime_level', 'discontent'
    buildings: dict containing counts of 'farms', 'docks', 'watchtowers', 'walls', 'barracks'
    chaos_level: float (0.0 to 1.0)
    """
    food_supply = min(1.0, (buildings.get("farms", 0) * FOOD_PER_FARM) + (buildings.get("docks", 0) * FOOD_PER_DOCK))
    safety_rating = min(1.0, (buildings.get("watchtowers", 0) * SAFETY_PER_TOWER) + (buildings.get("walls", 0) * SAFETY_PER_WALL))
    security_rating = min(1.0, buildings.get("barracks", 0) * SECURITY_PER_BARRACKS)

    phys_change = (food_supply + safety_rating) / 2.0 - WELLBEING_DECAY_RATE
    new_phys = max(0.0, min(1.0, stats.get("physical_well_being", 1.0) + phys_change * 0.1))

    mental_change = (1.0 - chaos_level) + (1.0 - stats.get("crime_level", 0.0)) - 1.0
    new_mental = max(0.0, min(1.0, stats.get("mental_well_being", 1.0) + mental_change * 0.1))

    discontent_pressure = (2.0 - new_phys - new_mental) / 2.0
    new_discontent = max(0.0, min(1.0, stats.get("discontent", 0.0) + (discontent_pressure - 0.4) * 0.15))

    crime_pressure = new_discontent - security_rating
    new_crime = max(0.0, min(1.0, stats.get("crime_level", 0.0) + crime_pressure * 0.1))

    event = "Stable"
    if new_discontent >= REVOLUTION_DISCONTENT_LIMIT and new_crime >= REVOLUTION_CRIME_LIMIT:
        event = "Revolution"
    elif new_discontent >= RIOT_DISCONTENT_LIMIT and new_crime >= RIOT_CRIME_LIMIT:
        event = "Rioting"

    trader_status = "Inactive"
    if food_supply >= TRADE_ABUNDANCE_LEVEL:
        trader_status = "Active - Trade Route Established"

    return {
        "physical_well_being": new_phys,
        "mental_well_being": new_mental,
        "discontent": new_discontent,
        "crime_level": new_crime,
        "food_supply": food_supply,
        "safety_rating": safety_rating,
        "security_rating": security_rating,
        "event": event,
        "trader_status": trader_status
    }

def process_living_world_tick(g, inventory, current_day, season_mod, reality_mod, weather, prisons=None, global_state=None):
    """
    Executes a complete living world simulation turn for a macro group.
    g: dict representing the macro group
    inventory: dict of resources currently held by the group
    prisons: dict containing the seal integrity of the 12 dragon prisons
    global_state: dict containing global convergence metrics
    """
    logs = []
    
    # Initialize basic inventory if empty
    resources_list = ["Lumber", "Stone", "Iron Ore", "Copper Ore", "Coal", "Grain", "Leather", "Dragonstone", "Voltaic Fleece", "Ozone-Milk", "Ghost Flower", "Night-Nectar", "Flour", "Peak-Cheese", "Smelted Steel", "Copper Wire", "Refined Aether Battery", "Tanned Strips", "Ostrakan Hardtack", "Caldera Spark-Bread", "Basic Weapons", "Aether-Wright PPE", "Silk-Steel Cables", "Leather Armor", "Rope"]
    for r in resources_list:
        if r not in inventory:
            inventory[r] = 0.0

    # Ensure prisons and global_state exist
    if prisons is None:
        prisons = {}
    if global_state is None:
        global_state = {"global_surge": False}

    # Initialize ecology states in macro group if missing
    if "flora_ghost_flower" not in g:
        g["flora_ghost_flower"] = 100.0
    if "flora_stone_root" not in g:
        g["flora_stone_root"] = 100.0
    if "fauna_sky_grazer" not in g:
        g["fauna_sky_grazer"] = 50.0
    if "fauna_timber_wolf" not in g:
        g["fauna_timber_wolf"] = 10.0

    # Initialize domestic structure counts
    if "domestic_greenhouses" not in g:
        g["domestic_greenhouses"] = 0
    if "domestic_orchards" not in g:
        g["domestic_orchards"] = 0
    if "domestic_pens" not in g:
        g["domestic_pens"] = 0
    if "domestic_kennels" not in g:
        g["domestic_kennels"] = 0

    # Initialize happiness & non-faction structures
    if "churches_count" not in g:
        g["churches_count"] = 0
    if "theatres_count" not in g:
        g["theatres_count"] = 0
    if "arenas_count" not in g:
        g["arenas_count"] = 0
    if "gambling_dens_count" not in g:
        g["gambling_dens_count"] = 0
    if "black_markets_count" not in g:
        g["black_markets_count"] = 0

    # Initialize Paragon Leader
    if "paragon" not in g or g["paragon"] is None:
        g["paragon"] = generate_paragon(g.get("name"), logs)
    paragon = g["paragon"]

    # Ensure alignment exists (backward compatibility)
    if "alignment" not in paragon:
        paragon["alignment"] = calculate_alignment(paragon["stats"], paragon["traits"])
    alignment = paragon["alignment"]

    # Ensure magic affinity exists
    if "magic_affinity" not in paragon:
        if random.random() < 0.5:
            paragon["magic_affinity"] = "Null"
        else:
            roll = random.random()
            if roll < 0.35:
                paragon["magic_affinity"] = "Sparkborn - Sensitive"
            elif roll < 0.65:
                paragon["magic_affinity"] = "Sparkborn - Attuned"
            elif roll < 0.85:
                paragon["magic_affinity"] = "Sparkborn - Adept"
            elif roll < 0.95:
                paragon["magic_affinity"] = "Sparkborn - Wielder"
            elif roll < 0.99:
                paragon["magic_affinity"] = "Sparkborn - Master"
            else:
                paragon["magic_affinity"] = "Sparkborn - Epic"
    magic_affinity = paragon["magic_affinity"]

    # Resolve weather dict/string inputs
    if isinstance(weather, dict):
        weather_dict = weather
        weather_type = weather.get("type", "Stable")
    else:
        weather_type = weather
        weather_dict = {"type": weather, "is_chaos_charged": False, "destination_prison": None}

    # Resolve weather multipliers
    growth_mult = 1.0
    degradation_rate = 0.0
    travel_cost = 1.0
    
    if weather_type == "Reality Storm":
        growth_mult = 0.5
        degradation_rate = 0.15
        travel_cost = 2.0
    elif weather_type == "Flux Monsoon":
        growth_mult = 2.0
        degradation_rate = 0.10
        travel_cost = 1.8
    elif weather_type == "Static Drought":
        growth_mult = 0.2
        degradation_rate = 0.05
        travel_cost = 1.2
    elif weather_type == "Aetheric Mist":
        growth_mult = 1.2
        degradation_rate = 0.01
        travel_cost = 1.5

    # Weather structure degradation
    if degradation_rate > 0.0:
        for bld_key, bld_name in [("farms_count", "Farm"), ("watchtowers_count", "Watchtower"), ("barracks_count", "Barracks"), ("mines_count", "Mine"), ("walls_count", "Wall Segment"), ("camps_count", "Camp"), ("docks_count", "Dock"), ("churches_count", "Church"), ("theatres_count", "Theatre"), ("arenas_count", "Arena")]:
            if g.get(bld_key, 0) > 0 and random.random() < degradation_rate * 0.15:
                g[bld_key] = max(0, g[bld_key] - 1)
                logs.append(f"🏚️ WEATHER DAMAGE: Extreme {weather_type} degraded and damaged a {bld_name} in {g['name']}!")
                break

    # Associate faction's Magistar Prison Entity
    magistar = g["magistar_id"]
    if magistar not in prisons:
        prisons[magistar] = 1.0

    # Reality-breaking storm path effects
    if weather_dict.get("is_chaos_charged"):
        dest_prison = weather_dict.get("destination_prison", magistar)
        logs.append(f"🌀 CHAOS STORM PATH: A chaos-charged {weather_type} converges towards nearest {dest_prison} Prison through {g['name']}!")
        
        # Weaken local prison seal
        if dest_prison in prisons:
            prisons[dest_prison] = max(0.0, prisons[dest_prison] - 0.05)
            logs.append(f"⚡ PRISON IMPACT: Chaos discharge weakened the {dest_prison} Prison seal by 5.0%!")

        # Choose a reality-breaking effect
        effect = random.choice(["Temporal Decay", "Aetheric Mutation", "Logic Corruption", "Alchemical Transmutation"])
        if effect == "Temporal Decay":
            degraded_any = False
            for bld_key, bld_name in [("farms_count", "Farm"), ("watchtowers_count", "Watchtower"), ("barracks_count", "Barracks"), ("mines_count", "Mine")]:
                if g.get(bld_key, 0) > 0:
                    g[bld_key] = max(0, g[bld_key] - 1)
                    logs.append(f"🌀 REALITY ANOMALY: Temporal Decay aged and crumbled a local {bld_name}!")
                    degraded_any = True
                    break
            if not degraded_any:
                logs.append(f"🌀 REALITY ANOMALY: Temporal echoes shifted through the landscape but found no buildings to decay.")
        elif effect == "Aetheric Mutation":
            g["fauna_timber_wolf"] = min(200.0, g["fauna_timber_wolf"] * 1.5)
            g["fauna_sky_grazer"] = max(0.0, g["fauna_sky_grazer"] * 0.7)
            logs.append(f"🐺 REALITY ANOMALY: Aetheric Mutation mutated the local fauna! Timber Wolf pack size swelled by 50% while Sky-Grazers scattered.")
        elif effect == "Logic Corruption":
            g["discontent"] = min(1.0, g["discontent"] + 0.15)
            g["crime_level"] = min(1.0, g["crime_level"] + 0.10)
            logs.append(f"🧠 REALITY ANOMALY: Logic Corruption spread mental static, increasing discontent and crime ratings.")
        elif effect == "Alchemical Transmutation":
            mutated = False
            if inventory.get("Iron Ore", 0.0) >= 5.0:
                inventory["Iron Ore"] -= 5.0
                inventory["Dragonstone"] = inventory.get("Dragonstone", 0.0) + 2.0
                logs.append(f"🧪 REALITY ANOMALY: Alchemical Mutation transmuted 5 Iron Ore into 2 Dragonstone crystals!")
                mutated = True
            elif inventory.get("Grain", 0.0) >= 10.0:
                inventory["Grain"] -= 10.0
                inventory["Ghost Flower"] = inventory.get("Ghost Flower", 0.0) + 3.0
                logs.append(f"🧪 REALITY ANOMALY: Alchemical Mutation transmuted 10 Grain into 3 wild Ghost Flowers!")
                mutated = True
            if not mutated:
                logs.append(f"🧪 REALITY ANOMALY: Ambient energy crackled, but local storage lacked raw elements to transmute.")

    # Get prison seal integrity impact on regional chaos level, scaling with closeness to the chaos structure
    prison_seal = prisons[magistar]
    if prison_seal < 1.0:
        proximity_mult = 1.0 - g.get("distance_to_chaos_structure", 0.5)
        g["chaos_level"] = min(1.0, g["chaos_level"] + (1.0 - prison_seal) * 0.12 * proximity_mult)

    # 1. Improved Population Math (Logistic growth with carrying capacity)
    camps = g.get("camps_count", 0)
    mines = g.get("mines_count", 0)
    docks = g.get("docks_count", 0)
    farms = g.get("farms_count", 0)
    watchtowers = g.get("watchtowers_count", 0)
    walls = g.get("walls_count", 0)
    barracks = g.get("barracks_count", 0)
    churches = g.get("churches_count", 0)
    theatres = g.get("theatres_count", 0)
    arenas = g.get("arenas_count", 0)

    carrying_capacity = 1000.0 + (farms * 1500.0) + (docks * 1000.0) + (camps * 500.0)
    growth_rate = 0.05 * season_mod.get("growth", 1.0)
    # Chaos slows and stresses population growth
    growth_rate *= (1.0 - 0.5 * g["chaos_level"])
    # Gravity prison multiplier from Magistars dampens growth
    gravity_mult = reality_mod.get("gravity_mult", 1.0)
    if gravity_mult > 1.0:
        growth_rate /= gravity_mult
        
    p_ratio = g["population"] / carrying_capacity
    dp = growth_rate * g["population"] * (1.0 - p_ratio)
    # Limit population drops
    new_pop = max(100.0, g["population"] + dp)

    # Faction economy resource consumption
    grain_consumption = float((new_pop / 100.0) * 0.05)
    lumber_consumption = float((new_pop / 100.0) * 0.02)
    stone_consumption = float((new_pop / 100.0) * 0.02)
    inventory["Grain"] = max(0.0, inventory["Grain"] - grain_consumption)
    inventory["Lumber"] = max(0.0, inventory["Lumber"] - lumber_consumption)
    inventory["Stone"] = max(0.0, inventory["Stone"] - stone_consumption)

    # 2. Resource Gathering & Biology/Ecology Ticks
    pop_efficiency = new_pop / 5000.0

    # Ecology update based on Lotka-Volterra dynamics
    gf = max(0.0, g["flora_ghost_flower"])
    sr = max(0.0, g["flora_stone_root"])
    sg = max(0.0, g["fauna_sky_grazer"])
    tw = max(0.0, g["fauna_timber_wolf"])

    gf_growth_rate = 0.12 * g["chaos_level"] * growth_mult * season_mod.get("growth", 1.0)
    sr_growth_rate = 0.08 * (1.0 - g["chaos_level"]) * growth_mult * season_mod.get("growth", 1.0)

    # Herbivore grazing
    consumption_gf = min(gf, 0.02 * gf * sg)

    # Grazer growth and predation
    sg_growth_rate = 0.06 * (1.0 + consumption_gf / max(1.0, sg))
    predation_sg = min(sg, 0.015 * sg * tw)

    # Wolf growth and decay
    tw_growth_rate = 0.04 * (1.0 + predation_sg / max(1.0, tw))
    tw_decay = 0.05

    # Harvesting limits tied to ecology populations
    harvest_ghost_flower = 0.0
    if gf > 10.0 and camps > 0:
        harvest_ghost_flower = min(gf * 0.1, float(random.randint(1, 2) * camps))
        gf -= harvest_ghost_flower

    harvest_lumber = min(sr, camps * 12.0 * pop_efficiency)
    sr = max(0.0, sr - harvest_lumber)

    # Non-lethal shearing vs cull
    harvest_fleece = 0.0
    if sg > 5.0 and camps > 0:
        harvest_fleece = min(sg * 0.05, float(random.randint(1, 2) * camps))
        sg = max(0.0, sg - harvest_fleece * 0.2) # shearing does not kill the whole beast

    # Non-lethal ozone-milk extraction
    harvest_ozone = 0.0
    if sg > 8.0 and docks > 0:
        harvest_ozone = min(sg * 0.06, float(random.randint(1, 3) * docks))

    wolf_hunt_efficiency = (watchtowers * 0.5 + barracks * 1.0)
    harvest_leather = camps * 4.0 * pop_efficiency
    if tw > 2.0 and wolf_hunt_efficiency > 0:
        extra_leather = min(tw * 0.2, float(random.randint(1, 2) * wolf_hunt_efficiency))
        tw = max(0.0, tw - extra_leather)
        harvest_leather += extra_leather

    # Baseline food gathering in non-chaos zones even without high local plant populations
    harvest_grain = farms * 15.0 * pop_efficiency * season_mod.get("growth", 1.0)
    if harvest_grain < 10.0 and g["chaos_level"] < 0.7:
        harvest_grain += float(farms * 4.0 * pop_efficiency) # Foraging backup baseline

    harvest_stone = mines * 10.0 * pop_efficiency
    harvest_ore = mines * 8.0 * pop_efficiency
    harvest_coal = mines * 6.0 * pop_efficiency
    
    # Rare resources chances
    harvest_dragonstone = 0.0
    if mines > 0 and random.random() < 0.15 * mines:
        harvest_dragonstone = float(random.randint(1, 3))

    harvest_nectar = 0.0
    if camps > 0 and random.random() < 0.15:
        harvest_nectar = float(random.randint(1, 2))

    # Apply updates to populations
    gf_new = gf + gf_growth_rate * gf * (1.0 - gf / 1000.0) - consumption_gf
    sr_new = sr + sr_growth_rate * sr * (1.0 - sr / 1000.0)
    sg_new = sg + sg_growth_rate * sg * (1.0 - sg / 500.0) - predation_sg
    tw_new = tw + (tw_growth_rate - tw_decay) * tw

    if weather_type == "Reality Storm":
        sg_new *= 0.90
        tw_new *= 0.85
        logs.append(f"🌀 TEMPORAL BLEED: Reality Storm causes temporal decay, reducing Sky-Grazer and Timber Wolf populations.")
    elif weather_type == "Static Drought":
        sg_new *= 0.85
        tw_new *= 0.90
        logs.append(f"☀️ DRY SPELL: Static Drought dehydrates the ecosystem, reducing fauna populations.")

    gf_new = max(0.0, min(1500.0, gf_new))
    sr_new = max(0.0, min(1500.0, sr_new))
    sg_new = max(0.0, min(1000.0, sg_new))
    tw_new = max(0.0, min(200.0, tw_new))

    g["flora_ghost_flower"] = gf_new
    g["flora_stone_root"] = sr_new
    g["fauna_sky_grazer"] = sg_new
    g["fauna_timber_wolf"] = tw_new

    # Add to inventory
    inventory["Grain"] += harvest_grain
    inventory["Lumber"] += harvest_lumber
    inventory["Leather"] += harvest_leather
    inventory["Stone"] += harvest_stone
    inventory["Iron Ore"] += harvest_ore
    inventory["Coal"] += harvest_coal
    inventory["Dragonstone"] += harvest_dragonstone
    inventory["Voltaic Fleece"] += harvest_fleece
    inventory["Ozone-Milk"] += harvest_ozone
    inventory["Ghost Flower"] += harvest_ghost_flower
    inventory["Night-Nectar"] += harvest_nectar

    # Domestic Facilities Processing (Domesticated Farming & Beast Training)
    greenhouses = int(g.get("domestic_greenhouses", 0))
    orchards = int(g.get("domestic_orchards", 0))
    pens = int(g.get("domestic_pens", 0))
    kennels = int(g.get("domestic_kennels", 0))

    # Greenhouse maintenance and output
    for _ in range(greenhouses):
        if inventory["Lumber"] >= 2.0:
            inventory["Lumber"] -= 2.0
            inventory["Ghost Flower"] += 1.5
            inventory["Night-Nectar"] += 1.0 # secondary alchemical resource

    # Orchard maintenance and output
    for _ in range(orchards):
        if inventory["Stone"] >= 1.5:
            inventory["Stone"] -= 1.5
            inventory["Lumber"] += 3.0
            inventory["Night-Nectar"] += 0.5 # secondary resin resource

    # Pen maintenance and output
    for _ in range(pens):
        if inventory["Grain"] >= 2.0:
            inventory["Grain"] -= 2.0
            inventory["Voltaic Fleece"] += 1.0
            inventory["Ozone-Milk"] += 2.0 # secondary food

    # Kennel maintenance and output (training wolves as tools/defense)
    for _ in range(kennels):
        if inventory["Ostrakan Hardtack"] >= 1.0:
            inventory["Ostrakan Hardtack"] -= 1.0
            inventory["Leather"] += 0.5

    # Calculate wealth rating and crime pressure scaling
    wealth = sum(inventory.values())

    # 3. Refining & Crafting (Production cycles)
    refined_steel = 0
    if inventory["Iron Ore"] >= 5 and inventory["Coal"] >= 3:
        craft_count = min(int(inventory["Iron Ore"] // 5), int(inventory["Coal"] // 3))
        craft_count = min(craft_count, 5)
        inventory["Iron Ore"] -= craft_count * 5
        inventory["Coal"] -= craft_count * 3
        inventory["Smelted Steel"] += craft_count
        refined_steel = craft_count

    flour_crafted = 0
    if inventory["Grain"] >= 4:
        craft_count = min(int(inventory["Grain"] // 4), 10)
        inventory["Grain"] -= craft_count * 4
        inventory["Flour"] += craft_count
        flour_crafted = craft_count

    rations_crafted = 0
    if inventory["Flour"] >= 2 and inventory["Leather"] >= 1:
        craft_count = min(int(inventory["Flour"] // 2), int(inventory["Leather"] // 1), 5)
        inventory["Flour"] -= craft_count * 2
        inventory["Leather"] -= craft_count * 1
        inventory["Ostrakan Hardtack"] += craft_count
        rations_crafted = craft_count

    batteries_crafted = 0
    if inventory["Dragonstone"] >= 2 and inventory["Coal"] >= 2:
        craft_count = min(int(inventory["Dragonstone"] // 2), int(inventory["Coal"] // 2), 2)
        inventory["Dragonstone"] -= craft_count * 2
        inventory["Coal"] -= craft_count * 2
        inventory["Refined Aether Battery"] += craft_count
        batteries_crafted = craft_count

    # 4. Social Well-Being Calculations
    kennel_bonus = kennels * 0.05 # Trained beasts boost safety and security ratings
    food_supply = min(1.0, (farms * FOOD_PER_FARM) + (docks * FOOD_PER_DOCK) + (inventory["Ostrakan Hardtack"] * 0.05) + (inventory["Ozone-Milk"] * 0.02))
    safety_rating = min(1.0, (watchtowers * SAFETY_PER_TOWER) + (walls * SAFETY_PER_WALL) + kennel_bonus)
    security_rating = min(1.0, barracks * SECURITY_PER_BARRACKS + kennel_bonus)

    phys_change = (food_supply + safety_rating) / 2.0 - WELLBEING_DECAY_RATE
    new_phys = max(0.0, min(1.0, g.get("physical_well_being", 1.0) + phys_change * 0.1))

    # Happiness buildings increase mental well-being
    happiness_bonus = (churches * 0.03) + (theatres * 0.03) + (arenas * 0.05)

    weather_multiplier = 1.5 if weather_type == "Reality Storm" else 1.0
    chaos_impact = g["chaos_level"] * weather_multiplier
    if magic_affinity == "Null":
        # Null leader stabilizes local minds against chaos
        chaos_impact *= 0.5
    mental_change = (1.0 - chaos_impact) + (1.0 - g.get("crime_level", 0.0)) - 1.0 + happiness_bonus
    
    # Leader Alignment passive pressure
    if alignment == "Heroic":
        mental_change += 0.10
    new_mental = max(0.0, min(1.0, g.get("mental_well_being", 1.0) + mental_change * 0.1))

    discontent_pressure = (2.0 - new_phys - new_mental) / 2.0
    new_discontent = max(0.0, min(1.0, g.get("discontent", 0.0) + (discontent_pressure - 0.4) * 0.15))

    # Crime pressure scales with wealth and alignment
    crime_pressure = new_discontent - security_rating + (wealth * 0.0003)
    if alignment == "Heroic":
        crime_pressure -= 0.15
    elif alignment == "Villainous":
        crime_pressure += 0.15
        # Villain drains local silos
        inventory["Grain"] = max(0.0, inventory["Grain"] - 2.0)
        inventory["Lumber"] = max(0.0, inventory["Lumber"] - 1.0)
        if random.random() < 0.20:
            logs.append(f"💸 TAXATION: Villainous leader {paragon['name']} siphoned 2 Grain and 1 Lumber from public reserves for personal wealth.")
            
    new_crime = max(0.0, min(1.0, g.get("crime_level", 0.0) + crime_pressure * 0.1))

    # Non-faction criminal structures built by Cartel or Barons under high crime
    gambling_dens = g.get("gambling_dens_count", 0)
    black_markets = g.get("black_markets_count", 0)
    if new_crime > 0.4 and random.random() < 0.15:
        if random.random() < 0.5 and gambling_dens < 3:
            g["gambling_dens_count"] = gambling_dens + 1
            gambling_dens += 1
            logs.append(f"🎲 SYNDICATE: The Obsidian Cartel established a new Gambling Den in {g['name']} due to high crime!")
        elif black_markets < 3:
            g["black_markets_count"] = black_markets + 1
            black_markets += 1
            logs.append(f"🕶️ SYNDICATE: Smugglers set up a Black Market in {g['name']} to move illegal assets!")

    # Illicit structure drains and crime boosts
    new_crime = min(1.0, new_crime + (gambling_dens * 0.02) + (black_markets * 0.03))
    if gambling_dens > 0:
        inventory["Grain"] = max(0.0, inventory["Grain"] - float(gambling_dens * 2.0))
    if black_markets > 0:
        if inventory.get("Smelted Steel", 0.0) >= black_markets * 0.5:
            inventory["Smelted Steel"] -= black_markets * 0.5
        if inventory.get("Dragonstone", 0.0) >= black_markets * 0.2:
            inventory["Dragonstone"] -= black_markets * 0.2

    event = "Stable"
    if new_discontent >= REVOLUTION_DISCONTENT_LIMIT and new_crime >= REVOLUTION_CRIME_LIMIT:
        event = "Revolution"
    elif new_discontent >= RIOT_DISCONTENT_LIMIT and new_crime >= RIOT_CRIME_LIMIT:
        event = "Rioting"

    # Present Unrest Events (Riots/Revolutions) to Paragon Leader for Decision
    if event in ["Rioting", "Revolution"] and paragon:
        p_stats = paragon["stats"]
        p_traits = paragon["traits"]
        p_decision = "Observe Unrest"
        
        if alignment == "Villainous":
            p_decision = "Brutal Crackdown"
        elif alignment == "Heroic":
            p_decision = "Heroic Negotiation"
        elif p_stats["Might"] >= 12 or "Short-tempered" in p_traits or "War Survivor" in p_traits:
            p_decision = "Violent Quell"
        elif p_stats["Charm"] >= 12 or "Diplomat" in p_traits:
            p_decision = "Diplomatic Compromise"
        elif p_stats["Logic"] >= 10 or "Sage" in p_traits:
            p_decision = "Logistical Sweeps"
            
        if p_decision == "Brutal Crackdown":
            casualties = int(new_pop * 0.06)
            new_pop = max(100.0, new_pop - casualties)
            new_discontent = max(0.0, new_discontent - 0.20)
            new_crime = max(0.0, new_crime - 0.15)
            logs.append(f"🚨 BRUTAL CRACKDOWN: Villainous leader {paragon['name']} dispatched heavily armed guards to crush the {event}! Order was brutally enforced, killing {casualties} citizens.")
            paragon["recent_decisions"].append(f"Brutally suppressed unrest via militia crackdown.")
            event = "Stable"
        elif p_decision == "Heroic Negotiation":
            new_discontent = max(0.0, new_discontent - 0.35)
            new_mental = min(1.0, new_mental + 0.15)
            logs.append(f"🤝 HEROIC RESOLVE: Heroic leader {paragon['name']} negotiated with riot leaders and distributed personal funds, peaceful resolution attained without casualties.")
            paragon["recent_decisions"].append(f"Safely resolved {event} through heroic negotiation.")
            event = "Stable"
        elif p_decision == "Violent Quell":
            casualties = int(new_pop * 0.03)
            new_pop = max(100.0, new_pop - casualties)
            new_discontent = max(0.0, new_discontent - 0.15)
            new_crime = max(0.0, new_crime - 0.20)
            logs.append(f"🚨 PARAGON SUPPRESSION: {paragon['name']} violently quelled the {event} using guard enforcement, causing {casualties} civilian casualties but restoring raw order.")
            paragon["recent_decisions"].append(f"Violently suppressed regional {event}.")
            event = "Stable"
        elif p_decision == "Diplomatic Compromise":
            pacified = False
            for res_key in ["Grain", "Lumber"]:
                if inventory.get(res_key, 0.0) >= 15.0:
                    inventory[res_key] -= 15.0
                    new_discontent = max(0.0, new_discontent - 0.25)
                    new_mental = min(1.0, new_mental + 0.10)
                    logs.append(f"🤝 PARAGON DIPLOMACY: {paragon['name']} resolved the {event} diplomatically by offering 15 {res_key} to appease the citizen grievances.")
                    paragon["recent_decisions"].append(f"Negotiated peace for {event} using {res_key} reserves.")
                    pacified = True
                    event = "Stable"
                    break
            if not pacified:
                p_decision = "Observe Unrest"
        elif p_decision == "Logistical Sweeps":
            new_discontent = max(0.0, new_discontent - 0.10)
            new_crime = min(1.0, new_crime + 0.05)
            logs.append(f"🧠 PARAGON LOGISTICS: {paragon['name']} diverted the {event} using logistical sweeps and scheduling changes, mildly stabilizing discontent.")
            paragon["recent_decisions"].append(f"Logistically redirected unrest during {event}.")
            
        if p_decision == "Observe Unrest":
            logs.append(f"⚠️ PARAGON HESITATION: {paragon['name']} hesitated to act against the {event}, allowing the unrest to lock down output.")
            paragon["recent_decisions"].append(f"Observed {event} with passive response.")

    trader_status = "Inactive"
    if food_supply >= TRADE_ABUNDANCE_LEVEL:
        trader_status = "Active - Trade Route Established"

    # 5. Dynamic Construction (Including Domesticated Farms, Beast Kennels, Happiness buildings)
    built_structure = None
    if inventory["Lumber"] >= 40 and inventory["Stone"] >= 40:
        if food_supply < 0.6:
            cost = BUILDING_COSTS["farms"]
            if inventory["Lumber"] >= cost["Lumber"] and inventory["Stone"] >= cost["Stone"]:
                inventory["Lumber"] -= cost["Lumber"]
                inventory["Stone"] -= cost["Stone"]
                g["farms_count"] += 1
                built_structure = "Farm"
        elif safety_rating < 0.6:
            cost = BUILDING_COSTS["watchtowers"]
            if inventory["Lumber"] >= cost["Lumber"] and inventory["Stone"] >= cost["Stone"]:
                inventory["Lumber"] -= cost["Lumber"]
                inventory["Stone"] -= cost["Stone"]
                g["watchtowers_count"] += 1
                built_structure = "Watchtower"
        elif new_crime > 0.4 and inventory["Smelted Steel"] >= 20:
            cost = BUILDING_COSTS["barracks"]
            if inventory["Lumber"] >= cost["Lumber"] and inventory["Stone"] >= cost["Stone"] and inventory["Smelted Steel"] >= cost["Smelted Steel"]:
                inventory["Lumber"] -= cost["Lumber"]
                inventory["Stone"] -= cost["Stone"]
                inventory["Smelted Steel"] -= cost["Smelted Steel"]
                g["barracks_count"] += 1
                built_structure = "Barracks"
        elif new_mental < 0.6:
            # Construct a happiness building
            if churches <= theatres and inventory["Lumber"] >= 40 and inventory["Stone"] >= 60:
                inventory["Lumber"] -= 40
                inventory["Stone"] -= 60
                g["churches_count"] = churches + 1
                built_structure = "Church"
            elif theatres <= arenas and inventory["Lumber"] >= 50 and inventory["Stone"] >= 30:
                inventory["Lumber"] -= 50
                inventory["Stone"] -= 30
                g["theatres_count"] = theatres + 1
                built_structure = "Theatre"
            elif inventory["Lumber"] >= 60 and inventory["Stone"] >= 80:
                inventory["Lumber"] -= 60
                inventory["Stone"] -= 80
                g["arenas_count"] = arenas + 1
                built_structure = "Arena"
        elif g["flora_ghost_flower"] > 50 and greenhouses < 3:
            cost = BUILDING_COSTS["greenhouse"]
            if inventory["Lumber"] >= cost["Lumber"] and inventory["Stone"] >= cost["Stone"]:
                inventory["Lumber"] -= cost["Lumber"]
                inventory["Stone"] -= cost["Stone"]
                g["domestic_greenhouses"] = greenhouses + 1
                built_structure = "Ghost Flower Greenhouse"
        elif g["flora_stone_root"] > 50 and orchards < 3:
            cost = BUILDING_COSTS["orchard"]
            if inventory["Lumber"] >= cost["Lumber"] and inventory["Stone"] >= cost["Stone"]:
                inventory["Lumber"] -= cost["Lumber"]
                inventory["Stone"] -= cost["Stone"]
                g["domestic_orchards"] = orchards + 1
                built_structure = "Stone-Root Orchard"
        elif g["fauna_sky_grazer"] > 25 and pens < 3:
            cost = BUILDING_COSTS["pen"]
            if inventory["Lumber"] >= cost["Lumber"] and inventory["Stone"] >= cost["Stone"]:
                inventory["Lumber"] -= cost["Lumber"]
                inventory["Stone"] -= cost["Stone"]
                g["domestic_pens"] = pens + 1
                built_structure = "Sky-Grazer Pen"
        elif g["fauna_timber_wolf"] > 5 and kennels < 3:
            cost = BUILDING_COSTS["kennel"]
            if inventory["Lumber"] >= cost["Lumber"] and inventory["Stone"] >= cost["Stone"]:
                inventory["Lumber"] -= cost["Lumber"]
                inventory["Stone"] -= cost["Stone"]
                g["domestic_kennels"] = kennels + 1
                built_structure = "Wolf Kennel (Trained Defense)"
        else:
            cost = BUILDING_COSTS["mines"]
            if inventory["Lumber"] >= cost["Lumber"] and inventory["Stone"] >= cost["Stone"]:
                inventory["Lumber"] -= cost["Lumber"]
                inventory["Stone"] -= cost["Stone"]
                g["mines_count"] += 1
                built_structure = "Mine"

    if built_structure:
        logs.append(f"🏗️ CONSTRUCTION: {g['name']} constructed a new {built_structure} to expand infrastructure.")

    # 6. Trade
    traded = False
    if trader_status == "Active - Trade Route Established" and random.random() < 0.30:
        if inventory["Ostrakan Hardtack"] >= 5:
            inventory["Ostrakan Hardtack"] -= 5
            inventory["Lumber"] += 15
            inventory["Stone"] += 15
            logs.append(f"🌾 TRADE: {g['name']} traded 5 units of Ostrakan Hardtack for 15 Lumber and 15 Stone via river channels.")
            traded = True
        elif inventory["Smelted Steel"] >= 3:
            inventory["Smelted Steel"] -= 3
            inventory["Stone"] += 25
            logs.append(f"⚔️ TRADE: {g['name']} exported 3 units of Smelted Steel to acquire 25 building Stone.")
            traded = True

    # 7. Wildlife Clashes (Coupled with populations, mitigated by barracks route patrol and Paragon)
    if random.random() < 0.12:
        beast_name = random.choice(["Sky-Grazer", "Cloud-Cutter Ray", "Timber Wolf", "Wild Boar"])
        p_decision = "Standard Defense"
        if paragon:
            p_stats = paragon["stats"]
            p_traits = paragon["traits"]
            if alignment == "Villainous":
                p_decision = "Ignore Danger"
            elif alignment == "Heroic":
                p_decision = "Guardian Shield"
            elif p_stats["Might"] >= 10 or p_stats["Finesse"] >= 10:
                p_decision = "Direct Hunt"
            elif p_stats["Awareness"] >= 10 or p_stats["Intuition"] >= 10:
                p_decision = "Evacuation"
            elif p_stats["Knowledge"] >= 10 or p_stats["Logic"] >= 10:
                p_decision = "Bait/Trap"

        if p_decision == "Ignore Danger":
            if beast_name == "Cloud-Cutter Ray":
                pop_loss = int(new_pop * 0.04)
                new_pop = max(100.0, new_pop - pop_loss)
                logs.append(f"🚨 WILDLIFE TERROR: Villainous leader {paragon['name']} ignored the {beast_name} threat! Citizens were left to fend for themselves, doubling casualties to {pop_loss}.")
            else:
                new_phys = max(0.0, new_phys - 0.10)
                logs.append(f"🚨 WILDLIFE TERROR: Villainous leader {paragon['name']} abandoned outlying camps to the {beast_name}, causing massive supply lanes panic.")
            paragon["recent_decisions"].append(f"Ignored threat of wild {beast_name}.")
            
        elif p_decision == "Guardian Shield":
            logs.append(f"🛡️ GUARDIAN SHIELD: Heroic leader {paragon['name']} personally guarded the borders from the wild {beast_name}, preventing all civilian casualties.")
            paragon["recent_decisions"].append(f"Protected citizenry from wild {beast_name}.")
            
        elif p_decision == "Direct Hunt":
            injury_risk = 0.25 if "Short-tempered" in p_traits else 0.10
            injured = False
            if random.random() < injury_risk:
                paragon["stats"]["Endurance"] = max(1, paragon["stats"]["Endurance"] - 1)
                injured = True
            
            if beast_name == "Cloud-Cutter Ray":
                inventory["Voltaic Fleece"] = inventory.get("Voltaic Fleece", 0.0) + 4.0
                logs.append(f"🤠 PARAGON HUNT: {paragon['name']} led a Direct Hunt on the Cloud-Cutter Ray! Slew the beast and harvested 4 Voltaic Fleece.{' The leader was injured.' if injured else ''}")
            elif beast_name == "Timber Wolf":
                inventory["Leather"] = inventory.get("Leather", 0.0) + 4.0
                g["fauna_timber_wolf"] = max(0.0, g["fauna_timber_wolf"] - 3.0)
                logs.append(f"🤠 PARAGON HUNT: {paragon['name']} hunted down the Timber Wolf pack, acquiring 4 Leather.{' The leader was wounded.' if injured else ''}")
            else:
                inventory["Leather"] = inventory.get("Leather", 0.0) + 2.0
                logs.append(f"🤠 PARAGON HUNT: {paragon['name']} hunted the charging {beast_name}, acquiring 2 Leather.")
            
            paragon["recent_decisions"].append(f"Hunted down wild {beast_name}.")
        
        elif p_decision == "Evacuation":
            logs.append(f"🤠 PARAGON EVACUATION: {paragon['name']} ordered local herders to evacuate from the {beast_name}'s path, suffering zero casualties.")
            paragon["recent_decisions"].append(f"Evacuated fields from {beast_name}.")
            
        elif p_decision == "Bait/Trap":
            if inventory.get("Grain", 0.0) >= 3.0:
                inventory["Grain"] -= 3.0
                if beast_name == "Cloud-Cutter Ray":
                    inventory["Voltaic Fleece"] = inventory.get("Voltaic Fleece", 0.0) + 2.0
                elif beast_name == "Timber Wolf":
                    inventory["Leather"] = inventory.get("Leather", 0.0) + 2.0
                else:
                    inventory["Leather"] = inventory.get("Leather", 0.0) + 1.0
                logs.append(f"🤠 PARAGON TRAP: {paragon['name']} set alchemical traps baited with 3 Grain, safely catching the {beast_name}.")
                paragon["recent_decisions"].append(f"Trapped wild {beast_name} safely.")
            else:
                p_decision = "Standard Defense"

        if p_decision == "Standard Defense":
            if beast_name == "Cloud-Cutter Ray":
                if barracks > 0 or watchtowers > 1:
                    logs.append(f"🦅 WILDLIFE: A giant Cloud-Cutter Ray swooped down on {g['name']} settlements but was driven off by the military route patrols.")
                else:
                    pop_loss = int(new_pop * 0.02)
                    new_pop = max(100.0, new_pop - pop_loss)
                    logs.append(f"🚨 WILDLIFE THREAT: An aggressive Cloud-Cutter Ray raided {g['name']}, causing {pop_loss} casualties among the population.")
            elif beast_name == "Sky-Grazer":
                if g["fauna_sky_grazer"] > 5:
                    if g["chaos_level"] > 0.6:
                        pop_loss = int(new_pop * 0.01)
                        new_pop = max(100.0, new_pop - pop_loss)
                        g["fauna_sky_grazer"] = max(0.0, g["fauna_sky_grazer"] - 2.0)
                        logs.append(f"💥 EXPLOSION: A panicked Sky-Grazer experienced an electrical blowout over {g['name']} pastures, injuring {pop_loss} workers.")
                    else:
                        inventory["Voltaic Fleece"] += 2
                        g["fauna_sky_grazer"] = max(0.0, g["fauna_sky_grazer"] - 1.0)
                        logs.append(f"🐏 WILDLIFE: Herders in {g['name']} successfully shored and harvested 2 Voltaic Fleece from migrating Sky-Grazers.")
            elif beast_name == "Timber Wolf":
                if g["fauna_timber_wolf"] > 2:
                    if watchtowers > 0 or barracks > 0:
                        inventory["Leather"] += 2
                        g["fauna_timber_wolf"] = max(0.0, g["fauna_timber_wolf"] - 2.0)
                        logs.append(f"🐺 WILDLIFE: Watchtowers or military patrols in {g['name']} spotted a Timber Wolf pack early; they eliminated them and harvested 2 Leather hides.")
                    else:
                        new_phys = max(0.0, new_phys - 0.05)
                        logs.append(f"⚠️ WILDLIFE: A Timber Wolf pack raided the outskirts of {g['name']}, disrupting local supply lanes and reducing safety.")
            else:
                inventory["Leather"] += 1
                logs.append(f"🐗 WILDLIFE: Hunters in {g['name']} tracked down a charging Wild Boar, acquiring 1 unit of raw Leather.")
            if paragon:
                paragon["recent_decisions"].append(f"Guards managed wildlife clash with {beast_name}.")

    # 7.5. Bandit Raids (Mitigated by barracks patrols and Paragon decisions)
    if random.random() < 0.08:
        p_decision = "Standard Defense"
        if paragon:
            p_stats = paragon["stats"]
            p_traits = paragon["traits"]
            if alignment == "Villainous":
                p_decision = "Collude Bribe"
            elif alignment == "Heroic":
                p_decision = "Heroic Charge"
            elif p_stats["Might"] >= 12 or "War Survivor" in p_traits:
                p_decision = "Proactive Assault"
            elif p_stats["Charm"] >= 12 or "Diplomat" in p_traits:
                p_decision = "Negotiated Bribe"
            elif p_stats["Fortitude"] >= 12:
                p_decision = "Defensive Fortify"

        if p_decision == "Collude Bribe":
            new_crime = min(1.0, new_crime + 0.10)
            stolen_lumber = min(inventory["Lumber"], 6.0)
            stolen_stone = min(inventory["Stone"], 6.0)
            inventory["Lumber"] -= stolen_lumber
            inventory["Stone"] -= stolen_stone
            logs.append(f"💸 BANDIT COLLUSION: Villainous leader {paragon['name']} accepted kickbacks from bandits, allowing them to plunder {stolen_lumber:.0f} Lumber and {stolen_stone:.0f} Stone.")
            paragon["recent_decisions"].append("Colluded with bandit raiders.")
        elif p_decision == "Heroic Charge":
            new_crime = max(0.0, new_crime - 0.12)
            logs.append(f"⚔️ HEROIC CHARGE: Heroic leader {paragon['name']} personally charged the bandit ambush, routing them completely with zero guard casualties!")
            paragon["recent_decisions"].append("Heroically defeated bandit ambush.")
        elif p_decision == "Proactive Assault":
            injury_risk = 0.30 if "Short-tempered" in p_traits else 0.15
            injured = False
            if random.random() < injury_risk:
                paragon["stats"]["Vitality"] = max(1, paragon["stats"]["Vitality"] - 1)
                injured = True
            new_crime = max(0.0, new_crime - 0.08)
            logs.append(f"⚔️ PARAGON PROACTIVE STRIKE: {paragon['name']} led a proactive strike on the bandit camp, scattering them.{' The leader was wounded.' if injured else ''}")
            paragon["recent_decisions"].append("Assaulted bandit hideout proactive.")
        elif p_decision == "Negotiated Bribe":
            bribed = False
            for res_key in ["Grain", "Lumber", "Stone"]:
                if inventory.get(res_key, 0.0) >= 10.0:
                    inventory[res_key] -= 10.0
                    logs.append(f"🤝 PARAGON NEGOTIATION: {paragon['name']} negotiated with the bandit chieftain, paying a bribe of 10 {res_key} to bypass the caravan routes safely.")
                    paragon["recent_decisions"].append(f"Bribed bandits using {res_key}.")
                    bribed = True
                    break
            if not bribed:
                p_decision = "Standard Defense"
        elif p_decision == "Defensive Fortify":
            if walls > 0:
                logs.append(f"🏰 PARAGON FORTIFICATION: {paragon['name']} withdrew all workers behind the stone walls, blocking the bandit raid with zero losses.")
                paragon["recent_decisions"].append("Deflected raid behind defensive walls.")
            else:
                stolen_lumber = min(inventory["Lumber"], 4.0)
                stolen_stone = min(inventory["Stone"], 4.0)
                inventory["Lumber"] -= stolen_lumber
                inventory["Stone"] -= stolen_stone
                new_phys = max(0.0, new_phys - 0.01)
                logs.append(f"🚨 BANDIT RAID: Fortify order failed due to lack of walls in {g['name']}. Bandits plundered {stolen_lumber:.0f} Lumber and {stolen_stone:.0f} Stone.")
                paragon["recent_decisions"].append("Attempted hunker down without walls.")

        if p_decision == "Standard Defense":
            if barracks > 0:
                logs.append(f"⚔️ PATROL SECURED: Route patrols from barracks routed a bandit ambush on {g['name']}'s shipping lanes.")
            else:
                stolen_lumber = min(inventory["Lumber"], 8.0)
                stolen_stone = min(inventory["Stone"], 8.0)
                inventory["Lumber"] -= stolen_lumber
                inventory["Stone"] -= stolen_stone
                new_phys = max(0.0, new_phys - 0.02)
                logs.append(f"🚨 BANDIT RAID: Bandits pillaged trade routes in {g['name']}! Stole {stolen_lumber:.0f} Lumber, {stolen_stone:.0f} Stone and injured workers.")
            if paragon:
                paragon["recent_decisions"].append("Left bandit ambush to guards.")

    # 8. Alchemical Successes
    if inventory["Ghost Flower"] >= 2 and random.random() < 0.30:
        inventory["Ghost Flower"] -= 2
        new_mental = min(1.0, new_mental + 0.15)
        new_discontent = max(0.0, new_discontent - 0.10)
        logs.append(f"🧪 ALCHEMY: Druids in {g['name']} refined Ghost Flowers into Aether-Clear medicine, clearing mental static and soothing unrest.")

    # 9. Cult Population, Infiltration & Devoted Subdivision
    if "cult_population" not in g:
        g["cult_population"] = g["population"] * g.get("cult_infiltration", 0.05)
    
    if "cult_devoted" not in g:
        g["cult_devoted"] = g["cult_population"] * 0.20

    # Recruits based on physical well-being (health), discontent, and crime
    cult_recruits = g["population"] * ((1.0 - new_phys) * 0.002 + new_discontent * 0.003 + new_crime * 0.005)
    g["cult_population"] = min(g["population"], max(0.0, g["cult_population"] + cult_recruits))
    
    # 15% of recruits join the Devoted priests based near the prison
    new_devoted = cult_recruits * 0.15
    g["cult_devoted"] = min(g["cult_population"], max(0.0, g["cult_devoted"] + new_devoted))
    g["cult_infiltration"] = g["cult_population"] / max(1.0, g["population"])
    
    # Devoted cultists actively weaken local prison seal
    seal_degrade = g["cult_devoted"] * 0.00003
    prisons[magistar] = max(0.0, prisons[magistar] - seal_degrade)
    if seal_degrade > 0.0005:
        logs.append(f"👁️ CULT DEVOTED: Devoted priests near {magistar} Prison weakened the seal by {seal_degrade*100:.3f}%.")

    # Cultist spread to adjacent factions (Secret Network extension)
    spread_target = None
    if g["cult_infiltration"] > 0.20 and random.random() < 0.30:
        adj_list = FACTION_ADJACENCY.get(g["name"], [])
        if adj_list:
            target_faction_name = random.choice(adj_list)
            spread_amount = int(g["cult_population"] * 0.02)
            if spread_amount > 0:
                spread_target = (target_faction_name, spread_amount)

    if g["cult_infiltration"] > 0.40 and random.random() < 0.25:
        # Paragon decision for Cult Infiltration Sabotage
        p_decision = "Unaware"
        if paragon:
            p_stats = paragon["stats"]
            p_traits = paragon["traits"]
            if alignment == "Villainous":
                p_decision = "Accept Cult Bribes"
            elif alignment == "Heroic":
                p_decision = "Heroic Counterintelligence"
            elif p_stats["Willpower"] >= 12 or "Zealous" in p_traits or "Highly Spiritual" in p_traits:
                p_decision = "Inquisition Purge"
            elif p_stats["Logic"] >= 12 or p_stats["Awareness"] >= 12:
                p_decision = "Counter Intelligence"

        sabotaged_structure = None
        if p_decision == "Accept Cult Bribes":
            prisons[magistar] = max(0.0, prisons[magistar] - 0.10)
            logs.append(f"👁️ CULT COLLUSION: Villainous leader {paragon['name']} took a bribe from cultists and deliberately ignored structural sabotage, weakening {magistar} Prison by 10.0%!")
            paragon["recent_decisions"].append("Permitted prison seal sabotage for bribes.")
        elif p_decision == "Heroic Counterintelligence":
            g["cult_population"] = max(0.0, g["cult_population"] * 0.50)
            g["cult_infiltration"] = g["cult_population"] / max(1.0, g["population"])
            logs.append(f"👁️ HEROIC INVESTIGATION: Heroic leader {paragon['name']} uncovered a deep cult cell network, arresting conspirators without causing panic.")
            paragon["recent_decisions"].append("Dismantled cult ring via counterintelligence.")
        elif p_decision == "Inquisition Purge":
            g["cult_population"] = max(0.0, g["cult_population"] * 0.70)
            g["cult_infiltration"] = g["cult_population"] / max(1.0, g["population"])
            new_discontent = min(1.0, new_discontent + 0.15)
            logs.append(f"👁️ PARAGON INQUISITION: {paragon['name']} executed an Inquisition Purge, hunting cultists down but sparking regional panic and discontent.")
            paragon["recent_decisions"].append("Ordered Inquisition Purge against cult infiltration.")
        elif p_decision == "Counter Intelligence":
            foil_chance = 0.85 if "Vigilant" in p_traits else 0.65
            if random.random() < foil_chance:
                g["cult_population"] = max(0.0, g["cult_population"] * 0.90)
                g["cult_infiltration"] = g["cult_population"] / max(1.0, g["population"])
                logs.append(f"👁️ PARAGON COUNTER-INTEL: {paragon['name']} intercepted secret communications and foiled a cultist sabotage plot.")
                paragon["recent_decisions"].append("Foiled cult sabotage plot via spy interception.")
            else:
                p_decision = "Unaware"

        if p_decision == "Unaware":
            # Trigger infiltration sabotage
            prisons[magistar] = max(0.0, prisons[magistar] - 0.06)
            if barracks > 0 and random.random() < 0.5:
                g["barracks_count"] = max(0, barracks - 1)
                sabotaged_structure = "Barracks"
            elif watchtowers > 0 and random.random() < 0.5:
                g["watchtowers_count"] = max(0, watchtowers - 1)
                sabotaged_structure = "Watchtower"
            else:
                g["farms_count"] = max(0, farms - 1)
                sabotaged_structure = "Farm"
            logs.append(f"⚠️ SABOTAGE: Chaos Cultists infiltrated positions of power in {g['name']} and sabotaged a {sabotaged_structure}! They weakened the seal of {magistar} Prison.")
            if paragon:
                paragon["recent_decisions"].append(f"Infiltration bypassed alerts; {sabotaged_structure} sabotaged.")

    # 10. Grey Warden Recruitment, Patrols, and Hunter Deployments
    if "warden_population" not in prisons:
        prisons["warden_population"] = 1500.0
    
    # Wardens recruit EXCLUSIVELY from Sparkborn (which is 50% of population)
    sparkborn_pool = new_pop * 0.5
    warden_recruits = sparkborn_pool * g["chaos_level"] * g["pressure"] * 0.002
    
    # Deduct recruits from population as they depart for the Spire
    new_pop = max(100.0, new_pop - warden_recruits)
    prisons["warden_recruits_accumulated"] = prisons.get("warden_recruits_accumulated", 0.0) + warden_recruits
    
    # Allocate Warden Sentinels to Patrols and Hunters locally
    # Patrols protect chaos zones (scaled by local chaos and proximity to Spire at Convergence edge)
    proximity_to_spire = 1.0 - g.get("distance_to_convergence", 0.6)
    patrol_priority = (g["chaos_level"] + proximity_to_spire) / 2.0
    allocated_patrols = (prisons["warden_population"] / 17.0) * patrol_priority * 1.5
    
    # Hunters hunt cultists (scaled by infiltration and proximity to local prison structures)
    proximity_to_prison = 1.0 - g.get("distance_to_chaos_structure", 0.5)
    hunter_priority = (g["cult_infiltration"] + proximity_to_prison) / 2.0
    allocated_hunters = (prisons["warden_population"] / 17.0) * hunter_priority * 1.5

    # Chaos suppression by patrols
    chaos_reduction = 0.03 * (allocated_patrols / 100.0)
    g["chaos_level"] = max(0.0, g["chaos_level"] - chaos_reduction)
    if chaos_reduction > 0.003:
        logs.append(f"🛡️ PATROL: Warden patrols ({allocated_patrols:.0f} sentinels) suppressed chaos by {chaos_reduction*100:.2f}%.")

    # Cultist eradication by hunters
    kill_rate = 0.05 * (allocated_hunters / 100.0)
    killed_network = int(g["cult_population"] * kill_rate)
    g["cult_population"] = max(0.0, g["cult_population"] - killed_network)
    
    killed_devoted = 0
    if g["cult_devoted"] > 0:
        killed_devoted = int(g["cult_devoted"] * kill_rate * 0.5)
        g["cult_devoted"] = max(0.0, g["cult_devoted"] - killed_devoted)
        
    total_killed = killed_network + killed_devoted
    if total_killed > 0:
        logs.append(f"⚔️ HUNTERS: Warden Hunters ({allocated_hunters:.0f} rangers) executed {total_killed} cultists (incl. {killed_devoted} Devoted) in {g['name']}.")

    # Autonomous prison repairs
    if prisons[magistar] < 1.0:
        warden_efficiency = prisons["warden_population"] / 1500.0
        repaired_val = 0.02 * warden_efficiency
        prisons[magistar] = min(1.0, prisons[magistar] + repaired_val)
        logs.append(f"🛡️ WARDENS: Grey Wardens (efficiency {warden_efficiency:.2f}) autonomously reinforced the {magistar} Prison seal by {repaired_val * 100:.2f}%. Current integrity: {prisons[magistar] * 100:.0f}%.")

    # 11. Magistar Prison Spike Effects
    proximity = g.get("distance_to_chaos_structure", 0.5)
    spike_chance = 0.30 * (1.0 - proximity)
    if g["is_active"] and random.random() < spike_chance:
        # Also 5% chance to convert 1% of population to cultists due to chaos trauma
        if random.random() < 0.05:
            trauma_converted = int(g["population"] * 0.01)
            g["cult_population"] = min(g["population"], g["cult_population"] + trauma_converted)
            g["cult_infiltration"] = g["cult_population"] / max(1.0, g["population"])
            logs.append(f"👁️ CULT SURGE: Chaos trauma from reality spike converted {trauma_converted} citizens into Cultists in {g['name']}!")
        
        if magistar == "Tiraton":
            if walls > 0:
                g["walls_count"] -= 1
                logs.append(f"🌀 REALITY SPIKE: Tiraton's extreme gravity prison field collapsed a wall segment in {g['name']}!")
            else:
                new_phys = max(0.0, new_phys - 0.08)
                logs.append(f"🌀 REALITY SPIKE: Tiraton's gravity spike crushed structures in {g['name']}, injuring citizens.")
        elif magistar == "Stagus":
            inventory["Grain"] = max(0.0, inventory["Grain"] - 5.0)
            logs.append(f"❄️ REALITY SPIKE: Stagus's thermal stillness froze the silos of {g['name']} , ruining some stored Grain.")
        elif magistar == "Metrion":
            new_crime = min(1.0, new_crime + 0.10)
            g["chaos_level"] = min(1.0, g["chaos_level"] + 0.05)
            logs.append(f"🔮 REALITY SPIKE: Metrion's logic decay infected the minds of {g['name']} , triggering erratic behaviors.")

    # Sparkborn leader magic discharge check
    discharge_chance = 0.0
    if "Sparkborn" in magic_affinity:
        tier = magic_affinity.split(" - ")[-1]
        tier_chances = {"Sensitive": 0.03, "Attuned": 0.06, "Adept": 0.12, "Wielder": 0.22, "Master": 0.35, "Epic": 0.55}
        discharge_chance = tier_chances.get(tier, 0.0)

    if discharge_chance > 0.0 and random.random() < discharge_chance:
        # Magical feedback slightly degrades local prison seal and increases local chaos
        prisons[magistar] = max(0.0, prisons[magistar] - 0.03)
        g["chaos_level"] = min(1.0, g["chaos_level"] + 0.04)
        logs.append(f"🔮 MAGIC FEEDBACK: Sparkborn leader {paragon['name']} ({magic_affinity}) experienced a magical spike, degrading {magistar} Prison seal by 3.0% and increasing local chaos by 4.0%!")

    # Tag-based interaction system resolver
    from tag_system import apply_tag_interactions
    active_tags = apply_tag_interactions(g, inventory, weather, prisons, logs)

    # Calculate population counts
    sparkborn_pop = new_pop * 0.5
    null_pop = new_pop * 0.5

    return {
        "population": new_pop,
        "active_tags": active_tags,
        "sparkborn_population": sparkborn_pop,
        "null_population": null_pop,
        "sparkborn_sensitive": sparkborn_pop * 0.35,
        "sparkborn_attuned": sparkborn_pop * 0.30,
        "sparkborn_adept": sparkborn_pop * 0.20,
        "sparkborn_wielder": sparkborn_pop * 0.10,
        "sparkborn_master": sparkborn_pop * 0.04,
        "sparkborn_epic": sparkborn_pop * 0.01,
        "physical_well_being": new_phys,
        "mental_well_being": new_mental,
        "discontent": new_discontent,
        "crime_level": new_crime,
        "food_supply": food_supply,
        "safety_rating": safety_rating,
        "security_rating": security_rating,
        "event": event,
        "trader_status": trader_status,
        "inventory": inventory,
        "logs": logs,
        "prisons": prisons,
        "cult_population": g["cult_population"],
        "cult_infiltration": g["cult_infiltration"],
        "cult_devoted": g["cult_devoted"],
        "allocated_patrols": allocated_patrols,
        "allocated_hunters": allocated_hunters,
        "spread_target": spread_target,
        "flora_ghost_flower": g["flora_ghost_flower"],
        "flora_stone_root": g["flora_stone_root"],
        "fauna_sky_grazer": g["fauna_sky_grazer"],
        "fauna_timber_wolf": g["fauna_timber_wolf"],
        "domestic_greenhouses": g["domestic_greenhouses"],
        "domestic_orchards": g["domestic_orchards"],
        "domestic_pens": g["domestic_pens"],
        "domestic_kennels": g["domestic_kennels"],
        "churches_count": g["churches_count"],
        "theatres_count": g["theatres_count"],
        "arenas_count": g["arenas_count"],
        "gambling_dens_count": g["gambling_dens_count"],
        "black_markets_count": g["black_markets_count"],
        "paragon": g["paragon"]
    }
