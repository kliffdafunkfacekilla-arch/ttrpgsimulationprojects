# ecology_system.py
# Full flora & fauna population dynamics, harvesting, and domestication for all species from Ostraka lore.
# Loads dynamically from world_settings.json or default_settings.json.

import random
import os
import json

# Resolve project root (one level up from modules/)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# ===========================
# BIOME SPECIES DISTRIBUTION (DEFAULTS)
# ===========================
BIOME_SPECIES = {
    "default": {
        "fauna_timber_wolf": 10.0,
        "fauna_wild_boar": 20.0,
        "fauna_red_deer": 30.0,
        "fauna_black_bear": 5.0,
        "fauna_domestic_sheep": 25.0,
        "fauna_draft_horse": 8.0,
        "fauna_peregrine_falcon": 12.0,
        "fauna_field_mouse": 40.0,
        "flora_common_oak": 200.0,
        "flora_wild_rye": 150.0,
        "flora_bluebell": 40.0,
        "flora_forest_fern": 60.0,
        "flora_plains_grass": 300.0,
    },
    "cold_mountain": {
        "fauna_cloud_ram": 30.0,
        "fauna_fur_wyrm": 15.0,
        "flora_alpine_spruce": 180.0,
    },
    "desert_arid": {
        "fauna_dune_dog": 20.0,
        "fauna_dust_skipper": 25.0,
        "fauna_glass_sand_eel": 5.0,
        "flora_ghost_flower": 100.0,
        "flora_saguaro": 60.0,
        "flora_desert_sage": 80.0,
    },
    "forest_canopy": {
        "fauna_draft_beetle": 15.0,
        "fauna_titan_aphid": 20.0,
        "fauna_night_carapace": 8.0,
        "flora_strangler_fig": 30.0,
    },
    "aquatic_river": {
        "fauna_abyssal_snail": 10.0,
        "fauna_river_fish": 50.0,
        "flora_marsh_reed": 80.0,
    },
    "ocean_depths": {
        "fauna_abyssal_whale": 5.0,
        "fauna_saltwater_fish": 100.0,
        "flora_ocean_kelp": 150.0,
    },
    "coastal_reef": {
        "fauna_reef_shark": 10.0,
        "fauna_coral_crab": 20.0,
        "fauna_seagull": 30.0,
        "flora_luminescent_coral": 50.0,
    },
    "airborne_altitude": {
        "fauna_sky_grazer": 50.0,
        "fauna_cloud_cutter_ray": 5.0,
        "fauna_glimmer_wings": 15.0,
        "fauna_gem_shell_beetle": 10.0,
    },
    "industrial_rocky": {
        "fauna_gritbore": 20.0,
        "fauna_furnace_tick": 12.0,
    },
    "volcanic_steppe": {
        "fauna_ash_bison": 15.0,
    },
    "underground": {
        "fauna_weaver_cow": 8.0,
        "flora_grave_roots": 30.0,
        "flora_silver_leaf": 15.0,
    },
    "swamp": {
        "flora_forest_fern": 120.0,
        "flora_grave_roots": 20.0,
    },
}

FACTION_BIOME_CATEGORIES = {
    "Ursine Hegemony": ["default", "cold_mountain", "airborne_altitude"],
    "River Folk": ["default", "aquatic_river", "forest_canopy"],
    "Sump-Kin": ["default", "swamp", "industrial_rocky", "underground"],
    "Iron Caladrea": ["default", "industrial_rocky", "volcanic_steppe", "cold_mountain"],
    "Vaneer Concord": ["default", "underground"],
    "Hive Collective": ["default", "forest_canopy"],
    "Avians": ["default", "airborne_altitude", "cold_mountain"],
    "Flower Valwey": ["default", "forest_canopy", "desert_arid"],
    "Sylvian": ["default", "forest_canopy"],
    "Sciute": ["default", "aquatic_river", "coastal_reef"],
    "Meridian Chain": ["default", "aquatic_river", "coastal_reef", "ocean_depths"],
    "Prism Lizards": ["default", "industrial_rocky", "underground"],
    "Canopy Clans": ["default", "forest_canopy", "airborne_altitude"],
    "East Hounds": ["default", "volcanic_steppe", "cold_mountain"],
    "Guirrilla Clans": ["default", "industrial_rocky", "underground"],
    "Theocracy": ["default", "aquatic_river", "coastal_reef", "ocean_depths"],
    "The Reliance": ["default", "underground", "desert_arid"],
}

ALL_FAUNA = [
    "fauna_sky_grazer", "fauna_glimmer_wings", "fauna_gritbore", "fauna_ash_bison",
    "fauna_cloud_cutter_ray", "fauna_cloud_ram", "fauna_draft_beetle", "fauna_dune_dog",
    "fauna_dust_skipper", "fauna_fur_wyrm", "fauna_furnace_tick", "fauna_gem_shell_beetle",
    "fauna_glass_sand_eel", "fauna_night_carapace", "fauna_abyssal_snail", "fauna_weaver_cow",
    "fauna_titan_aphid", "fauna_timber_wolf", "fauna_wild_boar", "fauna_red_deer",
    "fauna_peregrine_falcon", "fauna_black_bear", "fauna_domestic_sheep", "fauna_draft_horse",
    "fauna_field_mouse", "fauna_river_fish", "fauna_seagull", "fauna_reef_shark", 
    "fauna_abyssal_whale", "fauna_saltwater_fish", "fauna_coral_crab",
]

