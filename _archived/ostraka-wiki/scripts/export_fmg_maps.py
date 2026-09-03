import sys
import os
import sqlite3

# Add paths to find python_fmg packages
sys.path.append(r"c:\Users\krazy\Desktop\serene-shannon")
sys.path.append(r"c:\Users\krazy\Desktop\ostraka-wiki\scripts")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtCore import QRectF, QPointF

from python_fmg.core.db_sync import load_from_db
from python_fmg.renderers.renderer import WorldMapViewer
from python_fmg.core.grid import hex_to_pixel
from city_generator import generate_city_map

def export_maps():
    app = QApplication.instance() or QApplication(sys.argv)
    db_path = r"c:\Users\krazy\Desktop\serene-shannon\lore_forge_world.db"
    
    if not os.path.exists(db_path):
        print(f"[-] Database not found at: {db_path}")
        return
        
    state = load_from_db(db_path)
    if not state:
        print("[-] Failed to load map state from DB.")
        return
        
    viewer = WorldMapViewer()
    viewer.load_map(state)
    
    # Calculate scene bounding rect
    rect = viewer.scene.itemsBoundingRect()
    viewer.scene.setSceneRect(rect)
    
    output_dir = r"c:\Users\krazy\Desktop\ostraka-wiki\public"
    os.makedirs(output_dir, exist_ok=True)
    illus_dir = os.path.join(output_dir, "illustrations")
    os.makedirs(illus_dir, exist_ok=True)
    
    # 1. Export Global Maps
    modes = ["Biomes", "Elevation", "Factions & States"]
    for mode in modes:
        viewer.render_mode = mode
        for item in viewer.scene.items():
            if hasattr(item, 'update_style'):
                item.update_style()
                
        img = QImage(int(rect.width() + 40), int(rect.height() + 40), QImage.Format.Format_ARGB32)
        img.fill(0xFF0F111A)
        
        painter = QPainter(img)
        viewer.scene.render(painter)
        painter.end()
        
        safe_mode = mode.lower().replace(" & ", "_").replace(" ", "_")
        dest_filename = f"map_{safe_mode}.png"
        dest_path = os.path.join(output_dir, dest_filename)
        img.save(dest_path)
        print(f"[+] Exported global map overlay: {dest_path}")
        
    # 2. Export Settlement Map Assets (Both 2D City Layout and World Map Zoomed Crop)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.name, g.q, g.r 
        FROM settlements s
        JOIN global_hexes g ON s.global_hex_id = g.id
    """)
    settlements = [dict(row) for row in cursor.fetchall()]
    
    # Export Settlements
    viewer.render_mode = "Factions & States"
    for item in viewer.scene.items():
        if hasattr(item, 'update_style'):
            item.update_style()
            
    for s in settlements:
        name = s["name"]
        q = s["q"]
        r = s["r"]
        safe_name = name.lower().replace(" ", "_").replace("-", "_")
        
        # A. Procedural 2D Medieval City Map Layout
        city_map_path = os.path.join(illus_dir, f"city_map_{safe_name}.png")
        try:
            generate_city_map(name, name + "_seed", city_map_path)
            print(f"[+] Exported city map layout for '{name}': {city_map_path}")
        except Exception as ce:
            print(f"[-] Failed to generate city map for '{name}': {ce}")
            
        # B. World Map Zoomed Crop
        x, y = hex_to_pixel(q, r, viewer.cell_size)
        crop_size = 400
        crop_rect = QRectF(x - crop_size/2, y - crop_size/2, crop_size, crop_size)
        
        crop_img = QImage(crop_size, crop_size, QImage.Format.Format_ARGB32)
        crop_img.fill(0xFF0F111A)
        
        painter = QPainter(crop_img)
        viewer.scene.render(painter, target=QRectF(0, 0, crop_size, crop_size), source=crop_rect)
        painter.end()
        
        dest_crop_path = os.path.join(illus_dir, f"map_crop_{safe_name}.png")
        crop_img.save(dest_crop_path)
        print(f"[+] Exported zoomed map crop for '{name}': {dest_crop_path}")
        
    # 3. Export Faction Zoomed Crops (Centered on their capital / largest owned settlement)
    cursor.execute("SELECT id, name FROM factions")
    factions = [dict(row) for row in cursor.fetchall()]
    
    for f in factions:
        f_id = f["id"]
        f_name = f["name"]
        
        # Find largest settlement owned by this faction to center the map crop
        cursor.execute("""
            SELECT g.q, g.r 
            FROM settlements s
            JOIN global_hexes g ON s.global_hex_id = g.id
            WHERE s.faction_id = ?
            ORDER BY s.population DESC
            LIMIT 1
        """, (f_id,))
        cap_row = cursor.fetchone()
        
        if cap_row:
            q = cap_row["q"]
            r = cap_row["r"]
            x, y = hex_to_pixel(q, r, viewer.cell_size)
            
            crop_size = 400
            crop_rect = QRectF(x - crop_size/2, y - crop_size/2, crop_size, crop_size)
            
            crop_img = QImage(crop_size, crop_size, QImage.Format.Format_ARGB32)
            crop_img.fill(0xFF0F111A)
            
            painter = QPainter(crop_img)
            viewer.scene.render(painter, target=QRectF(0, 0, crop_size, crop_size), source=crop_rect)
            painter.end()
            
            safe_f_name = f_name.lower().replace(" ", "_").replace("-", "_")
            dest_crop_path = os.path.join(illus_dir, f"map_crop_{safe_f_name}.png")
            crop_img.save(dest_crop_path)
            print(f"[+] Exported zoomed faction crop for '{f_name}': {dest_crop_path}")
            
    conn.close()

if __name__ == "__main__":
    export_maps()
