# tag_system.py
import random

# ===========================
# WEATHER TAGS
# ===========================
WEATHER_TAGS = {
    "Reality Storm": ["chaos", "lightning", "force", "degrade", "destabilize", "wind"],
    "Flux Monsoon": ["water", "storm", "chaos", "flood", "growth", "wind"],
    "Static Drought": ["dry", "heat", "crack", "fire-hazard"],
    "Aetheric Mist": ["fog", "magic", "stealth"],
    "Stable": ["calm", "safe"]
}

# ===========================
# RESOURCE TAGS (Raw + Produced)
# ===========================
RESOURCE_TAGS = {
    # --- Raw Resources ---
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
    "D-Dust": ["magic", "powder", "chaos-active", "flammable"],
    "Salt": ["mineral", "holy", "dry", "preservative"],
    "Fungal Alloy": ["metal", "organic", "chaos-immune", "hard"],
    "Camouflage Dye": ["organic", "liquid", "stealth"],
    "Stone-Hide": ["organic", "hard", "fire-proof", "heavy"],
    "Wool": ["organic", "flammable", "flexible", "cold-resistant"],
    "Honeydew": ["organic", "liquid", "food", "sweet"],
    "Silk-Steel Thread": ["metal", "organic", "flexible", "hard"],
    "Anesthetic Toxin": ["organic", "liquid", "toxic", "alchemical"],
    "Resin": ["organic", "liquid", "flammable"],
    "Alloy Carapace": ["metal", "hard", "fire-proof"],
    "Crystal Chips": ["crystal", "magic", "hard"],
    "Stinger Weapon": ["organic", "electric", "combat"],
    "Luxury Meat": ["food", "organic"],
    "Venison": ["food", "organic"],
    "Fat": ["organic", "flammable", "food"],
    "Antler": ["organic", "hard", "craft"],
    # --- Tier 1 Produced ---
    "Flour": ["food", "organic", "powder", "flammable"],
    "Peak-Cheese": ["food", "organic"],
    "Smelted Steel": ["metal", "hard", "conductive", "fire-proof"],
    "Copper Wire": ["metal", "conductive", "flexible"],
    "Refined Aether Battery": ["magic", "electric", "energy", "explosive"],
    "Shadow-Set Ink": ["magic", "liquid", "chaos-active"],
    "Drained Fleece Wool": ["organic", "flexible", "cold-resistant"],
    "Tanned Strips": ["organic", "flexible", "hard"],
    "Charcoal": ["fuel", "carbon", "flammable"],
    "Bricks": ["stone", "hard", "fire-proof"],
    # --- Tier 2 Produced ---
    "Ostrakan Hardtack": ["food", "organic", "dry"],
    "Caldera Spark-Bread": ["food", "magic-active", "organic"],
    "Basic Weapons": ["metal", "combat"],
    "Iron Tools": ["metal", "hard", "craft"],
    "Grounding Chains": ["metal", "conductive", "holy"],
    "Aether-Wright PPE": ["organic", "flexible", "protection", "magic"],
    "Silk-Steel Cables": ["metal", "organic", "hard", "flexible"],
    "Leather Armor": ["organic", "flexible", "protection"],
    "Rope": ["organic", "flexible"],
    "Jitter-Rig": ["metal", "magic", "electric", "craft"],
}

# ===========================
# STRUCTURE TAGS
# ===========================
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
    "black_markets_count": ["wood", "structure", "flammable", "illicit", "trade"],
    # Domestication facilities
    "domestic_greenhouses": ["glass", "organic", "crop", "fragile"],
    "domestic_orchards": ["organic", "crop", "wood"],
    "domestic_pens": ["wood", "beast-contain", "flammable"],
    "domestic_kennels": ["wood", "beast-contain", "flammable"],
    "domestic_cloud_ram_pens": ["wood", "beast-contain", "cold-resistant"],
    "domestic_beetle_stables": ["wood", "beast-contain", "transport"],
    "domestic_weaver_farms": ["stone", "underground", "beast-contain", "silk"],
    "domestic_dune_dog_dens": ["wood", "beast-contain", "pest-control"],
    "domestic_snail_docks": ["stone", "water-adjacent", "transport"],
    "domestic_sheep_pastures": ["wood", "beast-contain", "flammable", "crop"],
    "domestic_horse_stables": ["wood", "beast-contain", "transport"],
    "domestic_aphid_farms": ["wood", "beast-contain", "food"],
    "domestic_falcon_roosts": ["wood", "height", "messenger"],
}

