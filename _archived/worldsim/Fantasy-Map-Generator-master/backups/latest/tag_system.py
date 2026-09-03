# tag_system.py
import random

# Tags by weather type
WEATHER_TAGS = {
    "Reality Storm": ["chaos", "lightning", "force", "degrade", "destabilize"],
    "Flux Monsoon": ["water", "storm", "chaos", "flood", "growth"],
    "Static Drought": ["dry", "heat", "crack", "fire-hazard"],
    "Aetheric Mist": ["fog", "magic", "stealth"],
    "Stable": ["calm", "safe"]
}

# Tags by inventory resource
RESOURCE_TAGS = {
    "Lumber": ["wood", "flammable", "organic"],
    "Stone": ["stone", "hard", "heavy", "fire-proof"],
    "Iron Ore": ["metal", "raw", "conductive"],
    "Copper Ore": ["metal", "raw", "conductive"],
    "Coal": ["fuel", "carbon", "flammable"],
    "Grain": ["food", "organic", "flammable", "dry"],
    "Leather": ["organic", "flexible"],
    "Dragonstone": ["magic", "crystal", "chaos-active"],
    "Voltaic Fleece": ["electric", "organic", "flammable"],
    "Ozone-Milk": ["liquid", "organic", "magic-active"],
    "Ghost Flower": ["organic", "magic", "delicate", "cold-resistant"],
    "Night-Nectar": ["organic", "liquid", "magic-active"],
    "Flour": ["food", "organic", "powder", "flammable"],
    "Peak-Cheese": ["food", "organic"],
    "Smelted Steel": ["metal", "hard", "conductive", "fire-proof"],
    "Copper Wire": ["metal", "conductive", "flexible"],
    "Refined Aether Battery": ["magic", "electric", "energy", "explosive"],
    "Ostrakan Hardtack": ["food", "organic", "dry"],
    "Caldera Spark-Bread": ["food", "magic-active", "organic"],
    "Basic Weapons": ["metal", "combat"],
    "Leather Armor": ["organic", "flexible", "protection"]
}

# Tags by building key
STRUCTURE_TAGS = {
    "farms_count": ["wood", "organic", "flammable", "crop"],
    "docks_count": ["wood", "water-adjacent", "flammable"],
    "mines_count": ["stone", "underground", "hard"],
    "watchtowers_count": ["wood", "tall", "height", "lightning-hazard", "flammable"],
    "walls_count": ["stone", "hard", "structure", "fire-proof"],
    "barracks_count": ["stone", "wood", "structure", "military", "flammable"],
    "churches_count": ["stone", "holy", "structure"],
    "theatres_count": ["wood", "structure", "flammable"],
    "arenas_count": ["stone", "structure"],
    "gambling_dens_count": ["wood", "structure", "flammable", "illicit"],
    "black_markets_count": ["wood", "structure", "flammable", "illicit"],
    "domestic_greenhouses": ["glass", "organic", "crop", "fragile"],
    "domestic_orchards": ["organic", "crop", "wood"],
    "domestic_pens": ["wood", "beast-contain", "flammable"],
    "domestic_kennels": ["wood", "beast-contain", "flammable"]
}

# Tags by flora and fauna population key
FLORA_FAUNA_TAGS = {
    "flora_ghost_flower": ["organic", "magic", "delicate"],
    "flora_stone_root": ["organic", "stone", "hard", "dry-resistant"],
    "fauna_sky_grazer": ["beast", "electric", "docile", "conductive"],
    "fauna_timber_wolf": ["beast", "carnivore", "cold-immune", "fur", "aggressive"]
}

def get_paragon_tags(paragon):
    """Generates lists of tags for a leader based on their magic affinity and traits."""
    if not paragon:
        return []
    tags = ["mortal", "leader"]
    affinity = paragon.get("magic_affinity", "Null")
    if "Sparkborn" in affinity:
        tags.extend(["magic-active", "conductive", "chaos-attuned"])
    else:
        tags.extend(["magic-void", "stable"])
        
    for trait in paragon.get("traits", []):
        if trait in ["Short-tempered", "Paranoid"]:
            tags.append("volatile")
        elif trait in ["Corrupt", "Spiteful"]:
            tags.append("decay")
        elif trait in ["Highly Spiritual", "Zealous"]:
            tags.append("holy")
        elif trait in ["Sage", "Diplomat"]:
            tags.append("mind-focus")
        elif trait in ["War Survivor", "Indomitable"]:
            tags.append("hardy")
    return tags

def get_biome_tags(faction_name):
    """Determines biome property tags based on faction names."""
    if not faction_name:
        return ["temperate"]
    name_upper = faction_name.upper()
    if "URSINE" in name_upper:
        return ["cold", "mountain", "snow"]
    elif "SUMP" in name_upper or "TOAD" in name_upper:
        return ["swamp", "wet", "acid"]
    elif "RIVER" in name_upper:
        return ["water", "wet", "temperate"]
    elif "CALADREA" in name_upper or "IRON" in name_upper:
        return ["rocky", "mountain", "temperate"]
    elif "FLOWER" in name_upper:
        return ["temperate", "lush", "fertile"]
    elif "CANOPY" in name_upper or "SYLVIAN" in name_upper:
        return ["forest", "wooded", "temperate"]
    else:
        return ["temperate"]

