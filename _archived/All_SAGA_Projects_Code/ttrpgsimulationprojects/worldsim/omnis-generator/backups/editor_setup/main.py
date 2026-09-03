# main.py
import sys
import os
from database import get_db_connection
from map_generator import generate_world
from simulation_engine import TTRPGWorldModel
from ui.viewer import MapViewer

def main():
    # Check if database has cells seeded
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM cells")
        count = cur.fetchone()[0]
    except Exception:
        count = 0
    cur.close()
    conn.close()
    
    if count == 0:
        print("Empty database detected. Generating initial world map...")
        generate_world(seed=42, num_cells=1000)
        
    # Initialize the Mesa simulation model
    print("Starting Mesa simulation model...")
    model = TTRPGWorldModel()
    
    # Initialize the Pygame MapViewer
    print("Launching Pygame desktop window...")
    viewer = MapViewer()
    viewer.model = model
    
    # Start the rendering loop
    viewer.run()

if __name__ == '__main__':
    main()