# ===========================
# FLORA & FAUNA TAGS (Complete from Lore)
# ===========================
FLORA_FAUNA_TAGS = {
    # === Unique Ostraka Wildlife ===
    "fauna_sky_grazer": ["beast", "electric", "docile", "conductive", "livestock", "explosive", "airborne"],
    "fauna_glimmer_wings": ["beast", "insect", "aggressive", "camouflage", "airborne"],
    "fauna_gritbore": ["beast", "scavenger", "rocky", "livestock", "heat-resistant"],
    "fauna_ash_bison": ["beast", "herbivore", "aggressive", "fire-resistant", "migratory"],
    "fauna_cloud_cutter_ray": ["beast", "apex-predator", "airborne", "electric", "aggressive"],
    "fauna_cloud_ram": ["beast", "livestock", "cold-resistant", "mountain", "wool", "docile"],
    "fauna_draft_beetle": ["beast", "insect", "docile", "transport", "wood"],
    "fauna_dune_dog": ["beast", "docile", "desert", "pest-control"],
    "fauna_dust_skipper": ["beast", "airborne", "scavenger", "desert"],
    "fauna_fur_wyrm": ["beast", "scavenger", "pest", "cold-resistant"],
    "fauna_furnace_tick": ["insect", "pest", "metal", "heat-resistant", "destructive"],
    "fauna_gem_shell_beetle": ["insect", "crystal", "airborne", "magic"],
    "fauna_glass_sand_eel": ["beast", "predator", "underground", "desert", "deadly"],
    "fauna_night_carapace": ["insect", "predator", "nocturnal", "food"],
    "fauna_abyssal_snail": ["beast", "aquatic", "transport", "docile"],
    "fauna_weaver_cow": ["beast", "insect", "underground", "silk", "docile"],
    "fauna_titan_aphid": ["insect", "docile", "forest", "food", "sweet"],
    # === Standard Stock Wildlife ===
    "fauna_timber_wolf": ["beast", "carnivore", "cold-immune", "fur", "aggressive"],
    "fauna_wild_boar": ["beast", "herbivore", "aggressive", "food", "leather"],
    "fauna_red_deer": ["beast", "herbivore", "docile", "food", "leather"],
    "fauna_peregrine_falcon": ["beast", "airborne", "docile", "messenger"],
    "fauna_black_bear": ["beast", "omnivore", "aggressive", "food", "fur"],
    "fauna_domestic_sheep": ["beast", "livestock", "docile", "wool", "food"],
    "fauna_draft_horse": ["beast", "transport", "docile", "livestock"],
    # === Unique Ostraka Flora ===
    "flora_ghost_flower": ["organic", "magic", "delicate", "alchemical"],
    "flora_grave_roots": ["organic", "carnivorous", "toxic", "wood", "dangerous"],
    "flora_stone_root": ["organic", "stone", "hard", "fire-proof", "dry-resistant"],
    "flora_strangler_fig": ["organic", "parasitic", "wood", "spreading"],
    "flora_silver_leaf": ["organic", "magic", "arcane", "delicate"],
    "flora_saguaro": ["organic", "desert", "water-store", "hard"],
    # === Standard Stock Flora ===
    "flora_common_oak": ["organic", "wood", "hard", "flammable"],
    "flora_wild_rye": ["organic", "food", "crop", "flammable"],
    "flora_bluebell": ["organic", "delicate", "toxic", "decorative"],
    "flora_forest_fern": ["organic", "wet", "packing", "dye"],
    "flora_alpine_spruce": ["organic", "wood", "cold-resistant", "flammable", "resin"],
    "flora_desert_sage": ["organic", "desert", "aromatic", "food"],
    "flora_plains_grass": ["organic", "crop", "food", "flammable"],
    "flora_marsh_reed": ["organic", "wet", "flexible"],
    "flora_ocean_kelp": ["organic", "aquatic", "food", "kelp"],
    "flora_luminescent_coral": ["organic", "aquatic", "stone", "coral", "magic", "decorative"],
    "fauna_field_mouse": ["beast", "scavenger", "pest", "docile"],
    "fauna_river_fish": ["beast", "aquatic", "food", "fish", "docile"],
    "fauna_seagull": ["beast", "airborne", "scavenger", "coastal"],
    "fauna_reef_shark": ["beast", "aquatic", "predator", "aggressive"],
    "fauna_abyssal_whale": ["beast", "aquatic", "apex-predator", "heavy", "docile"],
    "fauna_saltwater_fish": ["beast", "aquatic", "food", "fish", "docile"],
    "fauna_coral_crab": ["beast", "aquatic", "scavenger", "crustacean", "hard"],
}

