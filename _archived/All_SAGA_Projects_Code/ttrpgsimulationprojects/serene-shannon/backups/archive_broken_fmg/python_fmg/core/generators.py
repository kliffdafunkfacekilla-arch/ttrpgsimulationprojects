# python_fmg/core/generators.py
import os
import json
import math
import random
from typing import Dict, Tuple, List, Optional
import numpy as np
from scipy.spatial import Voronoi

from python_fmg.core.models import MapState, GlobalHex, Settlement, Faction, Religion, Culture, Province, Marker, TradeRoute, WorldEntity
from python_fmg.core.grid import get_hexes_in_radius, get_neighbors, step_towards_origin, is_in_20_triangle_net, hex_to_pixel

def deflect_current(direction: str, is_northern: bool) -> str:
    cw = {"SW": "NW", "NW": "NE", "NE": "SE", "SE": "SW"}
    ccw = {"SW": "SE", "SE": "NE", "NE": "NW", "NW": "SW"}
    return cw.get(direction, direction) if is_northern else ccw.get(direction, direction)

def find_astar_path(state, start_qr, end_qr, route_type="Land") -> List[Tuple[int, int]]:
    import heapq
    from python_fmg.core.grid import get_neighbors
    
    if start_qr == end_qr:
        return [start_qr]
        
    def get_hex_dist(c1, c2):
        return (abs(c1[0] - c2[0]) + abs(c1[0] + c1[1] - c2[0] - c2[1]) + abs(c1[1] - c2[1])) / 2
        
    open_set = []
    counter = 0
    heapq.heappush(open_set, (get_hex_dist(start_qr, end_qr), counter, start_qr))
    
    came_from = {}
    g_score = {start_qr: 0.0}
    
    while open_set:
        f, _, current = heapq.heappop(open_set)
        
        if current == end_qr:
            path = []
            curr = current
            while curr in came_from:
                path.append(curr)
                curr = came_from[curr]
            path.append(start_qr)
            path.reverse()
            return path
            
        for neighbor in get_neighbors(current[0], current[1]):
            if neighbor not in state.hexes:
                continue
                
            h_curr = state.hexes[current].elevation
            h_neigh = state.hexes[neighbor].elevation
            
            cost = 1.0
            elev_diff = abs(h_neigh - h_curr)
            cost += (elev_diff ** 2.5) * 5.0
            
            if h_neigh >= 10:
                cost += 50.0
                
            cell_neigh = state.hexes[neighbor]
            if cell_neigh.river_volume > 2:
                cost -= 0.5
                
            if route_type == "Sea":
                if h_neigh >= 3:
                    cost += 200.0
            else:
                if h_neigh < 3:
                    cost += 200.0
                    
            tentative_g = g_score[current] + cost
            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                counter += 1
                f_score = tentative_g + get_hex_dist(neighbor, end_qr)
                heapq.heappush(open_set, (f_score, counter, neighbor))
                
    return [start_qr, end_qr]

# Namesbase generator
NAMES_BASE = {
    "English": ["ton", "ham", "ford", "bury", "chester", "shire", "wood", "land", "mouth", "port", "stone", "bridge", "dale", "field"],
    "Elven": ["tara", "glor", "lorian", "elend", "mith", "rond", "dal", "tin", "thil", "nor", "dil", "lind", "ros", "find"],
    "Dwarven": ["dur", "gund", "grim", "bor", "krak", "baraz", "khaz", "duin", "fund", "thor", "mord", "dram", "thrum", "lod"],
    "Chaos": ["warp", "insurg", "vortex", "void", "dusk", "rift", "abyss", "shadow", "null", "plague", "ash", "rot", "carrion", "ruin"]
}

def generate_random_name(category: str) -> str:
    parts = NAMES_BASE.get(category, NAMES_BASE["English"])
    prefix = random.choice(["North", "South", "East", "West", "Old", "New", "High", "Low", "Stone", "Iron", "Gold", "Oak", "River", "Lake"])
    suffix = random.choice(parts)
    return f"{prefix} {suffix.capitalize()}"

