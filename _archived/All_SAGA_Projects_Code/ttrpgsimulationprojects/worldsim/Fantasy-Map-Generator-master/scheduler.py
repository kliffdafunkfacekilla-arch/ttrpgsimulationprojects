# scheduler.py
import os
import sys
import random

# Ensure stdout handles Unicode emojis cleanly on Windows PowerShell
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# Ensure modules directory is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'modules')))

from sqlalchemy import create_engine
from calendar_manager import CalendarManager
from magistar_plugin import calculate_reality_spike
from weather_system import calculate_weather
from oceanic_system import run_oceanic_tick
from expansion_system import run_expansion_tick
from rules_engine import (
    get_town_details, calculate_tech_level, 
    get_unlocked_transport, get_unlocked_buildings,
    process_well_being_tick, process_living_world_tick
)
from diplomacy_system import initialize_diplomacy, process_diplomacy_tick
from fringe_system import initialize_fringe_groups, process_fringe_tick

engine = create_engine('postgresql://user:password@localhost:5432/ostraka_world')

# Global Prison state for background scheduler
SCHEDULER_PRISONS = {
    "Tiraton": 1.0,
    "Stagus": 1.0,
    "Metrion": 1.0,
    "Aurgenas": 1.0,
    "Vecelo": 1.0,
    "Lophex": 1.0,
    "Tyrustis": 1.0,
    "Opecten": 1.0,
    "Carulkem": 1.0,
    "Termhill": 1.0,
    "Virantor": 1.0,
    "Gavusrix": 1.0,
    "warden_population": 1500.0,
    "warden_recruits_accumulated": 0.0
}

SCHEDULER_DIPLOMACY = initialize_diplomacy()
SCHEDULER_FRINGE_GROUPS = initialize_fringe_groups()

# Dummy functions to make it runnable and testable
def get_day_from_db():
    return 150

class DummyMacroGroup:
    def __init__(self, group_id, name, populations, stats, buildings_count, magistar_id="Tiraton", distance_to_chaos=0.5, distance_to_conv=0.6):
        self.id = group_id
        self.name = name
        self.settlement_populations = populations
        self.settlements = []
        self.population = sum(populations)
        self.chaos_level = 0.5
        self.pressure = 0.5
        self.magistar_id = magistar_id
        self.is_active = True
        self.geom = "dummy_geom"
        self.distance_to_chaos_structure = distance_to_chaos
        self.distance_to_convergence = distance_to_conv
        
        # Initial well-being stats
        self.physical_well_being = stats.get("physical", 0.8)
        self.mental_well_being = stats.get("mental", 0.8)
        self.crime_level = stats.get("crime", 0.2)
        self.discontent = stats.get("discontent", 0.1)
        
        # Active building configurations
        self.camps_count = buildings_count.get("camps", 0)
        self.mines_count = buildings_count.get("mines", 0)
        self.docks_count = buildings_count.get("docks", 0)
        self.farms_count = buildings_count.get("farms", 0)
        self.watchtowers_count = buildings_count.get("watchtowers", 0)
        self.walls_count = buildings_count.get("walls", 0)
        self.barracks_count = buildings_count.get("barracks", 0)
        
        self.kelp_farms_count = buildings_count.get("kelp_farms", 0)
        self.underwater_domes_count = buildings_count.get("underwater_domes", 0)
        self.coral_mines_count = buildings_count.get("coral_mines", 0)
        self.reef_walls_count = buildings_count.get("reef_walls", 0)

        # Infiltration level & Cult population
        self.cult_infiltration = 0.05
        self.cult_population = self.population * self.cult_infiltration
        self.cult_devoted = self.cult_population * 0.20

        # Ecology values
        self.flora_ghost_flower = 100.0
        self.flora_stone_root = 100.0
        self.fauna_sky_grazer = 50.0
        self.fauna_timber_wolf = 10.0

        # Domestic facilities
        self.domestic_greenhouses = 0
        self.domestic_orchards = 0
        self.domestic_pens = 0
        self.domestic_kennels = 0

        # Happiness & Syndicate/Illicit structures
        self.churches_count = 0
        self.theatres_count = 0
        self.arenas_count = 0
        self.gambling_dens_count = 0
        self.black_markets_count = 0

        # Leader / Paragon
        self.paragon = None

        # Initialize inventory
        self.inventory = {
            "Wealth": 50.0,
            "Lumber": 50.0,
            "Stone": 50.0,
            "Iron Ore": 10.0,
            "Copper Ore": 5.0,
            "Coal": 10.0,
            "Grain": 200.0,
            "Leather": 10.0,
            "Dragonstone": 2.0,
            "Voltaic Fleece": 0.0,
            "Ozone-Milk": 0.0,
            "Ghost Flower": 0.0,
            "Night-Nectar": 0.0,
            "Flour": 0.0,
            "Peak-Cheese": 0.0,
            "Smelted Steel": 0.0,
            "Copper Wire": 0.0,
            "Refined Aether Battery": 0.0,
            "Tanned Strips": 0.0,
            "Ostrakan Hardtack": 5.0,
            "Caldera Spark-Bread": 0.0,
            "Basic Weapons": 50.0,
            "Aether-Wright PPE": 0.0,
            "Silk-Steel Cables": 0.0,
            "Leather Armor": 50.0,
            "Rope": 0.0
        }
        
        self.buildings = {"farms": 1, "watchtowers": 1, "barracks": 0, "walls": 0}
        self.hub_wealth = 0
        self.ruined_hub_penalty = 0

