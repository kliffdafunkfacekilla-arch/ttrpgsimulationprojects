# map_generator.py
import numpy as np
import os
import json
import networkx as nx
from scipy.spatial import Voronoi
from shapely.geometry import Polygon, box
from database import get_db_connection, init_db, DB_PATH

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

def map_biome(biome_id):
    """Maps Azgaar FMG biome integer IDs to our standard biome names."""
    # 0 -> Marine (Ocean)
    # 4 -> Grassland (Plains)
    # 5, 6, 7, 8, 9 -> Forests (Forest)
    # 10, 11 -> Cold Desert / Glacier / Tundra (Mountain)
    # 12 -> Wetland (Swamp)
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
    Seeds the 17 factions:
      - Factions 1 to 10 are loaded from GeoJSON state IDs 1 to 10.
      - Factions 11 to 17 are seeded on unoccupied land cells.
    Seeds the 12 Traitor Anchor Prisons and precomputes the chaos spiral.
    """
    print("Importing Ostraka map data...")
    
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
    cell_centroids = {} # cell_id -> (cx, cy)
    state_cell_pops = {} # state_id -> list of (cell_id, population)
    
    # 2. Parse Cells
    for f in features:
        props = f["properties"]
        geom = f["geometry"]
        cell_id = int(props["id"])
        
        # Parse and normalize polygon coordinates
        if geom["type"] == "Polygon":
            exterior = geom["coordinates"][0]
        elif geom["type"] == "MultiPolygon":
            # Fallback to largest polygon
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
        
        # Calculate centroid
        cx, cy = poly.centroid.x, poly.centroid.y
        cell_centroids[cell_id] = (cx, cy)
        
        # Biome and elevation
        biome_id = props.get("biome", 0)
        biome = map_biome(biome_id)
        height = props.get("height", 0)
        
        # Normalize height into elevation [-1.0, 1.0]
        if height < 0:
            elevation = float(height / 3248.0)
        else:
            elevation = float(height / 22061.0)
            
        # Add to land list if elevation is land (>= 0)
        is_land = elevation >= 0
        state_id = int(props.get("state", 0))
        pop = int(props.get("population", 0))
        
        if is_land:
            land_cells.append({
                'id': cell_id,
                'state': state_id,
                'pop': pop,
                'center': (cx, cy)
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
            0.0             # chaos_base_modifier
        ))
        
        # Collect edges from neighbors
        for nb in props.get("neighbors", []):
            nb_id = int(nb)
            if cell_id < nb_id:
                edges.append((cell_id, nb_id))
                
    # 3. Determine Faction Assignments & Capitals
    # Find capital cells for factions 1 to 10 (the cell with the maximum population in that state)
    faction_capitals = {} # faction_id -> cell_id
    for state_id, cell_pops in state_cell_pops.items():
        if 1 <= state_id <= 10:
            capital_cell = max(cell_pops, key=lambda x: x[1])[0]
            faction_capitals[state_id] = capital_cell
            
    # Seed factions 11 to 17 on land cells that are currently state 0 (Neutrals)
    rng = np.random.default_rng(42)
    unoccupied_land = [c for c in land_cells if c['state'] == 0]
    unoccupied_land_ids = [c['id'] for c in unoccupied_land]
    
    # Pick 7 starting capitals for factions 11 to 17
    new_capitals = rng.choice(unoccupied_land_ids, size=7, replace=False)
    for idx, cell_id in enumerate(new_capitals):
        faction_id = 11 + idx
        faction_capitals[faction_id] = int(cell_id)
        # Update the state of these picked cells to match the new factions
        for c in land_cells:
            if c['id'] == cell_id:
                c['state'] = faction_id
                
    # Create macro group rows
    macro_group_rows = []
    neutral_id_counter = 18
    
    for c in land_cells:
        cell_id = c['id']
        state_id = c['state']
        pop = c['pop']
        
        # Check if this cell is a capital
        is_capital = False
        assigned_faction_id = 0
        assigned_faction_name = 'Neutrals'
        
        if 1 <= state_id <= 17:
            assigned_faction_id = state_id
            assigned_faction_name = FACTION_NAMES[state_id - 1]
            if faction_capitals.get(state_id) == cell_id:
                is_capital = True
                
        # Determine macro group parameters
        if is_capital:
            # Capital Outpost
            mg_id = assigned_faction_id # Faction ID is their primary key
            mg_pop = max(1000, pop)
            barracks = 1
            watchtowers = 1
            farms = 1
        elif assigned_faction_id > 0:
            # Normal faction cell
            mg_id = neutral_id_counter
            neutral_id_counter += 1
            mg_pop = max(100, pop)
            barracks = 0
            watchtowers = 0
            farms = 0
        else:
            # Unoccupied Neutral cell
            mg_id = neutral_id_counter
            neutral_id_counter += 1
            mg_pop = max(50, pop)
            barracks = 0
            watchtowers = 0
            farms = 0
            
        macro_group_rows.append((
            mg_id,
            cell_id,
            assigned_faction_id,
            assigned_faction_name,
            1 if is_capital else 0, # is_capital
            0.0,            # chaos_level
            mg_pop,
            0.0,            # discontent
            0.0,            # crime_level
            0.5,            # food_supply
            1.0,            # physical_well_being
            1.0,            # mental_well_being
            0.5,            # safety_rating
            0,              # camps_count
            0,              # mines_count
            farms,          # farms_count
            barracks,       # barracks_count
            watchtowers     # watchtowers_count
        ))
        
    # 4. Seed the 12 Traitor Anchor Prisons
    # Placed at specific locations representing the icosahedron anchors
    anchors = [
        (50.0, 1.0),                  # North Pole
        (50.0, 49.8),                 # South Pole
        # Upper Row (Y = 17.8)
        (10.0, 17.8), (30.0, 17.8), (50.0, 17.8), (70.0, 17.8), (90.0, 17.8),
        # Lower Row (Y = 33.0)
        (20.0, 33.0), (40.0, 33.0), (60.0, 33.0), (80.0, 33.0), (100.0, 33.0)
    ]
    
    prison_rows = []
    prison_cell_ids = []
    
    for idx, (px, py) in enumerate(anchors):
        # Find cell closest to (px, py)
        closest_cell_id = min(cell_centroids.keys(), key=lambda cid: np.hypot(cell_centroids[cid][0] - px, cell_centroids[cid][1] - py))
        prison_cell_ids.append(closest_cell_id)
        cx, cy = cell_centroids[closest_cell_id]
        prison_rows.append((idx + 1, closest_cell_id, cx, cy))
        
    # Find center cell (closest to (50.0, 25.4))
    center_cell_id = min(cell_centroids.keys(), key=lambda cid: np.hypot(cell_centroids[cid][0] - 50.0, cell_centroids[cid][1] - 25.4))
    
    # 5. Insert everything into the Database
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Bulk insert cells
    cur.executemany('''
        INSERT INTO cells (id, biome, elevation, depth_elevation, geom_wkt, food_supply, chaos_saturation, weather, chaos_base_modifier)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', cell_rows)
    
    # Bulk insert edges
    cur.executemany('''
        INSERT INTO cell_edges (cell_a, cell_b)
        VALUES (?, ?)
    ''', edges)
    
    # Bulk insert macro groups (Factions & Neutrals)
    cur.executemany('''
        INSERT INTO macro_groups (id, cell_id, faction_id, faction_name, is_capital, chaos_level, population, discontent, crime_level, food_supply, physical_well_being, mental_well_being, safety_rating, camps_count, mines_count, farms_count, barracks_count, watchtowers_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', macro_group_rows)
    
    # Bulk insert prisons
    cur.executemany('''
        INSERT INTO dragon_prisons (id, cell_id, x, y)
        VALUES (?, ?, ?, ?)
    ''', prison_rows)
    
    conn.commit()
    cur.close()
    conn.close()
    
    # 6. Precompute Chaos Spiral using NetworkX
    G = nx.Graph()
    G.add_nodes_from(cell_centroids.keys())
    G.add_edges_from(edges)
    
    from systems.spatial_chaos import compute_chaos_spiral, apply_chaos_spiral_to_database
    modifiers = compute_chaos_spiral(G, prison_cell_ids, center_cell_id)
    apply_chaos_spiral_to_database(modifiers)
    
    print(f"Ostraka map loaded successfully: {len(cell_rows)} cells, {len(edges)} edges, {len(macro_group_rows)} land groups, 12 Prisons.")
    return True

def generate_world(seed: int, num_cells: int = 1000):
    """
    Generates a Voronoi diagram using SciPy, constructs WKT polygons for closed cells,
    clips them to the [0, 100] x [0, 100] map boundary, computes cell adjacencies (edges),
    and inserts them into the SQLite database.
    Seeds active faction capitals and populates all other land cells as 'Neutrals'.
    """
    print(f"Generating world with seed {seed} and {num_cells} cells...")
    
    # Remove existing DB file to ensure schema updates take effect
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print("Removed old database file for clean schema setup.")
        except Exception as e:
            print(f"Warning: Could not remove old database: {e}")
            
    # Initialize fresh database tables
    init_db()
    
    rng = np.random.default_rng(seed)
    # Generate points in a 100x100 space
    points = rng.random((num_cells, 2)) * 100
    vor = Voronoi(points)
    
    # Define bounding box for clipping
    bbox = box(0, 0, 100, 100)
    
    # 1. Determine which points correspond to valid (closed) cells
    valid_cells = set()
    cell_rows = []
    
    # Mapping of cell_id (point index) -> polygon coordinates
    for point_idx in range(len(points)):
        region_idx = vor.point_region[point_idx]
        region = vor.regions[region_idx]
        
        # Skip open regions (contain -1 index = extends to infinity)
        if -1 in region or len(region) < 3:
            continue
            
        vertices = vor.vertices[region]
        
        # Build raw shapely polygon and clip it to bounding box
        poly = Polygon(vertices)
        clipped_poly = poly.intersection(bbox)
        
        # Skip if the clipped polygon is empty, invalid, or not a simple Polygon
        if clipped_poly.is_empty or clipped_poly.geom_type != 'Polygon':
            continue
            
        valid_cells.add(point_idx)
        wkt = clipped_poly.wkt
        
        # Determine biome and elevation
        elevation = float(rng.uniform(-1.0, 1.0))
        
        # If elevation is negative, force Ocean biome, else land biomes
        if elevation < 0:
            biome = 'Ocean'
        else:
            biome = rng.choice(['Forest', 'Plains', 'Desert', 'Mountain', 'Swamp'])
            
        cell_rows.append((
            point_idx,      # Use point index as cell ID
            biome,
            elevation,
            elevation,      # depth_elevation = elevation
            wkt,
            0.5,            # default food_supply
            0.0,            # default chaos_saturation
            'Clear',        # default weather
            0.0             # default chaos_base_modifier
        ))
        
    # 2. Extract cell edges (adjacencies) from SciPy Voronoi ridge_points
    edge_rows = []
    for ridge in vor.ridge_points:
        cell_a, cell_b = int(ridge[0]), int(ridge[1])
        # Only add edge if both cells are valid (closed)
        if cell_a in valid_cells and cell_b in valid_cells:
            # Enforce cell_a < cell_b to avoid duplicates
            if cell_a > cell_b:
                cell_a, cell_b = cell_b, cell_a
            edge_rows.append((cell_a, cell_b))
            
    # Remove duplicate edges if any
    edge_rows = list(set(edge_rows))
    
    # 3. Seed initial Factions and Neutrals
    land_cells = [row[0] for row in cell_rows if row[2] >= 0] # ID of land cells
    faction_names = ["Ursine Hegemony", "River Folk", "Sump-Kin", "Iron Caladrea", "Vaneer Concord"]
    
    macro_group_rows = []
    if land_cells and len(land_cells) >= len(faction_names):
        chosen_cells = rng.choice(land_cells, size=len(faction_names), replace=False)
        chosen_set = set(chosen_cells)
        
        # Real factions (faction_id 1 to 5)
        for i, faction_name in enumerate(faction_names):
            cell_id = int(chosen_cells[i])
            macro_group_rows.append((
                i + 1,          # ID (macro_group primary key)
                cell_id,        # cell_id
                i + 1,          # faction_id
                faction_name,   # faction_name
                1,              # is_capital (1 for capital)
                0.0,            # chaos_level
                1000,           # population
                0.0,            # discontent
                0.0,            # crime_level
                0.5,            # food_supply
                1.0,            # physical_well_being
                1.0,            # mental_well_being
                0.5,            # safety_rating
                0,              # camps_count
                0,              # mines_count
                1,              # farms_count
                1,              # barracks_count
                1               # watchtowers_count
            ))
            
        # Neutrals (faction_id = 0) for all other land cells
        neutral_id = len(faction_names) + 1
        for cell_id in land_cells:
            if cell_id not in chosen_set:
                macro_group_rows.append((
                    neutral_id,     # ID (macro_group primary key)
                    cell_id,        # cell_id
                    0,              # faction_id (0 = Neutrals)
                    'Neutrals',     # faction_name
                    0,              # is_capital (0 for non-capital)
                    0.0,            # chaos_level
                    100,            # population
                    0.0,            # discontent
                    0.0,            # crime_level
                    0.5,            # food_supply
                    1.0,            # physical_well_being
                    1.0,            # mental_well_being
                    0.5,            # safety_rating
                    0,              # camps_count
                    0,              # mines_count
                    0,              # farms_count
                    0,              # barracks_count
                    0               # watchtowers_count
                ))
                neutral_id += 1
                
    # 4. Insert into Database
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Truncate tables (redundant if DB file is deleted, but good practice)
    cur.execute('DELETE FROM cells')
    cur.execute('DELETE FROM cell_edges')
    cur.execute('DELETE FROM macro_groups')
    cur.execute('DELETE FROM simulation_logs')
    conn.commit()
    
    # Bulk insert cells
    cur.executemany('''
        INSERT INTO cells (id, biome, elevation, depth_elevation, geom_wkt, food_supply, chaos_saturation, weather, chaos_base_modifier)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', cell_rows)
    
    # Bulk insert edges
    cur.executemany('''
        INSERT INTO cell_edges (cell_a, cell_b)
        VALUES (?, ?)
    ''', edge_rows)
    
    # Bulk insert macro groups (Real Factions & Neutrals)
    if macro_group_rows:
        cur.executemany('''
            INSERT INTO macro_groups (id, cell_id, faction_id, faction_name, is_capital, chaos_level, population, discontent, crime_level, food_supply, physical_well_being, mental_well_being, safety_rating, camps_count, mines_count, farms_count, barracks_count, watchtowers_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', macro_group_rows)
        
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"Generation complete: {len(cell_rows)} cells created, {len(edge_rows)} edges registered, {len(macro_group_rows)} faction/neutral cells seeded.")
    return {
        'cells_created': len(cell_rows),
        'edges_created': len(edge_rows),
        'factions_created': len(macro_group_rows)
    }

if __name__ == '__main__':
    generate_world(seed=42, num_cells=1000)
