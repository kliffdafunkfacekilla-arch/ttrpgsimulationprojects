# python_fmg/core/generators.py
import math
import random
from typing import Dict, Tuple, List
from python_fmg.core.models import MapState, GlobalHex
from python_fmg.core.grid import get_hexes_in_radius, get_neighbors, step_towards_origin, is_in_20_triangle_net

def pseudo_noise(lon: float, lat: float, seed: int = 42) -> float:
    x = math.cos(lat) * math.cos(lon)
    y = math.cos(lat) * math.sin(lon)
    z = math.sin(lat)
    return (math.sin(x * 3 + seed) + math.cos(y * 3 + seed) + math.sin(z * 3 + seed)) / 3.0

def calculate_base_biome(elevation: float, temp: float, moisture: float) -> int:
    # Ocean Biomes
    if elevation < 0.0:
        if elevation < -0.6: return 12 # Abyssal Trench
        if temp > 0.4: return 10 # Coral Reef
        if temp < -0.4: return 11 # Arctic Ocean
        return 9 # Kelp Forest / Open Ocean

    # Land Biomes
    if temp < -0.8: return 8 # Arctic
    if elevation > 0.7:
        if temp > 0.6: return 7 # Volcano
        return 6 # Mountain
    if temp > 0.4: return 0 if moisture > 0.3 else 3 # Jungle vs Desert
    elif temp < -0.4: return 2 if moisture > 0.3 else 5 # Taiga vs Tundra
    else: return 1 if moisture > 0.3 else 4 # Forest vs Plains