_GLOBAL_GROUPS = None
_GLOBAL_GRID = None
_GLOBAL_SAGA_LOGS = []
_GLOBAL_RESOURCE_NODES = []
_GLOBAL_TERRITORY_CHANGES = []
_GLOBAL_TRADE_ROUTES = []
_GLOBAL_ECOLOGY_GRID = {} # id -> {biome, state, flora_pop, fauna_pop, flora_type, fauna_type}

def get_and_clear_territory_changes():
    global _GLOBAL_TERRITORY_CHANGES
    changes = list(_GLOBAL_TERRITORY_CHANGES)
    _GLOBAL_TERRITORY_CHANGES.clear()
    return changes

def get_global_resource_nodes():
    return _GLOBAL_RESOURCE_NODES

def log_saga_event(category, message):
    global _GLOBAL_SAGA_LOGS
    _GLOBAL_SAGA_LOGS.append(f"[{category}] {message}")
    if len(_GLOBAL_SAGA_LOGS) > 100:
        _GLOBAL_SAGA_LOGS.pop(0)
def get_saga_logs():
    """Returns the current saga log buffer and clears it for the next read."""
    global _GLOBAL_SAGA_LOGS
    logs = list(_GLOBAL_SAGA_LOGS)
    _GLOBAL_SAGA_LOGS.clear()
    return logs