def apply_tag_interactions(g, inventory, weather, prisons, logs):
    """
    Unified one-line resolver.
    Collects active tags across the macro group, resolves matching tag-to-tag interactions,
    and applies side-effects to simulation state variables.
    """
    active_sources = {}
    
    def add_source(tag, source_type, source_name, value):
        if tag not in active_sources:
            active_sources[tag] = []
        active_sources[tag].append((source_type, source_name, value))

    # Weather
    w_type = weather if isinstance(weather, str) else weather.get("type", "Stable")
    for t in WEATHER_TAGS.get(w_type, ["calm"]):
        add_source(t, "weather", w_type, 1.0)
    if isinstance(weather, dict) and weather.get("is_chaos_charged"):
        add_source("chaos-charged", "weather", w_type, 1.0)

    # Biome
    biome_tags = get_biome_tags(g.get("name", ""))
    for t in biome_tags:
        add_source(t, "biome", g.get("name", ""), 1.0)

    # Inventory Resources
    for res_name, count in inventory.items():
        if count > 0:
            for t in RESOURCE_TAGS.get(res_name, []):
                add_source(t, "resource", res_name, count)

    # Structures/Buildings
    for b_key, b_tags in STRUCTURE_TAGS.items():
        count = g.get(b_key, 0)
        if count > 0:
            for t in b_tags:
                add_source(t, "structure", b_key, count)

    # Flora & Fauna
    for f_key, f_tags in FLORA_FAUNA_TAGS.items():
        count = g.get(f_key, 0.0)
        if count > 0.0:
            for t in f_tags:
                add_source(t, "flora_fauna", f_key, count)

    # Paragon Leader
    p = g.get("paragon")
    p_tags = get_paragon_tags(p)
    for t in p_tags:
        add_source(t, "paragon", p.get("name", "Leader") if p else "Leader", 1.0)

    magistar = g.get("magistar_id", "Tiraton")

    # Reaction 1: Lightning + Wood (Burn wooden structures or resources)
    if "lightning" in active_sources and "wood" in active_sources:
        burned_anything = False
        for src in active_sources["wood"]:
            if src[0] == "structure":
                b_key = src[1]
                if g.get(b_key, 0) > 0:
                    g[b_key] = max(0, g[b_key] - 1)
                    logs.append(f"🔥 TAG REACTION: Lightning struck a wooden {b_key.replace('_count', '')} in {g['name']}, burning it to ash!")
                    burned_anything = True
                    break
        if not burned_anything:
            if inventory.get("Lumber", 0.0) >= 5.0:
                inventory["Lumber"] = max(0.0, inventory["Lumber"] - 5.0)
                logs.append(f"🔥 TAG REACTION: Lightning strike ignited the wood reserves of {g['name']}, destroying 5.0 Lumber!")
                burned_anything = True

    # Reaction 2: Flood + Crop/Grain (Rot crops)
    if "flood" in active_sources and "crop" in active_sources:
        if g.get("farms_count", 0) > 0 and random.random() < 0.4:
            g["farms_count"] = max(0, g["farms_count"] - 1)
            logs.append(f"🌾 TAG REACTION: Flood waters inundated and ruined a local Farm in {g['name']}!")
        elif inventory.get("Grain", 0.0) >= 8.0:
            inventory["Grain"] = max(0.0, inventory["Grain"] - 8.0)
            logs.append(f"🌾 TAG REACTION: Inundated conditions rotted 8.0 units of stored Grain in {g['name']}!")

    # Reaction 3: Dry/Heat + Wood/Flammable (Static Drought spontaneous ignition)
    if "dry" in active_sources and "wood" in active_sources and random.random() < 0.12:
        if inventory.get("Lumber", 0.0) >= 3.0:
            inventory["Lumber"] = max(0.0, inventory["Lumber"] - 3.0)
            logs.append(f"🔥 TAG REACTION: Extreme dry heat caused spontaneous ignition, destroying 3.0 Lumber in {g['name']}!")

    # Reaction 4: Chaos + Magic-Active (Feedback Spikes)
    if "chaos" in active_sources and "magic-active" in active_sources:
        if magistar in prisons:
            degrade = 0.02
            prisons[magistar] = max(0.0, prisons[magistar] - degrade)
            logs.append(f"🔮 TAG REACTION: Ambient chaos resonated with magic-active entities in {g['name']}, degrading {magistar} Prison seal by 2.0%!")

    # Reaction 5: Magic-Void + Chaos (Dampen chaos level)
    if "magic-void" in active_sources and "chaos" in active_sources:
        g["chaos_level"] = max(0.0, g["chaos_level"] - 0.05)
        logs.append(f"🧿 TAG REACTION: Magic-void aura of leader neutralized and dampened chaos in {g['name']} by 5.0%!")

    # Reaction 6: Acid + Stone (Corrosion of stone walls or mines)
    if "acid" in active_sources and "stone" in active_sources and random.random() < 0.20:
        if g.get("walls_count", 0) > 0:
            g["walls_count"] = max(0, g["walls_count"] - 1)
            logs.append(f"🧪 TAG REACTION: Acidic swamp runoff corroded and collapsed a Wall segment in {g['name']}!")

    # Return summary of active tags
    all_tags = sorted(list(active_sources.keys()))
    return all_tags
