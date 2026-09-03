# python_fmg/core/grid.py
import math
import random

def get_hexes_in_radius(r_max):
    """Returns all axial (q, r) coordinates within a hex radius of r_max."""
    coords = []
    for q in range(-r_max, r_max + 1):
        for r in range(max(-r_max, -q - r_max), min(r_max, -q + r_max) + 1):
            coords.append((q, r))
    return coords

def get_neighbors(q, r):
    """Returns the 6 immediate neighbors of a hex coordinate (q, r)."""
    return [(q, r-1), (q+1, r-1), (q+1, r), (q, r+1), (q-1, r+1), (q-1, r)]

def hex_to_pixel(q, r, size=10.0):
    """Converts axial hex coordinates to flat-topped pixel coordinates for rendering."""
    x = size * (3/2 * q)
    y = size * (math.sqrt(3)/2 * q + math.sqrt(3) * r)
    return x, y

def pixel_to_hex(x, y, size=10.0):
    """Converts pixel coordinates to nearest axial hex coordinate."""
    q = (2/3 * x) / size
    r = (-1/3 * x + math.sqrt(3)/3 * y) / size
    return hex_round(q, r)

def hex_round(q, r):
    """Rounds float axial coordinates to the nearest integer hex coordinate."""
    s = -q - r
    rq = round(q)
    rr = round(r)
    rs = round(s)
    
    q_diff = abs(rq - q)
    r_diff = abs(rr - r)
    s_diff = abs(rs - s)
    
    if q_diff > r_diff and q_diff > s_diff:
        rq = -rr - rs
    elif r_diff > s_diff:
        rr = -rq - rs
    return int(rq), int(rr)

def step_towards_origin(q, r):
    """
    Returns the neighbor coordinate that minimizes distance to the origin (0, 0)
    in axial hex coordinates.
    """
    neighbors = get_neighbors(q, r)
    # distance to origin in axial coords is (abs(q) + abs(q + r) + abs(r)) / 2
    def dist_origin(coord):
        nq, nr = coord
        return (abs(nq) + abs(nq + nr) + abs(nr)) / 2
    
    return min(neighbors, key=dist_origin)

# 91 offset coordinates for regional tier
REGIONAL_OFFSETS = get_hexes_in_radius(5)
assert len(REGIONAL_OFFSETS) == 91, "Geometry error: ring math failed to count 91 hexes"

def point_in_triangle(px, py, x1, y1, x2, y2, x3, y3):
    """Helper to check if point (px, py) is inside triangle (x1, y1) - (x2, y2) - (x3, y3)."""
    def sign(x, y, tx1, ty1, tx2, ty2):
        return (x - tx2) * (ty1 - ty2) - (tx1 - tx2) * (y - ty2)
    
    d1 = sign(px, py, x1, y1, x2, y2)
    d2 = sign(px, py, x2, y2, x3, y3)
    d3 = sign(px, py, x3, y3, x1, y1)
    
    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    
    return not (has_neg and has_pos)

def is_in_20_triangle_net(q, r, R=110, T=37):
    """Checks if axial coord (q, r) lies inside the 20-triangle layout bounding net."""
    size = 10.0
    px, py = hex_to_pixel(q, r, size)
    
    S = T * size * 1.5
    H = S * math.sqrt(3) / 2.0
    
    # Check each of the 20 triangles defined in Cartesian coordinates
    for c in range(-2, 3):
        Xc = c * S
        
        # 1. Belt UP
        if point_in_triangle(px, py, Xc, H/2, Xc + S, H/2, Xc + S/2, -H/2):
            return True
        # 2. Belt DOWN
        if point_in_triangle(px, py, Xc - S/2, -H/2, Xc + S/2, -H/2, Xc, H/2):
            return True
        # 3. Top Cap DOWN
        if point_in_triangle(px, py, Xc, -1.5*H, Xc + S, -1.5*H, Xc + S/2, -H/2):
            return True
        # 4. Bottom Cap UP
        if point_in_triangle(px, py, Xc - S/2, 1.5*H, Xc + S/2, 1.5*H, Xc, H/2):
            return True
            
    return False