ALL_FLORA = [
    "flora_ghost_flower", "flora_grave_roots", "flora_stone_root", "flora_strangler_fig",
    "flora_silver_leaf", "flora_saguaro", "flora_common_oak", "flora_wild_rye",
    "flora_bluebell", "flora_forest_fern", "flora_alpine_spruce", "flora_desert_sage",
    "flora_plains_grass", "flora_marsh_reed", "flora_ocean_kelp", "flora_luminescent_coral",
]

ALL_SPECIES = ALL_FAUNA + ALL_FLORA

SPECIES_PARAMS = {
    "fauna_sky_grazer":       {"growth": 0.06, "cap": 500.0, "chaos_aff": -0.3, "food_chain": "prey"},
    "fauna_glimmer_wings":    {"growth": 0.10, "cap": 200.0, "chaos_aff":  0.5, "food_chain": "predator"},
    "fauna_gritbore":         {"growth": 0.08, "cap": 300.0, "chaos_aff":  0.0, "food_chain": "scavenger"},
    "fauna_ash_bison":        {"growth": 0.04, "cap": 150.0, "chaos_aff": -0.2, "food_chain": "herbivore"},
    "fauna_cloud_cutter_ray": {"growth": 0.02, "cap":  30.0, "chaos_aff":  0.3, "food_chain": "apex"},
    "fauna_cloud_ram":        {"growth": 0.06, "cap": 300.0, "chaos_aff": -0.1, "food_chain": "herbivore"},
    "fauna_draft_beetle":     {"growth": 0.05, "cap": 200.0, "chaos_aff": -0.1, "food_chain": "herbivore"},
    "fauna_dune_dog":         {"growth": 0.07, "cap": 250.0, "chaos_aff":  0.0, "food_chain": "prey"},
    "fauna_dust_skipper":     {"growth": 0.08, "cap": 300.0, "chaos_aff":  0.0, "food_chain": "scavenger"},
    "fauna_fur_wyrm":         {"growth": 0.09, "cap": 200.0, "chaos_aff":  0.1, "food_chain": "scavenger"},
    "fauna_furnace_tick":     {"growth": 0.12, "cap": 250.0, "chaos_aff":  0.2, "food_chain": "pest"},
    "fauna_gem_shell_beetle": {"growth": 0.06, "cap": 150.0, "chaos_aff":  0.3, "food_chain": "prey"},
    "fauna_glass_sand_eel":   {"growth": 0.03, "cap":  50.0, "chaos_aff":  0.4, "food_chain": "apex"},
    "fauna_night_carapace":   {"growth": 0.05, "cap": 100.0, "chaos_aff":  0.1, "food_chain": "predator"},
    "fauna_abyssal_snail":    {"growth": 0.03, "cap": 100.0, "chaos_aff": -0.2, "food_chain": "herbivore"},
    "fauna_weaver_cow":       {"growth": 0.04, "cap":  80.0, "chaos_aff": -0.3, "food_chain": "prey"},
    "fauna_titan_aphid":      {"growth": 0.10, "cap": 400.0, "chaos_aff":  0.0, "food_chain": "prey"},
    "fauna_timber_wolf":      {"growth": 0.04, "cap": 200.0, "chaos_aff": -0.1, "food_chain": "predator"},
    "fauna_wild_boar":        {"growth": 0.07, "cap": 300.0, "chaos_aff": -0.1, "food_chain": "herbivore"},
    "fauna_red_deer":         {"growth": 0.08, "cap": 500.0, "chaos_aff": -0.2, "food_chain": "prey"},
    "fauna_peregrine_falcon": {"growth": 0.05, "cap": 200.0, "chaos_aff":  0.0, "food_chain": "predator"},
    "fauna_black_bear":       {"growth": 0.03, "cap":  80.0, "chaos_aff": -0.1, "food_chain": "predator"},
    "fauna_domestic_sheep":   {"growth": 0.09, "cap": 400.0, "chaos_aff": -0.3, "food_chain": "prey"},
    "fauna_draft_horse":      {"growth": 0.05, "cap": 150.0, "chaos_aff": -0.2, "food_chain": "prey"},
    "fauna_field_mouse":      {"growth": 0.15, "cap": 800.0, "chaos_aff":  0.1, "food_chain": "prey"},
    "fauna_river_fish":       {"growth": 0.12, "cap": 600.0, "chaos_aff": -0.1, "food_chain": "prey"},
    "fauna_seagull":          {"growth": 0.08, "cap": 400.0, "chaos_aff":  0.0, "food_chain": "scavenger"},
    "fauna_reef_shark":       {"growth": 0.03, "cap": 100.0, "chaos_aff":  0.2, "food_chain": "predator"},
    "fauna_abyssal_whale":    {"growth": 0.01, "cap":  20.0, "chaos_aff":  0.3, "food_chain": "apex"},
    "fauna_saltwater_fish":   {"growth": 0.14, "cap":1000.0, "chaos_aff": -0.2, "food_chain": "prey"},
    "fauna_coral_crab":       {"growth": 0.06, "cap": 300.0, "chaos_aff":  0.1, "food_chain": "scavenger"},
    "flora_ghost_flower":     {"growth": 0.12, "cap": 1500.0, "chaos_aff":  0.5, "food_chain": "flora"},
    "flora_grave_roots":      {"growth": 0.06, "cap":  400.0, "chaos_aff":  0.3, "food_chain": "flora"},
    "flora_stone_root":       {"growth": 0.08, "cap": 1500.0, "chaos_aff": -0.3, "food_chain": "flora"},
    "flora_strangler_fig":    {"growth": 0.10, "cap":  500.0, "chaos_aff":  0.2, "food_chain": "flora"},
    "flora_silver_leaf":      {"growth": 0.03, "cap":  200.0, "chaos_aff": -0.4, "food_chain": "flora"},
    "flora_saguaro":          {"growth": 0.04, "cap":  300.0, "chaos_aff":  0.0, "food_chain": "flora"},
    "flora_common_oak":       {"growth": 0.06, "cap": 2000.0, "chaos_aff": -0.2, "food_chain": "flora"},
    "flora_wild_rye":         {"growth": 0.12, "cap": 1500.0, "chaos_aff": -0.3, "food_chain": "flora"},
    "flora_bluebell":         {"growth": 0.10, "cap":  500.0, "chaos_aff": -0.1, "food_chain": "flora"},
    "flora_forest_fern":      {"growth": 0.09, "cap":  800.0, "chaos_aff":  0.0, "food_chain": "flora"},
    "flora_alpine_spruce":    {"growth": 0.05, "cap": 1500.0, "chaos_aff": -0.2, "food_chain": "flora"},
    "flora_desert_sage":      {"growth": 0.06, "cap":  600.0, "chaos_aff":  0.0, "food_chain": "flora"},
    "flora_plains_grass":     {"growth": 0.15, "cap": 3000.0, "chaos_aff":  0.0, "food_chain": "flora"},
    "flora_marsh_reed":       {"growth": 0.10, "cap": 1000.0, "chaos_aff":  0.0, "food_chain": "flora"},
    "flora_ocean_kelp":       {"growth": 0.15, "cap": 2000.0, "chaos_aff": -0.1, "food_chain": "flora"},
    "flora_luminescent_coral":{"growth": 0.02, "cap":  500.0, "chaos_aff":  0.4, "food_chain": "flora"},
}

