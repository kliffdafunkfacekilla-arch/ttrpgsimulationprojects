# map_generator.py
import numpy as np
import os
from scipy.spatial import Voronoi
from database import get_db_connection, init_db, DB_PATH

def generate_world(seed: int, num_cells: int = 1000):
    """
    Generates a Voronoi diagram using SciPy, constructs WKT polygons for closed cells,
    computes cell adjacencies (edges), and inserts them into the SQLite database.
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
            
        valid_cells.add(point_idx)
        vertices = vor.vertices[region]
        
        # Build WKT polygon string: POLYGON((x1 y1, x2 y2, ..., x1 y1))
        coords = ', '.join(f'{x:.4f} {y:.4f}' for x, y in vertices)
        first_vertex = f'{vertices[0][0]:.4f} {vertices[0][1]:.4f}'
        wkt = f'POLYGON(({coords}, {first_vertex}))'
        
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
                0,              # farms_count
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
            INSERT INTO macro_groups (id, cell_id, faction_id, faction_name, chaos_level, population, discontent, crime_level, food_supply, physical_well_being, mental_well_being, safety_rating, camps_count, mines_count, farms_count, barracks_count, watchtowers_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