def ingest_map_data(grid_data):
    """
    Called by the FastAPI Map Builder when you click "Save Layout to DB".
    Loops through the 10,000 tiles and dynamically sets the real starting stats for the Factions
    based on the painted geography, replacing the hardcoded defaults.
    """
    global _GLOBAL_GROUPS, _GLOBAL_GRID
    _GLOBAL_GRID = grid_data
    if _GLOBAL_GROUPS is None:
        _GLOBAL_GROUPS = []

    # Map of FactionID -> Stats Dictionary
    stats = {}

    for row in grid_data:
        for cell in row:
            fid = cell.get('factionId')
            if not fid:
                continue
                
            if fid not in stats:
                stats[fid] = {
                    "population": 0,
                    "forests": 0, "plains": 0, "mountains": 0, "deserts": 0,
                    "coastal": 0, "ocean": 0, "reef": 0, "abyssal": 0, "thermal": 0
                }
                
            # Sum Population
            stats[fid]["population"] += cell.get('population', 0)
            
            # Tally Biomes
            b = cell.get('biome', 'ocean')
            if b in stats[fid]:
                stats[fid][b] += 1
            else:
                stats[fid][b] = 1
                
            # Track coordinates for Center of Mass
            if "x_sum" not in stats[fid]:
                stats[fid]["x_sum"] = 0.0
                stats[fid]["y_sum"] = 0.0
                stats[fid]["cell_count"] = 0
            stats[fid]["x_sum"] += x
            stats[fid]["y_sum"] += y
            stats[fid]["cell_count"] += 1

    import math
    # Recreate the 12 Traitor Anchors (Icosahedron Convergence) in 100x100 grid scale
    anchors = []
    anchors.append((50.0, 2.0)) # North Pole
    anchors.append((50.0, 98.0)) # South Pole
    for i in range(5): anchors.append((100.0 * (0.1 + i * 0.2), 35.0)) # Upper Row
    for i in range(5): anchors.append((100.0 * (0.2 + i * 0.2), 65.0)) # Lower Row
    
    center = (50.0, 50.0)

    # Overwrite the DummyMacroGroups with real calculated data
    for group in _GLOBAL_GROUPS:
        if group.id in stats:
            s = stats[group.id]
            
            # Set Population
            group.population = max(10, s["population"]) # Prevent instant death if 0
            
            # Calculate Distance to Chaos Anchors
            if s.get("cell_count", 0) > 0:
                cx = s["x_sum"] / s["cell_count"]
                cy = s["y_sum"] / s["cell_count"]
                
                # Find shortest distance to any of the 12 anchors or the center (spiral path destination)
                min_dist = math.hypot(cx - center[0], cy - center[1])
                for ax, ay in anchors:
                    dist = math.hypot(cx - ax, cy - ay)
                    if dist < min_dist:
                        min_dist = dist
                        
                # Max possible distance on 100x100 grid from any anchor is roughly ~25-30
                # Normalize to 0.0 (right on top) to 1.0 (far away)
                normalized_dist = min(1.0, min_dist / 30.0)
                group.distance_to_chaos_structure = normalized_dist
            
            # Auto-generate Structures (1 Farm per 5 plains, 1 Mine per 2 mountains, etc)
            group.farms_count = s.get("plains", 0) // 5
            group.mines_count = s.get("mountains", 0) // 2
            group.camps_count = s.get("forests", 0) // 3
            group.kelp_farms_count = s.get("reef", 0) // 3 + s.get("coastal", 0) // 10
            
            # Special Deep Ocean structures
            if s.get("thermal", 0) > 0:
                group.inventory["Deep-Sea Vents (Geothermal Energy)"] = s.get("thermal") * 5
                
            print(f"[INGESTION] Built {group.name}: Pop {group.population}, {group.farms_count} Farms, {group.kelp_farms_count} Kelp Farms.")

    # Generate Rare Resource Nodes
    global _GLOBAL_RESOURCE_NODES
    _GLOBAL_RESOURCE_NODES = []
    import random
    
    geological_nodes = [
        {"name": "Luminescent Coral Mine", "icon": "🪸", "desc": "Yields Coral", "yield_range": (100, 300), "weight_water": 10, "weight_land": 0},
        {"name": "Ancient Steel Ruins", "icon": "⚔️", "desc": "Yields Smelted Steel", "yield_range": (50, 150), "weight_water": 1, "weight_land": 8},
        {"name": "Rich Iron Vein", "icon": "🪨", "desc": "Yields Iron", "yield_range": (200, 500), "weight_water": 0, "weight_land": 10},
        {"name": "Rich Copper Vein", "icon": "🟠", "desc": "Yields Copper", "yield_range": (200, 500), "weight_water": 0, "weight_land": 10},
        {"name": "Rich Nickel Vein", "icon": "🪨", "desc": "Yields Nickel", "yield_range": (200, 500), "weight_water": 1, "weight_land": 9},
        {"name": "Deep-Earth Geode", "icon": "💎", "desc": "Yields Crystal Chips", "yield_range": (50, 200), "weight_water": 4, "weight_land": 6},
        {"name": "Dragonstone Crater", "icon": "🔮", "desc": "Yields Dragonstone", "yield_range": (20, 60), "weight_water": 2, "weight_land": 2},
        # 12 Elemental Conductors
        {"name": "Rich Lithium Deposit", "icon": "⚡", "desc": "Yields Lithium (Willpower Conductor)", "yield_range": (50, 200), "weight_water": 2, "weight_land": 8},
        {"name": "Rich Osmium Vein", "icon": "⬛", "desc": "Yields Osmium (Might Conductor)", "yield_range": (50, 200), "weight_water": 4, "weight_land": 6},
        {"name": "Rich Tungsten Vein", "icon": "🔥", "desc": "Yields Tungsten (Fortitude Conductor)", "yield_range": (50, 200), "weight_water": 1, "weight_land": 9},
        {"name": "Rich Gold Vein", "icon": "🪙", "desc": "Yields Gold (Finesse Conductor)", "yield_range": (50, 200), "weight_water": 3, "weight_land": 7},
        {"name": "Rich Silver Vein", "icon": "🥈", "desc": "Yields Silver (Vitality Conductor)", "yield_range": (50, 200), "weight_water": 3, "weight_land": 7},
        {"name": "Rich Lead Vein", "icon": "🪨", "desc": "Yields Lead (Reflex Conductor)", "yield_range": (50, 200), "weight_water": 2, "weight_land": 8},
        {"name": "Rich Iridium Vein", "icon": "☄️", "desc": "Yields Iridium (Intuition Conductor)", "yield_range": (50, 200), "weight_water": 5, "weight_land": 5},
        {"name": "Rich Titanium Vein", "icon": "🛡️", "desc": "Yields Titanium (Endurance Conductor)", "yield_range": (50, 200), "weight_water": 2, "weight_land": 8},
        {"name": "Rich Silicon Deposit", "icon": "💻", "desc": "Yields Silicon (Logic Conductor)", "yield_range": (50, 200), "weight_water": 6, "weight_land": 4},
        {"name": "Rich Bismuth Vein", "icon": "🌈", "desc": "Yields Bismuth (Knowledge Conductor)", "yield_range": (50, 200), "weight_water": 3, "weight_land": 7},
        {"name": "Rich Chromium Vein", "icon": "✨", "desc": "Yields Chromium (Awareness Conductor)", "yield_range": (50, 200), "weight_water": 1, "weight_land": 9},
        {"name": "Rich Phosphorus Deposit", "icon": "🌟", "desc": "Yields Phosphorus (Charm Conductor)", "yield_range": (50, 200), "weight_water": 8, "weight_land": 2}
    ]
    
    # Collect cell lists per faction
    faction_cells = {}
    for row in grid_data:
        for cell in row:
            fid = cell.get('factionId')
            if not fid:
                continue
            if fid not in faction_cells:
                faction_cells[fid] = {"water": [], "land": []}
            
            c_id = cell.get('i')
            if c_id is not None:
                if cell.get('height', 20) < 20:
                    faction_cells[fid]["water"].append(c_id)
                else:
                    faction_cells[fid]["land"].append(c_id)

    # Assign nodes based on weights
    for fid, cells in faction_cells.items():
        # Maybe 1 water anomaly and 1 land anomaly per faction
        if cells["water"]:
            c_id = random.choice(cells["water"])
            pool = [n for n in geological_nodes if n["weight_water"] > 0]
            weights = [n["weight_water"] for n in pool]
            res = random.choices(pool, weights=weights, k=1)[0]
            _GLOBAL_RESOURCE_NODES.append({
                "cell": c_id,
                "faction_id": fid,
                "icon": res["icon"],
                "name": res["name"],
                "desc": res["desc"],
                "yield_remaining": random.randint(res["yield_range"][0], res["yield_range"][1]),
                "is_discovered": False
            })
            
        if cells["land"]:
            c_id = random.choice(cells["land"])
            pool = [n for n in geological_nodes if n["weight_land"] > 0]
            weights = [n["weight_land"] for n in pool]
            res = random.choices(pool, weights=weights, k=1)[0]
            _GLOBAL_RESOURCE_NODES.append({
                "cell": c_id,
                "faction_id": fid,
                "icon": res["icon"],
                "name": res["name"],
                "desc": res["desc"],
                "yield_remaining": random.randint(res["yield_range"][0], res["yield_range"][1]),
                "is_discovered": False
            })
            
    print(f"[INGESTION] Generated {len(_GLOBAL_RESOURCE_NODES)} Hard Resource Nodes on the map.")