PREDATION_MATRIX = {
    "fauna_timber_wolf": ["fauna_red_deer", "fauna_wild_boar", "fauna_domestic_sheep"],
    "fauna_black_bear": ["fauna_red_deer", "fauna_wild_boar", "fauna_domestic_sheep"],
    "fauna_cloud_cutter_ray": ["fauna_sky_grazer", "fauna_gem_shell_beetle", "fauna_glimmer_wings"],
    "fauna_night_carapace": ["fauna_titan_aphid", "fauna_dune_dog", "fauna_dust_skipper"],
    "fauna_glimmer_wings": ["fauna_domestic_sheep", "fauna_dune_dog", "fauna_titan_aphid"],
    "fauna_glass_sand_eel": ["fauna_dune_dog", "fauna_dust_skipper"],
    "fauna_peregrine_falcon": ["fauna_fur_wyrm", "fauna_dust_skipper", "fauna_field_mouse"],
    "fauna_reef_shark": ["fauna_saltwater_fish", "fauna_coral_crab"],
    "fauna_abyssal_whale": ["fauna_reef_shark", "fauna_saltwater_fish"],
}

HARVEST_TABLE = {
    "fauna_timber_wolf":      {"resource": "Leather",         "amount": 2.0, "lethal": True,  "secondary": None},
    "fauna_wild_boar":        {"resource": "Leather",         "amount": 1.5, "lethal": True,  "secondary": ("Grain", 1.0)},
    "fauna_red_deer":         {"resource": "Venison",         "amount": 2.0, "lethal": True,  "secondary": ("Antler", 0.5)},
    "fauna_black_bear":       {"resource": "Fat",             "amount": 3.0, "lethal": True,  "secondary": ("Leather", 2.0)},
    "fauna_ash_bison":        {"resource": "Stone-Hide",      "amount": 3.0, "lethal": True,  "secondary": ("Grain", 2.0)},
    "fauna_cloud_cutter_ray": {"resource": "Stinger Weapon",  "amount": 1.0, "lethal": True,  "secondary": ("Voltaic Fleece", 4.0)},
    "fauna_night_carapace":   {"resource": "Luxury Meat",     "amount": 2.0, "lethal": True,  "secondary": None},
    "fauna_gritbore":         {"resource": "Grain",           "amount": 1.5, "lethal": True,  "secondary": None},
    "fauna_glimmer_wings":    {"resource": "Camouflage Dye",  "amount": 1.0, "lethal": True,  "secondary": None},
    "fauna_furnace_tick":     {"resource": "Alloy Carapace",  "amount": 1.0, "lethal": True,  "secondary": None},
    "fauna_gem_shell_beetle": {"resource": "Crystal Chips",   "amount": 1.0, "lethal": True,  "secondary": None},
    "fauna_fur_wyrm":         {"resource": "Leather",         "amount": 0.5, "lethal": True,  "secondary": None},
    "fauna_glass_sand_eel":   {"resource": "Leather",         "amount": 1.0, "lethal": True,  "secondary": None},
    "fauna_sky_grazer":       {"resource": "Voltaic Fleece",  "amount": 1.0, "lethal": False, "secondary": ("Ozone-Milk", 2.0)},
    "fauna_cloud_ram":        {"resource": "Wool",            "amount": 1.5, "lethal": False, "secondary": ("Peak-Cheese", 1.0)},
    "fauna_domestic_sheep":   {"resource": "Wool",            "amount": 1.0, "lethal": False, "secondary": ("Grain", 0.5)},
    "fauna_draft_horse":      {"resource": "Leather",         "amount": 0.0, "lethal": False, "secondary": None},
    "fauna_draft_beetle":     {"resource": "Leather",         "amount": 0.0, "lethal": False, "secondary": None},
    "fauna_dune_dog":         {"resource": "Leather",         "amount": 0.0, "lethal": False, "secondary": None},
    "fauna_abyssal_snail":    {"resource": "Leather",         "amount": 0.0, "lethal": False, "secondary": None},
    "fauna_weaver_cow":       {"resource": "Silk-Steel Thread","amount": 2.0, "lethal": False, "secondary": None},
    "fauna_titan_aphid":      {"resource": "Honeydew",        "amount": 1.5, "lethal": False, "secondary": None},
    "fauna_peregrine_falcon": {"resource": "Leather",         "amount": 0.0, "lethal": False, "secondary": None},
    "fauna_dust_skipper":     {"resource": "Leather",         "amount": 0.0, "lethal": False, "secondary": None},
    "fauna_field_mouse":      {"resource": "Grain",           "amount": 0.0, "lethal": True,  "secondary": None},
    "fauna_river_fish":       {"resource": "Fish",            "amount": 1.5, "lethal": True,  "secondary": None},
    "fauna_seagull":          {"resource": "Guano",           "amount": 0.5, "lethal": True,  "secondary": None},
    "fauna_reef_shark":       {"resource": "Shark Tooth",     "amount": 1.0, "lethal": True,  "secondary": ("Fish", 2.0)},
    "fauna_abyssal_whale":    {"resource": "Whale Oil",       "amount": 4.0, "lethal": True,  "secondary": ("Meat", 4.0)},
    "fauna_saltwater_fish":   {"resource": "Fish",            "amount": 2.0, "lethal": True,  "secondary": None},
    "fauna_coral_crab":       {"resource": "Crab Shell",      "amount": 1.0, "lethal": True,  "secondary": ("Meat", 0.5)},
    "flora_ghost_flower":     {"resource": "Ghost Flower",    "amount": 1.0, "lethal": True,  "secondary": None},
    "flora_grave_roots":      {"resource": "Anesthetic Toxin","amount": 0.5, "lethal": False, "secondary": None},
    "flora_stone_root":       {"resource": "Lumber",          "amount": 3.0, "lethal": True,  "secondary": None},
    "flora_strangler_fig":    {"resource": "Rope",            "amount": 1.0, "lethal": True,  "secondary": None},
    "flora_silver_leaf":      {"resource": "Night-Nectar",    "amount": 0.5, "lethal": False, "secondary": None},
    "flora_saguaro":          {"resource": "Grain",           "amount": 0.5, "lethal": False, "secondary": None},
    "flora_common_oak":       {"resource": "Lumber",          "amount": 2.0, "lethal": True,  "secondary": None},
    "flora_wild_rye":         {"resource": "Grain",           "amount": 2.0, "lethal": True,  "secondary": None},
    "flora_bluebell":         {"resource": "Night-Nectar",    "amount": 0.3, "lethal": True,  "secondary": None},
    "flora_forest_fern":      {"resource": "Rope",            "amount": 0.5, "lethal": True,  "secondary": None},
    "flora_alpine_spruce":    {"resource": "Lumber",          "amount": 2.5, "lethal": True,  "secondary": ("Resin", 0.5)},
    "flora_desert_sage":      {"resource": "Grain",           "amount": 0.3, "lethal": False, "secondary": None},
    "flora_plains_grass":     {"resource": "Grain",           "amount": 0.5, "lethal": True,  "secondary": None},
    "flora_marsh_reed":       {"resource": "Rope",            "amount": 0.8, "lethal": True,  "secondary": None},
    "flora_ocean_kelp":       {"resource": "Kelp",            "amount": 2.0, "lethal": True,  "secondary": ("Fish", 0.5)},
    "flora_luminescent_coral":{"resource": "Coral",           "amount": 0.5, "lethal": True,  "secondary": ("Crystal Chips", 0.5)},
}

