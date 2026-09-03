# map_generator.py
import numpy as np
import os
import json
import random
import sys
import networkx as nx
from scipy.spatial import Voronoi
from shapely.geometry import Polygon, box
from database import get_db_connection, init_db, DB_PATH

# Ensure modules directory is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

from rules_engine import generate_paragon
from ecology_system import initialize_global_cell
from diplomacy_system import initialize_diplomacy
from fringe_system import initialize_fringe_groups

# Standard 17 Ostraka Faction Names in order of Lore
FACTION_NAMES = [
    "Ursine Hegemony",
    "River Folk",
    "Sump-Kin",
    "Iron Caladrea",
    "Vaneer Concord",
    "Hive Collective",
    "Avians",
    "Flower Valwey",
    "Sylvian",
    "Sciute",
    "Meridian Chain",
    "Prism Lizards",
    "Canopy Clans",
    "East Hounds",
    "Guirrilla Clans",
    "Theocracy",
    "The Reliance"
]

# 12 Traitor Anchor Prisons
PRISON_NAMES = [
    "Tiraton", "Stagus", "Metrion", "Aurgenas", "Vecelo", "Lophex",
    "Tyrustis", "Opecten", "Carulkem", "Termhill", "Virantor", "Gavusrix"
]

# Fringe Groups
FRINGE_NAMES = [
    "Obsidian Cartel", "Freesky Barons", "Ghost Wind Raiders", "Gilded Compass",
    "Crimson Coursairs", "Silent Current", "The Black Label", "The Otter Syndicate",
    "The Spring Ghosts"
]

def serialize_diplomacy(diplomacy):
    """Converts diplomacy dict (which has tuple keys in relations) to JSON string safely."""
    if not diplomacy:
        return "{}"
    ser_relations = {}
    for (f1, f2), val in diplomacy.get("relations", {}).items():
        ser_relations[f"{f1},{f2}"] = val
    data = dict(diplomacy)
    data["relations"] = ser_relations
    return json.dumps(data)

def map_biome(biome_id, elevation=0.0):
    """Maps Azgaar FMG biome integer IDs and elevation to our standard biome names."""
    if elevation < 0:
        # Determine ocean subaquatic biome based on elevation depth
        if elevation >= -0.15:
            return 'Coastal'
        elif elevation >= -0.4:
            return 'Reef'
        elif elevation >= -0.75:
            return 'Ocean'
        else:
            # Deep ocean: small chance of Thermal Vent, else Abyssal
            return 'Abyssal'
    
    # Land biomes
    if biome_id == 0:
        return 'Ocean'
    elif biome_id == 4:
        return 'Plains'
    elif biome_id in (5, 6, 7, 8, 9):
        return 'Forest'
    elif biome_id in (10, 11):
        return 'Mountain'
    elif biome_id == 12:
        return 'Swamp'
    elif biome_id == 1: # Hot desert
        return 'Desert'
    elif biome_id == 2: # Cold desert
        return 'Desert'
    elif biome_id == 3: # Savanna
        return 'Plains'
    else:
        return 'Plains'