def ingest_azgaar_data(azgaar_data):
    """
    Parses native Azgaar states and burgs to update the 17 Lore Factions.
    Assigns Paragon Leaders to every settlement.
    """
    global _GLOBAL_GROUPS
    from rules_engine import generate_paragon
    
    if _GLOBAL_GROUPS is None:
        get_all_macro_groups() # Initialize fallbacks
        
    states = azgaar_data.get("states", [])
    burgs = azgaar_data.get("burgs", [])
    cells = azgaar_data.get("cells", [])
    
    global _GLOBAL_ECOLOGY_GRID
    _GLOBAL_ECOLOGY_GRID.clear()
    
    state_id_to_name = {s["id"]: s["name"] for s in states}
    from ecology_system import initialize_global_cell
    
    # Initialize Cellular Ecology Grid
    for c in cells:
        cid = c["id"]
        _GLOBAL_ECOLOGY_GRID[cid] = {
            "id": cid,
            "biome": c.get("biome", 0),
            "state": c.get("state", 0),
            "neighbors": c.get("neighbors", []),
            "x": c.get("x", 0),
            "y": c.get("y", 0)
        }
        initialize_global_cell(_GLOBAL_ECOLOGY_GRID[cid], state_id_to_name.get(c.get("state", 0), "Unknown"))
    
    burgs_by_state = {}
    for b in burgs:
        sid = b["state"]
        if sid not in burgs_by_state:
            burgs_by_state[sid] = []
        
        # Generate settlement Paragons
        mayor = generate_paragon(state_id_to_name.get(sid, "Unknown"), [], role="Mayor")
        captain = generate_paragon(state_id_to_name.get(sid, "Unknown"), [], role="Captain")
        
        burgs_by_state[sid].append({
            "id": b["id"],
            "name": b["name"],
            "population": b["population"] * 1000,
            "mayor": mayor,
            "captain": captain
        })
        
    updated_count = 0
    for group in _GLOBAL_GROUPS:
        matched_state_id = next((sid for sid, name in state_id_to_name.items() if name.lower() == group.name.lower()), None)
        if matched_state_id is not None:
            faction_burgs = burgs_by_state.get(matched_state_id, [])
            if faction_burgs:
                group.settlements = faction_burgs
                group.population = sum(b["population"] for b in faction_burgs)
                group.settlement_populations = [b["population"] for b in faction_burgs]
                updated_count += 1
                
    return updated_count