DOMESTICATION_TABLE = {
    "fauna_sky_grazer": {
        "facility": "domestic_pens",
        "input": ("Grain", 2.0),
        "output": ("Voltaic Fleece", 1.0),
        "secondary": ("Ozone-Milk", 2.0),
        "tool_bonus": None,
    },
    "fauna_cloud_ram": {
        "facility": "domestic_cloud_ram_pens",
        "input": ("Grain", 1.5),
        "output": ("Wool", 2.0),
        "secondary": ("Peak-Cheese", 1.5),
        "tool_bonus": None,
    },
    "fauna_draft_beetle": {
        "facility": "domestic_beetle_stables",
        "input": ("Lumber", 1.0),
        "output": ("Lumber", 0.0),
        "secondary": None,
        "tool_bonus": "transport",
    },
    "fauna_weaver_cow": {
        "facility": "domestic_weaver_farms",
        "input": ("Grain", 3.0),
        "output": ("Silk-Steel Thread", 2.0),
        "secondary": None,
        "tool_bonus": None,
    },
    "fauna_dune_dog": {
        "facility": "domestic_dune_dog_dens",
        "input": ("Grain", 0.5),
        "output": ("Grain", 0.0),
        "secondary": None,
        "tool_bonus": "pest_control",
    },
    "fauna_abyssal_snail": {
        "facility": "domestic_snail_docks",
        "input": ("Stone", 1.0),
        "output": ("Stone", 0.0),
        "secondary": None,
        "tool_bonus": "heavy_transport",
    },
    "fauna_domestic_sheep": {
        "facility": "domestic_sheep_pastures",
        "input": ("Grain", 1.0),
        "output": ("Wool", 1.5),
        "secondary": ("Grain", 1.0),
        "tool_bonus": None,
    },
    "fauna_draft_horse": {
        "facility": "domestic_horse_stables",
        "input": ("Grain", 1.5),
        "output": ("Grain", 0.0),
        "secondary": None,
        "tool_bonus": "fast_transport",
    },
    "fauna_titan_aphid": {
        "facility": "domestic_aphid_farms",
        "input": ("Lumber", 0.5),
        "output": ("Honeydew", 2.0),
        "secondary": None,
        "tool_bonus": None,
    },
    "fauna_peregrine_falcon": {
        "facility": "domestic_falcon_roosts",
        "input": ("Grain", 0.5),
        "output": ("Grain", 0.0),
        "secondary": None,
        "tool_bonus": "messenger",
    },
    "fauna_timber_wolf": {
        "facility": "domestic_kennels",
        "input": ("Ostrakan Hardtack", 1.0),
        "output": ("Leather", 0.5),
        "secondary": None,
        "tool_bonus": "guard",
    },
}

