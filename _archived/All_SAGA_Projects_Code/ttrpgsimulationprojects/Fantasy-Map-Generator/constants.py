# constants.py
# Seasonal Rot Rules
WINTER_TRAVEL_COST = 2.5
SUMMER_GROWTH_MULT = 1.5

# City Growth Tiers
CITY_TIERS = {
    1: {"pop_req": 100, "gold_req": 500, "resource_req": ["Wood"]},
    2: {"pop_req": 1000, "gold_req": 5000, "resource_req": ["Iron", "Stone"]},
}

# Chaos Math
BASELINE_CHAOS = 0.5
MOON_PHASE_EFFECT = 1.5
