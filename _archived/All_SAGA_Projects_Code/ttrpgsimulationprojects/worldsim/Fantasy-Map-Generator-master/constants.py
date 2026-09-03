# constants.py
# Seasonal Rot Rules
WINTER_TRAVEL_COST = 2.5
SUMMER_GROWTH_MULT = 1.5

# Chaos Math
BASELINE_CHAOS = 0.5
MOON_PHASE_EFFECT = 1.5

# Town Sizes/Tiers based on Population
TOWN_TIERS = [
    {"name": "Camp", "min_pop": 0, "max_pop": 99, "score": 1},
    {"name": "Hamlet", "min_pop": 100, "max_pop": 499, "score": 2},
    {"name": "Village", "min_pop": 500, "max_pop": 1999, "score": 3},
    {"name": "Town", "min_pop": 2000, "max_pop": 9999, "score": 4},
    {"name": "City", "min_pop": 10000, "max_pop": float('inf'), "score": 5}
]

# Transport Unlocks based on Tech Level (combined town scores)
TRANSPORT_UNLOCKS = [
    {"name": "Foot Travel", "min_tech": 1},
    {"name": "Draft Horses", "min_tech": 3},
    {"name": "Naval Travel", "min_tech": 4},
    {"name": "Draft-Beetles", "min_tech": 5},
    {"name": "Airships", "min_tech": 8},
    {"name": "Snail-Draught", "min_tech": 10},
    {"name": "Aether-Skiffs", "min_tech": 12}
]

# Building Unlocks based on Tech Level (combined town scores)
BUILDING_UNLOCKS = [
    {"name": "Wooden Shacks", "min_tech": 1},
    {"name": "Stone Outposts", "min_tech": 4},
    {"name": "Brick Masonry", "min_tech": 7},
    {"name": "Iron Calderas", "min_tech": 10},
    {"name": "Sacred Spires", "min_tech": 15}
]

# --- Well-Being & Social Simulation Constants ---
WELLBEING_DECAY_RATE = 0.1     # Base rate well-being decays if unsupported
FOOD_PER_FARM = 0.15           # Food supply coefficient per farm
FOOD_PER_KELP_FARM = 0.18      # Food supply coefficient per kelp farm
FOOD_PER_DOCK = 0.10           # Food supply coefficient per dock
SAFETY_PER_TOWER = 0.15        # Safety coefficient per watchtower
SAFETY_PER_WALL = 0.20         # Safety coefficient per wall segment
SAFETY_PER_REEF_WALL = 0.25    # Safety coefficient per reef wall
SECURITY_PER_BARRACKS = 0.25   # Security coefficient per barracks building

# Threat Thresholds
RIOT_DISCONTENT_LIMIT = 0.7
RIOT_CRIME_LIMIT = 0.6
REVOLUTION_DISCONTENT_LIMIT = 0.9
REVOLUTION_CRIME_LIMIT = 0.8

# Trade Abundance Thresholds
TRADE_ABUNDANCE_LEVEL = 0.8
