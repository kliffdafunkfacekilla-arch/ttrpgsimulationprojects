# python_fmg/core/converter.py
import json
import math
from typing import Dict, Tuple, List
from python_fmg.core.models import MapState, GlobalHex, Settlement
from python_fmg.core.grid import get_hexes_in_radius, pixel_to_hex

def convert_azgaar_to_hex_grid(azgaar_json_data: dict, R: int = 57) -> MapState:
    """
    Converts irregular Voronoi cells from an Azgaar JSON map file into 
    the simulator's structured hexagonal grid (coordinates q, r).
    """
    # 1. Get graph dimensions to normalize coordinates
    info = azgaar_json_data.get("info", {})
    width = info.get("width", 1000.0)
    height = info.get("height", 1000.0)
    
    # 2. Get cells data
    cells_data = azgaar_json_data.get("cells", {})
    if not cells_data:
        # Fallback to alternative JSON structure
        cells_data = azgaar_json_data.get("data", {}).get("topology", {}).get("pack", {}).get("cells", {})
        
    # Get lists of coordinates
    points = cells_data.get("p", []) # [ [x1, y1], [x2, y2], ... ]
    biomes = cells_data.get("biome", [])
    heights = cells_data.get("h", [])
    temp = cells_data.get("temp", [])
    moist = cells_data.get("prec", [])
    
    # Get settlements (burgs)
    burgs = azgaar_json_data.get("burgs", [])
    if isinstance(burgs, dict):
        burgs = list(burgs.values())
        
    burg_map = {}
    for b in burgs:
        if not isinstance(b, dict) or "cell" not in b: continue
        burg_map[b["cell"]] = b

    # Create target hex coordinates list
    hex_coords = get_hexes_in_radius(R)
    
    # We will map each hex coordinate on the simulator grid to the closest Azgaar cell
    # First, let's normalize the hex grid coordinates to pixel space matching the Azgaar map scale
    hex_to_cell_data = {}
    
    # Calculate radius scale
    max_hex_dist = R * 1.5 # Approximate spacing multiplier
    
    for idx, (q, r) in enumerate(hex_coords):
        # Convert hex coordinate to normalized [-1, 1] range
        # Global center is (0, 0)
        norm_x = q / R
        norm_y = (r + q/2.0) / (R * math.sqrt(3)/2.0) # Correct for hex slant
        
        # Scale to match Azgaar pixel space centered in width/height
        pixel_x = (norm_x + 1.0) / 2.0 * width
        pixel_y = (norm_y + 1.0) / 2.0 * height
        
        # Find closest Azgaar Voronoi point
        closest_cell_idx = 0
        min_dist = float('inf')
        
        for c_idx, pt in enumerate(points):
            if not pt or len(pt) < 2: continue
            px, py = pt[0], pt[1]
            dist = (px - pixel_x)**2 + (py - pixel_y)**2
            if dist < min_dist:
                min_dist = dist
                closest_cell_idx = c_idx
                
        # Extract properties of closest cell
        biome_val = biomes[closest_cell_idx] if closest_cell_idx < len(biomes) else 4
        elev_val = heights[closest_cell_idx] if closest_cell_idx < len(heights) else 0
        temp_val = temp[closest_cell_idx] if closest_cell_idx < len(temp) else 0
        moist_val = moist[closest_cell_idx] if closest_cell_idx < len(moist) else 0
        
        # Create Hex cell
        # Scale elevation from [0, 100] to simulator scale [0, 15]
        scaled_elev = int(max(0, min(100, elev_val)) / 100.0 * 15)
        
        hx = GlobalHex(
            id=idx + 1,
            q=q,
            r=r,
            biome=int(biome_val),
            elevation=scaled_elev,
            p1=0,
            p2=int(temp_val),
            p3=int(moist_val),
            res=0
        )
        
        # Check if a burg was placed on this cell
        if closest_cell_idx in burg_map:
            b = burg_map[closest_cell_idx]
            hx.settlement = Settlement(
                name=b.get("name", "Settlement"),
                population=int(b.get("population", 50)),
                wealth=float(b.get("product", 100.0)),
                settlement_level=1
            )
            
        hex_to_cell_data[(q, r)] = hx
        
    return MapState(hexes=hex_to_cell_data)
