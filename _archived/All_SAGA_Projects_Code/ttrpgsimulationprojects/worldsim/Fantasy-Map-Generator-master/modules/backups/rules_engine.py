# rules_engine.py
# Calculates town size scores, unlocks, population well-being stats,
# resource gathering, production/crafting, dynamic construction, trading,
# wildlife encounters, alchemical lore events, Cult Infiltration, Prison/Warden physics,
# population death, paragon death/succession, and ecology integration.

import sys
import os
import random

# Ensure project root is in path to import constants
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from constants import (
    TOWN_TIERS, TRANSPORT_UNLOCKS, BUILDING_UNLOCKS,
    WELLBEING_DECAY_RATE, FOOD_PER_FARM, FOOD_PER_KELP_FARM, FOOD_PER_DOCK,
    SAFETY_PER_TOWER, SAFETY_PER_WALL, SAFETY_PER_REEF_WALL, SECURITY_PER_BARRACKS,
    RIOT_DISCONTENT_LIMIT, RIOT_CRIME_LIMIT,
    REVOLUTION_DISCONTENT_LIMIT, REVOLUTION_CRIME_LIMIT,
    TRADE_ABUNDANCE_LEVEL
)

# Import the new ecology system for full species management
from ecology_system import initialize_ecology, process_ecology_tick, ALL_SPECIES, ALL_FAUNA, ALL_FLORA, DOMESTICATION_TABLE

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
    "cloud_ram_pen": {"Lumber": 35, "Stone": 35},
    "beetle_stable": {"Lumber": 40, "Stone": 20},
    "weaver_farm": {"Lumber": 20, "Stone": 60},
    "dune_dog_den": {"Lumber": 20, "Stone": 15},
    "snail_dock": {"Lumber": 30, "Stone": 50},
    "sheep_pasture": {"Lumber": 25, "Stone": 25},
    "horse_stable": {"Lumber": 40, "Stone": 30},
    "aphid_farm": {"Lumber": 30, "Stone": 20},
    "falcon_roost": {"Lumber": 25, "Stone": 15},
    "church": {"Lumber": 40, "Stone": 60},
    "theatre": {"Lumber": 50, "Stone": 30},
    "arena": {"Lumber": 60, "Stone": 80},
    "kelp_farms": {"Lumber": 20, "Stone": 60, "Rope": 20},
    "underwater_domes": {"Lumber": 10, "Stone": 90, "Crystal Chips": 10},
    "coral_mines": {"Lumber": 20, "Stone": 50, "Basic Weapons": 10},
    "reef_walls": {"Stone": 150, "Coral": 50},
    "workshops": {"Lumber": 40, "Stone": 40, "Iron Ore": 20}
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

def generate_paragon(faction_name=None, history_logs=None, role="Supreme Leader"):
    """Generates a Paragon leader with 12 stats and Good/Bad traits based on lore/history."""
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

    # Base attributes 5 to 15
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
        log_str = " ".join(str(l) for l in history_logs).upper()
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

    # EXACTLY: 1 Blessing, 1 Curse, 3 Neutrals
    num_neutral = 3
    selected_neutrals = random.sample(neutral_pool, num_neutral)
    traits = [selected_good, selected_bad] + selected_neutrals
    
    # 1% chance for each neutral to mutate into an additional blessing or curse
    for i in range(2, 5): # The 3 neutrals are at index 2, 3, 4
        if random.random() < 0.01:
            if random.random() < 0.5:
                # Mutate to blessing
                remaining_good = [t for t in good_pool if t not in traits]
                if remaining_good:
                    traits[i] = random.choice(remaining_good)
            else:
                # Mutate to curse
                remaining_bad = [t for t in bad_pool if t not in traits]
                if remaining_bad:
                    traits[i] = random.choice(remaining_bad)

    traits = list(set(traits))
    
    # Apply stat buffs and debuffs based on traits
    trait_modifiers = {
        # Blessings
        "Diplomat": {"Charm": 2}, "War Survivor": {"Fortitude": 1, "Endurance": 1},
        "Vigilant": {"Reflex": 1, "Awareness": 1}, "Sage": {"Knowledge": 2},
        "Indomitable": {"Willpower": 2}, "Highly Spiritual": {"Intuition": 2},
        "Zealous": {"Might": 1, "Willpower": 1}, "Generous": {"Charm": 1, "Finesse": 1},
        "Just": {"Logic": 1, "Willpower": 1}, "Valiant": {"Might": 2},
        # Curses
        "Prejudiced": {"Charm": -2}, "Cowardly": {"Willpower": -2},
        "Short-tempered": {"Logic": -2}, "Corrupt": {"Finesse": 1, "Logic": -2},
        "Paranoid": {"Awareness": 1, "Charm": -2}, "Dogmatic": {"Logic": -2},
        "Cruel": {"Charm": -2, "Might": 1}, "Greedy": {"Finesse": 1, "Intuition": -2},
        "Suspicious": {"Awareness": 1, "Charm": -1}, "Spiteful": {"Logic": -1, "Charm": -1},
        # Neutrals
        "Stoic": {"Fortitude": 1, "Charm": -1}, "Ambitious": {"Willpower": 1, "Reflex": -1},
        "Eccentric": {"Intuition": 1, "Logic": -1}, "Traditionalist": {"Knowledge": 1, "Intuition": -1},
        "Cautious": {"Awareness": 1, "Might": -1}, "Struggler": {"Endurance": 1, "Finesse": -1},
        "Pragmatist": {"Logic": 1, "Charm": -1}, "Curious": {"Knowledge": 1, "Fortitude": -1},
        "Secretive": {"Finesse": 1, "Charm": -1}, "Stubborn": {"Willpower": 1, "Reflex": -1},
        "Nostalgic": {"Knowledge": 1, "Awareness": -1}, "Skeptical": {"Logic": 1, "Intuition": -1}
    }
    
    for t in traits:
        if t in trait_modifiers:
            for stat_name, mod in trait_modifiers[t].items():
                stats[stat_name] = max(1, stats.get(stat_name, 10) + mod)

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

    MAGIC_POWERS = ["Pyromancy", "Hydromancy", "Terramancy", "Aeromancy", "Biomancy", "Necromancy", "Chronomancy", "Photomancy", "Umbromancy", "Electromancy", "Cryomancy", "Aethermancy"]
    powers = []
    if magic_affinity != "Null":
        num_powers = 1
        if magic_affinity == "Sparkborn - Master": num_powers = 2
        elif magic_affinity == "Sparkborn - Epic": num_powers = 3
        powers = random.sample(MAGIC_POWERS, num_powers)

    return {
        "name": name,
        "culture": culture,
        "role": role,
        "stats": stats,
        "traits": traits,
        "alignment": alignment,
        "magic_affinity": magic_affinity,
        "magic_powers": powers,
        "age": random.randint(25, 55),
        "recent_decisions": []
    }

# ===========================
# PARAGON DEATH & SUCCESSION
# ===========================
def check_paragon_death(paragon, g, logs):
    """
    Checks if a paragon should die from age, stat degradation, or random events.
    Returns True if the paragon dies, False otherwise.
    """
    if not paragon:
        return False
    
    name = paragon.get("name", "Unknown Leader")
    stats = paragon.get("stats", {})
    age = paragon.get("age", 30)
    
    # Age the paragon each tick
    paragon["age"] = age + 1
    
    # Death from old age (increasing chance after 70)
    if age > 70:
        death_chance = (age - 70) * 0.02  # 2% per year over 70
        if random.random() < death_chance:
            logs.append(f"💀 PARAGON DEATH: {name} of {g['name']} died of old age at {age} years. A life of service ended.")
            return True
    
    # Death from stat degradation (Vitality or Endurance reaches 0)
    if stats.get("Vitality", 10) <= 0:
        logs.append(f"💀 PARAGON DEATH: {name} of {g['name']} succumbed to accumulated wounds. Vitality depleted entirely.")
        return True
    if stats.get("Endurance", 10) <= 0:
        logs.append(f"💀 PARAGON DEATH: {name} of {g['name']} collapsed from exhaustion. Endurance completely spent.")
        return True
    
    # Heroic sacrifice: Heroic leaders may sacrifice themselves during extreme crisis
    if paragon.get("alignment") == "Heroic" and g.get("chaos_level", 0.0) > 0.85 and random.random() < 0.05:
        logs.append(f"⭐ HEROIC SACRIFICE: {name} of {g['name']} gave their life to shield the people from a catastrophic chaos surge! They will be remembered as a legend.")
        return True
    
    return False

def handle_paragon_succession(g, old_paragon, logs):
    """
    Generates a new paragon after the old one dies.
    The new paragon is influenced by the old leader's legacy.
    """
    old_name = old_paragon.get("name", "Unknown")
    old_alignment = old_paragon.get("alignment", "Pragmatic")
    
    # Generate new paragon from recent history
    new_paragon = generate_paragon(g.get("name"), logs)
    
    # Legacy effects on settlement
    if old_alignment == "Heroic":
        # Smooth succession: people mourn but remain stable
        g["discontent"] = max(0.0, g.get("discontent", 0.0) + 0.05)
        g["mental_well_being"] = max(0.0, g.get("mental_well_being", 0.5) - 0.05)
        logs.append(f"👑 SUCCESSION: After the passing of beloved {old_name}, {new_paragon['name']} assumes leadership of {g['name']}. The people mourn but carry on.")
    elif old_alignment == "Villainous":
        # Chaotic succession: power vacuum
        g["discontent"] = min(1.0, g.get("discontent", 0.0) + 0.20)
        g["crime_level"] = min(1.0, g.get("crime_level", 0.0) + 0.15)
        logs.append(f"👑 SUCCESSION: The tyrant {old_name} is gone! {new_paragon['name']} seizes power in {g['name']} amid a dangerous power vacuum.")
    else:
        # Normal succession
        g["discontent"] = min(1.0, g.get("discontent", 0.0) + 0.10)
        logs.append(f"👑 SUCCESSION: {new_paragon['name']} replaces {old_name} as leader of {g['name']}.")
    
    g["paragon"] = new_paragon
    return new_paragon