def get_all_macro_groups():
    global _GLOBAL_GROUPS
    if _GLOBAL_GROUPS is not None:
        return _GLOBAL_GROUPS

    # Fallback initialization if grid hasn't been saved yet
    _GLOBAL_GROUPS = [
        DummyMacroGroup(1, "Ursine Hegemony", [4000], {"physical": 0.85, "mental": 0.80, "crime": 0.10, "discontent": 0.05}, {"camps": 2, "mines": 1, "docks": 1, "farms": 2, "watchtowers": 3, "walls": 2, "barracks": 2}, "Stagus", distance_to_chaos=0.7, distance_to_conv=0.8),
        DummyMacroGroup(2, "River Folk", [6000], {"physical": 0.80, "mental": 0.85, "crime": 0.15, "discontent": 0.10}, {"camps": 1, "mines": 1, "docks": 3, "farms": 3, "watchtowers": 1, "walls": 0, "barracks": 1}, "Tiraton", distance_to_chaos=0.2, distance_to_conv=0.5),
        DummyMacroGroup(3, "Sump-Kin", [5000], {"physical": 0.55, "mental": 0.50, "crime": 0.40, "discontent": 0.30}, {"camps": 2, "mines": 3, "docks": 2, "farms": 0, "watchtowers": 1, "walls": 0, "barracks": 2}, "Gavusrix", distance_to_chaos=0.1, distance_to_conv=0.3),
        DummyMacroGroup(4, "Iron Caladrea", [7000], {"physical": 0.75, "mental": 0.70, "crime": 0.20, "discontent": 0.15}, {"camps": 1, "mines": 4, "docks": 0, "farms": 1, "watchtowers": 2, "walls": 3, "barracks": 3}, "Aurgenas", distance_to_chaos=0.4, distance_to_conv=0.6),
        DummyMacroGroup(5, "Vaneer Concord", [9000], {"physical": 0.88, "mental": 0.75, "crime": 0.12, "discontent": 0.10}, {"camps": 2, "mines": 4, "docks": 1, "farms": 3, "watchtowers": 2, "walls": 3, "barracks": 4}, "Lophex", distance_to_chaos=0.6, distance_to_conv=0.6),
        DummyMacroGroup(6, "Hive Collective", [12000], {"physical": 0.90, "mental": 0.90, "crime": 0.05, "discontent": 0.05}, {"camps": 3, "mines": 2, "docks": 0, "farms": 6, "watchtowers": 2, "walls": 4, "barracks": 3}, "Tyrustis", distance_to_chaos=0.8, distance_to_conv=0.6),
        DummyMacroGroup(7, "Avians", [8000], {"physical": 0.92, "mental": 0.85, "crime": 0.08, "discontent": 0.08}, {"camps": 1, "mines": 1, "docks": 2, "farms": 2, "watchtowers": 4, "walls": 1, "barracks": 2}, "Opecten", distance_to_chaos=0.3, distance_to_conv=0.5),
        DummyMacroGroup(8, "Flower Valwey", [3000], {"physical": 0.85, "mental": 0.88, "crime": 0.10, "discontent": 0.05}, {"camps": 2, "mines": 1, "docks": 1, "farms": 4, "watchtowers": 1, "walls": 1, "barracks": 1}, "Vecelo", distance_to_chaos=0.9, distance_to_conv=0.9),
        DummyMacroGroup(9, "Sylvian", [6000], {"physical": 0.82, "mental": 0.80, "crime": 0.15, "discontent": 0.10}, {"camps": 3, "mines": 1, "docks": 0, "farms": 4, "watchtowers": 2, "walls": 1, "barracks": 2}, "Termhill", distance_to_chaos=0.5, distance_to_conv=0.7),
        DummyMacroGroup(10, "Sciute", [4000], {"physical": 0.80, "mental": 0.78, "crime": 0.12, "discontent": 0.08}, {"camps": 1, "mines": 2, "docks": 1, "farms": 2, "watchtowers": 2, "walls": 3, "barracks": 1}, "Carulkem", distance_to_chaos=0.5, distance_to_conv=0.7),
        DummyMacroGroup(11, "Meridian Chain", [8000], {"physical": 0.88, "mental": 0.82, "crime": 0.18, "discontent": 0.12}, {"camps": 2, "mines": 1, "docks": 4, "farms": 1, "watchtowers": 1, "walls": 1, "barracks": 3}, "Virantor", distance_to_chaos=0.3, distance_to_conv=0.6),
        DummyMacroGroup(12, "Prism Lizards", [5000], {"physical": 0.84, "mental": 0.80, "crime": 0.16, "discontent": 0.14}, {"camps": 1, "mines": 2, "docks": 1, "farms": 1, "watchtowers": 2, "walls": 2, "barracks": 2}, "Metrion", distance_to_chaos=0.2, distance_to_conv=0.5),
        DummyMacroGroup(13, "Canopy Clans", [3000], {"physical": 0.70, "mental": 0.65, "crime": 0.35, "discontent": 0.25}, {"camps": 5, "mines": 1, "docks": 0, "farms": 2, "watchtowers": 2, "walls": 0, "barracks": 1}, "Metrion", distance_to_chaos=0.2, distance_to_conv=0.5),
        DummyMacroGroup(14, "East Hounds", [3000], {"physical": 0.65, "mental": 0.70, "crime": 0.28, "discontent": 0.20}, {"camps": 3, "mines": 0, "docks": 0, "farms": 2, "watchtowers": 2, "walls": 0, "barracks": 2}, "Termhill", distance_to_chaos=0.5, distance_to_conv=0.7),
        DummyMacroGroup(15, "Guirrilla Clans", [1500], {"physical": 0.58, "mental": 0.62, "crime": 0.38, "discontent": 0.28}, {"camps": 4, "mines": 1, "docks": 0, "farms": 1, "watchtowers": 1, "walls": 0, "barracks": 1}, "Tiraton", distance_to_chaos=0.1, distance_to_conv=0.4),
        DummyMacroGroup(16, "Theocracy", [6000], {"physical": 0.72, "mental": 0.68, "crime": 0.22, "discontent": 0.18}, {"camps": 1, "mines": 1, "docks": 3, "farms": 2, "watchtowers": 2, "walls": 1, "barracks": 2}, "Virantor", distance_to_chaos=0.3, distance_to_conv=0.6),
        DummyMacroGroup(17, "The Reliance", [3000], {"physical": 0.95, "mental": 0.90, "crime": 0.05, "discontent": 0.02}, {"camps": 1, "mines": 2, "docks": 0, "farms": 1, "watchtowers": 1, "walls": 1, "barracks": 1}, "Gavusrix", distance_to_chaos=0.9, distance_to_conv=0.4)
    ]
    return _GLOBAL_GROUPS

def get_global_grid():
    global _GLOBAL_GRID
    return _GLOBAL_GRID

def get_global_trade_routes():
    global _GLOBAL_TRADE_ROUTES
    return _GLOBAL_TRADE_ROUTES

def get_all_fringe_groups():
    global SCHEDULER_FRINGE_GROUPS
    return SCHEDULER_FRINGE_GROUPS

def calculate_torque(geom):
    return 10.0