# Biomes matrix definition (FMG Standard)
BIOMES_MATRIX = [
    [1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 10], # moisture 0
    [3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 9, 9, 9, 9, 10, 10, 10], # moisture 1
    [5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 9, 9, 9, 9, 9, 10, 10, 10], # moisture 2
    [5, 6, 6, 6, 6, 6, 6, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9, 9, 9, 9, 9, 9, 10, 10, 10], # moisture 3
    [7, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9, 9, 9, 9, 9, 9, 9, 10, 10]  # moisture 4
]

def get_biome_id(moisture: int, temp: int, height: int, has_river: bool) -> int:
    if height < 3: 
        return 0 # Marine
    if temp < -5:
        return 10 # Tundra / Glacier
    if temp > -2 and ((moisture > 40 and height < 5) or (moisture > 24 and 5 <= height < 10)):
        return 12 # Wetland
    if temp >= 25 and not has_river and moisture < 8:
        return 1 # Hot desert
    moisture_band = min(moisture // 5, 4)
    temp_band = min(max(20 - temp, 0), 25)
    return BIOMES_MATRIX[moisture_band][temp_band]

def generate_world(
    R: int = 110, 
    elevation_seed: int = 100, 
    temp_offset: float = 0.0,
    temp_equator: float = 30.0,
    temp_pole: float = -15.0,
    precip_mult: float = 1.0,
    wind_angle: float = 90.0
) -> MapState:
    random.seed(elevation_seed)
    
    # 1. Gather icosahedron net coordinates
    all_coords = get_hexes_in_radius(R)
    net_coords = [c for c in all_coords if is_in_20_triangle_net(c[0], c[1], R, T=37)]
    outer_coords = [c for c in get_hexes_in_radius(R + 5) if not is_in_20_triangle_net(c[0], c[1], R, T=37)]
    
    # 2. Build Jittered Voronoi Seeds
    seeds = []
    coord_map = {} # maps seed index to (q, r)
    
    # Add inner seeds (jittered to create natural Voronoi cell shapes)
    for q, r in net_coords:
        x, y = hex_to_pixel(q, r, size=12.0)
        x += random.uniform(-4.5, 4.5)
        y += random.uniform(-4.5, 4.5)
        seeds.append([x, y])
        coord_map[len(seeds) - 1] = (q, r)
        
    # Add outer shell seeds (used to bound boundary cells so they are finite)
    for q, r in outer_coords:
        x, y = hex_to_pixel(q, r, size=12.0)
        seeds.append([x, y])
        
    # Run Voronoi triangulation
    vor = Voronoi(seeds)
    
    # 3. Retrieve Voronoi region vertices for each cell
    cell_vertices = {}
    for seed_idx, (q, r) in coord_map.items():
        region_idx = vor.point_region[seed_idx]
        region = vor.regions[region_idx]
        
        if -1 not in region and len(region) >= 3:
            verts = [vor.vertices[v_idx] for v_idx in region]
            cx = sum(v[0] for v in verts) / len(verts)
            cy = sum(v[1] for v in verts) / len(verts)
            verts.sort(key=lambda v: math.atan2(v[1] - cy, v[0] - cx))
            cell_vertices[(q, r)] = [(float(v[0]), float(v[1])) for v in verts]
        else:
            cell_vertices[(q, r)] = None
            
    # 4. Generate heights using fractal peaks & simplex approximations
    heights = {}
    for q, r in net_coords:
        dist = math.sqrt(q*q + r*r)
        noise1 = math.sin(q * 0.08) * math.cos(r * 0.08)
        noise2 = math.cos(q * 0.18 + r * 0.1) * 0.4
        val = int(8 + (noise1 + noise2) * 8 - (dist / R) * 4)
        heights[(q, r)] = max(1, min(15, val))
        
    # Apply mountain ridge perturbations
    for _ in range(5):
        peak = random.choice(net_coords)
        for q, r in net_coords:
            dist = math.sqrt((q-peak[0])**2 + (r-peak[1])**2)
            if dist < 15:
                heights[(q, r)] = min(15, heights[(q, r)] + int(5 * (1.0 - dist/15.0)))
                
    # 5. Climate Simulation (Temperatures & prevailing winds)
    temperatures = {}
    wind_dirs = {}
    moisture = {}
    
    map_height_max = R * 1.5
    
    # Load custom wind bands configuration from .worldsmith/config.json if present
    config_path = r"c:\Users\krazy\Desktop\serene-shannon\.worldsmith\config.json"
    wind_bands = [
        {"pct_max": 0.14, "dir": "SW"},
        {"pct_max": 0.43, "dir": "NE"},
        {"pct_max": 0.57, "dir": "SW"},
        {"pct_max": 0.71, "dir": "NW"},
        {"pct_max": 1.00, "dir": "NE"}
    ]
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f_conf:
                data = json.load(f_conf)
                if "wind_bands" in data:
                    wind_bands = data["wind_bands"]
        except:
            pass
            
    # Sort bands by pct_max to ensure correct order
    wind_bands = sorted(wind_bands, key=lambda b: b["pct_max"])
    
    for q, r in net_coords:
        lat_ratio = abs(r) / map_height_max
        base_temp = temp_equator - lat_ratio * (temp_equator - temp_pole) + temp_offset
        elev_cool = heights[(q, r)] * 1.5
        temperatures[(q, r)] = int(base_temp - elev_cool)
        
        # 7-Band Wind Vector Engine (dx, dy bindings)
        pct = (r + R) / (2.0 * R)
        w_dir = "NE"
        for band in wind_bands:
            if pct < band["pct_max"]:
                w_dir = band["dir"]
                break
        wind_dirs[(q, r)] = w_dir

    air_moisture = {coord: (100.0 if heights[coord] < 3 else 0.0) for coord in net_coords}
    rainfall = {coord: 0.0 for coord in net_coords}
    
    vecs = {
        'SW': (-1, 1),
        'NE': (1, -1),
        'NW': (-1, -1)
    }
    for sweep in range(12):
        new_air = {coord: 0.0 for coord in net_coords}
        for (q, r), air in air_moisture.items():
            if air <= 0: continue
            w_dir = wind_dirs.get((q, r), "NE")
            wq, wr = vecs.get(w_dir, (1, -1))
            nq, nr = q + wq, r + wr
            if (nq, nr) in heights:
                diff = heights[(nq, nr)] - heights[(q, r)]
                if diff > 0:
                    precip = air * (diff * 0.15) * precip_mult
                    precip = min(air, precip)
                    rainfall[(nq, nr)] += precip
                    new_air[(nq, nr)] += (air - precip)
                else:
                    new_air[(nq, nr)] += air
                    
        air_moisture = new_air
        for coord in air_moisture:
            if heights[coord] < 3:
                air_moisture[coord] = 100.0
                
    for coord in net_coords:
        moisture[coord] = min(25, int(rainfall[coord] / 8))
        
    # 7. Hydrology & River Gradient Descent
    river_volume = {coord: int(rainfall[coord] / 10) for coord in net_coords}
    is_lake = {coord: False for coord in net_coords}
    flow_targets = {}
    
    sorted_hexes = sorted(net_coords, key=lambda c: heights[c], reverse=True)
    for q, r in sorted_hexes:
        if heights[(q, r)] < 3: continue
        neighbors = get_neighbors(q, r)
        valid_n = [n for n in neighbors if n in heights]
        if not valid_n: continue
        
        lowest_n = min(valid_n, key=lambda n: heights[n])
        if heights[lowest_n] < heights[(q, r)]:
            river_volume[lowest_n] += river_volume[(q, r)]
            flow_targets[(q, r)] = lowest_n
        else:
            is_lake[(q, r)] = True
            
    # 8. Biomes Mapping
    biomes = {}
    prison_domains = {}
    prisons = [(0, -R), (R, -R), (R, 0), (0, R), (-R, R), (-R, 0)]
    domains = ["Nexus", "Ratio", "Vita", "Lux", "Omen", "Aura"]
    for i, p_coord in enumerate(prisons):
        if p_coord in heights:
            prison_domains[p_coord] = domains[i % len(domains)]
            
    leyline_paths = {}
    for p_q, p_r in prisons:
        if (p_q, p_r) not in heights: continue
        curr_q, curr_r = p_q, p_r
        while (curr_q, curr_r) != (0, 0) and (curr_q, curr_r) in heights:
            next_q, next_r = step_towards_origin(curr_q, curr_r)
            if (next_q, next_r) in heights:
                leyline_paths[(curr_q, curr_r)] = (next_q, next_r)
            curr_q, curr_r = next_q, next_r
            
    for coord in net_coords:
        if coord in prison_domains or coord == (0, 0):
            biomes[coord] = 13
        else:
            biomes[coord] = get_biome_id(moisture[coord], temperatures[coord], heights[coord], river_volume[coord] > 2)
            
    # Assemble cells list
    hex_objs = {}
    for idx, (q, r) in enumerate(net_coords):
        domain = prison_domains.get((q, r), None)
        p1_chaos = 255 if domain or (q, r) == (0, 0) else (200 if (q, r) in leyline_paths else max(0, min(255, int(heights[(q, r)] * 16))))
        res_val = 60000 if (q, r) in leyline_paths else 0
        
        hx = GlobalHex(
            id=idx + 1,
            q=q,
            r=r,
            biome=biomes[(q, r)],
            elevation=heights[(q, r)],
            p1=p1_chaos,
            p2=max(0, min(255, int(temperatures[(q, r)] + 40))),
            p3=max(0, min(255, int(moisture[(q, r)] * 10))),
            res=res_val,
            wind_direction=wind_dirs[(q, r)],
            river_volume=river_volume[(q, r)],
            is_lake=is_lake[(q, r)],
            chaos_domain=domain
        )
        # Attach custom Voronoi vertices
        hx.vertices = cell_vertices.get((q, r))
        hex_objs[(q, r)] = hx

    # 8.1 Ocean Currents Deflection
    for (q, r), hx in hex_objs.items():
        if hx.elevation < 3:
            hx.current_direction = hx.wind_direction
            
    vec_deflects = {'SW': (-1, 1), 'NE': (1, -1), 'NW': (-1, -1), 'SE': (1, 1)}
    for _ in range(3):
        for (q, r), hx in hex_objs.items():
            if hx.elevation >= 3: continue
            curr_dir = hx.current_direction or hx.wind_direction
            wq, wr = vec_deflects.get(curr_dir, (1, -1))
            nq, nr = q + wq, r + wr
            if (nq, nr) in heights and heights[(nq, nr)] >= 3:
                hx.current_direction = deflect_current(curr_dir, r < 0)
        
    for coord, target in flow_targets.items():
        if coord in hex_objs and target in hex_objs:
            hex_objs[coord].flow_target_id = hex_objs[target].id
            
    # 9. Porting Cultures expansion
    cultures = {}
    culture_colors = ["#E67E22", "#9B59B6", "#1ABC9C", "#3498DB", "#E74C3C", "#2ECC71", "#F1C40F", "#1ABC9C", "#F39C12", "#D35400"]
    culture_bases = ["English", "Elven", "Dwarven", "Chaos"]
    
    culture_centers = []
    land_hexes = [c for c in net_coords if heights[c] >= 3]
    if land_hexes:
        culture_centers = random.sample(land_hexes, min(len(land_hexes), 6))
        
    for c_id, center in enumerate(culture_centers):
        col = culture_colors[c_id % len(culture_colors)]
        base = culture_bases[c_id % len(culture_bases)]
        name = f"{base} Culture"
        cul = Culture(id=c_id + 1, name=name, language_base=base, color=col, center_q=center[0], center_r=center[1])
        cultures[cul.id] = cul
        
        queue = [center]
        visited = {center}
        hex_objs[center].culture_id = cul.id
        limit = 0
        while queue and limit < 60:
            limit += 1
            curr = queue.pop(0)
            for neighbor in get_neighbors(curr[0], curr[1]):
                if neighbor in heights and neighbor not in visited and heights[neighbor] >= 3:
                    visited.add(neighbor)
                    hex_objs[neighbor].culture_id = cul.id
                    queue.append(neighbor)
                    
    # 10. Porting States & Religions expansion
    factions = {}
    religions = {}
    religion_colors = ["#E84393", "#6C5CE7", "#0984E3", "#00B894", "#FDCB6E", "#E17055"]
    religion_names = ["Order", "Void Worship", "Nature Faith", "Sun Cult", "Lumina", "Lex Cult"]
    
    for r_id, center in enumerate(culture_centers):
        name = f"Path of {religion_names[r_id % len(religion_names)]}"
        col = religion_colors[r_id % len(religion_colors)]
        rel = Religion(id=r_id + 1, name=name, color=col, center_q=center[0], center_r=center[1])
        religions[rel.id] = rel
        
        queue = [center]
        visited = {center}
        hex_objs[center].religion_id = rel.id
        limit = 0
        while queue and limit < 80:
            limit += 1
            curr = queue.pop(0)
            for neighbor in get_neighbors(curr[0], curr[1]):
                if neighbor in heights and neighbor not in visited and heights[neighbor] >= 3:
                    visited.add(neighbor)
                    hex_objs[neighbor].religion_id = rel.id
                    queue.append(neighbor)
                    
    # 11. Porting Burgs generation & Namesbases
    settlement_id_counter = 1
    for coord in land_hexes:
        hx = hex_objs[coord]
        is_coastal = any(heights.get(n, 0) < 3 for n in get_neighbors(coord[0], coord[1]))
        if hx.river_volume > 8 or (is_coastal and random.random() < 0.08):
            category = "English"
            if hx.culture_id in cultures:
                category = cultures[hx.culture_id].language_base
            name = generate_random_name(category)
            
            sett = Settlement(
                id=settlement_id_counter,
                faction_id=1,
                faction_name="Neutral",
                name=name,
                population=random.randint(500, 8000),
                wealth=round(random.uniform(500.0, 5000.0), 2)
            )
            sett.valid_from = 0
            sett.valid_until = 9999
            sett.z_layer = "surface"
            hx.settlement = sett
            settlement_id_counter += 1
            
    # Define Factions / States
    faction_names = ["Kingdom of Sun", "Empire of Void", "Duchy of Stone", "Alliance of Iron", "Principality of Dawn", "Concord of Stars"]
    for f_id, center in enumerate(culture_centers):
        name = faction_names[f_id % len(faction_names)]
        fac = Faction(id=f_id + 1, name=name)
        factions[fac.id] = fac
        
        queue = [center]
        visited = {center}
        hex_objs[center].province_id = fac.id
        limit = 0
        while queue and limit < 75:
            limit += 1
            curr = queue.pop(0)
            for neighbor in get_neighbors(curr[0], curr[1]):
                if neighbor in heights and neighbor not in visited and heights[neighbor] >= 3:
                    visited.add(neighbor)
                    hex_objs[neighbor].province_id = fac.id
                    
                    hx_n = hex_objs[neighbor]
                    if hx_n.settlement:
                        hx_n.settlement.faction_id = fac.id
                        hx_n.settlement.faction_name = fac.name
                    queue.append(neighbor)
                    
    # 12. Markers (POIs)
    markers = []
    marker_types = ["Ruins", "Dungeon", "Cave", "Portal", "Obelisk"]
    for idx, coord in enumerate(random.sample(land_hexes, min(len(land_hexes), 15))):
        m = Marker(
            id=idx + 1,
            type=random.choice(marker_types),
            description=f"Ancient {random.choice(marker_types)} discovered on the map",
            global_q=coord[0],
            global_r=coord[1],
            resource_type="Gold" if random.random() < 0.5 else "Mana",
            resource_value=round(random.uniform(10, 100), 2)
        )
        markers.append(m)
        
    # 13. Routes (Roads linking settlements)
    routes = []
    route_id_counter = 1
    sett_coords = [c for c in land_hexes if hex_objs[c].settlement]
    for i, c1 in enumerate(sett_coords):
        for c2 in sett_coords[i+1 : i+4]:
            dist = (c1[0]-c2[0])**2 + (c1[1]-c2[1])**2
            if dist < 64:
                r = TradeRoute(
                    id=route_id_counter,
                    faction_id=hex_objs[c1].settlement.faction_id,
                    settlement_a_id=hex_objs[c1].settlement.id,
                    settlement_b_id=hex_objs[c2].settlement.id,
                    bandwidth=random.randint(5, 20),
                    route_type="Land" if heights[c2] >= 3 else "Sea"
                )
                r.z_layer = "surface"
                routes.append(r)
                route_id_counter += 1
                
    state = MapState(
        hexes=hex_objs, 
        factions=factions, 
        entities=[], 
        routes=routes, 
        religions=religions, 
        cultures=cultures, 
        provinces={}, 
        markers=markers
    )
    
    state.temperature_equator = temp_equator
    state.temperature_pole = temp_pole
    state.temperature_offset = temp_offset
    state.precipitation_multiplier = precip_mult
    state.wind_direction_angle = wind_angle
    
    return state
