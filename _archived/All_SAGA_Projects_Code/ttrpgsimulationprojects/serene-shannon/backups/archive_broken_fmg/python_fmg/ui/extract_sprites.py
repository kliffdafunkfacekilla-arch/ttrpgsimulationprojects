import os
import sys
from PIL import Image
from python_fmg.config import paths

def extract(src_path=None):
    if not src_path:
        local_copy = r"C:\Users\krazy\.gemini\antigravity-ide\brain\c471270a-0113-47ab-9920-40cb61c50607\media__1782977644757.jpg"
        if os.path.exists(local_copy):
            src_path = local_copy
            print(f"[+] Using local spritesheet source: {src_path}")
        else:
            dl_dir = r"C:\Users\krazy\Downloads"
            if os.path.exists(dl_dir):
                files = [os.path.join(dl_dir, f) for f in os.listdir(dl_dir) if f.startswith("_") and f.lower().endswith((".jpg", ".png", ".jpeg"))]
                if files:
                    src_path = max(files, key=os.path.getmtime)
                    print(f"[+] Detected newest Bing Image Creator tilemap: {src_path}")
                else:
                    print("[-] No tilemap spritesheet found.")
                    return
            else:
                print("[-] Spritesheet source path not found.")
                return

    dest_dir = str(paths.PUBLIC_TEXTURES)
    os.makedirs(dest_dir, exist_ok=True)
    
    img = Image.open(src_path)
    w, h = img.size
    
    if "media__1782977644757" in src_path or w == 1088 or (w == 1024 and h != 1024):
        print("[+] Slicing using 17-column layout coordinates...")
        col_w = w / 17.0
        row_bounds = [
            (30, 110),   # Row 0: Land Biomes
            (134, 214),  # Row 1: Underwater Biomes
            (248, 328),  # Row 2: Special Tiles
            (360, 440),  # Row 3: Roads
            (472, 552),  # Row 4: Zones
            (580, 652),  # Row 5: Resources
            (680, 750)   # Row 6: Structures
        ]
        
        biomes_mapping = {
            0: (0, 4),   # Jungle: Row 0, Col 4
            1: (0, 5),   # Forest: Row 0, Col 5
            2: (0, 7),   # Taiga: Row 0, Col 7
            3: (0, 2),   # Desert: Row 0, Col 2
            4: (0, 0),   # Plains: Row 0, Col 0
            5: (0, 8),   # Tundra: Row 0, Col 8
            6: (0, 10),  # Mountain: Row 0, Col 10
            7: (0, 12),  # Volcano: Row 0, Col 12
            8: (0, 9),   # Arctic: Row 0, Col 9
            9: (1, 4)    # Ocean: Row 1, Col 4
        }
        
        names_mapping = {
            0: "jungle_tile.png",
            1: "forest_tile.png",
            2: "taiga_tile.png",
            3: "desert_tile.png",
            4: "plains_tile.png",
            5: "tundra_tile.png",
            6: "mountain_tile.png",
            7: "volcano_tile.png",
            8: "arctic_tile.png",
            9: "ocean_tile.png"
        }
        
        for b_id, (row_idx, col_idx) in biomes_mapping.items():
            y_start, y_end = row_bounds[row_idx]
            x_start = int(col_idx * col_w)
            x_end = int((col_idx + 1) * col_w)
            
            cropped = img.crop((x_start, y_start, x_end, y_end))
            save_path = os.path.join(dest_dir, names_mapping[b_id])
            cropped.save(save_path)
            print(f"[+] Saved tile for biome {b_id} to: {save_path}")
            
    else:
        print("[+] Slicing using 10x9 square layout coordinates...")
        col_w = w / 10.0
        row_h = h / 9.0
        
        biomes_mapping = {
            0: (0, 1),   # Jungle
            1: (1, 8),   # Forest
            2: (0, 2),   # Taiga
            3: (0, 6),   # Desert
            4: (0, 0),   # Plains
            5: (1, 1),   # Tundra
            6: (1, 5),   # Mountain
            7: (1, 3),   # Volcano
            8: (1, 2),   # Arctic
            9: (3, 5)    # Ocean
        }
        
        names_mapping = {
            0: "jungle_tile.png",
            1: "forest_tile.png",
            2: "taiga_tile.png",
            3: "desert_tile.png",
            4: "plains_tile.png",
            5: "tundra_tile.png",
            6: "mountain_tile.png",
            7: "volcano_tile.png",
            8: "arctic_tile.png",
            9: "ocean_tile.png"
        }
        
        for b_id, (row_idx, col_idx) in biomes_mapping.items():
            y_start = int(row_idx * row_h)
            y_end = int((row_idx + 1) * row_h)
            x_start = int(col_idx * col_w)
            x_end = int((col_idx + 1) * col_w)
            
            cropped = img.crop((x_start, y_start, x_end, y_end))
            save_path = os.path.join(dest_dir, names_mapping[b_id])
            cropped.save(save_path)
            print(f"[+] Saved tile for biome {b_id} to: {save_path}")

def extract_place_icons(src_path, cols=4, rows=4):
    dest_dir = str(paths.PUBLIC_TEXTURES)
    os.makedirs(dest_dir, exist_ok=True)
    
    img = Image.open(src_path)
    w, h = img.size
    
    col_w = w / float(cols)
    row_h = h / float(rows)
    
    places_mapping = {
        "town": (0, 0),
        "cave": (0, 1),
        "caravan": (0, 2),
        "ruins": (0, 3),
        "keep": (1, 0),
        "dungeon": (1, 1),
        "ship": (1, 2)
    }
    
    for name, (row_idx, col_idx) in places_mapping.items():
        if row_idx < rows and col_idx < cols:
            y_start = int(row_idx * row_h)
            y_end = int((row_idx + 1) * row_h)
            x_start = int(col_idx * col_w)
            x_end = int((col_idx + 1) * col_w)
            
            cropped = img.crop((x_start, y_start, x_end, y_end))
            save_path = os.path.join(dest_dir, f"{name}_icon.png")
            cropped.save(save_path)
            print(f"[+] Saved place icon for {name} to: {save_path}")

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--places":
        extract_place_icons(sys.argv[2])
    else:
        path_arg = sys.argv[1] if len(sys.argv) > 1 else None
        extract(path_arg)
