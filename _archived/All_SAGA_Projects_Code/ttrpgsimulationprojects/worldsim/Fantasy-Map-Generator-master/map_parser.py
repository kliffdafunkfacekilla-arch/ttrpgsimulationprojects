import json
import os

def load_azgaar_geometry():
    file_path = os.path.join(os.path.dirname(__file__), 'OSTRAKA Cells 2026-06-01-07-50.geojson')
    
    if not os.path.exists(file_path):
        return {"error": "GeoJSON not found"}

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # We just want to extract a simplified representation for the frontend
    # If the file is 3.9MB, we send it as-is to the frontend to draw
    return data