def update_group_state(group_id, name, population, weather, tech_level, transports, buildings, stats_results):
    print(f"Updated group {group_id} ({name}): population={population:.2f}, weather={weather}")
    print(f"  Calculated Tech Level: {tech_level}")
    print(f"  Active Interaction Tags: {', '.join(stats_results.get('active_tags', []))}")
    print(f"  Unlocked Transports: {', '.join(transports)}")
    print(f"  Unlocked Buildings: {', '.join(buildings)}")
    print(f"  --- Social Stats & Threat ---")
    print(f"    Food Supply Rating: {stats_results['food_supply']:.2f}")
    print(f"    Safety Rating: {stats_results['safety_rating']:.2f}")
    print(f"    Security Rating: {stats_results['security_rating']:.2f}")
    print(f"    Physical Well-Being: {stats_results['physical_well_being']:.2f}")
    print(f"    Mental Well-Being: {stats_results['mental_well_being']:.2f}")
    print(f"    Discontent: {stats_results['discontent']:.2f}")
    print(f"    Crime Level: {stats_results['crime_level']:.2f}")
    print(f"    Warden Chaos Patrols: {stats_results.get('allocated_patrols', 0.0):.0f} Sentinels | Hunters: {stats_results.get('allocated_hunters', 0.0):.0f} Rangers")
    print(f"    Cult: Infiltration={stats_results.get('cult_infiltration', 0.05)*100:.1f}% | Devoted Priests={stats_results.get('cult_devoted', 0.0):.0f} | Network={stats_results.get('cult_population', 0.0) - stats_results.get('cult_devoted', 0.0):.0f}")
    print(f"    Demographics: Nulls={stats_results.get('null_population', population * 0.5):.0f} | Sparkborn={stats_results.get('sparkborn_population', population * 0.5):.0f} (Sens={stats_results.get('sparkborn_sensitive', 0.0):.0f}, Attu={stats_results.get('sparkborn_attuned', 0.0):.0f}, Adep={stats_results.get('sparkborn_adept', 0.0):.0f}, Wiel={stats_results.get('sparkborn_wielder', 0.0):.0f}, Mast={stats_results.get('sparkborn_master', 0.0):.0f}, Epic={stats_results.get('sparkborn_epic', 0.0):.0f})")
    print(f"    Happiness Buildings: Churches={stats_results.get('churches_count', 0)} | Theatres={stats_results.get('theatres_count', 0)} | Arenas={stats_results.get('arenas_count', 0)}")
    print(f"    Syndicate Structures: Gambling Dens={stats_results.get('gambling_dens_count', 0)} | Black Markets={stats_results.get('black_markets_count', 0)}")
    
    p = stats_results.get("paragon")
    if p:
        print(f"    👑 Paragon Leader: {p['name']} ({p['role']}) | Culture={p['culture']} | Alignment={p.get('alignment', 'Pragmatic')} | Magic={p.get('magic_affinity', 'Null')}")
        print(f"      Traits: {', '.join(p['traits'])}")
        print(f"      Stats: Might={p['stats']['Might']} Endur={p['stats']['Endurance']} Reflex={p['stats']['Reflex']} Vital={p['stats']['Vitality']} Fort={p['stats']['Fortitude']}")
        print(f"             Knowl={p['stats']['Knowledge']} Logic={p['stats']['Logic']} Aware={p['stats']['Awareness']} Intu={p['stats']['Intuition']} Charm={p['stats']['Charm']} Will={p['stats']['Willpower']}")
        if p.get("recent_decisions"):
            print(f"      Recent Decision: {p['recent_decisions'][-1]}")
            
    print(f"    State / Active Events: {stats_results['event']}")
    print(f"    Trader Status: {stats_results['trader_status']}")
    print(f"  --- Ecology & Wildlife ---")
    print(f"    Ghost Flower Flora: {stats_results.get('flora_ghost_flower', 0.0):.1f} | Stone-Root Flora: {stats_results.get('flora_stone_root', 0.0):.1f}")
    print(f"    Sky-Grazer Fauna: {stats_results.get('fauna_sky_grazer', 0.0):.1f} | Timber Wolf Fauna: {stats_results.get('fauna_timber_wolf', 0.0):.1f}")
    print(f"    Domestication: Greenhouses={stats_results.get('domestic_greenhouses', 0)} | Orchards={stats_results.get('domestic_orchards', 0)} | Pens={stats_results.get('domestic_pens', 0)} | Kennels (Wolves Trained)={stats_results.get('domestic_kennels', 0)}")