# ===========================
# FACTION CULTURE TAGS
# ===========================
FACTION_TAGS = {
    "Ursine Hegemony": ["cold", "mountain", "military", "holy", "hospitality"],
    "River Folk": ["water", "trade", "agile", "aquatic"],
    "Sump-Kin": ["swamp", "acid", "toxic", "industrial"],
    "Iron Caladrea": ["metal", "fire", "industrial", "stone", "mountain"],
    "Vaneer Concord": ["bureaucratic", "trade", "underground"],
    "Hive Collective": ["insect", "organic", "crop", "collective"],
    "Avians": ["airborne", "holy", "arcane", "judicial"],
    "Flower Valwey": ["organic", "crop", "alchemical", "growth"],
    "Sylvian": ["wood", "organic", "forest", "growth"],
    "Sciute": ["stone", "hard", "fire-proof", "construction"],
    "Meridian Chain": ["aquatic", "trade", "transport"],
    "Prism Lizards": ["crystal", "magic", "arcane"],
    "Canopy Clans": ["wood", "airborne", "electric"],
    "East Hounds": ["beast", "carnivore", "nomadic"],
    "Guirrilla Clans": ["stone", "underground", "guerrilla"],
    "Theocracy": ["aquatic", "holy", "fire", "magic"],
    "The Reliance": ["underground", "organic", "chaos-immune", "arcane"],
}

# ===========================
# PARAGON TAG GENERATION
# ===========================
def get_paragon_tags(paragon):
    """Generates lists of tags for a leader based on their magic affinity and traits."""
    if not paragon:
        return []
    tags = ["mortal", "leader"]
    affinity = paragon.get("magic_affinity", "Null")
    if "Sparkborn" in affinity:
        tags.extend(["magic-active", "conductive", "chaos-attuned"])
        tier = affinity.split(" - ")[-1] if " - " in affinity else "Sensitive"
        if tier in ["Master", "Epic"]:
            tags.append("arcane")
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
        elif trait in ["Vigilant"]:
            tags.append("awareness")
        elif trait in ["Generous", "Just"]:
            tags.append("prosperity")
        elif trait in ["Greedy", "Cruel"]:
            tags.append("oppressive")
        elif trait in ["Valiant"]:
            tags.append("combat")
    return tags

# ===========================
# BIOME TAG GENERATION
# ===========================
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
    elif "HIVE" in name_upper:
        return ["temperate", "fertile", "collective"]
    elif "AVIAN" in name_upper:
        return ["mountain", "airborne", "temperate"]
    elif "SCIUTE" in name_upper:
        return ["coastal", "rocky", "temperate"]
    elif "MERIDIAN" in name_upper:
        return ["aquatic", "coastal", "wet"]
    elif "PRISM" in name_upper or "LIZARD" in name_upper:
        return ["rocky", "crystal", "temperate"]
    elif "HOUND" in name_upper:
        return ["steppe", "windy", "temperate"]
    elif "GUIRRILLA" in name_upper:
        return ["canyon", "rocky", "dry"]
    elif "THEOCRACY" in name_upper:
        return ["aquatic", "coastal", "holy"]
    elif "RELIANCE" in name_upper:
        return ["underground", "dark", "dry"]
    elif "VANEER" in name_upper:
        return ["underground", "temperate"]
    else:
        return ["temperate"]