def import_ostraka_map():
    """
    Imports the actual Ostraka GeoJSON map data into the SQLite database.
    Normalizes coordinates to [0, 100] range while keeping the aspect ratio.
    Seeds the 17 factions, including subaquatic territories for ocean factions.
    Seeds the 12 Traitor Anchor Prisons and precomputes the chaos spiral.
    Initializes all detailed simulation fields (Paragons, Cults, Ecology, etc.).
    """
    print("Importing Ostraka map data with complete simulation settings...")
    
    # 1. Locate GeoJSON files
    fmg_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Fantasy-Map-Generator-master')
    geojson_path = os.path.join(fmg_dir, 'OSTRAKA Cells 2026-06-01-07-50.geojson')
    
    if not os.path.exists(geojson_path):
        print(f"Error: Ostraka cells GeoJSON not found at {geojson_path}.")
        return False
        
    # Remove existing DB file to ensure schema updates take effect
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print("Removed old database file for clean schema setup.")
        except Exception as e:
            print(f"Warning: Could not remove old database: {e}")
            
    # Initialize fresh database tables
    init_db()
    
    # Load GeoJSON
    with open(geojson_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    features = data.get("features", [])
    print(f"Loaded {len(features)} cells from GeoJSON.")
    
    # Bounding box coordinates from original inspection
    min_x = -182.3182
    max_x = 180.8182
    min_y = -92.3182
    max_y = 92.1818
    scale = 100.0 / 363.1364  # Scale factor based on X range
    
    cell_rows = []
    edges = []
    land_cells = []
    ocean_cells = []
    cell_centroids = {} # cell_id -> (cx, cy)
    state_cell_pops = {} # state_id -> list of (cell_id, population)
    
    # Seed 12 Prisons cell IDs
    anchors = [
        (50.0, 1.0),                  # North Pole
        (50.0, 49.8),                 # South Pole
        # Upper Row (Y = 17.8)
        (10.0, 17.8), (30.0, 17.8), (50.0, 17.8), (70.0, 17.8), (90.0, 17.8),
        # Lower Row (Y = 33.0)
        (20.0, 33.0), (40.0, 33.0), (60.0, 33.0), (80.0, 33.0), (100.0, 33.0)
    ]
    
    # We first collect centroids to find closest cells for prisons
    for f in features:
        props = f["properties"]
        geom = f["geometry"]
        cell_id = int(props["id"])
        
        if geom["type"] == "Polygon":
            exterior = geom["coordinates"][0]
        elif geom["type"] == "MultiPolygon":
            exterior = max(geom["coordinates"], key=lambda c: len(c[0]))[0]
        else:
            continue
            
        norm_coords = []
        for pt in exterior:
            norm_x = (pt[0] - min_x) * scale
            norm_y = (pt[1] - min_y) * scale
            norm_coords.append((norm_x, norm_y))
            
        poly = Polygon(norm_coords)
        cx, cy = poly.centroid.x, poly.centroid.y
        cell_centroids[cell_id] = (cx, cy)

    # Determine prison cells
    prison_cell_ids = []
    prison_names_by_id = {}
    for idx, (px, py) in enumerate(anchors):
        closest_id = min(cell_centroids.keys(), key=lambda cid: np.hypot(cell_centroids[cid][0] - px, cell_centroids[cid][1] - py))
        prison_cell_ids.append(closest_id)
        prison_names_by_id[closest_id] = PRISON_NAMES[idx]

    # Find center cell
    center_cell_id = min(cell_centroids.keys(), key=lambda cid: np.hypot(cell_centroids[cid][0] - 50.0, cell_centroids[cid][1] - 25.4))

    # 2. Parse Cells
    for f in features:
        props = f["properties"]
        geom = f["geometry"]
        cell_id = int(props["id"])
        
        if geom["type"] == "Polygon":
            exterior = geom["coordinates"][0]
        elif geom["type"] == "MultiPolygon":
            exterior = max(geom["coordinates"], key=lambda c: len(c[0]))[0]
        else:
            continue
            
        norm_coords = []
        for pt in exterior:
            norm_x = (pt[0] - min_x) * scale
            norm_y = (pt[1] - min_y) * scale
            norm_coords.append((norm_x, norm_y))
            
        poly = Polygon(norm_coords)
        wkt = poly.wkt
        cx, cy = cell_centroids[cell_id]
        
        biome_id = props.get("biome", 0)
        height = props.get("height", 0)
        
        # Normalize height
        if height < 0:
            elevation = float(height / 3248.0)
        else:
            elevation = float(height / 22061.0)
            
        biome = map_biome(biome_id, elevation)
        
        # Random Thermal Vent designation for abyssal cells
        if biome == 'Abyssal' and random.random() < 0.05:
            biome = 'Thermal'
            
        is_land = elevation >= 0
        state_id = int(props.get("state", 0))
        pop = int(props.get("population", 0))
        
        # Initialize cell religions/cults influence
        cults_influence = {prison: 0.0 for prison in PRISON_NAMES}
        cults_influence["Wardens"] = 0.0
        
        # Seed dominant cult based on geographical proximity to its prison anchor
        closest_prison_id = min(prison_cell_ids, key=lambda pid: np.hypot(cx - cell_centroids[pid][0], cy - cell_centroids[pid][1]))
        closest_prison_name = prison_names_by_id[closest_prison_id]
        dist_to_prison = np.hypot(cx - cell_centroids[closest_prison_id][0], cy - cell_centroids[closest_prison_id][1])
        
        # Cult influence decays with distance from prison
        cult_inf = max(0.01, min(0.30, 0.40 - (dist_to_prison / 30.0)))
        cults_influence[closest_prison_name] = round(cult_inf, 3)
        cults_influence["Wardens"] = round(max(0.01, min(0.25, 0.30 - (dist_to_prison / 25.0))), 3)
        
        # Initialize fringe groups influence
        fringe_influence = {fringe: 0.0 for fringe in FRINGE_NAMES}
        if biome in ['Ocean', 'Coastal', 'Reef', 'Abyssal', 'Thermal']:
            fringe_influence["Silent Current"] = 0.15
            fringe_influence["Crimson Coursairs"] = 0.05
        elif biome == 'Mountain':
            fringe_influence["Freesky Barons"] = 0.20
            fringe_influence["Ghost Wind Raiders"] = 0.08
        elif biome == 'Swamp':
            fringe_influence["The Otter Syndicate"] = 0.18
        else:
            fringe_influence["Obsidian Cartel"] = 0.05
            fringe_influence["Gilded Compass"] = 0.05
            
        # Initialize cell cellular ecology
        cell_eco = {"id": cell_id, "biome": biome_id, "state": state_id, "x": cx, "y": cy}
        state_name = FACTION_NAMES[state_id - 1] if 1 <= state_id <= 17 else "Neutrals"
        initialize_global_cell(cell_eco, state_name)
        
        flora_json = json.dumps({"name": cell_eco.get("flora", "flora_stone_root"), "population": cell_eco.get("flora_pop", 50.0)})
        fauna_json = json.dumps({"name": cell_eco.get("fauna", "fauna_timber_wolf"), "population": cell_eco.get("fauna_pop", 20.0)})
        
        if is_land:
            land_cells.append({
                'id': cell_id,
                'state': state_id,
                'pop': pop,
                'center': (cx, cy),
                'biome': biome,
                'elevation': elevation,
                'flora_json': flora_json,
                'fauna_json': fauna_json,
                'cults_json': json.dumps(cults_influence),
                'fringe_json': json.dumps(fringe_influence)
            })
            if state_id > 0:
                if state_id not in state_cell_pops:
                    state_cell_pops[state_id] = []
                state_cell_pops[state_id].append((cell_id, pop))
        else:
            ocean_cells.append({
                'id': cell_id,
                'state': state_id,
                'pop': pop,
                'center': (cx, cy),
                'biome': biome,
                'elevation': elevation,
                'flora_json': flora_json,
                'fauna_json': fauna_json,
                'cults_json': json.dumps(cults_influence),
                'fringe_json': json.dumps(fringe_influence)
            })
            if state_id > 0:
                if state_id not in state_cell_pops:
                    state_cell_pops[state_id] = []
                state_cell_pops[state_id].append((cell_id, pop))
                
        # Record cell details for bulk insertion
        cell_rows.append((
            cell_id,
            biome,
            elevation,
            elevation,      # depth_elevation = elevation
            wkt,
            0.5,            # food_supply
            0.0,            # chaos_saturation
            'Clear',        # weather
            0.0,            # chaos_base_modifier
            0,              # controlling_burg_id
            json.dumps(cults_influence),
            json.dumps(fringe_influence),
            flora_json,
            fauna_json
        ))
        
        for nb in props.get("neighbors", []):
            nb_id = int(nb)
            if cell_id < nb_id:
                edges.append((cell_id, nb_id))
                
    # 3. Determine Faction Assignments & Capitals
    faction_capitals = {}
    for state_id, cell_pops in state_cell_pops.items():
        if 1 <= state_id <= 17:
            capital_cell = max(cell_pops, key=lambda x: x[1])[0]
            faction_capitals[state_id] = capital_cell
            
    # Seed factions 11 to 17 on land or water cells that are currently state 0 (Neutrals)
    rng = np.random.default_rng(42)
    
    unoccupied_land = [c for c in land_cells if c['state'] == 0]
    unoccupied_land_ids = [c['id'] for c in unoccupied_land]
    
    unoccupied_water = [c for c in ocean_cells if c['state'] == 0]
    unoccupied_water_ids = [c['id'] for c in unoccupied_water]
    
    for fid in range(11, 18):
        if fid in [11, 16]: # Oceanic/coastal
            chosen = rng.choice(unoccupied_water_ids)
            faction_capitals[fid] = int(chosen)
            for c in ocean_cells:
                if c['id'] == chosen:
                    c['state'] = fid
        else: # Land
            chosen = rng.choice(unoccupied_land_ids)
            faction_capitals[fid] = int(chosen)
            for c in land_cells:
                if c['id'] == chosen:
                    c['state'] = fid
                    
    # Determine which cells contain a settlement (macro group)
    # Start with capitals
    settlement_cell_ids = set(faction_capitals.values())
    all_seeded_cells = land_cells + ocean_cells
    
    # Sort all cells by population in descending order and choose top 100 major settlement hubs
    sorted_cells = sorted(all_seeded_cells, key=lambda c: c['pop'], reverse=True)
    for c in sorted_cells[:100]:
        settlement_cell_ids.add(c['id'])
            
    # Re-map controlling settlements (Province Areas)
    cell_controlling_burg = {scid: scid for scid in settlement_cell_ids}
    visited_cells = set(settlement_cell_ids)
    queue = list(settlement_cell_ids)
    
    adj = {cid: [] for cid in cell_centroids.keys()}
    for ca, cb in edges:
        adj[ca].append(cb)
        adj[cb].append(ca)
        
    idx = 0
    while idx < len(queue):
        curr = queue[idx]
        idx += 1
        burg_id = cell_controlling_burg[curr]
        for nb in adj.get(curr, []):
            if nb not in visited_cells:
                visited_cells.add(nb)
                cell_controlling_burg[nb] = burg_id
                queue.append(nb)
                
    # Update cell rows with controlling_burg_id
    updated_cell_rows = []
    for row in cell_rows:
        cid = row[0]
        burg_id = cell_controlling_burg.get(cid, cid)
        row_list = list(row)
        row_list[9] = burg_id
        updated_cell_rows.append(tuple(row_list))
    cell_rows = updated_cell_rows

    # 4. Generate Macro Groups (Settlements / Populations) only for settlement cells
    macro_group_rows = []
    neutral_id_counter = 18
    
    settlement_mg_ids = {}
    for fid, cap_cell_id in faction_capitals.items():
        settlement_mg_ids[cap_cell_id] = fid
        
    inventory_template = {
        "Wealth": 50.0, "Lumber": 50.0, "Stone": 50.0, "Iron Ore": 10.0, "Copper Ore": 5.0,
        "Coal": 10.0, "Grain": 200.0, "Leather": 10.0, "Dragonstone": 2.0, "Voltaic Fleece": 0.0,
        "Ozone-Milk": 0.0, "Ghost Flower": 0.0, "Night-Nectar": 0.0, "Flour": 0.0, "Peak-Cheese": 0.0,
        "Smelted Steel": 0.0, "Copper Wire": 0.0, "Refined Aether Battery": 0.0, "Tanned Strips": 0.0,
        "Ostrakan Hardtack": 5.0, "Caldera Spark-Bread": 0.0, "Basic Weapons": 50.0,
        "Aether-Wright PPE": 0.0, "Silk-Steel Cables": 0.0, "Leather Armor": 50.0, "Rope": 0.0,
        "Coral": 0.0, "Kelp": 0.0, "Whale Oil": 0.0
    }
    
    for c in all_seeded_cells:
        cell_id = c['id']
        if cell_id not in settlement_cell_ids:
            continue
            
        if cell_id in settlement_mg_ids:
            mg_id = settlement_mg_ids[cell_id]
        else:
            mg_id = neutral_id_counter
            settlement_mg_ids[cell_id] = mg_id
            neutral_id_counter += 1
            
        state_id = c['state']
        pop = c['pop']
        biome = c['biome']
        elevation = c['elevation']
        
        is_capital = (cell_id in faction_capitals.values())
        assigned_faction_id = 0
        assigned_faction_name = 'Neutrals'
        
        if 1 <= state_id <= 17:
            assigned_faction_id = state_id
            assigned_faction_name = FACTION_NAMES[state_id - 1]
            
        paragon_role = "Ruler" if is_capital else ("Mayor" if pop > 1000 else "Captain")
        paragon_dict = generate_paragon(assigned_faction_name, [], role=paragon_role)
        
        is_aquatic = elevation < 0
        
        farms = 0
        kelp_farms = 0
        mines = 0
        coral_mines = 0
        camps = 0
        underwater_domes = 0
        walls = 0
        reef_walls = 0
        barracks = 0
        watchtowers = 0
        docks = 0
        
        mg_pop = max(100, pop)
        if is_capital:
            mg_pop = max(1000, pop)
            barracks = 1
            watchtowers = 1
            docks = 1
            if is_aquatic:
                kelp_farms = 1
                underwater_domes = 1
                reef_walls = 1
            else:
                farms = 1
                camps = 1
                walls = 1
        else:
            # Seed basic structures for town
            if is_aquatic:
                kelp_farms = 1 if random.random() < 0.5 else 0
            else:
                farms = 1 if random.random() < 0.5 else 0
            
        closest_prison_id = min(prison_cell_ids, key=lambda pid: np.hypot(cell_centroids[cell_id][0] - cell_centroids[pid][0], cell_centroids[cell_id][1] - cell_centroids[pid][1]))
        magistar_name = prison_names_by_id[closest_prison_id]
        
        cults_data = json.loads(c['cults_json'])
        dominant_cult_pop = mg_pop * cults_data.get(magistar_name, 0.05)
        dominant_cult_dev = dominant_cult_pop * 0.20
        
        settlements_list = [int(mg_pop * 0.7), int(mg_pop * 0.2), int(mg_pop * 0.1)]
        
        macro_group_rows.append((
            mg_id,
            cell_id,
            assigned_faction_id,
            assigned_faction_name,
            1 if is_capital else 0,
            0.0,            # chaos_level
            mg_pop,
            0.0,            # discontent
            0.0,            # crime_level
            0.5,            # food_supply
            1.0,            # physical_well_being
            1.0,            # mental_well_being
            0.5,            # safety_rating
            camps,
            mines,
            farms,
            barracks,
            watchtowers,
            0.0,            # pressure
            magistar_name,
            1,              # is_active
            0.0,            # distance_to_chaos_structure
            0.0,            # distance_to_convergence
            docks,
            walls,
            kelp_farms,
            underwater_domes,
            coral_mines,
            reef_walls,
            cults_data.get(magistar_name, 0.05),
            dominant_cult_pop,
            dominant_cult_dev,
            cults_data.get("flora_ghost_flower", 100.0),
            cults_data.get("flora_stone_root", 100.0),
            cults_data.get("fauna_sky_grazer", 50.0),
            cults_data.get("fauna_timber_wolf", 10.0),
            0,              # domestic_greenhouses
            0,              # domestic_orchards
            0,              # domestic_pens
            0,              # domestic_kennels
            0,              # churches_count
            0,              # theatres_count
            0,              # arenas_count
            0,              # gambling_dens_count
            0,              # black_markets_count
            0,              # workshops_count
            json.dumps(settlements_list),
            json.dumps(paragon_dict),
            json.dumps(inventory_template),
            0.0,            # hub_wealth
            0.0             # ruined_hub_penalty
        ))

    # 5. Seed the 12 Traitor Anchor Prisons
    prison_rows = []
    for idx, pid in enumerate(prison_cell_ids):
        cx, cy = cell_centroids[pid]
        prison_rows.append((idx + 1, pid, cx, cy, 1.0))

    # 6. Seed Hard Resource Nodes
    resource_nodes_rows = []
    geological_nodes = [
        {"name": "Luminescent Coral Mine", "icon": "🪸", "desc": "Yields Coral", "yield_range": (100, 300), "weight_water": 10, "weight_land": 0},
        {"name": "Ancient Steel Ruins", "icon": "⚔️", "desc": "Yields Smelted Steel", "yield_range": (50, 150), "weight_water": 1, "weight_land": 8},
        {"name": "Rich Iron Vein", "icon": "🪨", "desc": "Yields Iron", "yield_range": (200, 500), "weight_water": 0, "weight_land": 10},
        {"name": "Rich Copper Vein", "icon": "🟠", "desc": "Yields Copper", "yield_range": (200, 500), "weight_water": 0, "weight_land": 10},
        {"name": "Rich Nickel Vein", "icon": "🪨", "desc": "Yields Nickel", "yield_range": (200, 500), "weight_water": 1, "weight_land": 9},
        {"name": "Deep-Earth Geode", "icon": "💎", "desc": "Yields Crystal Chips", "yield_range": (50, 200), "weight_water": 4, "weight_land": 6},
        {"name": "Dragonstone Crater", "icon": "🔮", "desc": "Yields Dragonstone", "yield_range": (20, 60), "weight_water": 2, "weight_land": 2},
        # 12 Conductors
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
    
    faction_cell_lists = {fid: {"water": [], "land": []} for fid in range(1, 18)}
    for row in cell_rows:
        cid, biome, elev = row[0], row[1], row[2]
        matching_cell = next((c for c in all_seeded_cells if c['id'] == cid), None)
        if matching_cell:
            fid = matching_cell['state']
            if 1 <= fid <= 17:
                if elev < 0:
                    faction_cell_lists[fid]["water"].append(cid)
                else:
                    faction_cell_lists[fid]["land"].append(cid)
                    
    node_id_counter = 1
    for fid, cells in faction_cell_lists.items():
        if cells["water"]:
            c_id = random.choice(cells["water"])
            pool = [n for n in geological_nodes if n["weight_water"] > 0]
            weights = [n["weight_water"] for n in pool]
            res = random.choices(pool, weights=weights, k=1)[0]
            resource_nodes_rows.append((
                node_id_counter, c_id, fid, res["name"], res["icon"],
                res["desc"], float(random.randint(res["yield_range"][0], res["yield_range"][1])), 0
            ))
            node_id_counter += 1
            
        if cells["land"]:
            c_id = random.choice(cells["land"])
            pool = [n for n in geological_nodes if n["weight_land"] > 0]
            weights = [n["weight_land"] for n in pool]
            res = random.choices(pool, weights=weights, k=1)[0]
            resource_nodes_rows.append((
                node_id_counter, c_id, fid, res["name"], res["icon"],
                res["desc"], float(random.randint(res["yield_range"][0], res["yield_range"][1])), 0
            ))
            node_id_counter += 1

    # 7. Insert everything into the Database
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Bulk insert cells
    cur.executemany('''
        INSERT INTO cells (id, biome, elevation, depth_elevation, geom_wkt, food_supply, chaos_saturation, weather, chaos_base_modifier, controlling_burg_id, cults_json, fringe_json, flora_json, fauna_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', cell_rows)
    
    # Bulk insert edges
    cur.executemany('''
        INSERT INTO cell_edges (cell_a, cell_b)
        VALUES (?, ?)
    ''', edges)
    
    # Bulk insert macro groups (Factions & Neutrals)
    cur.executemany('''
        INSERT INTO macro_groups (id, cell_id, faction_id, faction_name, is_capital, chaos_level, population, discontent, crime_level, food_supply, physical_well_being, mental_well_being, safety_rating, camps_count, mines_count, farms_count, barracks_count, watchtowers_count, pressure, magistar_id, is_active, distance_to_chaos_structure, distance_to_convergence, docks_count, walls_count, kelp_farms_count, underwater_domes_count, coral_mines_count, reef_walls_count, cult_infiltration, cult_population, cult_devoted, flora_ghost_flower, flora_stone_root, fauna_sky_grazer, fauna_timber_wolf, domestic_greenhouses, domestic_orchards, domestic_pens, domestic_kennels, churches_count, theatres_count, arenas_count, gambling_dens_count, black_markets_count, workshops_count, settlements_json, paragon_json, inventory_json, hub_wealth, ruined_hub_penalty)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', macro_group_rows)
    
    # Bulk insert prisons
    cur.executemany('''
        INSERT INTO dragon_prisons (id, cell_id, x, y, seal_integrity)
        VALUES (?, ?, ?, ?, ?)
    ''', prison_rows)
    
    # Bulk insert resource nodes
    cur.executemany('''
        INSERT INTO resource_nodes (id, cell_id, faction_id, name, icon, description, yield_remaining, is_discovered)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', resource_nodes_rows)

    # Initialize Global State row
    cur.execute('''
        INSERT INTO global_state (id, current_day, warden_population, warden_recruits_accumulated, diplomacy_json, fringe_groups_json, trade_routes_json)
        VALUES (1, 150, 1500.0, 0.0, ?, ?, '[]')
    ''', (serialize_diplomacy(initialize_diplomacy()), json.dumps(initialize_fringe_groups())))
    
    conn.commit()
    cur.close()
    conn.close()
    
    # 8. Precompute Chaos Spiral using NetworkX
    G = nx.Graph()
    G.add_nodes_from(cell_centroids.keys())
    G.add_edges_from(edges)
    
    from systems.spatial_chaos import compute_chaos_spiral, apply_chaos_spiral_to_database
    modifiers = compute_chaos_spiral(G, prison_cell_ids, center_cell_id)
    apply_chaos_spiral_to_database(modifiers)
    
    print(f"Ostraka map loaded successfully: {len(cell_rows)} cells (including ocean), {len(edges)} edges, {len(macro_group_rows)} seeded macro groups, {len(resource_nodes_rows)} Resource Nodes, 12 Prisons.")
    return True

def generate_world(seed: int, num_cells: int = 1000):
    """
    Stub fallback that generates a Voronoi diagram using SciPy.
    Calls import_ostraka_map instead to load the real Ostraka map as requested by the user,
    ensuring we start with the complete 10k cells Ostraka map.
    """
    print("Generate World fallback called. Loading complete Ostraka map instead to satisfy editor requirements...")
    return import_ostraka_map()

if __name__ == '__main__':
    import_ostraka_map()