def generate_world(R: int = 110, elevation_seed: int = 100, temp_offset: float = 0.0) -> MapState:
    # Generate coordinates conformed to the 20-triangle D20 layout
    all_coords = get_hexes_in_radius(R)
    hex_coords = [c for c in all_coords if is_in_20_triangle_net(c[0], c[1], R, T=37)]
    
    map_size = R * 2
    
    elevation_map = {}
    temp_map = {}
    wind_map = {}
    
    for q, r in hex_coords:
        lon = (q / map_size) * math.pi * 2 - math.pi
        lat = (r / map_size) * math.pi - (math.pi / 2)

        if lat > 1.047: # Polar N
            wind_dir = "W"
            base_temp = -0.9
        elif lat > 0.26: # Temperate N
            wind_dir = "E"
            base_temp = 0.5
        elif lat > -0.26: # Equatorial
            wind_dir = "W"
            base_temp = 0.8
        elif lat > -1.047: # Temperate S
            wind_dir = "E"
            base_temp = 0.5
        else: # Polar S
            wind_dir = "W"
            base_temp = -0.9

        # Boost base elevations to generate beautiful continents/shores inside the D20 net
        elevation = pseudo_noise(lon, lat, seed=elevation_seed) * 0.4 + 0.25
        temp = pseudo_noise(lon, lat, seed=elevation_seed+1) * 0.3 + base_temp + temp_offset

        if elevation > 0.2:
            temp -= elevation * 0.5

        elevation_map[(q, r)] = elevation
        temp_map[(q, r)] = temp
        wind_map[(q, r)] = wind_dir

    # Orographic rainfall simulation
    air_mass = {k: (10.0 if v < 0.0 else 0.0) for k, v in elevation_map.items()}
    rainfall = {k: 0.0 for k in hex_coords}
    vecs = {'W': (-1, 0), 'E': (1, 0)}

    for sweep in range(15):
        new_air = {k: 0.0 for k in hex_coords}
        for (q, r), air in air_mass.items():
            if air <= 0: continue
            w_dir = wind_map.get((q, r), "W")
            wq, wr = vecs[w_dir]
            nq, nr = q + wq, r + wr
            if (nq, nr) in elevation_map:
                diff = elevation_map[(nq, nr)] - elevation_map[(q, r)]
                if diff > 0.05:
                    precip = air * diff * 2.0
                    if precip > air: precip = air
                    rainfall[(nq, nr)] += precip
                    new_air[(nq, nr)] += (air - precip)
                else:
                    new_air[(nq, nr)] += air

        air_mass = new_air
        for k in air_mass:
            if elevation_map[k] < 0.0:
                air_mass[k] = 10.0

    # Hydrology (Rivers & Lakes)
    river_volume = {k: int(rainfall[k]) for k in hex_coords}
    is_lake = {k: False for k in hex_coords}
    sorted_hexes = sorted(hex_coords, key=lambda k: elevation_map[k], reverse=True)

    for q, r in sorted_hexes:
        if river_volume[(q, r)] > 0 and elevation_map[(q, r)] >= 0.0:
            neighbors = get_neighbors(q, r)
            valid_n = [n for n in neighbors if n in elevation_map]
            if not valid_n: continue

            lowest = min(valid_n, key=lambda n: elevation_map[n])
            if elevation_map[lowest] < elevation_map[(q, r)]:
                river_volume[lowest] += river_volume[(q, r)]
            else:
                is_lake[(q, r)] = True

    # Prisons / Chaos setup
    inner_R = R // 2
    prisons = [
        (0, -R), (R, -R), (R, 0), (0, R), (-R, R), (-R, 0),
        (0, -inner_R), (inner_R, -inner_R), (inner_R, 0), (0, inner_R), (-inner_R, inner_R), (-inner_R, 0)
    ]
    domains = ["Mass", "Ordo", "Motus", "Flux", "Vita", "Nexus", "Ratio", "Anumis", "Lux", "Omen", "Aura", "Lex"]
    prison_domains = {}
    for i, p_coord in enumerate(prisons):
        if p_coord in elevation_map:
            prison_domains[p_coord] = domains[i % len(domains)]

    leyline_paths = {}
    for p_q, p_r in prisons:
        if (p_q, p_r) not in elevation_map:
            continue
        curr_q, curr_r = p_q, p_r
        while (curr_q, curr_r) != (0, 0) and (curr_q, curr_r) in elevation_map:
            next_q, next_r = step_towards_origin(curr_q, curr_r)
            if (next_q, next_r) in elevation_map:
                leyline_paths[(curr_q, curr_r)] = (next_q, next_r)
            curr_q, curr_r = next_q, next_r

    # Build Hex models
    hexes = {}
    for idx, (q, r) in enumerate(hex_coords):
        elevation_val = elevation_map[(q, r)]
        temp_val = temp_map[(q, r)]
        moist_val = rainfall[(q, r)] / 10.0
        
        biome = calculate_base_biome(elevation_val, temp_val, moist_val)
        
        domain = None
        if (q, r) in prison_domains:
            biome = 13  # Prison / Wastes
            p1_chaos = 255
            domain = prison_domains[(q, r)]
        elif (q, r) in leyline_paths:
            p1_chaos = 200
        elif (q, r) == (0, 0):
            biome = 13
            p1_chaos = 255
        else:
            p1_chaos = max(0, min(255, int(abs(elevation_val) * 50)))

        p2 = max(0, min(255, int(abs(temp_val) * 50)))
        p3_moisture = max(0, min(255, int((rainfall[(q, r)] + river_volume[(q, r)]) * 10)))
        res = 60000 if (q, r) in leyline_paths else 0
        
        scaled_elev = int(max(0.0, min(1.0, (elevation_val + 1.0) / 2.0)) * 15)

        hx = GlobalHex(
            id=idx + 1,
            q=q,
            r=r,
            biome=biome,
            elevation=scaled_elev,
            p1=p1_chaos,
            p2=p2,
            p3=p3_moisture,
            res=res,
            wind_direction=wind_map[(q, r)],
            river_volume=river_volume[(q, r)],
            is_lake=is_lake[(q, r)],
            chaos_domain=domain
        )
        hexes[(q, r)] = hx

    # Flow targets matching database mapping
    for coord, target_coord in leyline_paths.items():
        if coord in hexes and target_coord in hexes:
            hexes[coord].flow_target_id = hexes[target_coord].id

    return MapState(hexes=hexes)
