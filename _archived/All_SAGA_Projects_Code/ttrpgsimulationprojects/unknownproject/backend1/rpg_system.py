import random

DOMAINS = [
    "Pyromancy", "Cryomancy", "Aeromancy", "Geomancy", "Biomancy", "Necromancy",
    "Chronomancy", "Telepathy", "Telekinesis", "Abjuration", "Illusion", "Aetheric"
]

def generate_stats(biological_type, profession, entity_type="CITIZEN", traits=None):
    """
    Generates 12 core stats for a local entity, strictly constrained within a 0-9 scale.
    Now also returns a magic profile dictionary representing high-fantasy magic affinity.
    """
    if traits is None:
        traits = {}

    stats = {}
    core_keys = [
        "might", "endurance", "finesse", "reflex", "vitality", "fortitude",
        "knowledge", "logic", "awareness", "intuition", "charm", "willpower"
    ]

    # Generate base attribute values based on entity type tier
    for key in core_keys:
        if entity_type == "CITIZEN":
            # Citizens: Base rolls between 1 and 3. Small chance (10%) for a 0 (flaw) or 4 (talented).
            if random.random() < 0.10:
                stats[key] = random.choice([0, 4])
            else:
                stats[key] = random.randint(1, 3)
        elif entity_type == "PARAGON":
            # Paragons: Base rolls between 3 and 5.
            stats[key] = random.randint(3, 5)
        elif entity_type == "HERO":
            # Heroes: Base rolls between 4 and 6.
            stats[key] = random.randint(4, 6)
        else:
            stats[key] = random.randint(1, 3)

    # Apply Citizen minor +1 profession bumps
    if entity_type == "CITIZEN":
        prof_bumps = {
            "Guard": "might",
            "Scholar": "knowledge",
            "Miner": "endurance",
            "Woodcutter": "fortitude",
            "Weaver": "finesse",
            "Trader": "charm",
            "Farmer": "vitality"
        }
        bump_stat = prof_bumps.get(profession)
        if bump_stat:
            stats[bump_stat] += 1

    # Apply Paragon talent exceptional overrides (guarantees 6 or 7)
    if entity_type == "PARAGON":
        # Extract talent from traits or fall back based on profession
        talent = None
        if isinstance(traits, dict):
            talent = traits.get("talent")
        elif isinstance(traits, list):
            for t in traits:
                if t in ["TACTICS", "LORE", "STEALTH", "MEDICINE", "COMMAND", "DIPLOMACY"]:
                    talent = t
                    break
        
        if not talent:
            prof_talents = {
                "Guard": "TACTICS",
                "Scholar": "LORE",
                "Miner": "STEALTH",
                "Woodcutter": "STEALTH",
                "Weaver": "DIPLOMACY",
                "Trader": "DIPLOMACY",
                "Farmer": "MEDICINE"
            }
            talent = prof_talents.get(profession, random.choice(["TACTICS", "LORE", "STEALTH", "MEDICINE", "COMMAND", "DIPLOMACY"]))

        talent_stats = {
            "TACTICS": ["logic", "willpower", "might"],
            "LORE": ["knowledge", "logic", "awareness"],
            "STEALTH": ["finesse", "reflex"],
            "MEDICINE": ["intuition", "awareness", "vitality"],
            "COMMAND": ["willpower", "charm", "might"],
            "DIPLOMACY": ["charm", "logic", "willpower"]
        }

        relevant = talent_stats.get(talent, ["willpower"])
        for stat in relevant:
            stats[stat] = random.choice([6, 7])

    # Apply Hero traits legendary bumps (high chance of 7s or 8s)
    if entity_type == "HERO":
        relevant_stats = []
        
        # Check professional affinity
        if profession == "Guard":
            relevant_stats.extend(["might", "fortitude", "willpower"])
        elif profession == "Scholar":
            relevant_stats.extend(["knowledge", "logic", "willpower"])
        elif profession == "Miner":
            relevant_stats.extend(["endurance", "fortitude", "might"])
        elif profession == "Woodcutter":
            relevant_stats.extend(["fortitude", "endurance", "might"])
        elif profession == "Weaver":
            relevant_stats.extend(["finesse", "reflex", "intuition"])
        elif profession == "Trader":
            relevant_stats.extend(["charm", "logic", "intuition"])
        elif profession == "Farmer":
            relevant_stats.extend(["vitality", "endurance", "awareness"])

        # Check trait (personality and interest) affinities
        personality = None
        interest = None
        if isinstance(traits, dict):
            personality = traits.get("personality")
            interest = traits.get("interest")
        elif isinstance(traits, list):
            for t in traits:
                if t in ["BRAVE", "DILIGENT", "CUNNING", "PEACEFUL"]:
                    personality = t
                if t in ["THE_ARTS", "SURVIVAL", "COMMERCE", "METABOLISM", "LORE"]:
                    interest = t

        if personality == "BRAVE":
            relevant_stats.extend(["willpower", "might", "fortitude"])
        elif personality == "DILIGENT":
            relevant_stats.extend(["endurance", "logic", "willpower"])
        elif personality == "CUNNING":
            relevant_stats.extend(["finesse", "logic", "reflex"])
        elif personality == "PEACEFUL":
            relevant_stats.extend(["charm", "intuition", "awareness"])

        if interest == "THE_ARTS":
            relevant_stats.extend(["charm", "intuition", "finesse"])
        elif interest == "SURVIVAL":
            relevant_stats.extend(["vitality", "endurance", "awareness"])
        elif interest == "COMMERCE":
            relevant_stats.extend(["charm", "logic", "willpower"])
        elif interest == "METABOLISM":
            relevant_stats.extend(["vitality", "endurance", "might"])
        elif interest == "LORE":
            relevant_stats.extend(["knowledge", "logic", "awareness"])

        # Set relevant stats to 7 or 8 with high chance (70%)
        for stat in set(relevant_stats):
            if stat in stats and random.random() < 0.70:
                stats[stat] = random.choice([7, 8])

    # Strictly clamp all attributes to 0-9 scale
    for key in core_keys:
        stats[key] = max(0, min(9, stats[key]))

    # Generate magic profile (Phase 17)
    roll = random.randint(1, 100)
    tier = "Null"
    mastered = []
    touched = []

    if roll > 50:
        aptitude = random.randint(1, 100)
        if 1 <= aptitude <= 40:
            tier = "Spark"
            mastered = []
            touched = random.sample(DOMAINS, 1)
        elif 41 <= aptitude <= 80:
            tier = "Novice"
            mastered = random.sample(DOMAINS, 1)
            touched = []
        elif 81 <= aptitude <= 90:
            tier = "Adept"
            mastered = random.sample(DOMAINS, 1)
            remaining = [d for d in DOMAINS if d not in mastered]
            touched = random.sample(remaining, random.randint(1, 2))
        elif 91 <= aptitude <= 96:
            tier = "Expert"
            mastered = random.sample(DOMAINS, 2)
            remaining = [d for d in DOMAINS if d not in mastered]
            touched = random.sample(remaining, random.randint(2, 4))
        elif 97 <= aptitude <= 99:
            tier = "Archmage"
            mastered = random.sample(DOMAINS, random.randint(4, 6))
            remaining = [d for d in DOMAINS if d not in mastered]
            touched = remaining  # all others touched
        elif aptitude == 100:
            tier = "Grandmaster"
            mastered = list(DOMAINS)
            touched = []

    magic_profile = {
        "tier": tier,
        "mastered": mastered,
        "touched": touched
    }

    return stats, magic_profile

def calculate_derived_pools(stats):
    """
    Returns initial and max dynamic capacities based on calculated RPG stats.
    """
    hp = stats.get("endurance", 0) + stats.get("fortitude", 0) + stats.get("vitality", 0)
    composure = stats.get("willpower", 0) + stats.get("logic", 0) + stats.get("charm", 0)
    stamina = stats.get("might", 0) + stats.get("reflex", 0) + stats.get("finesse", 0)
    focus = stats.get("knowledge", 0) + stats.get("awareness", 0) + stats.get("intuition", 0)

    return {
        "hp": hp,
        "hp_max": hp,
        "composure": composure,
        "composure_max": composure,
        "stamina": stamina,
        "stamina_max": stamina,
        "focus": focus,
        "focus_max": focus
    }