def run_simulation_tick(delta_time_hours):
    """ The Master Loop """
    global SCHEDULER_PRISONS, SCHEDULER_DIPLOMACY, SCHEDULER_FRINGE_GROUPS
    cal = CalendarManager()
    current_day = get_day_from_db()
    groups = get_all_macro_groups()

    print("\n--- WEATHER & OCEANIC SYSTEMS ---")
    weather = calculate_weather(0.5, 0.5) # Using dummy value for example
    print(f"Weather generated: {len(weather.get('regions', []))} regions updated.")
    
    ocean_results = run_oceanic_tick(delta_time_hours, groups)
    print(f"Tide Strength: {ocean_results['metrics']['tide_strength']:.2f} | Water Quality: {ocean_results['metrics']['water_quality']:.2f}")
    for log in ocean_results['logs']:
        print(f"  {log}")

    print("\n--- AI EXPANSION & EMPIRE BUILDING ---")
    global _GLOBAL_TRADE_ROUTES
    expansion_logs, routes, wealth_bonus, ruined_penalty = run_expansion_tick(groups, _GLOBAL_GRID)
    _GLOBAL_TRADE_ROUTES = routes
    
    # Store bonuses for next wellbeing tick
    for g in groups:
        g.hub_wealth = wealth_bonus.get(g.id, 0)
        g.ruined_hub_penalty = ruined_penalty.get(g.id, 0)
        
    for log in expansion_logs:
        print(f"  {log}")

    print("\n--- GLOBAL ECOLOGY ---")
    from ecology_system import process_global_ecology_tick
    global _GLOBAL_ECOLOGY_GRID
    process_global_ecology_tick(_GLOBAL_ECOLOGY_GRID, "Clear")
    print(f"Ecology cellular automata processed for {len(_GLOBAL_ECOLOGY_GRID)} cells.")

    # 1. Physics & Chaos Processing
    for group in groups:
        season_mod = cal.apply_seasonal_modifier("Forest", current_day)
        reality_mod = calculate_reality_spike(group.magistar_id, group.is_active)
        is_oceanic = group.name in ["Theocracy", "Meridian Chain", "Sciute"]
        weather = calculate_weather(group.chaos_level, group.pressure, group.magistar_id, is_oceanic)

        torque = calculate_torque(group.geom)

        # Prepare dictionary for process_living_world_tick
        g_dict = {
            "id": group.id,
            "name": group.name,
            "population": group.population,
            "chaos_level": group.chaos_level,
            "pressure": group.pressure,
            "magistar_id": group.magistar_id,
            "is_active": group.is_active,
            "physical_well_being": group.physical_well_being,
            "mental_well_being": group.mental_well_being,
            "crime_level": group.crime_level,
            "discontent": group.discontent,
            "camps_count": group.camps_count,
            "mines_count": group.mines_count,
            "docks_count": group.docks_count,
            "farms_count": group.farms_count,
            "watchtowers_count": group.watchtowers_count,
            "walls_count": group.walls_count,
            "barracks_count": group.barracks_count,
            "kelp_farms_count": group.kelp_farms_count,
            "underwater_domes_count": group.underwater_domes_count,
            "coral_mines_count": group.coral_mines_count,
            "reef_walls_count": group.reef_walls_count,
            "cult_infiltration": group.cult_infiltration,
            "cult_population": group.cult_population,
            "cult_devoted": group.cult_devoted,
            "distance_to_chaos_structure": group.distance_to_chaos_structure,
            "distance_to_convergence": group.distance_to_convergence,
            "flora_ghost_flower": group.flora_ghost_flower,
            "flora_stone_root": group.flora_stone_root,
            "fauna_sky_grazer": group.fauna_sky_grazer,
            "fauna_timber_wolf": group.fauna_timber_wolf,
            "domestic_greenhouses": group.domestic_greenhouses,
            "domestic_orchards": group.domestic_orchards,
            "domestic_pens": group.domestic_pens,
            "domestic_kennels": group.domestic_kennels,
            "churches_count": group.churches_count,
            "theatres_count": group.theatres_count,
            "arenas_count": group.arenas_count,
            "gambling_dens_count": group.gambling_dens_count,
            "black_markets_count": group.black_markets_count,
            "paragon": group.paragon
        }

        stats = process_well_being_tick(
            g_dict,
            group.buildings,
            group.chaos_level,
            hub_wealth_bonus=getattr(group, "hub_wealth", 0),
            ruined_hub_penalty=getattr(group, "ruined_hub_penalty", 0)
        )

        tick_result = process_living_world_tick(
            g_dict, 
            group.inventory, 
            current_day, 
            season_mod, 
            reality_mod, 
            weather, # pass full weather dictionary
            prisons=SCHEDULER_PRISONS,
            resource_nodes=get_global_resource_nodes()
        )

        # Update the DummyMacroGroup object
        group.population = tick_result["population"]
        group.physical_well_being = tick_result["physical_well_being"]
        group.mental_well_being = tick_result["mental_well_being"]
        group.crime_level = tick_result["crime_level"]
        group.discontent = tick_result["discontent"]
        group.inventory = tick_result["inventory"]
        group.cult_infiltration = tick_result["cult_infiltration"]
        group.cult_population = tick_result["cult_population"]
        group.cult_devoted = tick_result["cult_devoted"]
        group.farms_count = g_dict["farms_count"]
        group.watchtowers_count = g_dict["watchtowers_count"]
        group.barracks_count = g_dict["barracks_count"]
        group.mines_count = g_dict["mines_count"]
        group.walls_count = g_dict["walls_count"]
        group.camps_count = g_dict["camps_count"]
        group.docks_count = g_dict["docks_count"]
        group.kelp_farms_count = g_dict["kelp_farms_count"]
        group.underwater_domes_count = g_dict["underwater_domes_count"]
        group.coral_mines_count = g_dict["coral_mines_count"]
        group.reef_walls_count = g_dict["reef_walls_count"]
        group.churches_count = tick_result["churches_count"]
        group.theatres_count = tick_result["theatres_count"]
        group.arenas_count = tick_result["arenas_count"]
        group.gambling_dens_count = tick_result["gambling_dens_count"]
        group.black_markets_count = tick_result["black_markets_count"]
        
        # Leader / Paragon update back
        group.paragon = tick_result.get("paragon")
        
        # Update ecology variables back
        group.flora_ghost_flower = tick_result["flora_ghost_flower"]
        group.flora_stone_root = tick_result["flora_stone_root"]
        group.fauna_sky_grazer = tick_result["fauna_sky_grazer"]
        group.fauna_timber_wolf = tick_result["fauna_timber_wolf"]

        # Update domestic facilities back
        group.domestic_greenhouses = tick_result["domestic_greenhouses"]
        group.domestic_orchards = tick_result["domestic_orchards"]
        group.domestic_pens = tick_result["domestic_pens"]
        group.domestic_kennels = tick_result["domestic_kennels"]
        
        SCHEDULER_PRISONS = tick_result["prisons"]

        if weather.get("is_chaos_charged"):
            log_saga_event("⚡ CHAOS CHARGE", f"A storm cell became charged with chaos in {group.name}, converging on {weather.get('destination_prison')} Prison!")

        # Handle Secret Cult Network spread to adjacent factions
        if tick_result.get("spread_target"):
            target_name, amount = tick_result["spread_target"]
            for target_g in groups:
                if target_g.name == target_name:
                    target_g.cult_population = min(target_g.population, target_g.cult_population + amount)
                    target_g.cult_infiltration = target_g.cult_population / max(1.0, target_g.population)
                    log_saga_event("🕸️ CULT SPREAD", f"Secret cult network branched from {group.name} into {target_name}, seeding {amount} cultists.")

        # Scale individual settlement populations
        scale_ratio = group.population / max(1.0, sum(group.settlement_populations))
        group.settlement_populations = [pop * scale_ratio for pop in group.settlement_populations]

        tech_level = calculate_tech_level(group.settlement_populations)
        unlocked_transports = get_unlocked_transport(tech_level)
        unlocked_buildings = get_unlocked_buildings(tech_level)

        # 3. Update Database / Log
        update_group_state(
            group.id, 
            name=group.name,
            population=group.population, 
            weather=weather['type'],
            tech_level=tech_level,
            transports=unlocked_transports,
            buildings=unlocked_buildings,
            stats_results=tick_result
        )

        for log_msg in tick_result["logs"]:
            log_saga_event("SAGA DETAIL", f"{group.name}: {log_msg}")

    # Process Inter-Faction Diplomacy
    groups_by_name = {g.name: g.__dict__ for g in groups}
    diplomacy_logs = []
    process_diplomacy_tick(SCHEDULER_DIPLOMACY, groups_by_name, diplomacy_logs)
    
    # Process Global Trade and Conflict
    global _GLOBAL_TERRITORY_CHANGES
    from modules.rules_engine import process_global_trade_and_conflict
    process_global_trade_and_conflict(groups, expansion_logs, get_global_resource_nodes(), _GLOBAL_TERRITORY_CHANGES)
    for log_msg in diplomacy_logs:
        log_saga_event("DIPLOMACY", log_msg)

    # Process Fringe Group Operations
    fringe_logs = []
    process_fringe_tick(SCHEDULER_FRINGE_GROUPS, groups_by_name, SCHEDULER_DIPLOMACY, fringe_logs)
    for log_msg in fringe_logs:
        log_saga_event("FRINGE_OPS", log_msg)

    # Global Convergence void drain of shattered moon leakage
    avg_seal = sum(SCHEDULER_PRISONS[name] for name in [
        "Tiraton", "Stagus", "Metrion", "Aurgenas", "Vecelo", "Lophex", 
        "Tyrustis", "Opecten", "Carulkem", "Termhill", "Virantor", "Gavusrix"
    ]) / 12.0
    if avg_seal < 0.75:
        for group in groups:
            proximity_mult = 1.0 - group.distance_to_chaos_structure
            group.chaos_level = min(1.0, group.chaos_level + 0.04 * proximity_mult)
            group.pressure = min(1.0, group.pressure + 0.04 * proximity_mult)
        log_saga_event("CONVERGENCE SURGE", f"Convergence average prison seal integrity at {avg_seal * 100:.0f}%. Chaos surging globally!")
    else:
        log_saga_event("CONVERGENCE", f"Void drain draining shattered moon leakage efficiently at {avg_seal * 100:.0f}% capacity.")

    # Warden natural selection decay & recruitment step
    warden_recruits = SCHEDULER_PRISONS.get("warden_recruits_accumulated", 0.0)
    warden_decay = SCHEDULER_PRISONS.get("warden_population", 1500.0) * 0.08
    SCHEDULER_PRISONS["warden_population"] = max(0.0, SCHEDULER_PRISONS.get("warden_population", 1500.0) - warden_decay + warden_recruits)
    # Reset accumulator
    SCHEDULER_PRISONS["warden_recruits_accumulated"] = 0.0
    
    log_saga_event("WARDEN TELEMETRY", f"🛡️ Grey Warden Population: {SCHEDULER_PRISONS['warden_population']:.2f} (-{warden_decay:.2f} decay, +{warden_recruits:.2f} recruits)")

    # Clean up depleted resource nodes
    global _GLOBAL_RESOURCE_NODES
    depleted = [n for n in _GLOBAL_RESOURCE_NODES if n.get("yield_remaining", 1) <= 0]
    for d in depleted:
        log_saga_event("NODE DEPLETED", f"The {d['name']} has been completely mined out and collapses!")
    _GLOBAL_RESOURCE_NODES = [n for n in _GLOBAL_RESOURCE_NODES if n.get("yield_remaining", 1) > 0]

    # Dynamic Dragonstone Meteor Strikes
    if avg_seal < 0.85 and random.random() < 0.15: # 15% chance if seals are weakening
        if _GLOBAL_GRID and len(_GLOBAL_GRID) > 0:
            row = random.choice(_GLOBAL_GRID)
            if row and len(row) > 0:
                cell = random.choice(row)
                c_id = cell.get('i')
                fid = cell.get('factionId')
                if c_id is not None:
                    _GLOBAL_RESOURCE_NODES.append({
                        "cell": c_id,
                        "faction_id": fid,
                        "icon": "🔮",
                        "name": "Dragonstone Crater",
                        "desc": "Fresh meteor strike! Yields Dragonstone.",
                        "yield_remaining": random.randint(30, 80),
                        "is_discovered": True # Meteors are loud, instantly discovered
                    })
                    log_saga_event("METEOR STRIKE", f"☄️ A chunk of the Shattered Moon crashed into the map, creating a fresh Dragonstone Crater! (Cell: {c_id})")

    # 4. Finalize
    log_saga_event("Tick Complete", f"World rotated and pressure adjusted for day {current_day}")

def debug_test_run():
    run_simulation_tick(1)

if __name__ == "__main__":
    debug_test_run()
