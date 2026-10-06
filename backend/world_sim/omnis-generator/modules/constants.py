# constants.py
# Seasonal Rot Rules, Chaos Math, Town Tiers, Tech Unlocks, Building Costs, and Production Recipes.
# Loads dynamically from world_settings.json or default_settings.json.

import os
import json

# Resolve project root (one level up from modules/)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# --- HARDCODED DEFAULTS (FALLBACK) ---
DEFAULT_TOWN_TIERS = [
    {"name": "Camp", "min_pop": 0, "max_pop": 99, "score": 1},
    {"name": "Hamlet", "min_pop": 100, "max_pop": 499, "score": 2},
    {"name": "Village", "min_pop": 500, "max_pop": 1999, "score": 3},
    {"name": "Town", "min_pop": 2000, "max_pop": 9999, "score": 4},
    {"name": "City", "min_pop": 10000, "max_pop": float('inf'), "score": 5}
]

DEFAULT_TRANSPORT_UNLOCKS = [
    {"name": "Foot Travel", "min_tech": 1},
    {"name": "Draft Horses", "min_tech": 3},
    {"name": "Naval Travel", "min_tech": 4},
    {"name": "Draft-Beetles", "min_tech": 5},
    {"name": "Airships", "min_tech": 8},
    {"name": "Snail-Draught", "min_tech": 10},
    {"name": "Aether-Skiffs", "min_tech": 12}
]

DEFAULT_BUILDING_UNLOCKS = [
    {"name": "Wooden Shacks", "min_tech": 1},
    {"name": "Stone Outposts", "min_tech": 4},
    {"name": "Brick Masonry", "min_tech": 7},
    {"name": "Iron Calderas", "min_tech": 10},
    {"name": "Sacred Spires", "min_tech": 15}
]