# ===========================
# POPULATION DEATH SYSTEM
# ===========================
def calculate_population_death(new_pop, g, inventory, weather_type, food_supply, logs):
    """
    Calculates population losses from various causes.
    Returns the new population after deaths.
    """
    total_deaths = 0
    
    # 1. Natural attrition: base death rate scaled inversely by physical well-being
    phys = g.get("physical_well_being", 0.8)
    natural_death_rate = 0.002 * (1.5 - phys)  # healthier = lower death rate
    natural_deaths = int(new_pop * natural_death_rate)
    total_deaths += natural_deaths
    
    # 2. Starvation: when food supply is critically low
    if food_supply < 0.3:
        starvation_rate = (0.3 - food_supply) * 0.05
        starvation_deaths = int(new_pop * starvation_rate)
        total_deaths += starvation_deaths
        if starvation_deaths > 10:
            logs.append(f"☠️ FAMINE: {starvation_deaths} citizens of {g['name']} starved due to critical food shortage!")
    
    # 3. Chaos exposure: high chaos zones cause ambient death
    chaos = g.get("chaos_level", 0.0)
    if chaos > 0.5:
        chaos_death_rate = (chaos - 0.5) * 0.008
        chaos_deaths = int(new_pop * chaos_death_rate)
        total_deaths += chaos_deaths
        if chaos_deaths > 5:
            logs.append(f"🌀 CHAOS DEATH: {chaos_deaths} citizens of {g['name']} perished from reality distortion exposure!")
    
    # 4. Disease/Plague: random event, more likely with overcrowding and poor health
    overcrowding = new_pop / max(1000.0, 1000.0 + g.get("farms_count", 0) * 1500.0)
    plague_chance = 0.02 * overcrowding * (1.5 - phys)
    if random.random() < plague_chance:
        plague_deaths = int(new_pop * random.uniform(0.01, 0.04))
        total_deaths += plague_deaths
        logs.append(f"🦠 PLAGUE: A disease outbreak in {g['name']} claimed {plague_deaths} lives!")
        g["physical_well_being"] = max(0.0, phys - 0.10)
    
    # 5. Storm casualties: reality storms and chaos-charged weather
    if weather_type == "Reality Storm":
        storm_deaths = int(new_pop * 0.003)
        total_deaths += storm_deaths
        if storm_deaths > 3:
            logs.append(f"🌪️ STORM DEATH: {storm_deaths} citizens of {g['name']} were torn apart by reality storm anomalies!")
    
    # Apply deaths
    new_pop = max(100.0, new_pop - total_deaths)
    return new_pop

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

def process_well_being_tick(stats, buildings, chaos_level, hub_wealth_bonus=0, ruined_hub_penalty=0):
    """
    Calculates physical/mental well-being, crime, discontent, and returns the updated values.
    stats: dict containing 'physical_well_being', 'mental_well_being', 'crime_level', 'discontent'
    buildings: dict containing counts of 'farms', 'docks', 'watchtowers', 'walls', 'barracks'
    chaos_level: float (0.0 to 1.0)
    hub_wealth_bonus: float, increases wellbeing
    ruined_hub_penalty: float, increases crime
    """
    food_supply = min(1.0, (buildings.get("farms", 0) * FOOD_PER_FARM) + (buildings.get("docks", 0) * FOOD_PER_DOCK))
    safety_rating = min(1.0, (buildings.get("watchtowers", 0) * SAFETY_PER_TOWER) + (buildings.get("walls", 0) * SAFETY_PER_WALL))
    security_rating = min(1.0, buildings.get("barracks", 0) * SECURITY_PER_BARRACKS)

    phys_change = (food_supply + safety_rating + (hub_wealth_bonus * 0.1)) / 2.0 - WELLBEING_DECAY_RATE
    new_phys = max(0.0, min(1.0, stats.get("physical_well_being", 1.0) + phys_change * 0.1))

    mental_change = (1.0 - chaos_level) + (1.0 - stats.get("crime_level", 0.0)) + (hub_wealth_bonus * 0.05) - 1.0
    new_mental = max(0.0, min(1.0, stats.get("mental_well_being", 1.0) + mental_change * 0.1))

    discontent_pressure = (2.0 - new_phys - new_mental) / 2.0
    new_discontent = max(0.0, min(1.0, stats.get("discontent", 0.0) + (discontent_pressure - 0.4) * 0.15))

    crime_pressure = new_discontent - security_rating + (ruined_hub_penalty * 0.2)
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

def process_global_trade_and_conflict(groups, logs, resource_nodes=None, territory_changes=None):
    """
    Simulates Trade, Crime (Smuggling), and Conflict (War) between factions over resources.
    This runs at the global level, comparing faction inventories.
    """
    if territory_changes is None:
        territory_changes = []
        
    aether_elements = ["Lithium", "Tungsten", "Titanium", "Chromium", "Iridium", "Osmium", "Silicon", "Bismuth", "Gold", "Silver", "Lead", "Phosphorus", "Iron", "Copper", "Nickel", "Dragonstone", "Coral", "Smelted Steel", "Crystal Chips"]
    
    # Shuffle groups to randomize initiator order
    initiators = list(groups)
    random.shuffle(initiators)
    
    for initiator in initiators:
        target = random.choice([g for g in groups if g.name != initiator.name])
        
        # ⚖️ TRADE
        # If initiator has excess of one resource and target has excess of another
        for e in aether_elements:
            if initiator.inventory.get(e, 0) > 50 and target.inventory.get(e, 0) < 10:
                # Find something target has that initiator wants
                target_excess = [te for te in aether_elements if target.inventory.get(te, 0) > 50 and initiator.inventory.get(te, 0) < 10]
                if target_excess:
                    trade_item = random.choice(target_excess)
                    # Execute Trade
                    initiator.inventory[e] -= 20
                    target.inventory[e] += 20
                    target.inventory[trade_item] -= 20
                    initiator.inventory[trade_item] += 20
                    
                    # Both gain wealth and happiness
                    initiator.inventory["Wealth"] = initiator.inventory.get("Wealth", 0.0) + 100.0
                    target.inventory["Wealth"] = target.inventory.get("Wealth", 0.0) + 100.0
                    initiator.mental_well_being = min(1.0, initiator.mental_well_being + 0.05)
                    target.mental_well_being = min(1.0, target.mental_well_being + 0.05)
                    
                    if random.random() < 0.1:
                        logs.append(f"⚖️ TRADE: The {initiator.name} and {target.name} executed a massive trade route, exchanging {e} for {trade_item}!")
                    break # One trade per initiator per tick
                    
        # 🗡️ CRIME (Smuggling)
        if initiator.crime_level > 0.6 and random.random() < 0.1:
            # Steal a random valuable element from target
            valuable = [e for e in aether_elements if target.inventory.get(e, 0) > 20]
            if valuable:
                stolen = random.choice(valuable)
                amount = float(random.randint(5, 15))
                target.inventory[stolen] -= amount
                initiator.inventory[stolen] = initiator.inventory.get(stolen, 0.0) + amount
                initiator.inventory["Wealth"] = initiator.inventory.get("Wealth", 0.0) + (amount * 5.0)
                
                target.discontent = min(1.0, target.discontent + 0.05)
                logs.append(f"🗡️ SMUGGLING: Syndicates from {initiator.name} smuggled {amount:.0f} {stolen} out of {target.name} territory!")

        # ⚔️ FIGHT (Territory Conquest)
        # Initiator is desperate for survival (starving/rioting)
        if initiator.physical_well_being < 0.4 and initiator.inventory.get("Wealth", 0.0) < 500:
            initiator_military = (initiator.population * 0.1) + (initiator.barracks_count * 50) + (initiator.inventory.get("Smelted Steel", 0) * 2)
            target_military = (target.population * 0.1) + (target.barracks_count * 50) + (target.inventory.get("Smelted Steel", 0) * 2)
            
            # Find a node owned by the target to conquer
            if resource_nodes and initiator_military > target_military * 1.2 and random.random() < 0.1:
                target_nodes = [n for n in resource_nodes if n.get("faction_id") == getattr(target, "id", None)]
                if target_nodes:
                    node_to_steal = random.choice(target_nodes)
                    
                    # Annex the node and the cell
                    old_faction_id = node_to_steal["faction_id"]
                    new_faction_id = getattr(initiator, "id", None)
                    
                    if new_faction_id is not None:
                        node_to_steal["faction_id"] = new_faction_id
                        
                        territory_changes.append({
                            "cell_id": node_to_steal["cell"],
                            "new_faction": new_faction_id,
                            "old_faction": old_faction_id
                        })
                        
                        # Casualties
                        initiator.population = max(10, initiator.population * 0.90)
                        target.population = max(10, target.population * 0.85)
                        target.physical_well_being -= 0.15
                        
                        logs.append(f"⚔️ TERRITORY CONQUEST: Driven by desperation, the {initiator.name} invaded {target.name}, permanently annexing the cell containing their {node_to_steal['name']}!")