def load_dynamic_ecology():
    """Loads all ecology parameters dynamically from settings JSON."""
    global BIOME_SPECIES, FACTION_BIOME_CATEGORIES, ALL_FAUNA, ALL_FLORA, ALL_SPECIES, SPECIES_PARAMS, PREDATION_MATRIX, HARVEST_TABLE, DOMESTICATION_TABLE
    # Resolve settings path
    settings = {}
    for filename in ['world_settings.json', 'default_settings.json']:
        path = os.path.join(_PROJECT_ROOT, filename)
        if os.path.isfile(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if 'ecology' in data:
                    settings = data['ecology']
                break
            except Exception:
                pass
                
    if not settings:
        return
        
    BIOME_SPECIES = settings.get('biome_species', BIOME_SPECIES)
    FACTION_BIOME_CATEGORIES = settings.get('faction_biome_categories', FACTION_BIOME_CATEGORIES)
    SPECIES_PARAMS = settings.get('species_params', SPECIES_PARAMS)
    PREDATION_MATRIX = settings.get('predation_matrix', PREDATION_MATRIX)
    
    # Process harvest table (handle list to tuple mapping for SQLite/Python compatibility)
    h_table = settings.get('harvest_table', {})
    if h_table:
        HARVEST_TABLE.clear()
        for k, v in h_table.items():
            sec = v.get('secondary')
            if sec and isinstance(sec, list) and len(sec) == 2:
                sec = (sec[0], sec[1])
            HARVEST_TABLE[k] = {
                "resource": v.get('resource'),
                "amount": v.get('amount'),
                "lethal": v.get('lethal'),
                "secondary": sec
            }
            
    # Process domestication table (handle list to tuple mapping for SQLite/Python compatibility)
    d_table = settings.get('domestication_table', {})
    if d_table:
        DOMESTICATION_TABLE.clear()
        for k, v in d_table.items():
            inp = v.get('input')
            if inp and isinstance(inp, list) and len(inp) == 2:
                inp = (inp[0], inp[1])
            out = v.get('output')
            if out and isinstance(out, list) and len(out) == 2:
                out = (out[0], out[1])
            sec = v.get('secondary')
            if sec and isinstance(sec, list) and len(sec) == 2:
                sec = (sec[0], sec[1])
            DOMESTICATION_TABLE[k] = {
                "facility": v.get('facility'),
                "input": inp,
                "output": out,
                "secondary": sec,
                "tool_bonus": v.get('tool_bonus')
            }
            
    ALL_FAUNA = [f for f in SPECIES_PARAMS.keys() if f.startswith("fauna_")]
    ALL_FLORA = [f for f in SPECIES_PARAMS.keys() if f.startswith("flora_")]
    ALL_SPECIES = ALL_FAUNA + ALL_FLORA

# Load immediately
load_dynamic_ecology()

def initialize_ecology(g, faction_name):
    """Initialize all species populations for a macro group based on its faction's biome."""
    categories = FACTION_BIOME_CATEGORIES.get(faction_name, ["default"])
    
    # Start all species at 0
    for species in ALL_SPECIES:
        if species not in g:
            g[species] = 0.0
    
    # Add species from each biome category this faction has
    for cat in categories:
        biome_species = BIOME_SPECIES.get(cat, {})
        for species, base_pop in biome_species.items():
            if species not in g or g[species] == 0.0:
                g[species] = base_pop * random.uniform(0.6, 1.4)
    
    # Stone root is universal (used for lumber everywhere)
    if g.get("flora_stone_root", 0.0) == 0.0:
        g["flora_stone_root"] = 100.0
    
    # Initialize all domestication facility counts
    for dom_key in ["domestic_greenhouses", "domestic_orchards", "domestic_pens", "domestic_kennels",
                     "domestic_cloud_ram_pens", "domestic_beetle_stables", "domestic_weaver_farms",
                     "domestic_dune_dog_dens", "domestic_snail_docks", "domestic_sheep_pastures",
                     "domestic_horse_stables", "domestic_aphid_farms", "domestic_falcon_roosts"]:
        if dom_key not in g:
            g[dom_key] = 0

def initialize_global_cell(cell, faction_name):
    """Initializes a single Azgaar cell with a dominant flora and fauna based on its region."""
    categories = FACTION_BIOME_CATEGORIES.get(faction_name, ["default"])
    
    possible_flora = []
    possible_fauna = []
    
    for cat in categories:
        for sp, pop in BIOME_SPECIES.get(cat, {}).items():
            if sp.startswith("flora"): possible_flora.append((sp, pop))
            if sp.startswith("fauna"): possible_fauna.append((sp, pop))
            
    if possible_flora:
        sp, base_pop = random.choice(possible_flora)
        cell["flora"] = sp
        cell["flora_pop"] = base_pop * random.uniform(0.5, 1.5)
    else:
        cell["flora"] = "flora_stone_root"
        cell["flora_pop"] = 50.0
        
    if possible_fauna:
        sp, base_pop = random.choice(possible_fauna)
        cell["fauna"] = sp
        cell["fauna_pop"] = base_pop * random.uniform(0.5, 1.5)
    else:
        cell["fauna"] = "fauna_timber_wolf"
        cell["fauna_pop"] = 20.0

def process_global_ecology_tick(grid, weather_type):
    """
    Runs Cellular Automata over the entire world grid.
    Animals and plants spread to neighboring cells if their population exceeds carrying capacity.
    """
    updates = {}
    
    for cid, cell in grid.items():
        flora = cell.get("flora")
        fauna = cell.get("fauna")
        f_pop = cell.get("flora_pop", 0)
        a_pop = cell.get("fauna_pop", 0)
        
        # Base growth rates
        f_params = SPECIES_PARAMS.get(flora, {"growth": 0.05, "cap": 1500.0, "food_chain": "flora"})
        a_params = SPECIES_PARAMS.get(fauna, {"growth": 0.05, "cap": 300.0, "food_chain": "prey"})
        
        # Per-cell cap is much smaller than Faction cap
        cell_f_cap = f_params["cap"] / 5.0
        cell_a_cap = a_params["cap"] / 5.0
        
        # Weather modifiers
        w_mod_f = 1.0
        w_mod_a = 1.0
        if weather_type == "Static Drought":
            w_mod_f = 0.5
            w_mod_a = 0.8
        elif weather_type == "Flux Monsoon":
            w_mod_f = 1.5
            
        f_growth = f_params["growth"] * w_mod_f
        a_growth = a_params["growth"] * w_mod_a
        
        # Predation logic within cell
        if a_params["food_chain"] == "predator":
            a_pop *= 0.98
        elif a_params["food_chain"] in ["herbivore", "prey"]:
            f_pop = max(0, f_pop - (a_pop * 0.05))
            
        # Logistic Growth
        f_pop += f_growth * f_pop * (1.0 - (f_pop / max(1, cell_f_cap)))
        a_pop += a_growth * a_pop * (1.0 - (a_pop / max(1, cell_a_cap)))
        
        updates[cid] = {"flora_pop": f_pop, "fauna_pop": a_pop}
        
        # Spreading Logic (Cellular Automata)
        if f_pop > cell_f_cap * 0.8 and cell.get("neighbors"):
            n_id = random.choice(cell["neighbors"])
            if n_id in grid:
                n_cell = grid[n_id]
                if n_cell.get("flora_pop", 0) < f_pop * 0.5:
                    if n_id not in updates: updates[n_id] = {}
                    updates[n_id]["flora"] = flora
                    updates[n_id]["flora_pop"] = n_cell.get("flora_pop", 0) + (f_pop * 0.1)
                    
        if a_pop > cell_a_cap * 0.8 and cell.get("neighbors"):
            n_id = random.choice(cell["neighbors"])
            if n_id in grid:
                n_cell = grid[n_id]
                if n_cell.get("fauna_pop", 0) < a_pop * 0.5:
                    if n_id not in updates: updates[n_id] = {}
                    updates[n_id]["fauna"] = fauna
                    updates[n_id]["fauna_pop"] = n_cell.get("fauna_pop", 0) + (a_pop * 0.1)
                    updates[cid]["fauna_pop"] -= (a_pop * 0.1)
                    
    # Apply updates
    for cid, up in updates.items():
        grid[cid].update(up)

def process_faction_harvesting(g, inventory, grid, camps, watchtowers, barracks, pop_efficiency):
    """Factions harvest resources from the global cells that they own."""
    harvests = {}
    
    # Get all cells owned by this faction
    faction_cells = [c for c in grid.values() if c.get("state") == g.get("id")]
    if not faction_cells:
        return harvests
        
    camps_per_cell = camps / max(1, len(faction_cells))
    military = watchtowers + barracks
    
    for cell in faction_cells:
        for sp_type, pop_key in [("flora", "flora_pop"), ("fauna", "fauna_pop")]:
            species = cell.get(sp_type)
            pop = cell.get(pop_key, 0)
            
            if pop < 5.0 or not species:
                continue
                
            h_info = HARVEST_TABLE.get(species)
            if not h_info or h_info["amount"] == 0:
                continue
                
            f_chain = SPECIES_PARAMS.get(species, {}).get("food_chain", "prey")
            if f_chain in ["apex", "predator"] and military < 1:
                continue
                
            if h_info["lethal"]:
                harvest_units = min(pop * 0.1, camps_per_cell * 10.0 * pop_efficiency)
                cell[pop_key] = max(0, pop - harvest_units)
            else:
                harvest_units = min(pop * 0.08, camps_per_cell * 5.0 * pop_efficiency)
                cell[pop_key] = max(0, pop - (harvest_units * 0.05))
                
            res_name = h_info["resource"]
            res_amount = harvest_units * h_info["amount"]
            if res_amount > 0:
                harvests[res_name] = harvests.get(res_name, 0) + res_amount
                inventory[res_name] = inventory.get(res_name, 0) + res_amount
                
            if h_info["secondary"]:
                sec_name, sec_mult = h_info["secondary"]
                sec_amt = harvest_units * sec_mult
                if sec_amt > 0:
                    harvests[sec_name] = harvests.get(sec_name, 0) + sec_amt
                    inventory[sec_name] = inventory.get(sec_name, 0) + sec_amt
                    
    # Domestication logic
    tool_bonuses = {}
    for species_key, dom_info in DOMESTICATION_TABLE.items():
        facility_key = dom_info["facility"]
        facility_count = int(g.get(facility_key, 0))
        if facility_count <= 0:
            continue
            
        input_res, input_amt = dom_info["input"]
        out_res, out_amt = dom_info["output"]
        
        for _ in range(facility_count):
            if inventory.get(input_res, 0.0) < input_amt: break
            inventory[input_res] -= input_amt
            if out_amt > 0:
                inventory[out_res] = inventory.get(out_res, 0) + out_amt
                harvests[out_res] = harvests.get(out_res, 0) + out_amt
            if dom_info["secondary"]:
                sec_res, sec_amt = dom_info["secondary"]
                inventory[sec_res] = inventory.get(sec_res, 0) + sec_amt
                harvests[sec_res] = harvests.get(sec_res, 0) + sec_amt
            if dom_info["tool_bonus"]:
                tool_bonuses[dom_info["tool_bonus"]] = tool_bonuses.get(dom_info["tool_bonus"], 0) + 1
                
    g["tool_transport_bonus"] = tool_bonuses.get("transport", 0) + tool_bonuses.get("fast_transport", 0) + tool_bonuses.get("heavy_transport", 0)
    g["tool_guard_bonus"] = tool_bonuses.get("guard", 0)
    g["tool_pest_control"] = tool_bonuses.get("pest_control", 0)
    g["tool_messenger_bonus"] = tool_bonuses.get("messenger", 0)
    
    chaos = g.get("chaos_level", 0.0)
    total_food_harvested = sum(v for k, v in harvests.items() if k in ["Grain", "Venison", "Luxury Meat", "Fat", "Honeydew"])
    if total_food_harvested < 10.0 and chaos < 0.7:
        forage_amount = max(5.0, float(camps * 4.0 * pop_efficiency))
        inventory["Grain"] = inventory.get("Grain", 0.0) + forage_amount
        harvests["Grain"] = harvests.get("Grain", 0.0) + forage_amount

    return harvests

def process_ecology_tick(g, inventory, season_mod, weather_type, growth_mult, camps, mines, docks, watchtowers, barracks, logs):
    """
    Processes one tick of ecology: growth, predation, harvesting, and domestication
    for ALL species in the simulation.
    """
    chaos = g.get("chaos_level", 0.0)
    season_growth = season_mod.get("growth", 1.0)
    pop_efficiency = g.get("population", 1000.0) / 5000.0
    
    harvests = {}
    
    # 1. Growth
    for species_key in ALL_SPECIES:
        pop = max(0.0, g.get(species_key, 0.0))
        if pop == 0.0:
            continue
        
        params = SPECIES_PARAMS.get(species_key, {"growth": 0.05, "cap": 500.0, "chaos_aff": 0.0})
        base_growth = params["growth"]
        cap = params["cap"]
        chaos_aff = params["chaos_aff"]
        
        chaos_mod = max(0.1, 1.0 + (chaos * chaos_aff))
        s_mod = season_growth if params["food_chain"] in ["flora", "herbivore", "prey"] else 1.0
        
        w_mod = growth_mult
        if weather_type == "Static Drought" and species_key.startswith("flora_"):
            w_mod *= 0.5
        elif weather_type == "Flux Monsoon" and species_key.startswith("flora_"):
            w_mod *= 1.5
        
        growth_rate = base_growth * chaos_mod * s_mod * w_mod
        ratio = pop / cap
        dp = growth_rate * pop * (1.0 - ratio)
        
        new_pop = max(0.0, min(cap, pop + dp))
        g[species_key] = new_pop
    
    # 2. Predation
    for predator_key, prey_list in PREDATION_MATRIX.items():
        pred_pop = g.get(predator_key, 0.0)
        if pred_pop < 1.0:
            continue
        
        for prey_key in prey_list:
            prey_pop = g.get(prey_key, 0.0)
            if prey_pop < 1.0:
                continue
            
            kill_rate = 0.015 * pred_pop / max(1.0, prey_pop)
            killed = max(0.0, min(prey_pop * 0.15, prey_pop * kill_rate))
            
            g[prey_key] = max(0.0, g[prey_key] - killed)
            g[predator_key] = min(SPECIES_PARAMS.get(predator_key, {}).get("cap", 200.0),
                                  g[predator_key] + killed * 0.1)
    
    # Weather
    if weather_type == "Reality Storm":
        for key in ALL_FAUNA:
            if g.get(key, 0.0) > 5.0:
                g[key] *= random.uniform(0.85, 0.95)
    elif weather_type == "Static Drought":
        for key in ALL_FAUNA:
            if g.get(key, 0.0) > 5.0:
                g[key] *= random.uniform(0.90, 0.98)
    
    # 3. Wild Harvesting
    for species_key, harvest_info in HARVEST_TABLE.items():
        pop = g.get(species_key, 0.0)
        if pop < 3.0:
            continue
        if harvest_info["amount"] == 0.0:
            continue
        
        params = SPECIES_PARAMS.get(species_key, {})
        food_chain = params.get("food_chain", "prey")
        
        if food_chain in ["apex", "predator"] and (watchtowers + barracks) < 1:
            continue
        if camps < 1 and food_chain not in ["apex", "predator"]:
            continue
        
        if harvest_info["lethal"]:
            max_harvest = pop * 0.10
            harvest_units = max(0.0, min(max_harvest, float(camps) * 2.0 * pop_efficiency))
            g[species_key] = max(0.0, g[species_key] - harvest_units)
        else:
            harvest_units = max(0.0, min(pop * 0.08, float(camps + docks) * 1.5 * pop_efficiency))
            g[species_key] = max(0.0, g[species_key] - harvest_units * 0.05)
        
        res_name = harvest_info["resource"]
        res_amount = harvest_units * harvest_info["amount"]
        if res_amount > 0.0:
            harvests[res_name] = harvests.get(res_name, 0.0) + res_amount
            inventory[res_name] = inventory.get(res_name, 0.0) + res_amount
        
        if harvest_info["secondary"]:
            sec_name, sec_mult = harvest_info["secondary"]
            sec_amount = harvest_units * sec_mult
            if sec_amount > 0.0:
                harvests[sec_name] = harvests.get(sec_name, 0.0) + sec_amount
                inventory[sec_name] = inventory.get(sec_name, 0.0) + sec_amount
    
    # 4. Domestication
    tool_bonuses = {}
    for species_key, dom_info in DOMESTICATION_TABLE.items():
        facility_key = dom_info["facility"]
        facility_count = int(g.get(facility_key, 0))
        if facility_count <= 0:
            continue
        
        input_res, input_amt = dom_info["input"]
        out_res, out_amt = dom_info["output"]
        
        for _ in range(facility_count):
            if inventory.get(input_res, 0.0) < input_amt:
                break
            
            inventory[input_res] -= input_amt
            if out_amt > 0.0:
                inventory[out_res] = inventory.get(out_res, 0.0) + out_amt
                harvests[out_res] = harvests.get(out_res, 0.0) + out_amt
            if dom_info["secondary"]:
                sec_res, sec_amt = dom_info["secondary"]
                inventory[sec_res] = inventory.get(sec_res, 0.0) + sec_amt
                harvests[sec_res] = harvests.get(sec_res, 0.0) + sec_amt
            if dom_info["tool_bonus"]:
                tool_bonuses[dom_info["tool_bonus"]] = tool_bonuses.get(dom_info["tool_bonus"], 0) + 1
    
    g["tool_transport_bonus"] = tool_bonuses.get("transport", 0) + tool_bonuses.get("fast_transport", 0) + tool_bonuses.get("heavy_transport", 0)
    g["tool_guard_bonus"] = tool_bonuses.get("guard", 0)
    g["tool_pest_control"] = tool_bonuses.get("pest_control", 0)
    g["tool_messenger_bonus"] = tool_bonuses.get("messenger", 0)
    
    if g["tool_pest_control"] > 0:
        for pest_key in ["fauna_furnace_tick", "fauna_fur_wyrm", "fauna_glimmer_wings"]:
            if g.get(pest_key, 0.0) > 3.0:
                g[pest_key] = max(0.0, g[pest_key] * (1.0 - 0.05 * g["tool_pest_control"]))
    
    # 5. Food Guarantee
    total_food_harvested = sum(v for k, v in harvests.items() if k in ["Grain", "Venison", "Luxury Meat", "Fat", "Honeydew"])
    if total_food_harvested < 10.0 and chaos < 0.7:
        forage_amount = max(5.0, float(camps * 4.0 * pop_efficiency))
        inventory["Grain"] = inventory.get("Grain", 0.0) + forage_amount
        harvests["Grain"] = harvests.get("Grain", 0.0) + forage_amount
    
    return harvests
