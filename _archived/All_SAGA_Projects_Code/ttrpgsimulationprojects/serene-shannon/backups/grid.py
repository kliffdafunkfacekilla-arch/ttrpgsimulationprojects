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

# 91 offset coordinates for regional tier
REGIONAL_OFFSETS = get_hexes_in_radius(5)
assert len(REGIONAL_OFFSETS) == 91, "Geometry error: ring math failed to count 91 hexes"