DEFAULT_BUILDING_COSTS = {
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

DEFAULT_PRODUCTION_RECIPES = [
    {"name": "Smelted Steel", "inputs": {"Iron Ore": 5.0, "Coal": 3.0}, "output": 1.0, "description": "Used to craft heavy arms and tools."},
    {"name": "Copper Wire", "inputs": {"Copper Ore": 1.0}, "output": 2.0, "description": "Conducts magical current for batteries."},
    {"name": "Refined Aether Battery", "inputs": {"Dragonstone": 2.0, "Coal": 2.0}, "output": 1.0, "description": "Feeds reality wards."},
    {"name": "Flour", "inputs": {"Grain": 4.0}, "output": 1.0, "description": "Milled from raw grain."},
    {"name": "Alcohol", "inputs": {"Flour": 3.0}, "output": 1.0, "description": "Brewed for tavern use."},
    {"name": "Basic Weapons", "inputs": {"Smelted Steel": 2.0, "Lumber": 2.0}, "output": 10.0, "description": "Armed equipment for barracks defense."},
    {"name": "Ostrakan Hardtack", "inputs": {"Flour": 2.0, "Leather": 1.0}, "output": 1.0, "description": "Sturdy travel rations."},
    {"name": "Jewelry (Gold)", "inputs": {"Gold": 1.0, "Crystal Chips": 2.0}, "output": 1.0, "description": "Fine ornament for wealth."},
    {"name": "Jewelry (Silver)", "inputs": {"Silver": 1.0, "Crystal Chips": 2.0}, "output": 1.0, "description": "Ornament crafted from silver."},
    {"name": "Fine Clothes (Silk-Steel)", "inputs": {"Silk-Steel Thread": 2.0}, "output": 1.0, "description": "Premium garments."},
    {"name": "Fine Clothes (Wool)", "inputs": {"Wool": 3.0}, "output": 1.0, "description": "Warm winter garments."},
    {"name": "Medicine", "inputs": {"Kelp": 3.0, "Anesthetic Toxin": 1.0}, "output": 1.0, "description": "Heals physical wounds."},
    {"name": "Toys", "inputs": {"Lumber": 3.0, "Leather": 1.0}, "output": 1.0, "description": "Brings joy and comfort."},
    {"name": "Fancy Food", "inputs": {"Luxury Meat": 2.0, "Peak-Cheese": 1.0}, "output": 1.0, "description": "Served to high nobility."},
    {"name": "Drained Fleece Wool", "inputs": {"Wool": 3.0}, "output": 1.0, "description": "Washed and prepared fleece."},
    {"name": "Grain", "inputs": {"Honeydew": 5.0}, "output": 3.0, "description": "Honeydew processed into grain supply."}
]

# Declare module-level variables with hardcoded fallbacks
WINTER_TRAVEL_COST = 2.5
SUMMER_GROWTH_MULT = 1.5
BASELINE_CHAOS = 0.5
MOON_PHASE_EFFECT = 1.5

TOWN_TIERS = list(DEFAULT_TOWN_TIERS)
TRANSPORT_UNLOCKS = list(DEFAULT_TRANSPORT_UNLOCKS)
BUILDING_UNLOCKS = list(DEFAULT_BUILDING_UNLOCKS)
BUILDING_COSTS = dict(DEFAULT_BUILDING_COSTS)
PRODUCTION_RECIPES = list(DEFAULT_PRODUCTION_RECIPES)

WELLBEING_DECAY_RATE = 0.1
FOOD_PER_FARM = 0.15
FOOD_PER_KELP_FARM = 0.18
FOOD_PER_DOCK = 0.10
SAFETY_PER_TOWER = 0.15
SAFETY_PER_WALL = 0.20
SAFETY_PER_REEF_WALL = 0.25
SECURITY_PER_BARRACKS = 0.25

RIOT_DISCONTENT_LIMIT = 0.7
RIOT_CRIME_LIMIT = 0.6
REVOLUTION_DISCONTENT_LIMIT = 0.9
REVOLUTION_CRIME_LIMIT = 0.8
TRADE_ABUNDANCE_LEVEL = 0.8

def load_dynamic_constants():
    """Loads constants from world_settings.json or default_settings.json dynamically."""
    global WINTER_TRAVEL_COST, SUMMER_GROWTH_MULT, BASELINE_CHAOS, MOON_PHASE_EFFECT
    global TOWN_TIERS, TRANSPORT_UNLOCKS, BUILDING_UNLOCKS, BUILDING_COSTS, PRODUCTION_RECIPES
    global WELLBEING_DECAY_RATE, FOOD_PER_FARM, FOOD_PER_KELP_FARM, FOOD_PER_DOCK
    global SAFETY_PER_TOWER, SAFETY_PER_WALL, SAFETY_PER_REEF_WALL, SECURITY_PER_BARRACKS
    global RIOT_DISCONTENT_LIMIT, RIOT_CRIME_LIMIT, REVOLUTION_DISCONTENT_LIMIT, REVOLUTION_CRIME_LIMIT
    global TRADE_ABUNDANCE_LEVEL

    # Resolve settings path
    settings = {}
    for filename in ['world_settings.json', 'default_settings.json']:
        path = os.path.join(_PROJECT_ROOT, filename)
        if os.path.isfile(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                break
            except Exception:
                pass

    if not settings:
        return

    # 1. Town tiers
    tiers = settings.get('town_tiers')
    if tiers:
        TOWN_TIERS.clear()
        for t in tiers:
            max_val = float('inf') if t.get('max_pop') is None else t.get('max_pop')
            TOWN_TIERS.append({
                "name": t.get('name', 'Tier'),
                "min_pop": t.get('min_pop', 0),
                "max_pop": max_val,
                "score": t.get('score', 1)
            })

    # 2. Tech transport unlocks
    trans = settings.get('transport_unlocks')
    if trans:
        TRANSPORT_UNLOCKS.clear()
        for tr in trans:
            TRANSPORT_UNLOCKS.append({
                "name": tr.get('name', 'Transport'),
                "min_tech": tr.get('min_tech', 1)
            })

    # 3. Building unlocks
    bld_un = settings.get('building_unlocks')
    if bld_un:
        BUILDING_UNLOCKS.clear()
        for b in bld_un:
            BUILDING_UNLOCKS.append({
                "name": b.get('name', 'Building'),
                "min_tech": b.get('min_tech', 1)
            })

    # 4. Building Costs
    bld_costs = settings.get('building_types')
    if bld_costs:
        BUILDING_COSTS.clear()
        for b in bld_costs:
            BUILDING_COSTS[b.get('name')] = b.get('cost', {})
        # Ensure we always have default fallback for buildings not defined in JSON
        for k, v in DEFAULT_BUILDING_COSTS.items():
            if k not in BUILDING_COSTS:
                BUILDING_COSTS[k] = v

    # 5. Production Recipes
    recipes = settings.get('production_recipes')
    if recipes:
        PRODUCTION_RECIPES.clear()
        for r in recipes:
            PRODUCTION_RECIPES.append({
                "name": r.get('name'),
                "inputs": r.get('inputs', {}),
                "output": r.get('output', 1.0),
                "description": r.get('description', '')
            })

    # 6. Coefficients and limits
    coeffs = settings.get('wellbeing_coefficients', {})
    if coeffs:
        WELLBEING_DECAY_RATE = coeffs.get('wellbeing_decay_rate', 0.1)
        FOOD_PER_FARM = coeffs.get('food_per_farm', 0.15)
        FOOD_PER_KELP_FARM = coeffs.get('food_per_kelp_farm', 0.18)
        FOOD_PER_DOCK = coeffs.get('food_per_dock', 0.10)
        SAFETY_PER_TOWER = coeffs.get('safety_per_tower', 0.15)
        SAFETY_PER_WALL = coeffs.get('safety_per_wall', 0.20)
        SAFETY_PER_REEF_WALL = coeffs.get('safety_per_reef_wall', 0.25)
        SECURITY_PER_BARRACKS = coeffs.get('security_per_barracks', 0.25)

        RIOT_DISCONTENT_LIMIT = coeffs.get('riot_discontent_limit', 0.7)
        RIOT_CRIME_LIMIT = coeffs.get('riot_crime_limit', 0.6)
        REVOLUTION_DISCONTENT_LIMIT = coeffs.get('revolution_discontent_limit', 0.9)
        REVOLUTION_CRIME_LIMIT = coeffs.get('revolution_crime_limit', 0.8)
        TRADE_ABUNDANCE_LEVEL = coeffs.get('trade_abundance_level', 0.8)

        WINTER_TRAVEL_COST = coeffs.get('winter_travel_cost', 2.5)
        SUMMER_GROWTH_MULT = coeffs.get('summer_growth_mult', 1.5)
        BASELINE_CHAOS = coeffs.get('baseline_chaos', 0.5)
        MOON_PHASE_EFFECT = coeffs.get('moon_phase_effect', 1.5)

# Load immediately at import time
load_dynamic_constants()