def process_living_world_tick(g, inventory, current_day, season_mod, reality_mod, weather, prisons=None, global_state=None, resource_nodes=None):
    """
    Executes a complete living world simulation turn for a macro group.
    g: dict representing the macro group
    inventory: dict of resources currently held by the group
    prisons: dict containing the seal integrity of the 12 dragon prisons
    global_state: dict containing global convergence metrics
    """
    logs = []
    
    # Initialize basic inventory if empty (including new lore resources)
    resources_list = [
        "Lumber", "Stone", "Iron Ore", "Copper Ore", "Coal", "Grain", "Leather",
        "Dragonstone", "Voltaic Fleece", "Ozone-Milk", "Ghost Flower", "Night-Nectar",
        "D-Dust", "Salt", "Fungal Alloy", "Camouflage Dye", "Stone-Hide", "Wool",
        "Honeydew", "Silk-Steel Thread", "Anesthetic Toxin", "Resin", "Alloy Carapace",
        "Crystal Chips", "Stinger Weapon", "Luxury Meat", "Venison", "Fat", "Antler",
        "Flour", "Peak-Cheese", "Smelted Steel", "Copper Wire", "Refined Aether Battery",
        "Shadow-Set Ink", "Drained Fleece Wool", "Tanned Strips", "Charcoal", "Bricks",
        "Ostrakan Hardtack", "Caldera Spark-Bread", "Basic Weapons", "Iron Tools",
        "Grounding Chains", "Aether-Wright PPE", "Silk-Steel Cables", "Leather Armor", "Rope",
        "Jitter-Rig"
    ]
    for r in resources_list:
        if r not in inventory:
            inventory[r] = 0.0

    # Ensure prisons and global_state exist
    if prisons is None:
        prisons = {}
    if global_state is None:
        global_state = {"global_surge": False}

    # Initialize full ecology using ecology_system
    if "ecology_initialized" not in g:
        initialize_ecology(g, g.get("name", ""))
        g["ecology_initialized"] = True

    # Initialize happiness & non-faction structures
    for key in ["churches_count", "theatres_count", "arenas_count", "gambling_dens_count", "black_markets_count"]:
        if key not in g:
            g[key] = 0

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
    
    MAGIC_POWERS = ["Pyromancy", "Hydromancy", "Terramancy", "Aeromancy", "Biomancy", "Necromancy", "Chronomancy", "Photomancy", "Umbromancy", "Electromancy", "Cryomancy", "Aethermancy"]
    if "magic_powers" not in paragon:
        powers = []
        if magic_affinity != "Null":
            num_powers = 1
            if magic_affinity == "Sparkborn - Master": num_powers = 2
            elif magic_affinity == "Sparkborn - Epic": num_powers = 3
            powers = random.sample(MAGIC_POWERS, num_powers)
        paragon["magic_powers"] = powers

    # Ensure age exists
    if "age" not in paragon:
        paragon["age"] = random.randint(25, 55)

    # Check for paragon death
    if check_paragon_death(paragon, g, logs):
        paragon = handle_paragon_succession(g, paragon, logs)
        alignment = paragon["alignment"]
        magic_affinity = paragon["magic_affinity"]

    # --- CALCULATE FACTION DOCTRINES (STANCES) ---
    p_stats = paragon["stats"]
    p_traits = paragon["traits"]
    
    # 1. Civil Stance (Oppressive, Authoritarian, Neutral, Liberal, Utopian)
    civil_score = (p_stats.get("Charm", 10) + p_stats.get("Willpower", 10)) / 2.0
    if g.get("crime_level", 0) > 0.5 or g.get("discontent", 0) > 0.5:
        civil_score -= 4 # Stress pushes towards authoritarian control
    if "Cruel" in p_traits or "Corrupt" in p_traits:
        civil_score -= 3
    if "Generous" in p_traits or "Diplomat" in p_traits:
        civil_score += 3
        
    if civil_score < 6: civil_stance = "Oppressive"
    elif civil_score < 9: civil_stance = "Authoritarian"
    elif civil_score < 12: civil_stance = "Neutral"
    elif civil_score < 15: civil_stance = "Liberal"
    else: civil_stance = "Utopian"
    
    # 2. Economical Stance (Scavenger, Subsistence, Balanced, Industrialist, Wealth-Focused)
    econ_score = (p_stats.get("Logic", 10) + p_stats.get("Knowledge", 10)) / 2.0
    food_ratio = min(1.0, (g.get("farms_count", 0) * 1500.0) / max(1.0, g.get("population", 1000.0)))
    if food_ratio < 0.4:
        econ_score -= 5 # Starving pushes towards scavenger/subsistence
    if "Greedy" in p_traits or "Ambitious" in p_traits:
        econ_score += 3
    if "Sage" in p_traits:
        econ_score += 2
        
    if econ_score < 6: econ_stance = "Scavenger"
    elif econ_score < 9: econ_stance = "Subsistence"
    elif econ_score < 12: econ_stance = "Balanced"
    elif econ_score < 15: econ_stance = "Industrialist"
    else: econ_stance = "Wealth-Focused"
    
    # 3. Political Stance (Isolationist, Defensive, Neutral, Expansionist, Aggressive)
    pol_score = (p_stats.get("Might", 10) + p_stats.get("Fortitude", 10)) / 2.0
    if g.get("chaos_level", 0) > 0.5:
        pol_score -= 3 # High chaos makes them turtle up
    if "War Survivor" in p_traits or "Cautious" in p_traits: 
        pol_score -= 3
    if "Valiant" in p_traits or "Zealous" in p_traits: 
        pol_score += 3
    
    if pol_score < 6: pol_stance = "Isolationist"
    elif pol_score < 9: pol_stance = "Defensive"
    elif pol_score < 12: pol_stance = "Neutral"
    elif pol_score < 15: pol_stance = "Expansionist"
    else: pol_stance = "Aggressive"
    
    # 4. Spark Stance (Banished, Indoctrinated, Accepted, Revered)
    # Stance is hard/sticky, only changing during high chaos or unrest
    doctrines = g.get("doctrines", {})
    spark_stance = doctrines.get("spark")
    
    if spark_stance is None or g.get("chaos_level", 0) > 0.8 or g.get("discontent", 0) > 0.8:
        new_stance = "Accepted" # Default fallback
        # Weigh the Paragon's stats and traits to determine cultural shift
        if "Cautious" in p_traits or "Paranoid" in p_traits or "Superstitious" in p_traits or p_stats.get("Logic", 0) > 15:
            new_stance = "Banished"
        elif "Cruel" in p_traits or "Ambitious" in p_traits or "Valiant" in p_traits or p_stats.get("Might", 0) > 15:
            new_stance = "Indoctrinated"
        elif "Zealous" in p_traits or "Stubborn" in p_traits or "Just" in p_traits or p_stats.get("Willpower", 0) > 15:
            new_stance = "Revered"
        elif "Sage" in p_traits or "Pragmatist" in p_traits or "Generous" in p_traits or p_stats.get("Charm", 0) > 15:
            new_stance = "Accepted"
            
        if spark_stance is not None and new_stance != spark_stance:
            reason = "Chaos Crisis" if g.get("chaos_level", 0) > 0.8 else "Civil Unrest"
            logs.append(f"⚖️ CULTURAL SHIFT: Due to extreme {reason}, {g['name']} has shifted its Spark Stance from {spark_stance} to {new_stance}!")
            
        spark_stance = new_stance

    g["doctrines"] = {"civil": civil_stance, "economical": econ_stance, "political": pol_stance, "spark": spark_stance}
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
        protected_by_elements = False
        aether_elements = ["Lithium", "Tungsten", "Titanium", "Chromium", "Iridium", "Osmium", "Silicon", "Bismuth", "Gold", "Silver", "Lead", "Phosphorus"]
        owned_elements = [e for e in aether_elements if inventory.get(e, 0) > 5]
        
        if len(owned_elements) >= 3:
            protected_by_elements = True
            for e in owned_elements[:3]:
                inventory[e] -= 1.0
            logs.append(f"🛡️ ELEMENTAL WARD: The {g['name']} channeled {owned_elements[0]}, {owned_elements[1]}, and {owned_elements[2]} to block weather damage!")
        
        if not protected_by_elements:
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
        
        chaos_blocked = False
        if len(owned_elements) >= 2:
            chaos_blocked = True
            for e in owned_elements[:2]: inventory[e] -= 1.0
            logs.append(f"🛡️ ELEMENTAL WARD: {g['name']} safely grounded the Chaos Reality Storm using {owned_elements[0]}!")
            
        if not chaos_blocked:
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
                # Mutate random fauna populations
                mutated_predator = random.choice([k for k in ALL_FAUNA if g.get(k, 0.0) > 1.0] or ["fauna_timber_wolf"])
                mutated_prey = random.choice([k for k in ALL_FAUNA if g.get(k, 0.0) > 1.0 and k != mutated_predator] or ["fauna_red_deer"])
                g[mutated_predator] = min(500.0, g.get(mutated_predator, 0.0) * 1.5)
                g[mutated_prey] = max(0.0, g.get(mutated_prey, 0.0) * 0.7)
                pred_name = mutated_predator.replace("fauna_", "").replace("_", " ").title()
                prey_name = mutated_prey.replace("fauna_", "").replace("_", " ").title()
                logs.append(f"🐺 REALITY ANOMALY: Aetheric Mutation mutated local fauna! {pred_name} swelled by 50% while {prey_name} scattered.")
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

    # Get prison seal integrity impact on regional chaos level
    prison_seal = prisons[magistar]
    if prison_seal < 1.0:
        proximity_mult = 1.0 - g.get("distance_to_chaos_structure", 0.5) # 1.0 if right on top of anchor, 0.0 if far away
        # The closer you are to the traitor anchors, the faster chaos leaks into your faction
        chaos_leak = (1.0 - prison_seal) * 0.12 * proximity_mult
        
        # Exponential chaos leakage if you are sitting on the convergence paths
        if proximity_mult > 0.8:
            chaos_leak *= 3.0
            logs.append(f"⚠️ REALITY TEAR: Faction {g['name']} is dangerously close to a Chaos Anchor! Ambient chaos surged!")
            
        g["chaos_level"] = min(1.0, g["chaos_level"] + chaos_leak)

    # ========================================
    # TRUE SPARKBORN MECHANICS
    # ========================================
    # 50% of the population is Sparkborn.
    sparkborn_pop = g.get("population", 1000.0) * 0.50
    
    # 1. Spark Stance (Cultural handling of magic)
    spark_stance = g.get("doctrines", {}).get("spark", "Accepted")
    
    refugee_drain = 0.0
    spark_stance_efficiency = 1.0
    spark_stance_growth = 1.0
    
    if spark_stance == "Banished":
        spark_stance_growth = 0.8
        refugee_drain = sparkborn_pop * 0.02 # 2% flee every tick
    elif spark_stance == "Indoctrinated":
        # Handled in security calculation later
        pass
    elif spark_stance == "Accepted":
        spark_stance_efficiency = 1.10
    elif spark_stance == "Revered":
        # Heavy chaos resistance, lower trade
        g["chaos_level"] = max(0.0, g["chaos_level"] - 0.05)
        
    # 2. Warden Compulsion
    # 0.5% of Sparkborn trigger ancient wards and leave the faction
    warden_recruits = sparkborn_pop * 0.005
    if g.get("chaos_level", 0.0) > 0.7:
        # Madness event
        logs.append(f"🔮 WARDEN COMPULSION: High chaos drove {int(warden_recruits)} Sparkborn in {g['name']} to madness!")
        g["crime_level"] = min(1.0, g.get("crime_level", 0.0) + 0.02)
        refugee_drain += warden_recruits # Counts as casualties/loss
    else:
        logs.append(f"🏛️ WARDEN COMPULSION: {int(warden_recruits)} Sparkborn left {g['name']} to answer the Spire's call.")
        # We could add to a global warden pool here if tracking.
        refugee_drain += warden_recruits
        
    # 3. Prison Proximity Resonance
    if g.get("distance_to_chaos_structure", 1.0) < 0.3:
        p_stats = paragon.get("stats", {})
        PRISON_STAT_MAP = {
            "Tiraton": "Might", "Stagus": "Fortitude", "Metrion": "Logic", 
            "Ignis": "Charm", "Aero": "Finesse", "Aqua": "Reflexes", 
            "Terra": "Fortitude", "Lumen": "Perception", "Umbra": "Guile", 
            "Chronos": "Knowledge", "Necros": "Willpower", "Aether": "Focus"
        }
        target_stat = PRISON_STAT_MAP.get(magistar, "Might")
        if target_stat in p_stats:
            p_stats[target_stat] = min(20, p_stats[target_stat] + 1)

    # 1. Population Math (Logistic growth with carrying capacity)
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
    
    kelp_farms = g.get("kelp_farms_count", 0)
    underwater_domes = g.get("underwater_domes_count", 0)
    coral_mines = g.get("coral_mines_count", 0)
    reef_walls = g.get("reef_walls_count", 0)

    carrying_capacity = 1000.0 + (farms * 1500.0) + (kelp_farms * 1500.0) + (docks * 1000.0) + (camps * 500.0) + (underwater_domes * 500.0)
    growth_rate = 0.05 * season_mod.get("growth", 1.0) * spark_stance_growth
    growth_rate *= (1.0 - 0.5 * g["chaos_level"])
    gravity_mult = reality_mod.get("gravity_mult", 1.0)
    if gravity_mult > 1.0:
        growth_rate /= gravity_mult
        
    p_ratio = g["population"] / carrying_capacity
    dp = growth_rate * g["population"] * (1.0 - p_ratio)
    new_pop = max(100.0, g["population"] + dp - refugee_drain)

    # Faction economy resource consumption
    grain_consumption = float((new_pop / 100.0) * 0.05)
    lumber_consumption = float((new_pop / 100.0) * 0.02)
    stone_consumption = float((new_pop / 100.0) * 0.02)
    
    # Check for starvation
    total_food_sources = ["Grain", "Kelp", "Ostrakan Hardtack", "Ozone-Milk", "Venison", "Luxury Meat", "Fish"]
    food_available = sum(inventory.get(f, 0.0) for f in total_food_sources)
    
    if food_available < grain_consumption:
        starvation_ratio = (grain_consumption - food_available) / grain_consumption
        new_pop = max(100.0, new_pop * (1.0 - (0.1 * starvation_ratio)))
        logs.append(f"💀 STARVATION: {g['name']} does not have enough food! The population is starving and dropping!")
        # Consume whatever is left
        for f in total_food_sources:
            inventory[f] = 0.0
    else:
        # Deduct consumption from grain/food
        remaining_to_eat = grain_consumption
        for f in total_food_sources:
            if remaining_to_eat <= 0: break
            eaten = min(inventory.get(f, 0.0), remaining_to_eat)
            inventory[f] -= eaten
            remaining_to_eat -= eaten
            
    inventory["Lumber"] = max(0.0, inventory.get("Lumber", 0.0) - lumber_consumption)
    inventory["Stone"] = max(0.0, inventory.get("Stone", 0.0) - stone_consumption)

    # 2. Ecology & Resource Gathering (delegated to ecology_system)
    pop_efficiency = new_pop / 5000.0
    
    # Syndicate Narcotics Addiction Penalty
    narcotics_addicted = False
    if inventory.get("Narcotics", 0.0) >= 3.0:
        narcotics_addicted = True
        pop_efficiency *= 0.5 # Massive 50% hit to production efficiency due to widespread addiction
        logs.append(f"📉 ADDICTION CRISIS: The population of {g['name']} is heavily addicted to Narcotics! Production efficiency has plummeted by 50%!")

    # Apply spark stance efficiency
    pop_efficiency *= spark_stance_efficiency

    # Mine-based resources (not ecology-dependent)
    harvest_stone = mines * 10.0 * pop_efficiency
    harvest_ore = mines * 8.0 * pop_efficiency
    harvest_coal = mines * 6.0 * pop_efficiency
    harvest_dragonstone = 0.0
    if mines > 0 and random.random() < 0.15 * mines:
        harvest_dragonstone = float(random.randint(1, 3))
        
    harvest_coral = coral_mines * 10.0 * pop_efficiency
    harvest_stone += coral_mines * 5.0 * pop_efficiency

    inventory["Stone"] += harvest_stone
    inventory["Iron Ore"] += harvest_ore
    inventory["Coal"] += harvest_coal
    inventory["Dragonstone"] += harvest_dragonstone
    inventory["Coral"] = inventory.get("Coral", 0.0) + harvest_coral

    # Farm-based grain (base production from cultivated fields)
    harvest_grain = farms * 15.0 * pop_efficiency * season_mod.get("growth", 1.0)
    inventory["Grain"] += harvest_grain
    
    harvest_kelp = kelp_farms * 20.0 * pop_efficiency * season_mod.get("growth", 1.0)
    inventory["Kelp"] = inventory.get("Kelp", 0.0) + harvest_kelp

    # Full ecology tick (all species harvesting, domestication)
    from ecology_system import process_faction_harvesting
    from scheduler import _GLOBAL_ECOLOGY_GRID
    ecology_harvests = process_faction_harvesting(
        g, inventory, _GLOBAL_ECOLOGY_GRID,
        camps, watchtowers, barracks, pop_efficiency
    )
    # Rare Resource Node Harvesting & Prospecting
    if resource_nodes:
        my_nodes = [n for n in resource_nodes if n.get("faction_id") == g.get("id")]
        for node in my_nodes:
            if node.get("yield_remaining", 0) <= 0:
                continue # Skip depleted nodes
                
            # PROSPECTING
            if not node.get("is_discovered", False):
                # Chance to discover based on watchtowers and population
                prospect_chance = 0.05 + (g.get("watchtowers_count", 0) * 0.02)
                if random.random() < prospect_chance:
                    node["is_discovered"] = True
                    logs.append(f"🔍 PROSPECTING: The {g['name']} have discovered a hidden {node['name']} in their territory!")
                continue # Cannot harvest until discovered
                
            # Determine yield type based on node name
            # e.g. "Rich Tungsten Vein" -> "Tungsten", "Dragonstone Crater" -> "Dragonstone"
            yield_resource = "Wealth"
            if "Dragonstone" in node["name"]: yield_resource = "Dragonstone"
            elif "Coral" in node["name"]: yield_resource = "Coral"
            elif "Steel" in node["name"]: yield_resource = "Smelted Steel"
            elif "Geode" in node["name"]: yield_resource = "Crystal Chips"
            elif "Rich" in node["name"]:
                parts = node["name"].split()
                if len(parts) >= 2:
                    yield_resource = parts[1]
            
            # INFRASTRUCTURE REQUIREMENT
            mines = g.get("mines_count", 0)
            if mines <= 0 and "Coral" not in node["name"] and "Dragonstone" not in node["name"]:
                # Need mines for basic geological veins
                if random.random() < 0.05:
                    logs.append(f"⚠️ INFRASTRUCTURE: The {g['name']} know of a {node['name']} but lack the Mines to extract it!")
                continue
                
            # COMPLEX ELEMENT REQUIREMENT (Tech level / Population proxy)
            is_element = yield_resource not in ["Wealth", "Dragonstone", "Coral", "Smelted Steel", "Iron", "Copper", "Nickel", "Crystal Chips"]
            if is_element and population < 2000:
                if random.random() < 0.05:
                    logs.append(f"⚠️ TECH LEVEL: The {g['name']} lack the advanced civilization (Population > 2000) to safely extract the volatile {yield_resource} from their {node['name']}!")
                continue
                
            # Extract up to 15 yield per tick
            attempted_amount = float(random.randint(5, 15)) * pop_efficiency * (1.0 + (mines * 0.1))
            actual_amount = min(attempted_amount, float(node["yield_remaining"]))
            
            # Deplete the node
            node["yield_remaining"] -= actual_amount
            
            inventory[yield_resource] = inventory.get(yield_resource, 0.0) + actual_amount
            inventory["Wealth"] = inventory.get("Wealth", 0.0) + actual_amount * 3.0
            
            if random.random() < 0.2 and actual_amount > 1.0:
                logs.append(f"⛏️ RARE HARVEST: {g['name']} expedition successfully mined {actual_amount:.0f} {yield_resource} from their {node['name']}! ({node['yield_remaining']:.0f} remaining)")


    # Apply tool bonuses from domestication
    kennel_bonus = g.get("tool_guard_bonus", 0) * 0.05
    transport_bonus = g.get("tool_transport_bonus", 0)

    # Calculate wealth rating and crime pressure scaling
    wealth = sum(inventory.values())

    # 3. Refining & Crafting (Production cycles)
    workshops = g.get("workshops_count", 0)
    
    refined_steel = 0
    if workshops > 0 and inventory["Iron Ore"] >= 5 and inventory["Coal"] >= 3:
        craft_count = min(int(inventory["Iron Ore"] // 5), int(inventory["Coal"] // 3))
        craft_count = min(craft_count, workshops * 5)
        inventory["Iron Ore"] -= craft_count * 5
        inventory["Coal"] -= craft_count * 3
        inventory["Smelted Steel"] = inventory.get("Smelted Steel", 0.0) + craft_count
        refined_steel = craft_count

    flour_crafted = 0
    if workshops > 0 and inventory["Grain"] >= 4:
        craft_count = min(int(inventory["Grain"] // 4), workshops * 10)
        inventory["Grain"] -= craft_count * 4
        inventory["Flour"] = inventory.get("Flour", 0.0) + craft_count
        flour_crafted = craft_count
        
    # Alcohol Crafting (Luxury Good)
    if workshops > 0 and inventory.get("Flour", 0.0) >= 3:
        craft_count = min(int(inventory["Flour"] // 3), workshops * 3)
        inventory["Flour"] -= craft_count * 3
        inventory["Alcohol"] = inventory.get("Alcohol", 0.0) + craft_count
        
    # Weapon Crafting (Military Supply)
    if workshops > 0 and inventory.get("Smelted Steel", 0.0) >= 2 and inventory.get("Lumber", 0.0) >= 2:
        craft_count = min(int(inventory["Smelted Steel"] // 2), int(inventory["Lumber"] // 2), workshops * 5)
        inventory["Smelted Steel"] -= craft_count * 2
        inventory["Lumber"] -= craft_count * 2
        inventory["Basic Weapons"] = inventory.get("Basic Weapons", 0.0) + (craft_count * 10)

    rations_crafted = 0
    if workshops > 0 and inventory.get("Flour", 0.0) >= 2 and inventory.get("Leather", 0.0) >= 1:
        craft_count = min(int(inventory["Flour"] // 2), int(inventory["Leather"] // 1), workshops * 5)
        inventory["Flour"] -= craft_count * 2
        inventory["Leather"] -= craft_count * 1
        inventory["Ostrakan Hardtack"] = inventory.get("Ostrakan Hardtack", 0.0) + craft_count
        rations_crafted = craft_count

    batteries_crafted = 0
    if workshops > 0 and inventory.get("Dragonstone", 0.0) >= 2 and inventory.get("Coal", 0.0) >= 2:
        craft_count = min(int(inventory["Dragonstone"] // 2), int(inventory["Coal"] // 2), workshops * 2)
        inventory["Dragonstone"] -= craft_count * 2
        inventory["Coal"] -= craft_count * 2
        inventory["Refined Aether Battery"] = inventory.get("Refined Aether Battery", 0.0) + craft_count
        batteries_crafted = craft_count

    # Luxury: Jewelry
    if workshops > 0 and (inventory.get("Gold", 0.0) >= 1 or inventory.get("Silver", 0.0) >= 1) and inventory.get("Crystal Chips", 0.0) >= 2:
        metal_used = "Gold" if inventory.get("Gold", 0.0) >= 1 else "Silver"
        craft_count = min(int(inventory[metal_used] // 1), int(inventory["Crystal Chips"] // 2), workshops * 2)
        inventory[metal_used] -= craft_count * 1
        inventory["Crystal Chips"] -= craft_count * 2
        inventory["Jewelry"] = inventory.get("Jewelry", 0.0) + craft_count

    # Luxury: Fine Clothes
    if workshops > 0 and (inventory.get("Silk-Steel Thread", 0.0) >= 2 or inventory.get("Wool", 0.0) >= 3):
        cloth_mat = "Silk-Steel Thread" if inventory.get("Silk-Steel Thread", 0.0) >= 2 else "Wool"
        cloth_cost = 2 if cloth_mat == "Silk-Steel Thread" else 3
        craft_count = min(int(inventory[cloth_mat] // cloth_cost), workshops * 3)
        inventory[cloth_mat] -= craft_count * cloth_cost
        inventory["Fine Clothes"] = inventory.get("Fine Clothes", 0.0) + craft_count

    # Medicine
    if workshops > 0 and inventory.get("Kelp", 0.0) >= 3 and inventory.get("Anesthetic Toxin", 0.0) >= 1:
        craft_count = min(int(inventory["Kelp"] // 3), int(inventory["Anesthetic Toxin"] // 1), workshops * 4)
        inventory["Kelp"] -= craft_count * 3
        inventory["Anesthetic Toxin"] -= craft_count * 1
        inventory["Medicine"] = inventory.get("Medicine", 0.0) + craft_count

    # Entertainment: Toys/Comfort Items
    if workshops > 0 and inventory.get("Lumber", 0.0) >= 3 and inventory.get("Leather", 0.0) >= 1:
        craft_count = min(int(inventory["Lumber"] // 3), int(inventory["Leather"] // 1), workshops * 4)
        inventory["Lumber"] -= craft_count * 3
        inventory["Leather"] -= craft_count * 1
        inventory["Toys"] = inventory.get("Toys", 0.0) + craft_count

    # Fancy Food
    if workshops > 0 and inventory.get("Luxury Meat", 0.0) >= 2 and inventory.get("Peak-Cheese", 0.0) >= 1:
        craft_count = min(int(inventory["Luxury Meat"] // 2), int(inventory["Peak-Cheese"] // 1), workshops * 3)
        inventory["Luxury Meat"] -= craft_count * 2
        inventory["Peak-Cheese"] -= craft_count * 1
        inventory["Fancy Food"] = inventory.get("Fancy Food", 0.0) + craft_count

    # Wool -> Drained Fleece Wool
    if workshops > 0 and inventory.get("Wool", 0.0) >= 3:
        craft_count = min(int(inventory["Wool"] // 3), workshops * 3)
        inventory["Wool"] -= craft_count * 3
        inventory["Drained Fleece Wool"] = inventory.get("Drained Fleece Wool", 0.0) + craft_count
    
    # Honeydew -> food/trade value
    if inventory.get("Honeydew", 0.0) >= 5:
        craft_count = min(int(inventory["Honeydew"] // 5), 3)
        inventory["Honeydew"] -= craft_count * 5
        inventory["Grain"] += craft_count * 3  # converts to food value

    # 4. Social Well-Being Calculations
    # Note: Kelp counts as equivalent to Grain for food, handled by FOOD_PER_KELP_FARM coefficient
    food_supply = min(1.0, (farms * FOOD_PER_FARM) + (kelp_farms * FOOD_PER_KELP_FARM) + (docks * FOOD_PER_DOCK) + (inventory["Ostrakan Hardtack"] * 0.05) + (inventory.get("Ozone-Milk", 0.0) * 0.02) + (inventory.get("Venison", 0.0) * 0.03) + (inventory.get("Luxury Meat", 0.0) * 0.05) + (inventory.get("Fish", 0.0) * 0.04))
    
    # MILITARY MAINTENANCE
    military_active = barracks > 0
    if military_active:
        weapon_cost = float(barracks * 2.0)
        if inventory.get("Basic Weapons", 0.0) >= weapon_cost:
            inventory["Basic Weapons"] -= weapon_cost
        else:
            # Military collapses without weapons
            barracks = max(0, barracks - 1)
            g["barracks_count"] = barracks
            logs.append(f"⚠️ DISARMAMENT: {g['name']} ran out of Basic Weapons! A Barracks has been abandoned!")
            
    safety_rating = min(1.0, (watchtowers * SAFETY_PER_TOWER) + (walls * SAFETY_PER_WALL) + (reef_walls * SAFETY_PER_REEF_WALL) + kennel_bonus)
    security_rating = min(1.0, barracks * SECURITY_PER_BARRACKS + kennel_bonus)
    
    spark_stance = g.get("doctrines", {}).get("spark", "Accepted")
    if spark_stance == "Indoctrinated":
        security_rating = min(1.0, security_rating + 0.20) # Magic users drafted to military

    phys_change = (food_supply + safety_rating) / 2.0 - WELLBEING_DECAY_RATE
    new_phys = max(0.0, min(1.0, g.get("physical_well_being", 1.0) + phys_change * 0.1))

    # Happiness buildings increase mental well-being
    happiness_bonus = (churches * 0.03) + (theatres * 0.03) + (arenas * 0.05)
    
    if spark_stance == "Indoctrinated":
        happiness_bonus -= 0.15 # Forced service lowers morale
    elif spark_stance == "Revered":
        happiness_bonus += 0.20 # Spiritual reverence brings peace
    messenger_bonus = g.get("tool_messenger_bonus", 0) * 0.02

    # LUXURY GOODS & MEDICINE
    alcohol_bonus = 0.0
    alcohol_crime_penalty = 0.0
    luxury_bonus = 0.0
    medicine_phys_bonus = 0.0
    
    # Paragon Hoarding check
    hoarding = False
    if alignment == "Villainous" and random.random() < 0.4:
        hoarding = True
        logs.append(f"👑 CORRUPTION: Villainous leader {paragon['name']} hoarded luxury items from the public, enriching themselves but starving the economy of joy!")
        
    for item, qty in [("Jewelry", 2.0), ("Fine Clothes", 3.0), ("Toys", 5.0), ("Fancy Food", 5.0)]:
        if inventory.get(item, 0.0) >= qty:
            inventory[item] -= qty
            if not hoarding:
                luxury_bonus += 0.05
    
    if inventory.get("Narcotics", 0.0) >= 3.0:
        inventory["Narcotics"] -= 3.0
        if not hoarding:
            luxury_bonus += 0.20
            alcohol_crime_penalty += 0.15
            medicine_phys_bonus -= 0.05
            
    if inventory.get("Medicine", 0.0) >= 2.0:
        inventory["Medicine"] -= 2.0
        if not hoarding or random.random() < 0.5: # Even corrupt leaders might distribute medicine to keep workers alive
            medicine_phys_bonus += 0.10

    if inventory.get("Alcohol", 0.0) >= 5.0:
        inventory["Alcohol"] -= 5.0
        if not hoarding:
            alcohol_bonus = 0.15
            alcohol_crime_penalty += 0.05
        
    weather_multiplier = 1.5 if weather_type == "Reality Storm" else 1.0
    chaos_impact = g["chaos_level"] * weather_multiplier
    if magic_affinity == "Null":
        chaos_impact *= 0.5
    mental_change = (1.0 - chaos_impact) + (1.0 - g.get("crime_level", 0.0)) - 1.0 + happiness_bonus + messenger_bonus + alcohol_bonus + luxury_bonus
    
    if alignment == "Heroic":
        mental_change += 0.10
    new_mental = max(0.0, min(1.0, g.get("mental_well_being", 1.0) + mental_change * 0.1))

    discontent_pressure = (2.0 - new_phys - new_mental - medicine_phys_bonus) / 2.0
    
    # Doctrine: Civil Stance Modifiers
    civil_stance = g.get("doctrines", {}).get("civil", "Neutral")
    if civil_stance == "Oppressive":
        discontent_pressure += 0.20
    elif civil_stance == "Authoritarian":
        discontent_pressure += 0.10
    elif civil_stance == "Liberal":
        discontent_pressure -= 0.10
    elif civil_stance == "Utopian":
        discontent_pressure -= 0.20
        
    if spark_stance == "Accepted":
        discontent_pressure += 0.05 # Nulls grow jealous of magic users
        
    new_discontent = max(0.0, min(1.0, g.get("discontent", 0.0) + (discontent_pressure - 0.4) * 0.15))

    # Crime pressure scales with wealth and alignment
    crime_pressure = new_discontent - security_rating + (wealth * 0.0003) + alcohol_crime_penalty
    
    # Doctrine: Civil Stance affects Crime (Oppression crushes crime, Utopia invites it)
    if civil_stance == "Oppressive":
        crime_pressure -= 0.30
    elif civil_stance == "Authoritarian":
        crime_pressure -= 0.15
    elif civil_stance == "Liberal":
        crime_pressure += 0.10
    elif civil_stance == "Utopian":
        crime_pressure += 0.25
        
    if spark_stance == "Revered":
        crime_pressure += 0.15 # Revered magic users exploit the law
        
    econ_stance = g.get("doctrines", {}).get("economical", "Balanced")
    if econ_stance == "Wealth-Focused":
        crime_pressure += (wealth * 0.0005) # Extreme greed breeds syndicates
    if alignment == "Heroic":
        crime_pressure -= 0.15
    elif alignment == "Villainous":
        crime_pressure += 0.15
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

    # Illicit structure drains, crime boosts, and Syndicate Narcotics production
    new_crime = min(1.0, new_crime + (gambling_dens * 0.02) + (black_markets * 0.03))
    
    # -------------------------------------------------------------
    # PHASE 13: Local Settlement Paragon Modifiers
    # Mayors and Captains influence the local populations!
    # -------------------------------------------------------------
    if "settlements" in g and len(g["settlements"]) > 0:
        total_pop = sum(s.get("population", 1) for s in g["settlements"])
        local_crime_mod = 0.0
        local_discontent_mod = 0.0
        
        for burg in g["settlements"]:
            pop_weight = burg.get("population", 1) / max(1, total_pop)
            mayor = burg.get("mayor")
            captain = burg.get("captain")
            
            # Mayor Impact
            if mayor:
                alignment = mayor.get("alignment", "Pragmatic")
                if alignment == "Villainous" or "Corrupt" in mayor.get("traits", []):
                    local_crime_mod += 0.05 * pop_weight
                    local_discontent_mod += 0.02 * pop_weight
                elif alignment == "Heroic" or "Generous" in mayor.get("traits", []):
                    local_discontent_mod -= 0.05 * pop_weight
                    
            # Captain Impact
            if captain:
                c_stats = captain.get("stats", {})
                if c_stats.get("Might", 10) > 12:
                    local_crime_mod -= 0.03 * pop_weight
                if "Short-tempered" in captain.get("traits", []):
                    local_discontent_mod += 0.03 * pop_weight
                    
        new_crime = max(0.0, min(1.0, new_crime + local_crime_mod))
        new_discontent = max(0.0, min(1.0, new_discontent + local_discontent_mod))
        
        if local_crime_mod > 0.03 and random.random() < 0.05:
            logs.append(f"⚖️ CORRUPTION: Corrupt Mayors in {g['name']} have driven up the local Crime Rate!")
        elif local_discontent_mod < -0.03 and random.random() < 0.05:
            logs.append(f"🕊️ GOOD LEADERSHIP: Heroic Mayors in {g['name']} have improved local morale, lowering Discontent.")
    # -------------------------------------------------------------
    
    syndicate_structures = gambling_dens + black_markets
    if syndicate_structures > 0:
        # Syndicates brew narcotics from Flora, or if desperate, steal public Grain
        if inventory.get("Ghost Flower", 0.0) >= 2 or inventory.get("Night-Nectar", 0.0) >= 2:
            narc_mat = "Ghost Flower" if inventory.get("Ghost Flower", 0.0) >= 2 else "Night-Nectar"
            craft_count = min(int(inventory[narc_mat] // 2), syndicate_structures * 3)
            inventory[narc_mat] -= craft_count * 2
            inventory["Narcotics"] = inventory.get("Narcotics", 0.0) + craft_count
            if random.random() < 0.1:
                logs.append(f"☠️ CARTEL BREWING: Syndicates in {g['name']} hijacked {narc_mat} to flood the streets with Narcotics!")
        elif inventory.get("Grain", 0.0) >= 10:
            craft_count = min(int(inventory["Grain"] // 5), syndicate_structures * 2)
            inventory["Grain"] -= craft_count * 5
            inventory["Narcotics"] = inventory.get("Narcotics", 0.0) + craft_count
            if random.random() < 0.1:
                logs.append(f"☠️ CARTEL BREWING: Syndicates in {g['name']} stole public Grain reserves to distill highly addictive Narcotics!")
                
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

    # Present Unrest Events to Paragon Leader for Decision
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
            inventory["Grain"] = max(0.0, inventory["Grain"] - 5.0)
            inventory["Lumber"] = max(0.0, inventory["Lumber"] - 3.0)
            new_discontent = max(0.0, new_discontent - 0.15)
            logs.append(f"🤝 DIPLOMATIC COMPROMISE: Paragon {paragon['name']} negotiated with protest leaders in {g['name']}, distributing 5 Grain and 3 Lumber to calm tensions.")
            paragon["recent_decisions"].append(f"Negotiated peace using public resources.")
            event = "Stable"
        elif p_decision == "Logistical Sweeps":
            inventory["Smelted Steel"] = max(0.0, inventory.get("Smelted Steel", 0.0) - 2.0)
            new_crime = max(0.0, new_crime - 0.20)
            logs.append(f"🛡️ LOGISTICAL SWEEP: Sagacious leader {paragon['name']} coordinated precise raids against syndicates in {g['name']}, massively reducing crime!")
            paragon["recent_decisions"].append(f"Executed tactical sweeps on syndicate strongholds.")
            event = "Stable"
        elif p_decision == "Observe Unrest":
            logs.append(f"⚖️ INACTION: Pragmatic leader {paragon['name']} allowed the {event} to run its course in {g['name']}.")
            paragon["recent_decisions"].append(f"Allowed civil unrest to process naturally.")

    # (Harvesting and Domestication is processed earlier in the loop)
    
    # Process specialized production from structures
    from rules_engine_production import process_structures_production
    prod_yields = process_structures_production(g, inventory, mines, barracks, new_discontent)
    
    for k, v in prod_yields.items():
        inventory[k] = inventory.get(k, 0.0) + v

    trader_status = "Inactive"
    if food_supply >= TRADE_ABUNDANCE_LEVEL:
        trader_status = "Active - Trade Route Established"

    # 5. Dynamic Construction (Including new Domestication Facilities)
    built_structure = None
    
    faction_name = g["name"]
    build_aquatic = faction_name == "Theocracy"
    build_mixed = faction_name in ["River Folk", "Meridian Chain"]
    
    # --- Paragon Trait Override Logic ---
    pol_stance = g.get("doctrines", {}).get("political", "Neutral")
    p_traits = paragon.get("traits", [])
    
    # Paragons can override faction doctrine with their own personality
    military_focus = pol_stance in ["Aggressive", "Expansionist"] or "Paranoid" in p_traits or "Short-Tempered" in p_traits
    pacifist_focus = pol_stance in ["Isolationist", "Defensive"] or "Peaceful" in p_traits or "Cowardly" in p_traits
    corrupt_focus = "Corrupt" in p_traits or "Greedy" in p_traits
    generous_focus = "Generous" in p_traits or "Heroic" in p_traits
    
    # Corrupt leaders sometimes just embezzle construction funds entirely
    if corrupt_focus and random.random() < 0.3:
        logs.append(f"👑 EMBEZZLEMENT: Villainous leader {paragon['name']} cancelled public works and pocketed the construction funds in {g['name']}!")
        paragon["recent_decisions"].append("Embezzled faction construction funds for personal wealth.")
        inventory["Wealth"] = inventory.get("Wealth", 0.0) + 50.0
        # Skip construction
    elif inventory["Lumber"] >= 10 and inventory["Stone"] >= 40:
        # Override Thresholds based on Paragon Traits
        food_threshold = 0.6 if not pacifist_focus else 0.8
        if military_focus: food_threshold = 0.3 # Militarist/Paranoid ignores food shortages
        if generous_focus: food_threshold = 0.9 # Generous leaders prioritize feeding people
        
        safety_threshold = 0.6 if not military_focus else 0.9
        if pacifist_focus: safety_threshold = 0.2 # Pacifist/Cowardly ignores safety or panics? Wait, Cowardly might want walls. Let's stick to Pacifist ignores safety.
        if generous_focus: safety_threshold = 0.4 # Generous favors food/culture over military
        
        
        # 1. Food Check
        if food_supply < food_threshold:
            cost_land = BUILDING_COSTS["farms"]
            cost_aqua = BUILDING_COSTS["kelp_farms"]
            # Choose aquatic if Theocracy, mixed chooses randomly if affordable, else land
            if build_aquatic or (build_mixed and random.random() < 0.5):
                if inventory["Lumber"] >= cost_aqua["Lumber"] and inventory["Stone"] >= cost_aqua["Stone"] and inventory.get("Rope", 0.0) >= cost_aqua["Rope"]:
                    inventory["Lumber"] -= cost_aqua["Lumber"]
                    inventory["Stone"] -= cost_aqua["Stone"]
                    inventory["Rope"] -= cost_aqua["Rope"]
                    g["kelp_farms_count"] = g.get("kelp_farms_count", 0) + 1
                    built_structure = "Kelp Farm"
            else:
                if inventory["Lumber"] >= cost_land["Lumber"] and inventory["Stone"] >= cost_land["Stone"]:
                    inventory["Lumber"] -= cost_land["Lumber"]
                    inventory["Stone"] -= cost_land["Stone"]
                    g["farms_count"] += 1
                    built_structure = "Farm"
                    
        # 2. Safety/Military Check
        elif safety_rating < safety_threshold and not pacifist_focus:
            cost_land = BUILDING_COSTS["walls"]
            cost_aqua = BUILDING_COSTS["reef_walls"]
            if build_aquatic or (build_mixed and random.random() < 0.5):
                if inventory["Stone"] >= cost_aqua["Stone"] and inventory.get("Coral", 0.0) >= cost_aqua["Coral"]:
                    inventory["Stone"] -= cost_aqua["Stone"]
                    inventory["Coral"] -= cost_aqua["Coral"]
                    g["reef_walls_count"] = g.get("reef_walls_count", 0) + 1
                    built_structure = "Reef Wall"
            else:
                if inventory["Lumber"] >= cost_land["Lumber"] and inventory["Stone"] >= cost_land["Stone"]:
                    inventory["Lumber"] -= cost_land["Lumber"]
                    inventory["Stone"] -= cost_land["Stone"]
                    g["walls_count"] += 1
                    built_structure = "Wall"
                    
        # 3. Resource Extraction Check
        elif inventory.get("Stone", 0.0) < 50 or (military_focus and inventory.get("Iron Ore", 0.0) < 20):
            cost_land = BUILDING_COSTS["mines"]
            cost_aqua = BUILDING_COSTS["coral_mines"]
            if build_aquatic or (build_mixed and random.random() < 0.5):
                if inventory["Lumber"] >= cost_aqua["Lumber"] and inventory["Stone"] >= cost_aqua["Stone"] and inventory.get("Basic Weapons", 0.0) >= cost_aqua["Basic Weapons"]:
                    inventory["Lumber"] -= cost_aqua["Lumber"]
                    inventory["Stone"] -= cost_aqua["Stone"]
                    inventory["Basic Weapons"] -= cost_aqua["Basic Weapons"]
                    g["coral_mines_count"] = g.get("coral_mines_count", 0) + 1
                    built_structure = "Coral Mine"
            else:
                if inventory["Lumber"] >= cost_land["Lumber"] and inventory["Stone"] >= cost_land["Stone"]:
                    inventory["Lumber"] -= cost_land["Lumber"]
                    inventory["Stone"] -= cost_land["Stone"]
                    g["mines_count"] += 1
                    built_structure = "Mine"
                    
        # 4. Barracks Check
        elif (new_crime > 0.4 or military_focus) and not pacifist_focus and inventory.get("Smelted Steel", 0.0) >= 20:
            cost = BUILDING_COSTS["barracks"]
            if inventory["Lumber"] >= cost["Lumber"] and inventory["Stone"] >= cost["Stone"] and inventory["Smelted Steel"] >= cost["Smelted Steel"]:
                inventory["Lumber"] -= cost["Lumber"]
                inventory["Stone"] -= cost["Stone"]
                inventory["Smelted Steel"] -= cost["Smelted Steel"]
                g["barracks_count"] += 1
                built_structure = "Barracks"
        elif g.get("workshops_count", 0) < mines:
            # Need workshops to refine ore
            cost = BUILDING_COSTS["workshops"]
            if inventory["Lumber"] >= cost["Lumber"] and inventory["Stone"] >= cost["Stone"] and inventory.get("Iron Ore", 0.0) >= cost["Iron Ore"]:
                inventory["Lumber"] -= cost["Lumber"]
                inventory["Stone"] -= cost["Stone"]
                inventory["Iron Ore"] -= cost["Iron Ore"]
                g["workshops_count"] = g.get("workshops_count", 0) + 1
                built_structure = "Workshop"
        elif new_mental < 0.6:
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
        else:
            # Try to build domestication facilities for species that are present
            dom_built = False
            for species_key, dom_info in DOMESTICATION_TABLE.items():
                facility_key = dom_info["facility"]
                if g.get(species_key, 0.0) > 15.0 and g.get(facility_key, 0) < 3:
                    # Find matching building cost
                    cost_key = facility_key.replace("domestic_", "")
                    cost = BUILDING_COSTS.get(cost_key, {"Lumber": 30, "Stone": 30})
                    can_build = all(inventory.get(r, 0.0) >= a for r, a in cost.items())
                    if can_build:
                        for r, a in cost.items():
                            inventory[r] -= a
                        g[facility_key] = g.get(facility_key, 0) + 1
                        built_structure = facility_key.replace("domestic_", "").replace("_", " ").title()
                        dom_built = True
                        break
            
            if not dom_built:
                cost = BUILDING_COSTS["mines"]
                if inventory["Lumber"] >= cost["Lumber"] and inventory["Stone"] >= cost["Stone"]:
                    inventory["Lumber"] -= cost["Lumber"]
                    inventory["Stone"] -= cost["Stone"]
                    g["mines_count"] += 1
                    built_structure = "Mine"

    if built_structure:
        logs.append(f"🏗️ CONSTRUCTION: {g['name']} constructed a new {built_structure} to expand infrastructure.")

    # 6. Trade (enhanced with transport bonus)
    traded = False
    trade_bonus = 1.0 + transport_bonus * 0.2
    if trader_status == "Active - Trade Route Established" and random.random() < 0.30 * trade_bonus:
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

    # 7. Wildlife Clashes
    if random.random() < 0.12:
        # Pick from species that actually exist in the area
        active_aggressive = [k for k in ALL_FAUNA if "aggressive" in ([] if g.get(k, 0.0) < 3.0 else ["aggressive"]) or g.get(k, 0.0) > 20.0]
        beast_name = random.choice(["Sky-Grazer", "Cloud-Cutter Ray", "Timber Wolf", "Wild Boar", "Ash-Bison", "Night-Carapace", "Glimmer-Wings"])
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
            pop_loss = int(new_pop * 0.03)
            new_pop = max(100.0, new_pop - pop_loss)
            logs.append(f"🚨 WILDLIFE TERROR: Villainous leader {paragon['name']} ignored the {beast_name} threat! {pop_loss} citizens perished.")
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
            inventory["Leather"] = inventory.get("Leather", 0.0) + 3.0
            logs.append(f"🤠 PARAGON HUNT: {paragon['name']} led a Direct Hunt on the {beast_name}, acquiring 3 Leather.{' The leader was wounded.' if injured else ''}")
            paragon["recent_decisions"].append(f"Hunted down wild {beast_name}.")
        elif p_decision == "Evacuation":
            logs.append(f"🤠 PARAGON EVACUATION: {paragon['name']} ordered local herders to evacuate from the {beast_name}'s path, suffering zero casualties.")
            paragon["recent_decisions"].append(f"Evacuated fields from {beast_name}.")
        elif p_decision == "Bait/Trap":
            if inventory.get("Grain", 0.0) >= 3.0:
                inventory["Grain"] -= 3.0
                inventory["Leather"] = inventory.get("Leather", 0.0) + 2.0
                logs.append(f"🤠 PARAGON TRAP: {paragon['name']} set alchemical traps baited with 3 Grain, safely catching the {beast_name}.")
                paragon["recent_decisions"].append(f"Trapped wild {beast_name} safely.")
            else:
                p_decision = "Standard Defense"
        if p_decision == "Standard Defense":
            if barracks > 0 or watchtowers > 1:
                logs.append(f"🦅 WILDLIFE: Military patrols in {g['name']} drove off a wild {beast_name}.")
            else:
                pop_loss = int(new_pop * 0.02)
                new_pop = max(100.0, new_pop - pop_loss)
                logs.append(f"🚨 WILDLIFE THREAT: An aggressive {beast_name} raided {g['name']}, causing {pop_loss} casualties among the population.")
            if paragon:
                paragon["recent_decisions"].append(f"Guards managed wildlife clash with {beast_name}.")

    # 7.5. Bandit Raids
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

    # Cult recruitment scales massively with proximity to Chaos Anchors and Convergence Spiral Paths
    proximity = g.get("distance_to_chaos_structure", 1.0)
    anchor_multiplier = 1.0
    if proximity < 0.2:
        anchor_multiplier = 8.0 # Extreme growth right on top of an anchor
    elif proximity < 0.4:
        anchor_multiplier = 4.0
    elif proximity < 0.6:
        anchor_multiplier = 2.0
        
    cult_recruits = g["population"] * ((1.0 - new_phys) * 0.002 + new_discontent * 0.003 + new_crime * 0.005) * anchor_multiplier
    g["cult_population"] = min(g["population"], max(0.0, g["cult_population"] + cult_recruits))
    
    new_devoted = cult_recruits * 0.15
    g["cult_devoted"] = min(g["cult_population"], max(0.0, g["cult_devoted"] + new_devoted))
    g["cult_infiltration"] = g["cult_population"] / max(1.0, g["population"])

    
    seal_degrade = g["cult_devoted"] * 0.00003
    prisons[magistar] = max(0.0, prisons[magistar] - seal_degrade)
    if seal_degrade > 0.0005:
        logs.append(f"👁️ CULT DEVOTED: Devoted priests near {magistar} Prison weakened the seal by {seal_degrade*100:.3f}%.")

    # Cultist spread to adjacent factions
    spread_target = None
    if g["cult_infiltration"] > 0.20 and random.random() < 0.30:
        adj_list = FACTION_ADJACENCY.get(g["name"], [])
        if adj_list:
            target_faction_name = random.choice(adj_list)
            spread_amount = int(g["cult_population"] * 0.02)
            if spread_amount > 0:
                spread_target = (target_faction_name, spread_amount)

    if g["cult_infiltration"] > 0.40 and random.random() < 0.25:
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
    
    sparkborn_pool = new_pop * 0.5
    warden_recruits = sparkborn_pool * g["chaos_level"] * g["pressure"] * 0.002
    
    new_pop = max(100.0, new_pop - warden_recruits)
    prisons["warden_recruits_accumulated"] = prisons.get("warden_recruits_accumulated", 0.0) + warden_recruits
    
    proximity_to_spire = 1.0 - g.get("distance_to_convergence", 0.6)
    patrol_priority = (g["chaos_level"] + proximity_to_spire) / 2.0
    allocated_patrols = (prisons["warden_population"] / 17.0) * patrol_priority * 1.5
    
    proximity_to_prison = 1.0 - g.get("distance_to_chaos_structure", 0.5)
    hunter_priority = (g["cult_infiltration"] + proximity_to_prison) / 2.0
    allocated_hunters = (prisons["warden_population"] / 17.0) * hunter_priority * 1.5

    chaos_reduction = 0.03 * (allocated_patrols / 100.0)
    g["chaos_level"] = max(0.0, g["chaos_level"] - chaos_reduction)
    if chaos_reduction > 0.003:
        logs.append(f"🛡️ PATROL: Warden patrols ({allocated_patrols:.0f} sentinels) suppressed chaos by {chaos_reduction*100:.2f}%.")

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

    if prisons[magistar] < 1.0:
        warden_efficiency = prisons["warden_population"] / 1500.0
        repaired_val = 0.02 * warden_efficiency
        prisons[magistar] = min(1.0, prisons[magistar] + repaired_val)
        logs.append(f"🛡️ WARDENS: Grey Wardens (efficiency {warden_efficiency:.2f}) autonomously reinforced the {magistar} Prison seal by {repaired_val * 100:.2f}%. Current integrity: {prisons[magistar] * 100:.0f}%.")

    # 11. Magistar Prison Spike Effects
    proximity = g.get("distance_to_chaos_structure", 0.5)
    spike_chance = 0.30 * (1.0 - proximity)
    if g["is_active"] and random.random() < spike_chance:
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
        prisons[magistar] = max(0.0, prisons[magistar] - 0.03)
        g["chaos_level"] = min(1.0, g["chaos_level"] + 0.04)
        logs.append(f"🔮 MAGIC FEEDBACK: Sparkborn leader {paragon['name']} ({magic_affinity}) experienced a magical spike, degrading {magistar} Prison seal by 3.0% and increasing local chaos by 4.0%!")

    # 12. POPULATION DEATH (natural attrition, starvation, chaos, disease, storms)
    new_pop = calculate_population_death(new_pop, g, inventory, weather_type, food_supply, logs)

    # Tag-based interaction system resolver
    from tag_system import apply_tag_interactions
    active_tags = apply_tag_interactions(g, inventory, weather, prisons, logs)

    # Calculate population counts
    sparkborn_pop = new_pop * 0.5
    null_pop = new_pop * 0.5

    # Store security_rating on g for other systems to read
    g["security_rating"] = security_rating

    # Build return dict with all species
    result = {
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
        "churches_count": g["churches_count"],
        "theatres_count": g["theatres_count"],
        "arenas_count": g["arenas_count"],
        "gambling_dens_count": g["gambling_dens_count"],
        "black_markets_count": g["black_markets_count"],
        "paragon": g["paragon"],
    }

    # Add all species populations to result
    for species_key in ALL_SPECIES:
        result[species_key] = g.get(species_key, 0.0)

    # Add all domestication facility counts to result
    for dom_key in ["domestic_greenhouses", "domestic_orchards", "domestic_pens", "domestic_kennels",
                     "domestic_cloud_ram_pens", "domestic_beetle_stables", "domestic_weaver_farms",
                     "domestic_dune_dog_dens", "domestic_snail_docks", "domestic_sheep_pastures",
                     "domestic_horse_stables", "domestic_aphid_farms", "domestic_falcon_roosts"]:
        result[dom_key] = g.get(dom_key, 0)

    return result