# ===========================
# FRINGE GROUP TAGS
# ===========================
FRINGE_TAGS = {
    "Obsidian Cartel and Sister Org": ["illicit", "trade", "underground", "stealth"],
    "Freesky Barons": ["airborne", "chaos-active", "trade", "mining"],
    "Ghost Wind Raiders": ["airborne", "stealth", "aggressive", "combat"],
    "Gilded Compass": ["trade", "bureaucratic", "wealth"],
    "Crimson Coursairs": ["aquatic", "trade", "stealth", "illicit"],
    "Silent Current": ["aquatic", "underground", "stealth", "illicit"],
    "The Black Label": ["combat", "military", "hard", "mercenary"],
    "The Otter Syndicate": ["aquatic", "illicit", "trade", "stealth"],
    "The Spring Ghosts": ["stealth", "chaos-attuned", "deadly", "magic"],
}

# ===========================
# UNIFIED TAG INTERACTION RESOLVER
# ===========================
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

    # Faction culture tags
    faction_tags = FACTION_TAGS.get(g.get("name", ""), [])
    for t in faction_tags:
        add_source(t, "faction", g.get("name", ""), 1.0)

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

    # ================================================================
    # REACTION RULES
    # ================================================================

    # --- Reaction 1: Lightning + Wood (Burn wooden structures or resources) ---
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

    # --- Reaction 2: Flood + Crop/Grain (Rot crops) ---
    if "flood" in active_sources and "crop" in active_sources:
        if g.get("farms_count", 0) > 0 and random.random() < 0.4:
            g["farms_count"] = max(0, g["farms_count"] - 1)
            logs.append(f"🌾 TAG REACTION: Flood waters inundated and ruined a local Farm in {g['name']}!")
        elif inventory.get("Grain", 0.0) >= 8.0:
            inventory["Grain"] = max(0.0, inventory["Grain"] - 8.0)
            logs.append(f"🌾 TAG REACTION: Inundated conditions rotted 8.0 units of stored Grain in {g['name']}!")

    # --- Reaction 3: Dry/Heat + Wood/Flammable (Spontaneous ignition) ---
    if "dry" in active_sources and "wood" in active_sources and random.random() < 0.12:
        if inventory.get("Lumber", 0.0) >= 3.0:
            inventory["Lumber"] = max(0.0, inventory["Lumber"] - 3.0)
            logs.append(f"🔥 TAG REACTION: Extreme dry heat caused spontaneous ignition, destroying 3.0 Lumber in {g['name']}!")

    # --- Reaction 4: Chaos + Magic-Active (Feedback Spikes) ---
    if "chaos" in active_sources and "magic-active" in active_sources:
        if magistar in prisons:
            degrade = 0.02
            prisons[magistar] = max(0.0, prisons[magistar] - degrade)
            logs.append(f"🔮 TAG REACTION: Ambient chaos resonated with magic-active entities in {g['name']}, degrading {magistar} Prison seal by 2.0%!")

    # --- Reaction 5: Magic-Void + Chaos (Dampen chaos level) ---
    if "magic-void" in active_sources and "chaos" in active_sources:
        g["chaos_level"] = max(0.0, g["chaos_level"] - 0.05)
        logs.append(f"🧿 TAG REACTION: Magic-void aura of leader neutralized and dampened chaos in {g['name']} by 5.0%!")

    # --- Reaction 6: Acid + Stone (Corrosion of stone walls or mines) ---
    if "acid" in active_sources and "stone" in active_sources and random.random() < 0.20:
        if g.get("walls_count", 0) > 0:
            g["walls_count"] = max(0, g["walls_count"] - 1)
            logs.append(f"🧪 TAG REACTION: Acidic swamp runoff corroded and collapsed a Wall segment in {g['name']}!")

    # --- Reaction 7: Holy + Chaos (Holy Purge: reduce chaos and cult) ---
    if "holy" in active_sources and "chaos" in active_sources:
        holy_strength = sum(1 for src in active_sources["holy"] if src[0] in ["structure", "paragon"])
        if holy_strength > 0 and random.random() < 0.25:
            g["chaos_level"] = max(0.0, g["chaos_level"] - 0.03 * holy_strength)
            cult_purged = int(g.get("cult_population", 0.0) * 0.03 * holy_strength)
            g["cult_population"] = max(0.0, g.get("cult_population", 0.0) - cult_purged)
            g["cult_infiltration"] = g.get("cult_population", 0.0) / max(1.0, g.get("population", 1000.0))
            logs.append(f"✝️ TAG REACTION: Holy wards in {g['name']} purged {cult_purged} cultists and suppressed chaos by {3.0 * holy_strength:.1f}%!")

    # --- Reaction 8: Electric + Water/Wet (Shock aquatic systems) ---
    if "electric" in active_sources and ("water" in active_sources or "wet" in active_sources) and random.random() < 0.15:
        if g.get("docks_count", 0) > 0:
            g["docks_count"] = max(0, g["docks_count"] - 1)
            logs.append(f"⚡ TAG REACTION: Electrical discharge through waterways short-circuited a Dock in {g['name']}!")
        if g.get("fauna_abyssal_snail", 0.0) > 5.0:
            g["fauna_abyssal_snail"] = max(0.0, g["fauna_abyssal_snail"] - 3.0)
            logs.append(f"⚡ TAG REACTION: Electrical discharge stunned 3 Abyssal Snails in {g['name']}'s waterways!")

    # --- Reaction 9: Cold + Delicate (Cold snap kills delicate flora) ---
    if "cold" in active_sources and "delicate" in active_sources and random.random() < 0.20:
        for flora_key in ["flora_ghost_flower", "flora_bluebell", "flora_silver_leaf"]:
            if g.get(flora_key, 0.0) > 5.0:
                lost = g[flora_key] * 0.15
                g[flora_key] = max(0.0, g[flora_key] - lost)
                flora_name = flora_key.replace("flora_", "").replace("_", " ").title()
                logs.append(f"❄️ TAG REACTION: Cold snap froze and killed {lost:.0f} {flora_name} in {g['name']}!")
                break

    # --- Reaction 10: Aggressive + Docile (Predators attack livestock) ---
    if "aggressive" in active_sources and "docile" in active_sources and random.random() < 0.15:
        predator_keys = [k for k, v in FLORA_FAUNA_TAGS.items() if "aggressive" in v and g.get(k, 0.0) > 2.0]
        prey_keys = [k for k, v in FLORA_FAUNA_TAGS.items() if "docile" in v and g.get(k, 0.0) > 2.0]
        if predator_keys and prey_keys:
            predator = random.choice(predator_keys)
            prey = random.choice(prey_keys)
            killed = min(g.get(prey, 0.0) * 0.1, g.get(predator, 0.0) * 0.5)
            g[prey] = max(0.0, g.get(prey, 0.0) - killed)
            pred_name = predator.replace("fauna_", "").replace("_", " ").title()
            prey_name = prey.replace("fauna_", "").replace("_", " ").title()
            logs.append(f"🐺 TAG REACTION: Wild {pred_name} pack attacked {prey_name} herd in {g['name']}, killing {killed:.0f}!")

    # --- Reaction 11: Parasitic + Wood (Strangler Fig damages wooden structures) ---
    if "parasitic" in active_sources and "wood" in active_sources and random.random() < 0.12:
        for b_key in ["farms_count", "watchtowers_count", "theatres_count", "domestic_orchards"]:
            if g.get(b_key, 0) > 0:
                g[b_key] = max(0, g[b_key] - 1)
                b_name = b_key.replace("_count", "").replace("domestic_", "").replace("_", " ").title()
                logs.append(f"🌿 TAG REACTION: Strangler Fig vines overran and crushed a {b_name} in {g['name']}!")
                break

    # --- Reaction 12: Toxic + Water (Poisons aquatic fauna, reduces food) ---
    if "toxic" in active_sources and ("water" in active_sources or "wet" in active_sources) and random.random() < 0.15:
        for fauna_key in ["fauna_abyssal_snail", "fauna_red_deer"]:
            if g.get(fauna_key, 0.0) > 3.0:
                lost = g[fauna_key] * 0.1
                g[fauna_key] = max(0.0, g[fauna_key] - lost)
                f_name = fauna_key.replace("fauna_", "").replace("_", " ").title()
                logs.append(f"☠️ TAG REACTION: Toxic runoff in {g['name']}'s waterways poisoned {lost:.0f} {f_name}!")
                break
        if inventory.get("Grain", 0.0) >= 4.0:
            inventory["Grain"] = max(0.0, inventory["Grain"] - 4.0)
            logs.append(f"☠️ TAG REACTION: Toxic contamination spoiled 4 units of stored Grain in {g['name']}!")

    # --- Reaction 13: Underground + Force (Mine collapse) ---
    if "underground" in active_sources and "force" in active_sources and random.random() < 0.10:
        if g.get("mines_count", 0) > 0:
            g["mines_count"] = max(0, g["mines_count"] - 1)
            logs.append(f"💥 TAG REACTION: Tectonic force caused a mine collapse in {g['name']}!")
        for fauna_key in ["fauna_weaver_cow", "fauna_gritbore"]:
            if g.get(fauna_key, 0.0) > 5.0:
                lost = g[fauna_key] * 0.2
                g[fauna_key] = max(0.0, g[fauna_key] - lost)
                f_name = fauna_key.replace("fauna_", "").replace("_", " ").title()
                logs.append(f"💥 TAG REACTION: Seismic force displaced {lost:.0f} underground {f_name} in {g['name']}!")

    # --- Reaction 14: Pest + Crop/Food (Pest infestation) ---
    if "pest" in active_sources and ("crop" in active_sources or "food" in active_sources) and random.random() < 0.18:
        if inventory.get("Grain", 0.0) >= 6.0:
            inventory["Grain"] = max(0.0, inventory["Grain"] - 6.0)
            logs.append(f"🐛 TAG REACTION: Pest infestation devoured 6 units of stored Grain in {g['name']}!")
        elif g.get("farms_count", 0) > 0 and random.random() < 0.3:
            g["farms_count"] = max(0, g["farms_count"] - 1)
            logs.append(f"🐛 TAG REACTION: Furnace-Tick swarm ruined a Farm's crops in {g['name']}!")

    # --- Reaction 15: Migratory + Crop (Stampede damages farms) ---
    if "migratory" in active_sources and "crop" in active_sources and random.random() < 0.10:
        if g.get("farms_count", 0) > 0:
            g["farms_count"] = max(0, g["farms_count"] - 1)
            logs.append(f"🦬 TAG REACTION: An Ash-Bison stampede trampled through farmland in {g['name']}, destroying a Farm!")

    # --- Reaction 16: Explosive + Fire/Lightning (Chain detonation) ---
    if "explosive" in active_sources and ("fire-hazard" in active_sources or "lightning" in active_sources) and random.random() < 0.08:
        if inventory.get("Refined Aether Battery", 0.0) >= 1.0:
            inventory["Refined Aether Battery"] = max(0.0, inventory["Refined Aether Battery"] - 1.0)
            # Chain damage
            for b_key in ["barracks_count", "watchtowers_count", "mines_count"]:
                if g.get(b_key, 0) > 0 and random.random() < 0.4:
                    g[b_key] = max(0, g[b_key] - 1)
                    b_name = b_key.replace("_count", "").title()
                    logs.append(f"💥 TAG REACTION: Aether Battery detonation chain-reaction destroyed a {b_name} in {g['name']}!")
                    break
            logs.append(f"💥 TAG REACTION: A stored Aether Battery detonated in {g['name']} due to fire/lightning exposure!")

    # --- Reaction 17: Arcane + Holy (Silver-Leaf preserves knowledge) ---
    if "arcane" in active_sources and "holy" in active_sources and random.random() < 0.20:
        g["mental_well_being"] = min(1.0, g.get("mental_well_being", 0.5) + 0.05)
        logs.append(f"📜 TAG REACTION: Arcane Silver-Leaf archives and holy wards harmonized, boosting scholarship and mental well-being in {g['name']}!")

    # --- Reaction 18: Transport + Trade (Draft animals improve trade) ---
    if "transport" in active_sources and "trade" in active_sources and random.random() < 0.20:
        transport_count = sum(1 for src in active_sources.get("transport", []) if src[0] in ["flora_fauna", "structure"])
        if transport_count > 0:
            bonus_grain = transport_count * 2.0
            inventory["Grain"] = inventory.get("Grain", 0.0) + bonus_grain
            logs.append(f"🐴 TAG REACTION: Draft animals boosted trade caravan efficiency in {g['name']}, yielding {bonus_grain:.0f} extra Grain!")

    # --- Reaction 19: Nocturnal + Flammable (Night predators raid camps) ---
    if "nocturnal" in active_sources and "flammable" in active_sources and random.random() < 0.10:
        if g.get("fauna_night_carapace", 0.0) > 3.0:
            if inventory.get("Grain", 0.0) >= 3.0:
                inventory["Grain"] = max(0.0, inventory["Grain"] - 3.0)
                logs.append(f"🌙 TAG REACTION: Night-Carapace beetles raided food stores under cover of darkness in {g['name']}, consuming 3 Grain!")

    # --- Reaction 20: Metal + Acid (Corrodes metal resources) ---
    if "acid" in active_sources and "metal" in active_sources and random.random() < 0.12:
        if inventory.get("Smelted Steel", 0.0) >= 2.0:
            inventory["Smelted Steel"] = max(0.0, inventory["Smelted Steel"] - 2.0)
            logs.append(f"🧪 TAG REACTION: Acidic fumes corroded 2 units of Smelted Steel in {g['name']}!")
        elif inventory.get("Basic Weapons", 0.0) >= 1.0:
            inventory["Basic Weapons"] = max(0.0, inventory["Basic Weapons"] - 1.0)
            logs.append(f"🧪 TAG REACTION: Acidic fumes rusted and corroded 1 unit of Basic Weapons in {g['name']}!")

    # --- Reaction 21: Silk + Structure (Weaver-Cow silk strengthens structures) ---
    if "silk" in active_sources and "structure" in active_sources and random.random() < 0.15:
        inventory["Silk-Steel Thread"] = inventory.get("Silk-Steel Thread", 0.0) + 1.0
        logs.append(f"🕸️ TAG REACTION: Weaver-Cow silk production reinforced infrastructure in {g['name']}, yielding 1 Silk-Steel Thread!")

    # --- Reaction 22: Crystal + Magic (Dragonstone resonance amplifies magic) ---
    if "crystal" in active_sources and "magic" in active_sources and random.random() < 0.12:
        g["chaos_level"] = min(1.0, g.get("chaos_level", 0.0) + 0.02)
        if inventory.get("Dragonstone", 0.0) >= 1.0:
            inventory["Refined Aether Battery"] = inventory.get("Refined Aether Battery", 0.0) + 0.5
            logs.append(f"💎 TAG REACTION: Crystal-magic resonance in {g['name']} spontaneously charged 0.5 Aether Batteries but increased chaos by 2%!")

    # --- Reaction 23: Camouflage + Livestock (Glimmer-Wings ambush livestock) ---
    if "camouflage" in active_sources and "livestock" in active_sources and random.random() < 0.12:
        livestock_keys = [k for k, v in FLORA_FAUNA_TAGS.items() if "livestock" in v and g.get(k, 0.0) > 3.0]
        if livestock_keys:
            target = random.choice(livestock_keys)
            killed = min(g.get(target, 0.0) * 0.08, 5.0)
            g[target] = max(0.0, g.get(target, 0.0) - killed)
            t_name = target.replace("fauna_", "").replace("_", " ").title()
            logs.append(f"🦋 TAG REACTION: Camouflaged Glimmer-Wings ambushed {t_name} in {g['name']}, killing {killed:.0f}!")

    # --- Reaction 24: Destructive + Metal (Furnace-Ticks eat metal infrastructure) ---
    if "destructive" in active_sources and "metal" in active_sources and random.random() < 0.10:
        if inventory.get("Iron Ore", 0.0) >= 3.0:
            inventory["Iron Ore"] = max(0.0, inventory["Iron Ore"] - 3.0)
            inventory["Alloy Carapace"] = inventory.get("Alloy Carapace", 0.0) + 1.0
            logs.append(f"🐛 TAG REACTION: Furnace-Ticks consumed 3 Iron Ore in {g['name']}, leaving behind 1 Alloy Carapace!")

    # --- Reaction 25: Desert + Growth (Desert bloom accelerates arid flora) ---
    if "desert" in active_sources and "growth" in active_sources:
        for flora_key in ["flora_saguaro", "flora_desert_sage", "flora_ghost_flower"]:
            if g.get(flora_key, 0.0) > 0.0:
                boost = g[flora_key] * 0.08
                g[flora_key] = min(1500.0, g[flora_key] + boost)
        logs.append(f"🌵 TAG REACTION: Rare moisture during growth season caused a desert bloom in {g['name']}, boosting arid flora!")

    # --- Reaction 26: Carnivorous + Beast (Grave-Roots trap wildlife) ---
    if "carnivorous" in active_sources and "beast" in active_sources and random.random() < 0.10:
        small_prey = [k for k, v in FLORA_FAUNA_TAGS.items() 
                      if "docile" in v and g.get(k, 0.0) > 3.0 
                      and k not in ["fauna_abyssal_snail", "fauna_ash_bison"]]
        if small_prey:
            target = random.choice(small_prey)
            killed = min(g.get(target, 0.0) * 0.05, 3.0)
            g[target] = max(0.0, g.get(target, 0.0) - killed)
            t_name = target.replace("fauna_", "").replace("_", " ").title()
            logs.append(f"🌿 TAG REACTION: Grave-Root vines trapped and consumed {killed:.0f} {t_name} in {g['name']}!")

    # --- Reaction 27: Prosperity + Crop (Generous leader boosts harvests) ---
    if "prosperity" in active_sources and "crop" in active_sources and random.random() < 0.20:
        inventory["Grain"] = inventory.get("Grain", 0.0) + 5.0
        logs.append(f"🌾 TAG REACTION: Prosperous leadership in {g['name']} inspired workers, yielding 5 bonus Grain!")

    # --- Reaction 28: Oppressive + Military (Cruel leader drains morale but boosts security) ---
    if "oppressive" in active_sources and "military" in active_sources and random.random() < 0.20:
        g["discontent"] = min(1.0, g.get("discontent", 0.0) + 0.03)
        g["crime_level"] = max(0.0, g.get("crime_level", 0.0) - 0.05)
        logs.append(f"⛓️ TAG REACTION: Oppressive military rule in {g['name']} crushed crime but bred resentment!")

    # --- Reaction 29: Coral + Chaos (Coral Bleaching/Hyper-calcification) ---
    if "coral" in active_sources and "chaos" in active_sources and random.random() < 0.20:
        if g.get("flora_luminescent_coral", 0.0) > 5.0:
            lost = g["flora_luminescent_coral"] * 0.2
            g["flora_luminescent_coral"] = max(0.0, g["flora_luminescent_coral"] - lost)
            logs.append(f"☠️ TAG REACTION: Chaos exposure bleached and killed {lost:.0f} Luminescent Coral in {g['name']}!")

    # --- Reaction 30: Underwater + Lightning/Electric (Massive AOE Shock) ---
    if ("aquatic" in active_sources or "underwater" in active_sources) and "electric" in active_sources and random.random() < 0.25:
        aquatic_fauna = [k for k, v in FLORA_FAUNA_TAGS.items() if "aquatic" in v and "fauna" in k and g.get(k, 0.0) > 5.0]
        if aquatic_fauna:
            for target in aquatic_fauna:
                killed = g[target] * 0.15
                g[target] = max(0.0, g[target] - killed)
            logs.append(f"⚡ TAG REACTION: Electrical discharge in {g['name']}'s waters sent a shockwave, killing 15% of all aquatic life!")

    # --- Reaction 31: Kelp + Fire (Nullification) ---
    if "kelp" in active_sources and "fire" in active_sources and random.random() < 0.50:
        logs.append(f"🔥 TAG REACTION: Fire attacks near {g['name']} were harmlessly nullified by the damp kelp forests.")

    # Return summary of active tags
    all_tags = sorted(list(active_sources.keys()))
    return all_tags
