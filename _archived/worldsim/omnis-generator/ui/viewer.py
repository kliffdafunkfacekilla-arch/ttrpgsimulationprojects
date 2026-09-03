# ui/viewer.py
import pygame
import os
import numpy as np
import json
import math
from shapely.wkt import loads
from database import get_db_connection
from ui.settings_dialogs import (
    edit_calendar_dialog,
    edit_elevation_dialog,
    edit_factions_dialog,
    edit_settlements_dialog,
    edit_ecology_dialog,
    edit_resources_recipes_dialog,
    edit_cults_dialog,
    edit_fringe_dialog
)
from modules.calendar_manager import CalendarManager

# Standard 17 Ostraka Faction Names
FACTION_NAMES = [
    "Ursine Hegemony",
    "River Folk",
    "Sump-Kin",
    "Iron Caladrea",
    "Vaneer Concord",
    "Hive Collective",
    "Avians",
    "Flower Valwey",
    "Sylvian",
    "Sciute",
    "Meridian Chain",
    "Prism Lizards",
    "Canopy Clans",
    "East Hounds",
    "Guirrilla Clans",
    "Theocracy",
    "The Reliance"
]

# 12 Prisons / Cults
PRISON_NAMES = [
    "Tiraton", "Stagus", "Metrion", "Aurgenas", "Vecelo", "Lophex",
    "Tyrustis", "Opecten", "Carulkem", "Termhill", "Virantor", "Gavusrix"
]

# Fringe Groups
FRINGE_NAMES = [
    "Obsidian Cartel", "Freesky Barons", "Ghost Wind Raiders", "Gilded Compass",
    "Crimson Coursairs", "Silent Current", "The Black Label", "The Otter Syndicate",
    "The Spring Ghosts"
]

# Biome list for cycling
BIOMES_LIST = ['Ocean', 'Plains', 'Forest', 'Desert', 'Mountain', 'Swamp', 'Coastal', 'Reef', 'Abyssal', 'Thermal']

# Wind directions for cycling
WIND_DIRECTIONS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

# Resource node types
NODE_TYPES = [
    {"name": "Rich Iron Vein", "icon": "Fe", "desc": "Yields Iron", "yield": 400.0},
    {"name": "Rich Copper Vein", "icon": "Cu", "desc": "Yields Copper", "yield": 400.0},
    {"name": "Luminescent Coral Mine", "icon": "Co", "desc": "Yields Coral", "yield": 200.0},
    {"name": "Dragonstone Crater", "icon": "Ds", "desc": "Yields Dragonstone", "yield": 50.0},
    {"name": "Rich Osmium Vein", "icon": "Os", "desc": "Yields Osmium", "yield": 150.0},
    {"name": "Ancient Steel Ruins", "icon": "St", "desc": "Yields Smelted Steel", "yield": 100.0},
    {"name": "Coal Seam", "icon": "Cl", "desc": "Yields Coal", "yield": 350.0},
    {"name": "Grain Stockpile", "icon": "Gr", "desc": "Yields Grain", "yield": 500.0},
]

def wrap_text(text, font, max_width):
    """Utility function to wrap text for Pygame drawing."""
    words = text.split(' ')
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        test_line = ' '.join(current_line)
        if font.size(test_line)[0] > max_width:
            current_line.pop()
            lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    return lines

def load_world_settings():
    """Loads settings from world_settings.json, falling back to default_settings.json."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    ws_path = os.path.join(base_dir, 'world_settings.json')
    ds_path = os.path.join(base_dir, 'default_settings.json')
    
    if os.path.exists(ws_path):
        with open(ws_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    elif os.path.exists(ds_path):
        with open(ds_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_world_settings(settings):
    """Saves settings to world_settings.json."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    ws_path = os.path.join(base_dir, 'world_settings.json')
    with open(ws_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)


class MapViewer:
    def __init__(self, screen_width=1280, screen_height=720):
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("TTRPG World Builder & Simulator (Unified)")
        
        # Navigation
        self.zoom = 7.0  # Default zoom factor
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.dragging = False
        self.dragged = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # Map center coordinates
        self.map_center_x = 50.0
        self.map_center_y = 50.0
        
        # Selection & Editor Tabs
        self.selected_cell = None
        self.active_tab = 'stats'  # 'stats', 'build', 'cults', 'biome'
        
        # Simulation model connection
        self.model = None
        self.autoplay = False
        self.last_tick_time = 0
        
        # Visual Layers
        self.active_layer = 'biomes'
        
        # Calendar & Cosmology state
        self.current_day = 0
        self.year = 1
        self.day_of_year = 1
        self.month_name = ""
        self.season_name = ""
        self.moon_phases = {}
        
        # Data caches
        self.cells = []
        self.edges = []
        self.factions = {}  # cell_id -> faction_data
        self.resource_nodes = []
        
        # Spatial partitioning grid buckets for instant hover lookups
        self.grid_buckets = {}
        
        # Premium palette for all 17 factions
        self.faction_colors = {
            1: (180, 50, 50),     # Red - Ursine Hegemony
            2: (50, 180, 50),     # Green - River Folk
            3: (100, 100, 180),   # Purple/Blue - Sump-Kin
            4: (180, 150, 50),    # Orange/Yellow - Iron Caladrea
            5: (180, 50, 180),    # Pink - Vaneer Concord
            6: (50, 180, 180),    # Cyan - Hive Collective
            7: (230, 126, 34),    # Dark Orange - Avians
            8: (46, 204, 113),    # Emerald Green - Flower Valwey
            9: (39, 174, 96),     # Nephrite Green - Sylvian
            10: (241, 196, 15),   # Sun Yellow - Sciute
            11: (155, 89, 182),   # Amethyst Purple - Meridian Chain
            12: (52, 152, 219),   # Peter River Blue - Prism Lizards
            13: (26, 188, 156),   # Turquoise - Canopy Clans
            14: (243, 156, 18),   # Orange - East Hounds
            15: (149, 165, 166),  # Asbestos Grey - Guirrilla Clans
            16: (211, 84, 0),     # Pumpkin Orange - Theocracy
            17: (127, 140, 141)   # Concrete Grey - The Reliance
        }
        self.logs = []
        
        # ============ EDITOR STATE ============
        self.edit_mode = True  # Default to True so brush clicks paint immediately
        self.brush_radius = 3      # Number of cells radius (1-20)
        self.brush_power = 5       # Strength 1-10
        self.brush_tool = 'paint_biome'  # Active brush tool name
        self.brush_tools_list = [
            'elev_up', 'elev_down', 'elev_smooth', 'elev_level',
            'paint_biome', 'paint_faction', 'paint_cult', 'paint_fringe',
            'paint_ecology', 'place_resource', 'place_chaos', 'place_convergence'
        ]
        self.brush_tool_labels = {
            'elev_up': 'Elevation Up',
            'elev_down': 'Elevation Down',
            'elev_smooth': 'Elevation Smooth',
            'elev_level': 'Elevation Level',
            'paint_biome': 'Paint Biome',
            'paint_faction': 'Paint Faction',
            'paint_cult': 'Paint Cult',
            'paint_fringe': 'Paint Fringe',
            'paint_ecology': 'Paint Ecology',
            'place_resource': 'Place Resource',
            'place_chaos': 'Place Chaos Node',
            'place_convergence': 'Place Convergence',
        }
        # Palette selections for painting
        self.selected_biome_idx = 0
        self.selected_faction_idx = 0
        self.selected_cult_idx = 0
        self.selected_fringe_idx = 0
        self.selected_resource_idx = 0
        self.active_elevation = 0.5  # Target elevation for Level brush
        self.painting = False  # Is mouse currently painting
        
        # ============ CONFIG OVERLAY STATE ============
        self.config_overlay_open = False
        self.config_tab = 'physics'  # 'physics', 'calendar', 'entities', 'rules'
        self.world_settings = load_world_settings()
        self.config_scroll_y = 0  # Scroll offset for long config pages
        
        # Load assets
        self.sprites = {}
        self.textures = {}  # Store original-size cleaned textures for tiling
        self.small_sprites = {} # Pre-scaled sprites for structures (high performance)
        
        self.load_spritesheet()
        self.sync_data()

    def remove_checkerboard(self, surface):
        """Removes the white/grey checkerboard background of a sprite using an optimized BFS flood-fill from edges."""
        w, h = surface.get_size()
        visited = [[False] * h for _ in range(w)]
        queue = []
        
        for x in range(w):
            queue.append((x, 0))
            visited[x][0] = True
            queue.append((x, h - 1))
            visited[x][h - 1] = True
        for y in range(1, h - 1):
            queue.append((0, y))
            visited[0][y] = True
            queue.append((w - 1, y))
            visited[w - 1][y] = True
            
        idx = 0
        while idx < len(queue):
            x, y = queue[idx]
            idx += 1
            
            color = surface.get_at((x, y))
            is_white = color.r >= 240 and color.g >= 240 and color.b >= 240
            is_grey = (210 <= color.r <= 235 and 
                       210 <= color.g <= 235 and 
                       210 <= color.b <= 235 and 
                       abs(color.r - color.g) <= 5 and 
                       abs(color.g - color.b) <= 5)
                       
            if is_white or is_grey:
                surface.set_at((x, y), (0, 0, 0, 0))
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and not visited[nx][ny]:
                        visited[nx][ny] = True
                        queue.append((nx, ny))

    def load_spritesheet(self):
        """Loads and slices the spritesheet, removes checkerboards, and caches textures/sprites."""
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')
        sheet_path = os.path.join(assets_dir, 'spritesheet.png')
        
        if not os.path.exists(sheet_path):
            print(f"Warning: Spritesheet not found at {sheet_path}. Running with fallback shapes.")
            return

        try:
            sheet = pygame.image.load(sheet_path).convert_alpha()
            y_bounds = [0, 127, 255, 383, 511, 639, 768, 891, 1010, 1126, 1253, 1393, 1534]
            tile_w = 176
            cols = 16
            
            for r in range(12):
                y_start = y_bounds[r]
                y_end = y_bounds[r + 1]
                h = y_end - y_start
                for c in range(cols):
                    rect = pygame.Rect(c * tile_w + 2, y_start + 2, tile_w - 4, h - 4)
                    sub = sheet.subsurface(rect).copy()
                    
                    self.remove_checkerboard(sub)
                    self.textures[(r + 1, c + 1)] = sub
                    
                    scaled = pygame.transform.smoothscale(sub, (32, 23))
                    self.sprites[(r + 1, c + 1)] = scaled
                    
                    # Pre-cache small 20x15 versions for structures (massive performance boost)
                    self.small_sprites[(r + 1, c + 1)] = pygame.transform.smoothscale(sub, (20, 15))
            print(f"Successfully loaded, sliced, and trimmed spritesheet: {len(self.sprites)} sprites cached.")
        except Exception as e:
            print(f"Error loading spritesheet: {e}")

    def populate_node_types(self):
        """Constructs placeable resource node types dynamically from self.world_settings."""
        resources = self.world_settings.get('resources_and_materials', [])
        recipes = self.world_settings.get('production_recipes', [])
        
        global NODE_TYPES
        NODE_TYPES = []
        
        def get_icon(name):
            if "Iron" in name: return "Fe"
            if "Copper" in name: return "Cu"
            if "Coral" in name: return "Co"
            if "Dragon" in name: return "Ds"
            if "Osmium" in name: return "Os"
            if "Steel" in name: return "St"
            if "Coal" in name: return "Cl"
            if "Grain" in name: return "Gr"
            if "Wood" in name or "Lumber" in name: return "Wd"
            if "Stone" in name: return "St"
            clean = "".join([c for c in name if c.isalnum()])
            return clean[:2].capitalize() if len(clean) >= 2 else name[:2].upper()
            
        def get_color(name):
            if "Iron" in name: return (120, 120, 120)
            if "Copper" in name: return (184, 115, 51)
            if "Coral" in name: return (255, 127, 80)
            if "Dragon" in name: return (186, 85, 211)
            if "Osmium" in name: return (0, 206, 209)
            if "Steel" in name: return (70, 130, 180)
            if "Coal" in name: return (50, 50, 50)
            if "Grain" in name: return (200, 180, 50)
            if "Wood" in name or "Lumber" in name: return (139, 90, 43)
            if "Stone" in name: return (140, 140, 140)
            return (200, 180, 50)
            
        for res in resources:
            name = res.get('name')
            harvest = res.get('harvested_from', 'General')
            node_name = f"Rich {name}" if "Vein" not in name and "Seam" not in name and "Crater" not in name else name
            NODE_TYPES.append({
                "name": node_name,
                "icon": get_icon(name),
                "desc": f"Yields {name} (from {harvest})",
                "yield": 400.0,
                "color": get_color(name)
            })
            
        for rec in recipes:
            name = rec.get('name')
            desc = rec.get('description', 'Refined good')
            node_name = f"Ancient {name} Depot" if "Ruins" not in name and "Depot" not in name else name
            NODE_TYPES.append({
                "name": node_name,
                "icon": get_icon(name),
                "desc": desc,
                "yield": 200.0,
                "color": get_color(name)
            })

    def sync_data(self):
        """Queries the current cells, edges, factions, and logs from SQLite database."""
        # Re-initialize simulation model in-memory to load new database edits
        if self.model:
            from simulation_engine import TTRPGWorldModel
            old_tick = self.model.current_tick
            self.model = TTRPGWorldModel()
            self.model.current_tick = old_tick
            
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Fetch cells
        cur.execute('SELECT * FROM cells')
        cell_rows = cur.fetchall()
        self.cells = []
        self.grid_buckets = {}
        
        for row in cell_rows:
            try:
                poly = loads(row['geom_wkt'])
                coords = list(poly.exterior.coords)
                centroid_x, centroid_y = poly.centroid.x, poly.centroid.y
                
                # Parse JSON fields
                cults_influence = json.loads(row['cults_json']) if row['cults_json'] else {}
                fringe_influence = json.loads(row['fringe_json']) if row['fringe_json'] else {}
                flora = json.loads(row['flora_json']) if row['flora_json'] else {}
                fauna = json.loads(row['fauna_json']) if row['fauna_json'] else {}
                
                cell_dict = {
                    'id': row['id'],
                    'biome': row['biome'],
                    'elevation': row['elevation'],
                    'depth_elevation': row['depth_elevation'],
                    'food_supply': row['food_supply'],
                    'chaos_saturation': row['chaos_saturation'],
                    'weather': row['weather'],
                    'controlling_burg_id': row['controlling_burg_id'],
                    'cults_influence': cults_influence,
                    'fringe_influence': fringe_influence,
                    'flora': flora,
                    'fauna': fauna,
                    'coords': coords,
                    'center': (centroid_x, centroid_y)
                }
                
                self.cells.append(cell_dict)
                
                # Spatial partitioning grid buckets (10x10 area size)
                bx = int(centroid_x / 10)
                by = int(centroid_y / 10)
                bkey = (bx, by)
                if bkey not in self.grid_buckets:
                    self.grid_buckets[bkey] = []
                self.grid_buckets[bkey].append(cell_dict)
                
            except Exception as e:
                print(f"Error loading polygon WKT for cell {row['id']}: {e}")
                
        # Calculate dynamic map center boundaries
        if self.cells:
            xs = [c['center'][0] for c in self.cells]
            ys = [c['center'][1] for c in self.cells]
            self.map_center_x = (min(xs) + max(xs)) / 2.0
            self.map_center_y = (min(ys) + max(ys)) / 2.0
        else:
            self.map_center_x = 50.0
            self.map_center_y = 50.0
                
        # 2. Fetch edges
        cur.execute('SELECT cell_a, cell_b FROM cell_edges')
        self.edges = [dict(r) for r in cur.fetchall()]
        
        # 3. Fetch macro groups (factions)
        cur.execute('SELECT * FROM macro_groups')
        self.factions = {r['cell_id']: dict(r) for r in cur.fetchall()}
        
        # 4. Fetch resource nodes
        cur.execute('SELECT * FROM resource_nodes')
        self.resource_nodes = [dict(r) for r in cur.fetchall()]
        
        # 5. Fetch logs
        cur.execute('SELECT * FROM simulation_logs ORDER BY id DESC LIMIT 5')
        self.logs = [dict(r) for r in cur.fetchall()]
        
        # 6. Fetch global state & calendar progress
        cur.execute('SELECT current_day FROM global_state WHERE id = 1')
        row_gs = cur.fetchone()
        self.current_day = row_gs[0] if row_gs else 0
        
        # Re-populate dynamic placeable node types
        self.populate_node_types()
        
        # Calculate season/moons based on current day
        cal_settings = self.world_settings.get('calendar', {})
        cal_mgr = CalendarManager(settings=cal_settings)
        year_len = cal_mgr.days_per_year
        self.year = (self.current_day // year_len) + 1
        self.day_of_year = (self.current_day % year_len) + 1
        self.month_name = cal_mgr.get_month_name(self.current_day)
        self.season_name = cal_mgr.get_season(self.current_day)
        self.moon_phases = cal_mgr.get_moon_phase(self.current_day)
        
        cur.close()
        conn.close()

    def to_screen(self, x, y):
        """Converts map coordinates to viewport screen coordinates centered around the map center."""
        viewport_w = 960
        viewport_h = 720
        screen_x = int((x - self.map_center_x) * self.zoom + (viewport_w / 2) + self.pan_x)
        screen_y = int((y - self.map_center_y) * self.zoom + (viewport_h / 2) + self.pan_y)
        return screen_x, screen_y

    def from_screen(self, sx, sy):
        """Converts screen coordinates back to map coordinates."""
        viewport_w = 960
        viewport_h = 720
        mx = (sx - (viewport_w / 2) - self.pan_x) / self.zoom + self.map_center_x
        my = (sy - (viewport_h / 2) - self.pan_y) / self.zoom + self.map_center_y
        return mx, my

    def get_cell_at_pos(self, mouse_pos):
        """Finds the cell closest to the click position in screen coordinates using spatial grid buckets (instant)."""
        if mouse_pos[0] >= 960:
            return None
        mx, my = self.from_screen(mouse_pos[0], mouse_pos[1])
        
        bx = int(mx / 10)
        by = int(my / 10)
        
        # Search this bucket and neighboring 8 buckets
        candidates = []
        for dbx in [-1, 0, 1]:
            for dby in [-1, 0, 1]:
                bkey = (bx + dbx, by + dby)
                if bkey in self.grid_buckets:
                    candidates.extend(self.grid_buckets[bkey])
                    
        if not candidates:
            candidates = self.cells
            
        if not candidates:
            return None
            
        closest_cell = min(candidates, key=lambda c: (c['center'][0] - mx)**2 + (c['center'][1] - my)**2)
        dist = np.hypot(closest_cell['center'][0] - mx, closest_cell['center'][1] - my)
        
        if dist < 10.0:
            return closest_cell
        return None

    def get_cells_in_brush(self, map_x, map_y):
        """Returns all cells within the brush radius of a map coordinate."""
        if not self.cells:
            return []
        
        # Estimate average cell spacing from first few cells
        map_radius = self.brush_radius * 1.5  # Approximate map units per cell radius
        
        bx_min = int((map_x - map_radius) / 10) - 1
        bx_max = int((map_x + map_radius) / 10) + 1
        by_min = int((map_y - map_radius) / 10) - 1
        by_max = int((map_y + map_radius) / 10) + 1
        
        candidates = []
        for bx in range(bx_min, bx_max + 1):
            for by in range(by_min, by_max + 1):
                bkey = (bx, by)
                if bkey in self.grid_buckets:
                    candidates.extend(self.grid_buckets[bkey])
        
        result = []
        r_sq = map_radius * map_radius
        for c in candidates:
            cx, cy = c['center']
            dx = cx - map_x
            dy = cy - map_y
            if dx*dx + dy*dy <= r_sq:
                result.append(c)
        return result

    def get_cell_color(self, cell):
        """Calculates color for a cell based on the active layer."""
        if self.active_layer == 'elevation':
            elev = cell['elevation']
            if elev < 0: # Ocean depths
                val = int(abs(elev) * 150) + 50
                return (20, 20, max(50, min(255, val)))
            else: # Land
                val = int(elev * 180) + 70
                return (val, int(val * 0.9), int(val * 0.7))
                
        elif self.active_layer == 'factions':
            # Look up faction via the controlling settlement (province) of the cell
            burg_id = cell.get('controlling_burg_id')
            faction_info = self.factions.get(burg_id)
            if faction_info:
                fid = faction_info['faction_id']
                return self.faction_colors.get(fid, (150, 150, 150))
            return (220, 220, 220) if cell['elevation'] >= 0 else (40, 60, 90)
            
        elif self.active_layer == 'settlements':
            burg_id = cell.get('controlling_burg_id')
            if burg_id:
                # Generate consistent colors for province influence areas
                r = (burg_id * 37) % 200 + 55
                g = (burg_id * 59) % 200 + 55
                b = (burg_id * 83) % 200 + 55
                return (r, g, b)
            return (220, 220, 220) if cell['elevation'] >= 0 else (40, 60, 90)
            
        elif self.active_layer == 'cults':
            if cell.get('cults_influence'):
                dominant_cult = None
                max_inf = 0.0
                for name, inf in cell['cults_influence'].items():
                    if inf > max_inf:
                        max_inf = inf
                        dominant_cult = name
                
                if dominant_cult and max_inf > 0.02:
                    cult_colors = {
                        "Tiraton": (231, 76, 60),      # Bright Red
                        "Stagus": (46, 204, 113),       # Light Green
                        "Metrion": (52, 152, 219),      # Light Blue
                        "Aurgenas": (241, 196, 15),     # Yellow
                        "Vecelo": (155, 89, 182),      # Purple
                        "Lophex": (26, 188, 156),       # Turquoise
                        "Tyrustis": (230, 126, 34),     # Orange
                        "Opecten": (52, 73, 94),        # Dark Blue-Grey
                        "Carulkem": (243, 156, 18),     # Dark Yellow/Orange
                        "Termhill": (149, 165, 166),    # Silver
                        "Virantor": (120, 40, 140),     # Dark Purple
                        "Gavusrix": (180, 50, 50),      # Dark Red
                        "Wardens": (240, 240, 240)      # White
                    }
                    base_color = cult_colors.get(dominant_cult, (150, 150, 150))
                    factor = min(1.0, max_inf * 3.0)
                    r = int(base_color[0] * factor + 40 * (1 - factor))
                    g = int(base_color[1] * factor + 40 * (1 - factor))
                    b = int(base_color[2] * factor + 40 * (1 - factor))
                    return (r, g, b)
            return (40, 40, 40)
            
        elif self.active_layer == 'fringe':
            if cell.get('fringe_influence'):
                dominant_fringe = None
                max_inf = 0.0
                for name, inf in cell['fringe_influence'].items():
                    if inf > max_inf:
                        max_inf = inf
                        dominant_fringe = name
                
                if dominant_fringe and max_inf > 0.02:
                    fringe_colors = {
                        "Obsidian Cartel": (30, 30, 30),        # Near Black
                        "Freesky Barons": (135, 206, 235),     # Sky Blue
                        "Ghost Wind Raiders": (218, 165, 32),   # Goldenrod
                        "Gilded Compass": (255, 215, 0),       # Gold
                        "Crimson Coursairs": (220, 20, 60),     # Crimson
                        "Silent Current": (0, 128, 128),        # Teal
                        "The Black Label": (75, 0, 130),        # Indigo
                        "The Otter Syndicate": (139, 69, 19),   # Saddle Brown
                        "The Spring Ghosts": (144, 238, 144)    # Light Green
                    }
                    base_color = fringe_colors.get(dominant_fringe, (150, 150, 150))
                    factor = min(1.0, max_inf * 4.0)
                    r = int(base_color[0] * factor + 40 * (1 - factor))
                    g = int(base_color[1] * factor + 40 * (1 - factor))
                    b = int(base_color[2] * factor + 40 * (1 - factor))
                    return (r, g, b)
            return (40, 40, 40)
            
        elif self.active_layer == 'ecology':
            flora_pop = cell.get('flora', {}).get('population', 0.0)
            fauna_pop = cell.get('fauna', {}).get('population', 0.0)
            green = int(min(255, (flora_pop / 100.0) * 200))
            red = int(min(255, (fauna_pop / 50.0) * 200))
            return (red, green, 40)
            
        elif self.active_layer == 'resources':
            return (45, 45, 45)
            
        else: # 'biomes' layer (default)
            if cell['chaos_saturation'] > 0.8:
                return (139, 0, 0)
            biome = cell['biome']
            biome_colors = {
                'Forest': (45, 106, 45),
                'Plains': (168, 201, 110),
                'Desert': (212, 168, 67),
                'Mountain': (138, 138, 138),
                'Swamp': (74, 122, 74),
                'Ocean': (26, 95, 138),
                'Coastal': (72, 180, 195),
                'Reef': (219, 112, 147),
                'Abyssal': (10, 25, 60),
                'Thermal': (120, 20, 60)
            }
            return biome_colors.get(biome, (200, 200, 200))

    def draw_map(self):
        """Draws cells, borders, edges, and sprites with optimized boundary frustum culling directly to screen."""
        pygame.draw.rect(self.screen, (30, 30, 30), (0, 0, 960, 720))
        
        if not self.cells:
            return
            
        # Frustum culling bounds in map coordinates (avoids drawing offscreen cells)
        viewport_w = 960
        viewport_h = 720
        x0 = (0 - (viewport_w / 2) - self.pan_x) / self.zoom + self.map_center_x
        x1 = (viewport_w - (viewport_w / 2) - self.pan_x) / self.zoom + self.map_center_x
        y0 = (0 - (viewport_h / 2) - self.pan_y) / self.zoom + self.map_center_y
        y1 = (viewport_h - (viewport_h / 2) - self.pan_y) / self.zoom + self.map_center_y
        
        margin = 15.0  # Buffer margin
        mx_min, mx_max = min(x0, x1) - margin, max(x0, x1) + margin
        my_min, my_max = min(y0, y1) - margin, max(y0, y1) + margin
        
        # 1. Draw Cell Polygons (Solid layer backgrounds)
        for cell in self.cells:
            cx, cy = cell['center']
            if not (mx_min <= cx <= mx_max and my_min <= cy <= my_max):
                continue
                
            surface_coords = [self.to_screen(x, y) for x, y in cell['coords']]
            if len(surface_coords) < 3:
                continue
                
            color = self.get_cell_color(cell)
            pygame.draw.polygon(self.screen, color, surface_coords)
            pygame.draw.polygon(self.screen, (50, 50, 50), surface_coords, 1)

        # 2. Draw Sprite Overlays (Capitals, Units, Weather, and Placed Structures) only on settlement cells when zoomed in
        if self.zoom >= 10.0:
            for cell in self.cells:
                cx, cy = cell['center']
                if not (mx_min <= cx <= mx_max and my_min <= cy <= my_max):
                    continue
                    
                scx, scy = self.to_screen(cx, cy)
                
                # Check if this exact cell is a settlement hub cell
                faction_info = self.factions.get(cell['id'])
                is_subaquatic = cell['elevation'] < 0
                
                sprite = None
                if faction_info:
                    if faction_info.get('is_capital') == 1:
                        if is_subaquatic:
                            sprite = self.sprites.get((6, 12))  # Sunken Ruins
                        else:
                            sprite = self.sprites.get((10, 10)) # Castle Keep
                    elif faction_info['faction_id'] > 0 and faction_info.get('barracks_count', 0) > 0:
                        if is_subaquatic:
                            sprite = self.sprites.get((11, 10)) # School of Fish
                        else:
                            fid = faction_info['faction_id']
                            faction_unit_cols = {
                                1: 1, 2: 2, 3: 3, 4: 4, 5: 5,
                                6: 8, 7: 5, 8: 9, 9: 12, 10: 7,
                                11: 10, 12: 11, 13: 5, 14: 2, 15: 3,
                                16: 10, 17: 12
                            }
                            unit_col = faction_unit_cols.get(fid)
                            if unit_col:
                                sprite = self.sprites.get((11, unit_col))
                            
                if sprite:
                    self.screen.blit(sprite, (scx - 16, scy - 11))
                    
                # Placed Structures drawn around the center (only on settlement cells)
                if faction_info:
                    if is_subaquatic:
                        if faction_info.get('kelp_farms_count', 0) > 0:
                            s = self.small_sprites.get((4, 5))
                            if s: self.screen.blit(s, (scx - 22, scy - 18))
                                
                        if faction_info.get('coral_mines_count', 0) > 0:
                            s = self.small_sprites.get((4, 4))
                            if s: self.screen.blit(s, (scx + 2, scy - 18))
                                
                        if faction_info.get('underwater_domes_count', 0) > 0:
                            s = self.small_sprites.get((10, 4))
                            if s: self.screen.blit(s, (scx - 22, scy + 3))
                                
                        if faction_info.get('reef_walls_count', 0) > 0:
                            s = self.small_sprites.get((4, 7))
                            if s: self.screen.blit(s, (scx + 2, scy + 3))
                    else:
                        if faction_info.get('farms_count', 0) > 0:
                            s = self.small_sprites.get((10, 1))
                            if s: self.screen.blit(s, (scx - 22, scy - 18))
                                
                        if faction_info.get('mines_count', 0) > 0:
                            s = self.small_sprites.get((10, 3))
                            if s: self.screen.blit(s, (scx + 2, scy - 18))
                                
                        if faction_info.get('barracks_count', 0) > 0:
                            s = self.small_sprites.get((10, 10))
                            if s: self.screen.blit(s, (scx - 22, scy + 3))
                                
                        if faction_info.get('watchtowers_count', 0) > 0:
                            s = self.small_sprites.get((10, 11))
                            if s: self.screen.blit(s, (scx + 2, scy + 3))

                # Local Weather Overlays
                if cell['weather'] == 'Chaos Storm':
                    effect = self.sprites.get((12, 5))
                    if effect: self.screen.blit(effect, (scx - 16, scy - 11))
                        
        # 3. Draw Resource Node Markers (Active circles with 2-char label)
        if self.active_layer == 'resources' and self.zoom >= 3.0:
            font_node = pygame.font.SysFont("arial", 10, bold=True)
            for node in getattr(self, 'resource_nodes', []):
                cid = node['cell_id']
                cell = next((c for c in self.cells if c['id'] == cid), None)
                if cell:
                    cx, cy = cell['center']
                    if not (mx_min <= cx <= mx_max and my_min <= cy <= my_max):
                        continue
                    scx, scy = self.to_screen(cx, cy)
                    if 0 <= scx < 960 and 0 <= scy < 720:
                        name = node['name']
                        node_style = next((nt for nt in NODE_TYPES if nt['name'] == name), None)
                        if node_style:
                            color = node_style['color']
                            label = node_style['icon']
                        else:
                            if "Iron" in name:
                                color, label = (120, 120, 120), "Fe"
                            elif "Copper" in name:
                                color, label = (184, 115, 51), "Cu"
                            elif "Coral" in name:
                                color, label = (255, 127, 80), "Co"
                            elif "Dragonstone" in name:
                                color, label = (186, 85, 211), "Ds"
                            elif "Osmium" in name:
                                color, label = (0, 206, 209), "Os"
                            elif "Steel" in name:
                                color, label = (70, 130, 180), "St"
                            elif "Coal" in name:
                                color, label = (50, 50, 50), "Cl"
                            elif "Grain" in name:
                                color, label = (200, 180, 50), "Gr"
                            else:
                                color, label = (200, 180, 50), "R"
                            
                        pygame.draw.circle(self.screen, (30, 30, 30), (scx, scy), 9)
                        pygame.draw.circle(self.screen, color, (scx, scy), 8)
                        
                        txt = font_node.render(label, True, (255, 255, 255) if color[0] < 180 else (0, 0, 0))
                        txt_rect = txt.get_rect(center=(scx, scy))
                        self.screen.blit(txt, txt_rect)
                        
        # 4. Highlight Selected Cell Outline
        if self.selected_cell:
            surface_coords = [self.to_screen(x, y) for x, y in self.selected_cell['coords']]
            if len(surface_coords) >= 3:
                pygame.draw.polygon(self.screen, (255, 255, 0), surface_coords, 3)

        # 5. Draw Brush Cursor Circle when in edit mode
        if self.edit_mode:
            mouse_pos = pygame.mouse.get_pos()
            if mouse_pos[0] < 960:
                # Draw brush radius circle at mouse position
                map_radius = self.brush_radius * 1.5
                screen_radius = int(map_radius * self.zoom)
                if screen_radius > 1:
                    pygame.draw.circle(self.screen, (255, 255, 0, 128), mouse_pos, screen_radius, 2)
                    # Draw crosshair
                    pygame.draw.line(self.screen, (255, 255, 0), (mouse_pos[0] - 5, mouse_pos[1]), (mouse_pos[0] + 5, mouse_pos[1]), 1)
                    pygame.draw.line(self.screen, (255, 255, 0), (mouse_pos[0], mouse_pos[1] - 5), (mouse_pos[0], mouse_pos[1] + 5), 1)

    def draw_tooltip(self):
        """Draws a hover tooltip near the mouse cursor with cell data/information."""
        mouse_pos = pygame.mouse.get_pos()
        if mouse_pos[0] >= 960 or mouse_pos[1] >= 720:
            return
        if self.config_overlay_open:
            return
            
        cell = self.get_cell_at_pos(mouse_pos)
        if not cell:
            return
            
        cell_id = cell['id']
        controlling_burg_id = cell.get('controlling_burg_id')
        province_info = self.factions.get(controlling_burg_id)
        
        lines = []
        lines.append(f"Cell ID: {cell_id} | Controlling Hub ID: {controlling_burg_id}")
        lines.append(f"Biome: {cell['biome']} (Elev: {cell['elevation']:.2f})")
        lines.append(f"Weather: {cell['weather']}")
        
        # Display specific details based on active layer to make layers self-explanatory
        if self.active_layer == 'cults' and cell.get('cults_influence'):
            lines.append("Cult Influences:")
            sorted_cults = sorted(cell['cults_influence'].items(), key=lambda x: x[1], reverse=True)
            for name, val in sorted_cults[:3]:
                if val > 0.0:
                    lines.append(f" - {name}: {val*100:.0f}%")
        elif self.active_layer == 'fringe' and cell.get('fringe_influence'):
            lines.append("Fringe Group Influences:")
            sorted_fringe = sorted(cell['fringe_influence'].items(), key=lambda x: x[1], reverse=True)
            for name, val in sorted_fringe[:3]:
                if val > 0.0:
                    lines.append(f" - {name}: {val*100:.0f}%")
        elif self.active_layer == 'ecology':
            lines.append(f"Ecology (Flora): {cell['flora'].get('name', 'None')} ({cell['flora'].get('population', 0.0):.1f})")
            lines.append(f"Ecology (Fauna): {cell['fauna'].get('name', 'None')} ({cell['fauna'].get('population', 0.0):.1f})")
            
        matching_node = next((n for n in getattr(self, 'resource_nodes', []) if n['cell_id'] == cell_id), None)
        if matching_node:
            lines.append(f"Resource Node: {matching_node['name']} ({matching_node['yield_remaining']:.0f} left)")
            
        if province_info:
            f_name = province_info['faction_name']
            is_cap = " (Capital)" if (province_info.get('is_capital') == 1 and cell_id == controlling_burg_id) else ""
            if cell_id == controlling_burg_id:
                lines.append(f"Settlement Hub: {f_name}{is_cap}")
            else:
                lines.append(f"Province/Faction: {f_name}{is_cap}")
            lines.append(f"Prov Pop: {province_info['population']} | Discontent: {province_info['discontent']:.2f}")
        
        font = pygame.font.SysFont("arial", 12)
        line_surfaces = [font.render(line, True, (255, 255, 255)) for line in lines]
        
        width = max(s.get_width() for s in line_surfaces) + 20
        height = sum(s.get_height() for s in line_surfaces) + 14
        
        tx = mouse_pos[0] + 15
        ty = mouse_pos[1] + 15
        if tx + width > 960:
            tx = mouse_pos[0] - width - 15
        if ty + height > 720:
            ty = mouse_pos[1] - height - 15
            
        tooltip_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        tooltip_surf.fill((30, 34, 42, 230))
        pygame.draw.rect(tooltip_surf, (80, 90, 100), (0, 0, width, height), 1)
        
        curr_y = 7
        for s in line_surfaces:
            tooltip_surf.blit(s, (10, curr_y))
            curr_y += s.get_height()
            
        self.screen.blit(tooltip_surf, (tx, ty))

    def draw_sidebar(self):
        """Draws control buttons, legend panel, editor tools, and advanced tabbed editor."""
        sidebar_x = 960
        pygame.draw.rect(self.screen, (40, 44, 52), (sidebar_x, 0, 320, 720))
        pygame.draw.line(self.screen, (80, 80, 80), (sidebar_x, 0), (sidebar_x, 720), 2)
        
        font_large = pygame.font.SysFont("arial", 20, bold=True)
        font_medium = pygame.font.SysFont("arial", 14, bold=True)
        font_small = pygame.font.SysFont("arial", 12)
        font_small_bold = pygame.font.SysFont("arial", 11, bold=True)
        font_tiny = pygame.font.SysFont("arial", 10)
        
        # Render Title
        title = font_large.render("TTRPG World Conductor", True, (255, 255, 255))
        self.screen.blit(title, (sidebar_x + 20, 10))
        
        # Simulation stats
        tick_val = self.model.current_tick if self.model else 0
        tick_text = font_small.render(f"Tick: {tick_val}", True, (170, 220, 255))
        self.screen.blit(tick_text, (sidebar_x + 20, 36))
        
        layer_text = font_small.render(f"Layer: {self.active_layer.upper()}", True, (255, 255, 150))
        self.screen.blit(layer_text, (sidebar_x + 100, 36))
        
        autoplay_status = "ON" if self.autoplay else "OFF"
        color = (100, 255, 100) if self.autoplay else (255, 100, 100)
        auto_text = font_small.render(f"Auto: {autoplay_status}", True, color)
        self.screen.blit(auto_text, (sidebar_x + 220, 36))
        
        # Render Real-Time Simulation Calendar Date & Moon Phases
        year_text = f"Year {self.year}, Day {self.day_of_year} | {self.month_name} ({self.season_name})"
        self.screen.blit(font_small_bold.render(year_text, True, (235, 245, 255)), (sidebar_x + 20, 56))
        
        moons_str = "Moons: " + ", ".join([f"{name}: {phase}" for name, phase in getattr(self, 'moon_phases', {}).items()])
        self.screen.blit(font_tiny.render(moons_str, True, (170, 180, 195)), (sidebar_x + 20, 74))
        
        # Actions Grid (Y = 96 to 144)
        self.buttons = {
            'tick': pygame.Rect(sidebar_x + 20, 96, 90, 22),
            'auto': pygame.Rect(sidebar_x + 115, 96, 90, 22),
            'edit_toggle': pygame.Rect(sidebar_x + 210, 96, 90, 22),
            'sync': pygame.Rect(sidebar_x + 20, 122, 90, 22),
            'save_json': pygame.Rect(sidebar_x + 115, 122, 90, 22),
            'push_db': pygame.Rect(sidebar_x + 210, 122, 90, 22),
        }
        
        btn_labels = {
            'tick': "Run Tick",
            'auto': "Autoplay",
            'edit_toggle': "Paint Mode",
            'sync': "Sync DB",
            'save_json': "Save settings",
            'push_db': "Push DB",
        }
        
        btn_colors = {
            'edit_toggle': (70, 130, 70) if self.edit_mode else (60, 70, 85),
        }
        
        for name, rect in self.buttons.items():
            bg = btn_colors.get(name, (60, 70, 85))
            pygame.draw.rect(self.screen, bg, rect, border_radius=4)
            txt = font_tiny.render(btn_labels[name], True, (230, 240, 255))
            txt_rect = txt.get_rect(center=rect.center)
            self.screen.blit(txt, txt_rect)
            
        # Section title
        self.screen.blit(font_small_bold.render("VISUAL LAYERS & SETTINGS", True, (255, 200, 100)), (sidebar_x + 20, 150))
        
        # Array of layers with paint and settings side by side (Y = 168 to 366)
        layers_list = [
            ('biomes', 'Biomes', 'biomes'),
            ('elevation', 'Climate', 'elevation'),
            ('calendar', 'Calendar', 'calendar'),
            ('factions', 'Factions', 'factions'),
            ('settlements', 'Settlements', 'settlements'),
            ('cults', 'Cults', 'cults'),
            ('fringe', 'Fringe', 'fringe'),
            ('ecology', 'Ecology', 'ecology'),
            ('resources', 'Resources', 'resources')
        ]
        
        for idx, (lay_id, name, settings_id) in enumerate(layers_list):
            y = 168 + idx * 22
            
            # Left Button: Select / Paint
            rect_paint = pygame.Rect(sidebar_x + 20, y, 130, 18)
            self.buttons[f'lay_{lay_id}'] = rect_paint
            
            is_active = (self.active_layer == lay_id)
            bg_paint = (90, 120, 90) if is_active else (45, 50, 62)
            pygame.draw.rect(self.screen, bg_paint, rect_paint, border_radius=3)
            if is_active:
                pygame.draw.rect(self.screen, (150, 255, 150), rect_paint, 1, border_radius=3)
            
            paint_label = f"Paint {name}" if lay_id != 'calendar' else "Calendar Info"
            txt_paint = font_tiny.render(paint_label, True, (255, 255, 255) if is_active else (160, 160, 160))
            self.screen.blit(txt_paint, txt_paint.get_rect(center=rect_paint.center))
            
            # Right Button: Edit Settings
            rect_edit = pygame.Rect(sidebar_x + 170, y, 130, 18)
            self.buttons[f'edit_settings_{settings_id}'] = rect_edit
            pygame.draw.rect(self.screen, (100, 80, 110), rect_edit, border_radius=3)
            
            txt_edit = font_tiny.render(f"Edit {name}", True, (245, 235, 255))
            self.screen.blit(txt_edit, txt_edit.get_rect(center=rect_edit.center))
            
        # Brush controls (Y = 372 to 438)
        y = 372
        self.screen.blit(font_small.render(f"Brush Radius: {self.brush_radius}", True, (200, 210, 230)), (sidebar_x + 20, y))
        self.buttons['radius_minus'] = pygame.Rect(sidebar_x + 200, y, 35, 18)
        self.buttons['radius_plus'] = pygame.Rect(sidebar_x + 245, y, 35, 18)
        pygame.draw.rect(self.screen, (100, 70, 70), self.buttons['radius_minus'], border_radius=3)
        pygame.draw.rect(self.screen, (70, 100, 70), self.buttons['radius_plus'], border_radius=3)
        self.screen.blit(font_small_bold.render("-", True, (255,255,255)), font_small_bold.render("-", True, (255,255,255)).get_rect(center=self.buttons['radius_minus'].center))
        self.screen.blit(font_small_bold.render("+", True, (255,255,255)), font_small_bold.render("+", True, (255,255,255)).get_rect(center=self.buttons['radius_plus'].center))
        y += 20
        
        self.screen.blit(font_small.render(f"Brush Power: {self.brush_power}", True, (200, 210, 230)), (sidebar_x + 20, y))
        self.buttons['power_minus'] = pygame.Rect(sidebar_x + 200, y, 35, 18)
        self.buttons['power_plus'] = pygame.Rect(sidebar_x + 245, y, 35, 18)
        pygame.draw.rect(self.screen, (100, 70, 70), self.buttons['power_minus'], border_radius=3)
        pygame.draw.rect(self.screen, (70, 100, 70), self.buttons['power_plus'], border_radius=3)
        self.screen.blit(font_small_bold.render("-", True, (255,255,255)), font_small_bold.render("-", True, (255,255,255)).get_rect(center=self.buttons['power_minus'].center))
        self.screen.blit(font_small_bold.render("+", True, (255,255,255)), font_small_bold.render("+", True, (255,255,255)).get_rect(center=self.buttons['power_plus'].center))
        y += 20
        
        # Display Palette picker based on active layer
        if self.active_layer == 'biomes':
            self.brush_tool = 'paint_biome'
            self.screen.blit(font_small_bold.render("Active Biome to Paint:", True, (200, 200, 255)), (sidebar_x + 20, y))
            y += 16
            self.buttons['palette_prev'] = pygame.Rect(sidebar_x + 20, y, 24, 18)
            self.buttons['palette_next'] = pygame.Rect(sidebar_x + 276, y, 24, 18)
            pygame.draw.rect(self.screen, (80, 70, 60), self.buttons['palette_prev'], border_radius=3)
            pygame.draw.rect(self.screen, (80, 70, 60), self.buttons['palette_next'], border_radius=3)
            self.screen.blit(font_small_bold.render("<", True, (255,255,255)), font_small_bold.render("<", True, (255,255,255)).get_rect(center=self.buttons['palette_prev'].center))
            self.screen.blit(font_small_bold.render(">", True, (255,255,255)), font_small_bold.render(">", True, (255,255,255)).get_rect(center=self.buttons['palette_next'].center))
            biome_name = BIOMES_LIST[self.selected_biome_idx % len(BIOMES_LIST)]
            self.screen.blit(font_small_bold.render(biome_name, True, (255, 230, 150)), (sidebar_x + 52, y + 1))
            
        elif self.active_layer == 'elevation':
            self.screen.blit(font_small_bold.render("Elevation Brush Mode:", True, (200, 200, 255)), (sidebar_x + 20, y))
            y += 16
            modes = ['elev_up', 'elev_down', 'elev_smooth', 'elev_level']
            mode_lbls = {'elev_up': 'Up', 'elev_down': 'Down', 'elev_smooth': 'Smooth', 'elev_level': 'Level'}
            for mi, mode in enumerate(modes):
                bx = sidebar_x + 20 + mi * 70
                rect = pygame.Rect(bx, y, 66, 18)
                self.buttons[f'tool_{mode}'] = rect
                is_m_active = (self.brush_tool == mode)
                bg = (100, 110, 80) if is_m_active else (55, 60, 70)
                pygame.draw.rect(self.screen, bg, rect, border_radius=3)
                if is_m_active:
                    pygame.draw.rect(self.screen, (150, 255, 150), rect, 1, border_radius=3)
                txt = font_tiny.render(mode_lbls[mode], True, (255, 255, 255) if is_m_active else (170, 170, 170))
                self.screen.blit(txt, txt.get_rect(center=rect.center))
                
        elif self.active_layer == 'factions':
            self.brush_tool = 'paint_faction'
            self.screen.blit(font_small_bold.render("Active Faction to Paint:", True, (200, 200, 255)), (sidebar_x + 20, y))
            y += 16
            self.buttons['palette_prev'] = pygame.Rect(sidebar_x + 20, y, 24, 18)
            self.buttons['palette_next'] = pygame.Rect(sidebar_x + 276, y, 24, 18)
            pygame.draw.rect(self.screen, (80, 70, 60), self.buttons['palette_prev'], border_radius=3)
            pygame.draw.rect(self.screen, (80, 70, 60), self.buttons['palette_next'], border_radius=3)
            self.screen.blit(font_small_bold.render("<", True, (255,255,255)), font_small_bold.render("<", True, (255,255,255)).get_rect(center=self.buttons['palette_prev'].center))
            self.screen.blit(font_small_bold.render(">", True, (255,255,255)), font_small_bold.render(">", True, (255,255,255)).get_rect(center=self.buttons['palette_next'].center))
            
            ent = self.world_settings.get('entities', {})
            factions = ent.get('factions', [])
            if factions:
                fac = factions[self.selected_faction_idx % len(factions)]
                fcolor_hex = fac.get('color', '#888888')
                try:
                    r = int(fcolor_hex[1:3], 16)
                    g = int(fcolor_hex[3:5], 16)
                    b = int(fcolor_hex[5:7], 16)
                    fcolor = (r, g, b)
                except Exception:
                    fcolor = (150, 150, 150)
                pygame.draw.rect(self.screen, fcolor, (sidebar_x + 50, y + 2, 14, 14), border_radius=2)
                self.screen.blit(font_small.render(fac['name'][:22], True, (255, 230, 150)), (sidebar_x + 70, y + 1))
                
        elif self.active_layer == 'settlements':
            self.brush_tool = 'paint_faction'
            self.screen.blit(font_small_bold.render("Active Province Faction:", True, (200, 200, 255)), (sidebar_x + 20, y))
            y += 16
            self.buttons['palette_prev'] = pygame.Rect(sidebar_x + 20, y, 24, 18)
            self.buttons['palette_next'] = pygame.Rect(sidebar_x + 276, y, 24, 18)
            pygame.draw.rect(self.screen, (80, 70, 60), self.buttons['palette_prev'], border_radius=3)
            pygame.draw.rect(self.screen, (80, 70, 60), self.buttons['palette_next'], border_radius=3)
            self.screen.blit(font_small_bold.render("<", True, (255,255,255)), font_small_bold.render("<", True, (255,255,255)).get_rect(center=self.buttons['palette_prev'].center))
            self.screen.blit(font_small_bold.render(">", True, (255,255,255)), font_small_bold.render(">", True, (255,255,255)).get_rect(center=self.buttons['palette_next'].center))
            
            ent = self.world_settings.get('entities', {})
            factions = ent.get('factions', [])
            if factions:
                fac = factions[self.selected_faction_idx % len(factions)]
                fcolor_hex = fac.get('color', '#888888')
                try:
                    r = int(fcolor_hex[1:3], 16)
                    g = int(fcolor_hex[3:5], 16)
                    b = int(fcolor_hex[5:7], 16)
                    fcolor = (r, g, b)
                except Exception:
                    fcolor = (150, 150, 150)
                pygame.draw.rect(self.screen, fcolor, (sidebar_x + 50, y + 2, 14, 14), border_radius=2)
                self.screen.blit(font_small.render(fac['name'][:22], True, (255, 230, 150)), (sidebar_x + 70, y + 1))
                
        elif self.active_layer == 'cults':
            self.brush_tool = 'paint_cult'
            self.screen.blit(font_small_bold.render("Active Cult to Paint:", True, (200, 200, 255)), (sidebar_x + 20, y))
            y += 16
            self.buttons['palette_prev'] = pygame.Rect(sidebar_x + 20, y, 24, 18)
            self.buttons['palette_next'] = pygame.Rect(sidebar_x + 276, y, 24, 18)
            pygame.draw.rect(self.screen, (80, 70, 60), self.buttons['palette_prev'], border_radius=3)
            pygame.draw.rect(self.screen, (80, 70, 60), self.buttons['palette_next'], border_radius=3)
            self.screen.blit(font_small_bold.render("<", True, (255,255,255)), font_small_bold.render("<", True, (255,255,255)).get_rect(center=self.buttons['palette_prev'].center))
            self.screen.blit(font_small_bold.render(">", True, (255,255,255)), font_small_bold.render(">", True, (255,255,255)).get_rect(center=self.buttons['palette_next'].center))
            
            cult_list = self.world_settings.get('cult_names', PRISON_NAMES) + ["Wardens"]
            cult_name = cult_list[self.selected_cult_idx % len(cult_list)]
            self.screen.blit(font_small_bold.render(cult_name, True, (255, 230, 150)), (sidebar_x + 52, y + 1))
            
        elif self.active_layer == 'fringe':
            self.brush_tool = 'paint_fringe'
            self.screen.blit(font_small_bold.render("Active Fringe Group to Paint:", True, (200, 200, 255)), (sidebar_x + 20, y))
            y += 16
            self.buttons['palette_prev'] = pygame.Rect(sidebar_x + 20, y, 24, 18)
            self.buttons['palette_next'] = pygame.Rect(sidebar_x + 276, y, 24, 18)
            pygame.draw.rect(self.screen, (80, 70, 60), self.buttons['palette_prev'], border_radius=3)
            pygame.draw.rect(self.screen, (80, 70, 60), self.buttons['palette_next'], border_radius=3)
            self.screen.blit(font_small_bold.render("<", True, (255,255,255)), font_small_bold.render("<", True, (255,255,255)).get_rect(center=self.buttons['palette_prev'].center))
            self.screen.blit(font_small_bold.render(">", True, (255,255,255)), font_small_bold.render(">", True, (255,255,255)).get_rect(center=self.buttons['palette_next'].center))
            
            ent = self.world_settings.get('entities', {})
            fringe = ent.get('fringe_groups', [])
            if fringe:
                fg = fringe[self.selected_fringe_idx % len(fringe)]
                self.screen.blit(font_small.render(fg['name'][:22], True, (255, 230, 150)), (sidebar_x + 52, y + 1))
                
        elif self.active_layer == 'ecology':
            self.brush_tool = 'paint_ecology'
            self.screen.blit(font_small_bold.render("Ecology Paint Target:", True, (200, 200, 255)), (sidebar_x + 20, y))
            y += 16
            self.buttons['palette_prev'] = pygame.Rect(sidebar_x + 20, y, 24, 18)
            self.buttons['palette_next'] = pygame.Rect(sidebar_x + 276, y, 24, 18)
            pygame.draw.rect(self.screen, (80, 70, 60), self.buttons['palette_prev'], border_radius=3)
            pygame.draw.rect(self.screen, (80, 70, 60), self.buttons['palette_next'], border_radius=3)
            self.screen.blit(font_small_bold.render("<", True, (255,255,255)), font_small_bold.render("<", True, (255,255,255)).get_rect(center=self.buttons['palette_prev'].center))
            self.screen.blit(font_small_bold.render(">", True, (255,255,255)), font_small_bold.render(">", True, (255,255,255)).get_rect(center=self.buttons['palette_next'].center))
            
            targets = ["Flora Population", "Fauna Population"]
            self.screen.blit(font_small_bold.render(targets[self.selected_biome_idx % 2], True, (255, 230, 150)), (sidebar_x + 52, y + 1))
            
        elif self.active_layer == 'resources':
            self.brush_tool = 'place_resource'
            self.screen.blit(font_small_bold.render("Active Resource Node:", True, (200, 200, 255)), (sidebar_x + 20, y))
            y += 16
            self.buttons['palette_prev'] = pygame.Rect(sidebar_x + 20, y, 24, 18)
            self.buttons['palette_next'] = pygame.Rect(sidebar_x + 276, y, 24, 18)
            pygame.draw.rect(self.screen, (80, 70, 60), self.buttons['palette_prev'], border_radius=3)
            pygame.draw.rect(self.screen, (80, 70, 60), self.buttons['palette_next'], border_radius=3)
            self.screen.blit(font_small_bold.render("<", True, (255,255,255)), font_small_bold.render("<", True, (255,255,255)).get_rect(center=self.buttons['palette_prev'].center))
            self.screen.blit(font_small_bold.render(">", True, (255,255,255)), font_small_bold.render(">", True, (255,255,255)).get_rect(center=self.buttons['palette_next'].center))
            
            if NODE_TYPES:
                res = NODE_TYPES[self.selected_resource_idx % len(NODE_TYPES)]
                self.screen.blit(font_small.render(res['name'][:22], True, (255, 230, 150)), (sidebar_x + 52, y + 1))
                
        y = 444
        pygame.draw.line(self.screen, (80, 80, 80), (sidebar_x + 20, y), (sidebar_x + 300, y), 2)
        
        # Display selected cell details OR legend/event logs at the bottom Y = 450 to 715
        if self.selected_cell:
            self._draw_cell_details(sidebar_x, font_large, font_medium, font_small, font_small_bold)
        else:
            self._draw_legend_and_logs(sidebar_x, font_medium, font_small, font_small_bold)

    def _draw_cell_details(self, sidebar_x, font_large, font_medium, font_small, font_small_bold):
        """Draws the per-cell detail editor tabs when a cell is selected (shifted to bottom half)."""
        cell = self.selected_cell
        cell_id = cell['id']
        controlling_burg_id = cell.get('controlling_burg_id', cell_id)
        faction_info = self.factions.get(controlling_burg_id)
        is_sub = cell['elevation'] < 0
        
        # Setup Tabs Bar (Y = 420)
        self.tabs = {
            'stats': pygame.Rect(sidebar_x + 10, 420, 68, 22),
            'build': pygame.Rect(sidebar_x + 83, 420, 68, 22),
            'cults': pygame.Rect(sidebar_x + 156, 420, 68, 22),
            'biome': pygame.Rect(sidebar_x + 229, 420, 81, 22),
        }
        
        tab_labels = {'stats': "1. Stats", 'build': "2. Build", 'cults': "3. Cults", 'biome': "4. Biome/Node"}
        for t_name, rect in self.tabs.items():
            t_color = (80, 95, 110) if self.active_tab == t_name else (45, 50, 60)
            pygame.draw.rect(self.screen, t_color, rect, border_top_left_radius=4, border_top_right_radius=4)
            txt = font_small_bold.render(tab_labels[t_name], True, (255, 255, 255) if self.active_tab == t_name else (160, 160, 160))
            txt_rect = txt.get_rect(center=rect.center)
            self.screen.blit(txt, txt_rect)
            
        # Render Content Area Background (Y = 442)
        pygame.draw.rect(self.screen, (50, 55, 68), (sidebar_x + 10, 442, 300, 268), border_radius=4)
        
        def draw_adjust_row(y, label, val_str, minus_rect, plus_rect):
            lbl = font_small.render(label, True, (200, 210, 230))
            val = font_small_bold.render(val_str, True, (255, 255, 255))
            self.screen.blit(lbl, (sidebar_x + 20, y))
            self.screen.blit(val, (sidebar_x + 130, y))
            
            # Minus
            pygame.draw.rect(self.screen, (100, 70, 70), minus_rect, border_radius=3)
            m_txt = font_small_bold.render("-", True, (255, 255, 255))
            self.screen.blit(m_txt, m_txt.get_rect(center=minus_rect.center))
            
            # Plus
            pygame.draw.rect(self.screen, (70, 100, 70), plus_rect, border_radius=3)
            p_txt = font_small_bold.render("+", True, (255, 255, 255))
            self.screen.blit(p_txt, p_txt.get_rect(center=plus_rect.center))
            
        self.edit_buttons = {}
        matching_node = next((n for n in getattr(self, 'resource_nodes', []) if n['cell_id'] == cell_id), None)
        
        # TAB 1: STATS
        if self.active_tab == 'stats':
            owner_name = faction_info['faction_name'] if faction_info else "Water (Unoccupied)"
            is_cap_str = " (Capital)" if (faction_info and faction_info.get('is_capital') == 1 and cell_id == controlling_burg_id) else ""
            
            self.edit_buttons['change_faction'] = pygame.Rect(sidebar_x + 20, 455, 280, 24)
            pygame.draw.rect(self.screen, (70, 80, 100), self.edit_buttons['change_faction'], border_radius=4)
            txt = font_small_bold.render(f"Faction: {owner_name[:20]}{is_cap_str}", True, (255, 230, 150))
            self.screen.blit(txt, txt.get_rect(center=self.edit_buttons['change_faction'].center))
            
            faction_unit_cols = {
                1: 1, 2: 2, 3: 3, 4: 4, 5: 5,
                6: 8, 7: 5, 8: 9, 9: 12, 10: 7,
                11: 10, 12: 11, 13: 5, 14: 2, 15: 3,
                16: 10, 17: 12
            }
            if faction_info:
                fid = faction_info['faction_id']
                if fid > 0:
                    unit_col = faction_unit_cols.get(fid)
                    if unit_col:
                        u_sprite = self.small_sprites.get((11, unit_col)) if not is_sub else self.small_sprites.get((11, 10))
                        if u_sprite:
                            self.screen.blit(u_sprite, (sidebar_x + 280, 457))
            
            pop_val = faction_info['population'] if faction_info else 0
            discontent = faction_info['discontent'] if faction_info else 0.0
            crime = faction_info['crime_level'] if faction_info else 0.0
            
            self.edit_buttons['pop_minus'] = pygame.Rect(sidebar_x + 210, 490, 35, 20)
            self.edit_buttons['pop_plus'] = pygame.Rect(sidebar_x + 255, 490, 35, 20)
            draw_adjust_row(493, "Population:", f"{pop_val}", self.edit_buttons['pop_minus'], self.edit_buttons['pop_plus'])
            
            self.edit_buttons['dis_minus'] = pygame.Rect(sidebar_x + 210, 520, 35, 20)
            self.edit_buttons['dis_plus'] = pygame.Rect(sidebar_x + 255, 520, 35, 20)
            draw_adjust_row(523, "Discontent:", f"{discontent:.2f}", self.edit_buttons['dis_minus'], self.edit_buttons['dis_plus'])
            
            self.edit_buttons['crime_minus'] = pygame.Rect(sidebar_x + 210, 550, 35, 20)
            self.edit_buttons['crime_plus'] = pygame.Rect(sidebar_x + 255, 550, 35, 20)
            draw_adjust_row(553, "Crime Level:", f"{crime:.2f}", self.edit_buttons['crime_minus'], self.edit_buttons['crime_plus'])
            
            self.edit_buttons['toggle_capital'] = pygame.Rect(sidebar_x + 210, 580, 80, 20)
            pygame.draw.rect(self.screen, (80, 90, 110), self.edit_buttons['toggle_capital'], border_radius=3)
            cap_txt = font_small_bold.render("Toggle Cap", True, (255, 255, 255))
            self.screen.blit(cap_txt, cap_txt.get_rect(center=self.edit_buttons['toggle_capital'].center))
            self.screen.blit(font_small.render("Capital Status:", True, (200, 210, 230)), (sidebar_x + 20, 583))
            
            if faction_info and faction_info.get('is_capital') == 1 and cell_id == controlling_burg_id:
                c_sprite = self.small_sprites.get((10, 10)) if not is_sub else self.small_sprites.get((6, 12))
                if c_sprite:
                    self.screen.blit(c_sprite, (sidebar_x + 180, 580))
            
            if faction_info:
                pw = faction_info.get('physical_well_being', 1.0)
                mw = faction_info.get('mental_well_being', 1.0)
                wp = faction_info.get('hub_wealth', 0.0)
                pr = faction_info.get('pressure', 0.0)
                self.screen.blit(font_small.render(f"Physical/Mental Health: {pw:.2f} / {mw:.2f}", True, (170, 175, 185)), (sidebar_x + 20, 615))
                self.screen.blit(font_small.render(f"Hub Wealth / Crisis Pressure: {wp:.1f} / {pr:.2f}", True, (170, 175, 185)), (sidebar_x + 20, 635))
            else:
                self.screen.blit(font_small.render("No settlement active in this cell.", True, (170, 175, 185)), (sidebar_x + 20, 615))
                
        # TAB 2: BUILD
        elif self.active_tab == 'build':
            if faction_info:
                if is_sub:
                    self.edit_buttons['kelp_minus'] = pygame.Rect(sidebar_x + 210, 455, 35, 20)
                    self.edit_buttons['kelp_plus'] = pygame.Rect(sidebar_x + 255, 455, 35, 20)
                    draw_adjust_row(458, "Kelp Farms:", f"{faction_info['kelp_farms_count']}", self.edit_buttons['kelp_minus'], self.edit_buttons['kelp_plus'])
                    s = self.small_sprites.get((4, 5))
                    if s: self.screen.blit(s, (sidebar_x + 180, 458))
                    
                    self.edit_buttons['coral_minus'] = pygame.Rect(sidebar_x + 210, 485, 35, 20)
                    self.edit_buttons['coral_plus'] = pygame.Rect(sidebar_x + 255, 485, 35, 20)
                    draw_adjust_row(488, "Coral Mines:", f"{faction_info['coral_mines_count']}", self.edit_buttons['coral_minus'], self.edit_buttons['coral_plus'])
                    s = self.small_sprites.get((4, 4))
                    if s: self.screen.blit(s, (sidebar_x + 180, 488))
                    
                    self.edit_buttons['domes_minus'] = pygame.Rect(sidebar_x + 210, 515, 35, 20)
                    self.edit_buttons['domes_plus'] = pygame.Rect(sidebar_x + 255, 515, 35, 20)
                    draw_adjust_row(518, "Aquatic Domes:", f"{faction_info['underwater_domes_count']}", self.edit_buttons['domes_minus'], self.edit_buttons['domes_plus'])
                    s = self.small_sprites.get((10, 4))
                    if s: self.screen.blit(s, (sidebar_x + 180, 518))
                    
                    self.edit_buttons['walls_minus'] = pygame.Rect(sidebar_x + 210, 545, 35, 20)
                    self.edit_buttons['walls_plus'] = pygame.Rect(sidebar_x + 255, 545, 35, 20)
                    draw_adjust_row(548, "Reef Walls:", f"{faction_info['reef_walls_count']}", self.edit_buttons['walls_minus'], self.edit_buttons['walls_plus'])
                    s = self.small_sprites.get((4, 7))
                    if s: self.screen.blit(s, (sidebar_x + 180, 548))
                else:
                    self.edit_buttons['farms_minus'] = pygame.Rect(sidebar_x + 210, 455, 35, 20)
                    self.edit_buttons['farms_plus'] = pygame.Rect(sidebar_x + 255, 455, 35, 20)
                    draw_adjust_row(458, "Farms:", f"{faction_info['farms_count']}", self.edit_buttons['farms_minus'], self.edit_buttons['farms_plus'])
                    s = self.small_sprites.get((10, 1))
                    if s: self.screen.blit(s, (sidebar_x + 180, 458))
                    
                    self.edit_buttons['mines_minus'] = pygame.Rect(sidebar_x + 210, 485, 35, 20)
                    self.edit_buttons['mines_plus'] = pygame.Rect(sidebar_x + 255, 485, 35, 20)
                    draw_adjust_row(488, "Mines:", f"{faction_info['mines_count']}", self.edit_buttons['mines_minus'], self.edit_buttons['mines_plus'])
                    s = self.small_sprites.get((10, 3))
                    if s: self.screen.blit(s, (sidebar_x + 180, 488))
                    
                    self.edit_buttons['barracks_minus'] = pygame.Rect(sidebar_x + 210, 515, 35, 20)
                    self.edit_buttons['barracks_plus'] = pygame.Rect(sidebar_x + 255, 515, 35, 20)
                    draw_adjust_row(518, "Barracks:", f"{faction_info['barracks_count']}", self.edit_buttons['barracks_minus'], self.edit_buttons['barracks_plus'])
                    s = self.small_sprites.get((10, 10))
                    if s: self.screen.blit(s, (sidebar_x + 180, 518))
                    
                    self.edit_buttons['towers_minus'] = pygame.Rect(sidebar_x + 210, 545, 35, 20)
                    self.edit_buttons['towers_plus'] = pygame.Rect(sidebar_x + 255, 545, 35, 20)
                    draw_adjust_row(548, "Watchtowers:", f"{faction_info['watchtowers_count']}", self.edit_buttons['towers_minus'], self.edit_buttons['towers_plus'])
                    s = self.small_sprites.get((10, 11))
                    if s: self.screen.blit(s, (sidebar_x + 180, 548))
                    
                    self.edit_buttons['workshops_minus'] = pygame.Rect(sidebar_x + 210, 575, 35, 20)
                    self.edit_buttons['workshops_plus'] = pygame.Rect(sidebar_x + 255, 575, 35, 20)
                    draw_adjust_row(578, "Workshops:", f"{faction_info['workshops_count']}", self.edit_buttons['workshops_minus'], self.edit_buttons['workshops_plus'])
                    s = self.small_sprites.get((10, 12))
                    if s: self.screen.blit(s, (sidebar_x + 180, 578))
                    
                self.edit_buttons['toggle_docks'] = pygame.Rect(sidebar_x + 210, 610, 80, 20)
                pygame.draw.rect(self.screen, (80, 90, 110), self.edit_buttons['toggle_docks'], border_radius=3)
                docks_status = "Enabled" if faction_info.get('docks_count', 0) > 0 else "None"
                dock_txt = font_small_bold.render("Toggle Docks", True, (255, 255, 255))
                self.screen.blit(dock_txt, dock_txt.get_rect(center=self.edit_buttons['toggle_docks'].center))
                self.screen.blit(font_small.render(f"Docks/Harbor: {docks_status}", True, (200, 210, 230)), (sidebar_x + 20, 613))
            else:
                self.screen.blit(font_small.render("No settlement active in this cell.", True, (170, 175, 185)), (sidebar_x + 20, 455))
                
        # TAB 3: CULTS
        elif self.active_tab == 'cults':
            prisons = self.world_settings.get('cult_names', PRISON_NAMES) + ["Wardens"]
            sorted_cults = sorted(cell['cults_influence'].items(), key=lambda x: x[1], reverse=True)
            active_cults = [(k, v) for k, v in sorted_cults if v > 0.0][:3]
            while len(active_cults) < 3:
                for p in prisons:
                    if p not in [x[0] for x in active_cults]:
                        active_cults.append((p, 0.0))
                        break
                        
            self.top_cults_drawn = [x[0] for x in active_cults]
            
            # Draw 3 Cult rows
            for ci, (name, val) in enumerate(active_cults):
                cy_row = 455 + ci * 45
                self.edit_buttons[f'cult_inf_{ci}_minus'] = pygame.Rect(sidebar_x + 210, cy_row, 35, 20)
                self.edit_buttons[f'cult_inf_{ci}_plus'] = pygame.Rect(sidebar_x + 255, cy_row, 35, 20)
                draw_adjust_row(cy_row + 3, f"{name[:14]}:", f"{val*100:.0f}%", self.edit_buttons[f'cult_inf_{ci}_minus'], self.edit_buttons[f'cult_inf_{ci}_plus'])
                
            seal_found = None
            prisons_list = self.world_settings.get('prisons', [])
            for p in prisons_list:
                if p['cell_id'] == cell_id:
                    seal_found = p['seal_integrity']
                    break
                    
            if seal_found is not None:
                self.screen.blit(font_small_bold.render("Reality Anchor (Dragon Prison)", True, (255, 100, 100)), (sidebar_x + 20, 595))
                self.screen.blit(font_small.render(f"Seal Integrity: {seal_found*100:.1f}%", True, (200, 200, 200)), (sidebar_x + 20, 615))
            else:
                self.screen.blit(font_small.render("No Magistar Prisons located here.", True, (170, 175, 185)), (sidebar_x + 20, 595))
                
        # TAB 4: BIOME/NODE
        elif self.active_tab == 'biome':
            # Biome Cycle
            self.edit_buttons['change_biome'] = pygame.Rect(sidebar_x + 210, 455, 80, 20)
            pygame.draw.rect(self.screen, (80, 90, 110), self.edit_buttons['change_biome'], border_radius=3)
            btn_txt = font_small_bold.render("Cycle Biome", True, (255, 255, 255))
            self.screen.blit(btn_txt, btn_txt.get_rect(center=self.edit_buttons['change_biome'].center))
            self.screen.blit(font_small.render(f"Biome: {cell['biome']}", True, (200, 210, 230)), (sidebar_x + 20, 458))
            
            # Resource Nodes Cycle
            self.edit_buttons['cycle_node'] = pygame.Rect(sidebar_x + 210, 490, 80, 20)
            pygame.draw.rect(self.screen, (80, 90, 110), self.edit_buttons['cycle_node'], border_radius=3)
            node_txt = font_small_bold.render("Cycle Type", True, (255, 255, 255))
            self.screen.blit(node_txt, node_txt.get_rect(center=self.edit_buttons['cycle_node'].center))
            
            node_name = matching_node['name'] if matching_node else "None"
            self.screen.blit(font_small.render(f"Resource Node: {node_name[:14]}", True, (200, 210, 230)), (sidebar_x + 20, 493))
            
            if matching_node:
                self.edit_buttons['yield_minus'] = pygame.Rect(sidebar_x + 210, 525, 35, 20)
                self.edit_buttons['yield_plus'] = pygame.Rect(sidebar_x + 255, 525, 35, 20)
                draw_adjust_row(528, "Yield Level:", f"{matching_node['yield_remaining']:.0f}", self.edit_buttons['yield_minus'], self.edit_buttons['yield_plus'])
                
                self.edit_buttons['clear_node'] = pygame.Rect(sidebar_x + 210, 560, 80, 20)
                pygame.draw.rect(self.screen, (120, 70, 70), self.edit_buttons['clear_node'], border_radius=3)
                clr_txt = font_small_bold.render("Delete Node", True, (255, 255, 255))
                self.screen.blit(clr_txt, clr_txt.get_rect(center=self.edit_buttons['clear_node'].center))
                self.screen.blit(font_small.render("Delete Resource:", True, (200, 210, 230)), (sidebar_x + 20, 563))
            else:
                self.screen.blit(font_small.render("Node yield controls inactive.", True, (150, 150, 150)), (sidebar_x + 20, 528))
                
            # Reality modifiers
            self.screen.blit(font_small.render(f"Ecology (Flora): {cell['flora'].get('name', 'None')} ({cell['flora'].get('population', 0.0):.1f})", True, (170, 175, 185)), (sidebar_x + 20, 600))
            self.screen.blit(font_small.render(f"Ecology (Fauna): {cell['fauna'].get('name', 'None')} ({cell['fauna'].get('population', 0.0):.1f})", True, (170, 175, 185)), (sidebar_x + 20, 620))
            self.screen.blit(font_small.render(f"Chaos Saturation: {cell['chaos_saturation']:.2f}", True, (170, 175, 185)), (sidebar_x + 20, 640))
            self.screen.blit(font_small.render(f"Local weather pressure: {cell['food_supply']:.2f}", True, (170, 175, 185)), (sidebar_x + 20, 660))
            
        # Deselect Button (Y = 678)
        self.edit_buttons['deselect'] = pygame.Rect(sidebar_x + 20, 678, 280, 24)
        pygame.draw.rect(self.screen, (60, 70, 80), self.edit_buttons['deselect'], border_radius=4)
        txt = font_small_bold.render("Deselect Cell", True, (255, 255, 255))
        self.screen.blit(txt, txt.get_rect(center=self.edit_buttons['deselect'].center))

    def _draw_legend_and_logs(self, sidebar_x, font_medium, font_small, font_small_bold):
        """Draws legend panel and simulation logs when no cell is selected (shifted)."""
        legend_title = font_medium.render(f"Visual Legend: {self.active_layer.upper()}", True, (255, 200, 100))
        self.screen.blit(legend_title, (sidebar_x + 20, 450))
        
        ly = 470
        if self.active_layer == 'biomes':
            biomes_list = [
                ('Plains', (168, 201, 110)),
                ('Forest', (45, 106, 45)),
                ('Desert', (212, 168, 67)),
                ('Mountain', (138, 138, 138)),
                ('Swamp', (74, 122, 74)),
                ('Coastal Water', (72, 180, 195)),
                ('Coral Reefs', (219, 112, 147)),
                ('Open Ocean', (26, 95, 138)),
                ('Abyssal Trench', (10, 25, 60)),
                ('Thermal Vents', (120, 20, 60))
            ]
            for idx, (name, col) in enumerate(biomes_list):
                bx = sidebar_x + 20 if idx % 2 == 0 else sidebar_x + 160
                by = ly + (idx // 2) * 15
                pygame.draw.rect(self.screen, col, (bx, by + 2, 12, 12), border_radius=2)
                self.screen.blit(font_small.render(name, True, (200, 200, 200)), (bx + 20, by))
            ly += 5 * 15
        elif self.active_layer == 'elevation':
            self.screen.blit(font_small.render("Heightmap / Depth gradient:", True, (200, 200, 200)), (sidebar_x + 20, ly))
            ly += 16
            for h_idx in range(30):
                val = h_idx / 30.0
                col = (int(val * 180) + 70, int(val * 162) + 63, int(val * 126) + 49)
                pygame.draw.rect(self.screen, col, (sidebar_x + 20, ly + h_idx, 15, 1))
            self.screen.blit(font_small.render("- High Mountains", True, (180, 180, 180)), (sidebar_x + 42, ly + 2))
            self.screen.blit(font_small.render("- Low Land", True, (180, 180, 180)), (sidebar_x + 42, ly + 18))
            ly += 36
            for d_idx in range(30):
                val = d_idx / 30.0
                col = (20, 20, max(50, min(255, int(val * 150) + 50)))
                pygame.draw.rect(self.screen, col, (sidebar_x + 20, ly + d_idx, 15, 1))
            self.screen.blit(font_small.render("- Shallow Waters", True, (180, 180, 180)), (sidebar_x + 42, ly + 2))
            self.screen.blit(font_small.render("- Abyssal Depths", True, (180, 180, 180)), (sidebar_x + 42, ly + 18))
            ly += 45
        elif self.active_layer == 'factions':
            self.screen.blit(font_small.render("Territories of the Factions:", True, (200, 200, 200)), (sidebar_x + 20, ly))
            ly += 18
            sorted_fids = sorted(self.faction_colors.keys())
            ent = self.world_settings.get('entities', {})
            factions = ent.get('factions', [])
            for idx, fid in enumerate(sorted_fids[:8]):
                bx = sidebar_x + 20 if idx % 2 == 0 else sidebar_x + 160
                by = ly + (idx // 2) * 15
                col = self.faction_colors.get(fid, (150,150,150))
                pygame.draw.rect(self.screen, col, (bx, by + 2, 12, 12), border_radius=2)
                fac_name = factions[fid - 1]['name'] if fid - 1 < len(factions) else f"Faction {fid}"
                self.screen.blit(font_small.render(fac_name[:16], True, (200, 200, 200)), (bx + 20, by))
            ly += 4 * 15
        elif self.active_layer == 'settlements':
            self.screen.blit(font_small.render("Settlement Influence Areas (Provinces):", True, (200, 200, 200)), (sidebar_x + 20, ly))
            ly += 18
            self.screen.blit(font_small.render("Cells with matching colors are controlled", True, (170, 170, 170)), (sidebar_x + 20, ly))
            ly += 14
            self.screen.blit(font_small.render("by the same local Settlement center.", True, (170, 170, 170)), (sidebar_x + 20, ly))
            ly += 15
        elif self.active_layer == 'cults':
            self.screen.blit(font_small.render("Prisons & Cult Influences:", True, (200, 200, 200)), (sidebar_x + 20, ly))
            ly += 18
            cult_legend = [
                ("Tiraton (Red)", (231, 76, 60)),
                ("Stagus (Green)", (46, 204, 113)),
                ("Metrion (Blue)", (52, 152, 219)),
                ("Vecelo (Purple)", (155, 89, 182)),
                ("Wardens (White)", (240, 240, 240))
            ]
            for idx, (name, col) in enumerate(cult_legend):
                bx = sidebar_x + 20 if idx % 2 == 0 else sidebar_x + 160
                by = ly + (idx // 2) * 15
                pygame.draw.rect(self.screen, col, (bx, by + 2, 12, 12), border_radius=2)
                self.screen.blit(font_small.render(name[:16], True, (200, 200, 200)), (bx + 20, by))
            ly += 3 * 15
        elif self.active_layer == 'fringe':
            self.screen.blit(font_small.render("Bands of Fringe Actors Influence:", True, (200, 200, 200)), (sidebar_x + 20, ly))
            ly += 18
            fringe_legend = [
                ("Obsidian (Black)", (30, 30, 30)),
                ("Freesky (SkyBlue)", (135, 206, 235)),
                ("Crimson (Red)", (220, 20, 60)),
                ("Otter Syn (Brown)", (139, 69, 19)),
                ("Silent Cur (Teal)", (0, 128, 128))
            ]
            for idx, (name, col) in enumerate(fringe_legend):
                bx = sidebar_x + 20 if idx % 2 == 0 else sidebar_x + 160
                by = ly + (idx // 2) * 15
                pygame.draw.rect(self.screen, col, (bx, by + 2, 12, 12), border_radius=2)
                self.screen.blit(font_small.render(name[:16], True, (200, 200, 200)), (bx + 20, by))
            ly += 3 * 15
        elif self.active_layer == 'ecology':
            self.screen.blit(font_small.render("Flora / Fauna Biomass Densities:", True, (200, 200, 200)), (sidebar_x + 20, ly))
            ly += 18
            pygame.draw.rect(self.screen, (0, 200, 40), (sidebar_x + 20, ly + 2, 12, 12), border_radius=2)
            self.screen.blit(font_small.render("High Flora Population (Green)", True, (180, 180, 180)), (sidebar_x + 40, ly))
            ly += 15
            pygame.draw.rect(self.screen, (200, 0, 40), (sidebar_x + 20, ly + 2, 12, 12), border_radius=2)
            self.screen.blit(font_small.render("High Fauna Population (Red)", True, (180, 180, 180)), (sidebar_x + 40, ly))
            ly += 15
            pygame.draw.rect(self.screen, (200, 200, 40), (sidebar_x + 20, ly + 2, 12, 12), border_radius=2)
            self.screen.blit(font_small.render("High Mixed Coexistence (Yellow)", True, (180, 180, 180)), (sidebar_x + 40, ly))
            ly += 15
        elif self.active_layer == 'resources':
            self.screen.blit(font_small.render("Geological Resource Node Types:", True, (200, 200, 200)), (sidebar_x + 20, ly))
            ly += 18
            nodes = [
                ("Fe - Rich Iron Vein", (120, 120, 120)),
                ("Cu - Rich Copper Vein", (184, 115, 51)),
                ("Co - Coral Mine", (255, 127, 80)),
                ("Ds - Dragonstone Crater", (186, 85, 211)),
                ("Os - Osmium Conductor", (0, 206, 209)),
                ("St - Ancient Steel Ruins", (70, 130, 180))
            ]
            for idx, (name, col) in enumerate(nodes[:6]):
                bx = sidebar_x + 20 if idx % 2 == 0 else sidebar_x + 160
                by = ly + (idx // 2) * 15
                pygame.draw.circle(self.screen, col, (bx + 6, by + 7), 6)
                self.screen.blit(font_small.render(name[:16], True, (200, 200, 200)), (bx + 20, by))
            ly += 3 * 15
            
        # Wrapped logs
        font_log = pygame.font.SysFont("arial", 10)
        logs_title = font_medium.render("Simulation Event Logs:", True, (255, 200, 100))
        self.screen.blit(logs_title, (sidebar_x + 20, 565))
        
        log_y = 585
        for entry in self.logs[:4]:
            desc = entry['description']
            tick = entry['tick_number']
            ev_type = entry['event_type']
            text_str = f"[{tick}] [{ev_type}] {desc}"
            
            color_map = {1: (200, 200, 200), 3: (255, 255, 180), 5: (255, 150, 150)}
            log_color = color_map.get(entry.get('severity', 1), (200, 200, 200))
            
            wrapped_lines = wrap_text(text_str, font_log, 280)
            for line in wrapped_lines[:2]:
                log_lbl = font_log.render(line, True, log_color)
                self.screen.blit(log_lbl, (sidebar_x + 20, log_y))
                log_y += 13
            log_y += 4
            if log_y > 710:
                break

    # ============ TKINTER DIALOGUE HELPERS ============
    def select_from_list(self, title, prompt, items):
        import tkinter as tk
        from tkinter import simpledialog
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            
            full_prompt = prompt + "\n" + "\n".join(f"{idx+1}. {item}" for idx, item in enumerate(items))
            ans = simpledialog.askinteger(title, full_prompt, parent=root, minvalue=1, maxvalue=len(items))
            root.destroy()
            if ans is not None:
                return items[ans - 1]
        except Exception as e:
            print(f"Tkinter select list error: {e}")
        return None

    def ask_string(self, title, prompt, initialvalue=""):
        import tkinter as tk
        from tkinter import simpledialog
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            ans = simpledialog.askstring(title, prompt, initialvalue=initialvalue, parent=root)
            root.destroy()
            return ans
        except Exception as e:
            print(f"Tkinter ask string error: {e}")
        return None

    def ask_float(self, title, prompt, initialvalue=0.0):
        import tkinter as tk
        from tkinter import simpledialog
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            ans = simpledialog.askfloat(title, prompt, initialvalue=initialvalue, parent=root)
            root.destroy()
            return ans
        except Exception as e:
            print(f"Tkinter ask float error: {e}")
        return None

    def ask_int(self, title, prompt, initialvalue=0):
        import tkinter as tk
        from tkinter import simpledialog
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            ans = simpledialog.askinteger(title, prompt, initialvalue=initialvalue, parent=root)
            root.destroy()
            return ans
        except Exception as e:
            print(f"Tkinter ask int error: {e}")
        return None

    def ask_color(self, title, initialcolor="#ffffff"):
        import tkinter as tk
        from tkinter import colorchooser
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            color = colorchooser.askcolor(title=title, color=initialcolor, parent=root)
            root.destroy()
            return color[1]
        except Exception as e:
            print(f"Tkinter ask color error: {e}")
        return None

    def edit_biomes_settings(self):
        costs = self.world_settings.get('travel_costs', {})
        biomes = list(costs.keys())
        sel = self.select_from_list("Edit Biome Travel Costs", "Select a biome to edit travel costs:", biomes)
        if not sel: return
        b_costs = costs[sel]
        walk = self.ask_float("Walking Cost", f"Enter walking cost for {sel}:", b_costs.get('walking', 1.0))
        if walk is None: return
        ride = self.ask_float("Riding Cost", f"Enter riding cost for {sel}:", b_costs.get('riding', 1.0))
        if ride is None: return
        boat = self.ask_float("Boating Cost", f"Enter boating cost for {sel}:", b_costs.get('boating', 1.0))
        if boat is None: return
        costs[sel] = {"walking": walk, "riding": ride, "boating": boat}
        self.world_settings['travel_costs'] = costs
        save_world_settings(self.world_settings)
        print(f"Updated travel costs for {sel}.")

    def edit_elevation_settings(self):
        edit_elevation_dialog(self)
        self.world_settings = load_world_settings()
        self.populate_node_types()

    def edit_calendar_settings(self):
        edit_calendar_dialog(self)
        self.world_settings = load_world_settings()
        self.populate_node_types()

    def edit_factions_settings(self):
        edit_factions_dialog(self)
        self.world_settings = load_world_settings()
        self.populate_node_types()

    def edit_cults_prisons_settings(self):
        edit_cults_dialog(self)
        self.world_settings = load_world_settings()
        self.populate_node_types()

    def edit_fringe_settings(self):
        edit_fringe_dialog(self)
        self.world_settings = load_world_settings()
        self.populate_node_types()

    def edit_ecology_settings(self):
        edit_ecology_dialog(self)
        self.world_settings = load_world_settings()
        self.populate_node_types()

    def edit_resources_recipes_settings(self):
        edit_resources_recipes_dialog(self)
        self.world_settings = load_world_settings()
        self.populate_node_types()

    def edit_settlements_settings(self):
        edit_settlements_dialog(self)
        self.world_settings = load_world_settings()
        self.populate_node_types()

    def reload_in_memory_constants(self):
        """Reloads the constants module and copies the updated values into rules_engine's namespace."""
        try:
            import sys
            import modules.constants
            # Re-read settings from JSON
            modules.constants.load_dynamic_constants()
            print("Constants reloaded dynamically in modules.constants.")
            
            # Update rules_engine namespace variables
            for mod_name in ['modules.rules_engine', 'rules_engine']:
                if mod_name in sys.modules:
                    re_mod = sys.modules[mod_name]
                    for const_name in [
                        'TOWN_TIERS', 'TRANSPORT_UNLOCKS', 'BUILDING_UNLOCKS',
                        'WELLBEING_DECAY_RATE', 'FOOD_PER_FARM', 'FOOD_PER_KELP_FARM', 'FOOD_PER_DOCK',
                        'SAFETY_PER_TOWER', 'SAFETY_PER_WALL', 'SAFETY_PER_REEF_WALL', 'SECURITY_PER_BARRACKS',
                        'RIOT_DISCONTENT_LIMIT', 'RIOT_CRIME_LIMIT',
                        'REVOLUTION_DISCONTENT_LIMIT', 'REVOLUTION_CRIME_LIMIT',
                        'TRADE_ABUNDANCE_LEVEL', 'WINTER_TRAVEL_COST', 'SUMMER_GROWTH_MULT',
                        'BASELINE_CHAOS', 'MOON_PHASE_EFFECT'
                    ]:
                        if hasattr(modules.constants, const_name):
                            setattr(re_mod, const_name, getattr(modules.constants, const_name))
            print("Updated constants copied to rules_engine module namespace.")
        except Exception as e:
            print(f"Error reloading in-memory constants: {e}")

    # ============ BRUSH PAINTING ============
    def apply_brush(self, screen_pos):
        """Applies the active brush tool to all cells within the brush radius at the given screen position."""
        if screen_pos[0] >= 960:
            return
        
        map_x, map_y = self.from_screen(screen_pos[0], screen_pos[1])
        affected_cells = self.get_cells_in_brush(map_x, map_y)
        
        if not affected_cells:
            return
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        power_factor = self.brush_power / 10.0  # Normalize power to 0.1-1.0
        
        for cell in affected_cells:
            cell_id = cell['id']
            
            if self.brush_tool == 'elev_up':
                increment = 0.05 * power_factor
                cur.execute("UPDATE cells SET elevation = MIN(1.0, elevation + ?), depth_elevation = MIN(1.0, depth_elevation + ?) WHERE id = ?", (increment, increment, cell_id))
                
            elif self.brush_tool == 'elev_down':
                decrement = 0.05 * power_factor
                cur.execute("UPDATE cells SET elevation = MAX(-1.0, elevation - ?), depth_elevation = MAX(-1.0, depth_elevation - ?) WHERE id = ?", (decrement, decrement, cell_id))
                
            elif self.brush_tool == 'elev_smooth':
                # Average elevation with neighbors
                neighbor_elevs = []
                for other in affected_cells:
                    if other['id'] != cell_id:
                        neighbor_elevs.append(other['elevation'])
                if neighbor_elevs:
                    avg = sum(neighbor_elevs) / len(neighbor_elevs)
                    smoothed = cell['elevation'] + (avg - cell['elevation']) * 0.3 * power_factor
                    cur.execute("UPDATE cells SET elevation = ?, depth_elevation = ? WHERE id = ?", (smoothed, smoothed, cell_id))
                    
            elif self.brush_tool == 'elev_level':
                target = self.active_elevation
                current = cell['elevation']
                new_elev = current + (target - current) * 0.5 * power_factor
                cur.execute("UPDATE cells SET elevation = ?, depth_elevation = ? WHERE id = ?", (new_elev, new_elev, cell_id))
                
            elif self.brush_tool == 'paint_biome':
                new_biome = BIOMES_LIST[self.selected_biome_idx % len(BIOMES_LIST)]
                new_elev = -0.5 if new_biome in ['Ocean', 'Coastal', 'Reef', 'Abyssal', 'Thermal'] else max(0.1, cell['elevation'])
                cur.execute("UPDATE cells SET biome = ?, elevation = ?, depth_elevation = ? WHERE id = ?", (new_biome, new_elev, new_elev, cell_id))
                
            elif self.brush_tool == 'paint_faction':
                faction_idx = self.selected_faction_idx % len(FACTION_NAMES)
                faction_id = faction_idx + 1
                faction_name = FACTION_NAMES[faction_idx]
                # Update the controlling burg's faction, or create a new macro_group entry
                burg_id = cell.get('controlling_burg_id')
                if burg_id:
                    cur.execute("UPDATE macro_groups SET faction_id = ?, faction_name = ? WHERE cell_id = ?", (faction_id, faction_name, burg_id))
                    
            elif self.brush_tool == 'paint_cult':
                cult_list = self.world_settings.get('cult_names', PRISON_NAMES) + ["Wardens"]
                cult_name = cult_list[self.selected_cult_idx % len(cult_list)]
                cur.execute("SELECT cults_json FROM cells WHERE id = ?", (cell_id,))
                row = cur.fetchone()
                cults_inf = json.loads(row[0]) if row and row[0] else {}
                current_val = cults_inf.get(cult_name, 0.0)
                new_val = min(1.0, current_val + 0.05 * power_factor)
                cults_inf[cult_name] = round(new_val, 3)
                cur.execute("UPDATE cells SET cults_json = ? WHERE id = ?", (json.dumps(cults_inf), cell_id))
                
            elif self.brush_tool == 'paint_fringe':
                fringe_name = FRINGE_NAMES[self.selected_fringe_idx % len(FRINGE_NAMES)]
                cur.execute("SELECT fringe_json FROM cells WHERE id = ?", (cell_id,))
                row = cur.fetchone()
                fringe_inf = json.loads(row[0]) if row and row[0] else {}
                current_val = fringe_inf.get(fringe_name, 0.0)
                new_val = min(1.0, current_val + 0.05 * power_factor)
                fringe_inf[fringe_name] = round(new_val, 3)
                cur.execute("UPDATE cells SET fringe_json = ? WHERE id = ?", (json.dumps(fringe_inf), cell_id))
                
            elif self.brush_tool == 'paint_ecology':
                targets = ["flora", "fauna"]
                target_type = targets[self.selected_biome_idx % 2]
                
                # Fetch target species list from settings
                species_list = self.world_settings.get('entities', {}).get(target_type, [])
                if species_list:
                    # Select the first species as default
                    spec = species_list[0]
                    # Update cell JSON
                    cur.execute(f"SELECT {target_type}_json FROM cells WHERE id = ?", (cell_id,))
                    row_val = cur.fetchone()[0]
                    data = json.loads(row_val) if row_val else {}
                    data['name'] = spec['name']
                    # Add to population
                    current_pop = data.get('population', 0.0)
                    new_pop = min(100.0, current_pop + 10.0 * power_factor)
                    data['population'] = round(new_pop, 2)
                    cur.execute(f"UPDATE cells SET {target_type}_json = ? WHERE id = ?", (json.dumps(data), cell_id))
                
            elif self.brush_tool == 'place_resource':
                # Only place on the center cell, not all cells in brush
                if cell == affected_cells[0]:
                    node_def = NODE_TYPES[self.selected_resource_idx % len(NODE_TYPES)]
                    burg_id = cell.get('controlling_burg_id')
                    faction_id = 0
                    if burg_id and burg_id in self.factions:
                        faction_id = self.factions[burg_id].get('faction_id', 0)
                    cur.execute("DELETE FROM resource_nodes WHERE cell_id = ?", (cell_id,))
                    cur.execute("INSERT INTO resource_nodes (cell_id, faction_id, name, icon, description, yield_remaining, is_discovered) VALUES (?, ?, ?, ?, ?, ?, 1)",
                                (cell_id, faction_id, node_def['name'], node_def['icon'], node_def['desc'], node_def['yield']))
                                
            elif self.brush_tool == 'place_chaos':
                # Place chaos node on center cell only
                if cell == affected_cells[0]:
                    cur.execute("UPDATE cells SET chaos_saturation = 1.0, chaos_base_modifier = 1.0 WHERE id = ?", (cell_id,))
                    # Record in settings
                    if 'winds_and_temps' not in self.world_settings:
                        self.world_settings['winds_and_temps'] = {}
                    chaos_nodes = self.world_settings['winds_and_temps'].get('chaos_nodes', [])
                    # Avoid duplicates
                    if not any(n.get('cell_id') == cell_id for n in chaos_nodes):
                        chaos_nodes.append({"cell_id": cell_id, "x": cell['center'][0], "y": cell['center'][1]})
                    self.world_settings['winds_and_temps']['chaos_nodes'] = chaos_nodes
                    
            elif self.brush_tool == 'place_convergence':
                if cell == affected_cells[0]:
                    if 'winds_and_temps' not in self.world_settings:
                        self.world_settings['winds_and_temps'] = {}
                    conv_locs = self.world_settings['winds_and_temps'].get('convergence_locations', [])
                    # Avoid duplicates
                    if not any(l.get('cell_id') == cell_id for l in conv_locs):
                        conv_locs.append({"cell_id": cell_id, "x": cell['center'][0], "y": cell['center'][1]})
                    self.world_settings['winds_and_temps']['convergence_locations'] = conv_locs
        
        conn.commit()
        cur.close()
        conn.close()

    def load_heightmap(self):
        """Opens a file dialog to select a heightmap image, samples brightness at cell centroids, updates elevations."""
        print("[Heightmap] Opening file selection dialog. Please check if the window is open behind the Pygame app.")
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)  # Force dialog to top
            
            hmap_path = filedialog.askopenfilename(
                parent=root,
                title="Select Heightmap Image",
                filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.tga;*.gif")]
            )
            root.destroy()
            
            if not hmap_path:
                print("[Heightmap] Loading cancelled by user.")
                return
        except Exception as e:
            # Fallback if tkinter dialog fails
            print(f"[Heightmap] File dialog error ({e}). Falling back to 'heightmap.png' in project root.")
            base_dir = os.path.dirname(os.path.dirname(__file__))
            hmap_path = os.path.join(base_dir, 'heightmap.png')
            
            if not os.path.exists(hmap_path):
                print(f"[Heightmap] No fallback heightmap.png found at {hmap_path}")
                return
        
        try:
            from PIL import Image
            img = Image.open(hmap_path).convert('L')  # Greyscale
            img_w, img_h = img.size
            pixels = img.load()
            
            if not self.cells:
                return
            
            # Find map coordinate bounds
            xs = [c['center'][0] for c in self.cells]
            ys = [c['center'][1] for c in self.cells]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            range_x = max_x - min_x if max_x > min_x else 1.0
            range_y = max_y - min_y if max_y > min_y else 1.0
            
            conn = get_db_connection()
            cur = conn.cursor()
            
            for cell in self.cells:
                cx, cy = cell['center']
                # Map cell centroid to image pixel
                px = int(((cx - min_x) / range_x) * (img_w - 1))
                py = int(((cy - min_y) / range_y) * (img_h - 1))
                px = max(0, min(img_w - 1, px))
                py = max(0, min(img_h - 1, py))
                
                brightness = pixels[px, py] / 255.0  # 0.0 (dark/low) to 1.0 (bright/high)
                # Map brightness to elevation: 0.0 = deep ocean (-1.0), 0.5 = sea level (0.0), 1.0 = mountain (1.0)
                elevation = (brightness * 2.0) - 1.0
                
                cur.execute("UPDATE cells SET elevation = ?, depth_elevation = ? WHERE id = ?", (elevation, elevation, cell['id']))
                
                # Auto-assign biome based on elevation
                if elevation < -0.5:
                    biome = 'Abyssal'
                elif elevation < -0.2:
                    biome = 'Ocean'
                elif elevation < 0.0:
                    biome = 'Coastal'
                elif elevation < 0.3:
                    biome = 'Plains'
                elif elevation < 0.5:
                    biome = 'Forest'
                elif elevation < 0.7:
                    biome = 'Desert'
                else:
                    biome = 'Mountain'
                cur.execute("UPDATE cells SET biome = ? WHERE id = ?", (biome, cell['id']))
            
            conn.commit()
            cur.close()
            conn.close()
            
            self.sync_data()
            print(f"Heightmap loaded from {hmap_path}: {len(self.cells)} cells updated.")
            
        except ImportError:
            print("Pillow (PIL) not installed. Run: pip install Pillow")
        except Exception as e:
            print(f"Error loading heightmap: {e}")

    def push_settings_to_db(self):
        """Pushes current world_settings to the simulation database and model."""
        save_world_settings(self.world_settings)
        print("Settings saved to world_settings.json")
        
        if self.model:
            self.model.settings = self.world_settings
            
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # 1. Sync Factions (rename/recolor)
            ent = self.world_settings.get('entities', {})
            factions = ent.get('factions', [])
            for fac in factions:
                fid = fac.get('id')
                fname = fac.get('name')
                cur.execute("UPDATE macro_groups SET faction_name = ? WHERE faction_id = ?", (fname, fid))
            
            # 2. Sync Chaos Saturation
            cur.execute("UPDATE cells SET chaos_saturation = 0.0, chaos_base_modifier = 0.0")
            wt = self.world_settings.get('winds_and_temps', {})
            chaos_nodes = wt.get('chaos_nodes', [])
            for node in chaos_nodes:
                cid = node.get('cell_id')
                cur.execute("UPDATE cells SET chaos_saturation = 1.0, chaos_base_modifier = 1.0 WHERE id = ?", (cid,))
                
            # 3. Sync Dragon Prisons
            cur.execute("DELETE FROM dragon_prisons")
            prisons = self.world_settings.get('prisons', [])
            for p in prisons:
                cur.execute("INSERT INTO dragon_prisons (id, cell_id, x, y, seal_integrity) VALUES (?, ?, ?, ?, ?)",
                            (p.get('id'), p.get('cell_id'), p.get('x'), p.get('y'), p.get('seal_integrity', 1.0)))
                            
            # 4. Sync Resource Nodes Factions
            cur.execute("""
                UPDATE resource_nodes 
                SET faction_id = COALESCE((
                    SELECT m.faction_id 
                    FROM macro_groups m 
                    JOIN cells c ON c.controlling_burg_id = m.cell_id 
                    WHERE c.id = resource_nodes.cell_id
                ), 0)
            """)

            # 5. Recalculate Euclidean proximity distances
            cur.execute("SELECT id, geom_wkt FROM cells")
            cell_rows = cur.fetchall()
            cell_centers = {}
            for row in cell_rows:
                try:
                    poly = loads(row['geom_wkt'])
                    cell_centers[row['id']] = (poly.centroid.x, poly.centroid.y)
                except Exception:
                    pass
            
            # Bounding box diagonal for distance normalization
            if cell_centers:
                xs = [pt[0] for pt in cell_centers.values()]
                ys = [pt[1] for pt in cell_centers.values()]
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)
                max_map_distance = math.sqrt((max_x - min_x)**2 + (max_y - min_y)**2)
                if max_map_distance == 0:
                    max_map_distance = 1.0
            else:
                max_map_distance = 100.0
                
            # Convergence Locations coordinates
            conv_locs = wt.get('convergence_locations', [])
            conv_pts = [(l.get('x'), l.get('y')) for l in conv_locs if l.get('x') is not None]
            
            # Chaos Node/Prison locations coordinates
            prison_pts = [(p.get('x'), p.get('y')) for p in prisons if p.get('x') is not None]
            if not prison_pts:
                # Fallback: use chaos nodes coordinates
                prison_pts = [(n.get('x'), n.get('y')) for n in chaos_nodes if n.get('x') is not None]
                
            # Recalculate and update macro_groups distances
            cur.execute("SELECT id, cell_id FROM macro_groups")
            mg_rows = cur.fetchall()
            for mg in mg_rows:
                mg_id = mg['id']
                cell_id = mg['cell_id']
                
                # Get settlement center
                pt = cell_centers.get(cell_id)
                if not pt:
                    continue
                sx, sy = pt
                
                # Nearest prison distance
                min_prison_dist = max_map_distance
                for px, py in prison_pts:
                    d = math.sqrt((sx - px)**2 + (sy - py)**2)
                    if d < min_prison_dist:
                        min_prison_dist = d
                # Normalize (0.0 = closest, 1.0 = farthest). Default to 1.0 if no prisons.
                norm_prison = min_prison_dist / max_map_distance if prison_pts else 1.0
                norm_prison = max(0.0, min(1.0, norm_prison))
                
                # Nearest convergence spire distance
                min_conv_dist = max_map_distance
                for cx, cy in conv_pts:
                    d = math.sqrt((sx - cx)**2 + (sy - cy)**2)
                    if d < min_conv_dist:
                        min_conv_dist = d
                norm_conv = min_conv_dist / max_map_distance if conv_pts else 1.0
                norm_conv = max(0.0, min(1.0, norm_conv))
                
                # Update macro_groups
                cur.execute("""
                    UPDATE macro_groups 
                    SET distance_to_chaos_structure = ?, distance_to_convergence = ? 
                    WHERE id = ?
                """, (norm_prison, norm_conv, mg_id))
                
            conn.commit()
            print("Successfully updated database factions, chaos nodes, prisons, resource nodes, and recalculated proximity distances.")
        except Exception as e:
            conn.rollback()
            print(f"Error executing push_settings_to_db: {e}")
        finally:
            cur.close()
            conn.close()
            
        self.sync_data()

    def handle_config_click(self, pos):
        """Handles clicks within the config overlay."""
        if not hasattr(self, 'config_buttons'):
            return
            
        for name, rect in self.config_buttons.items():
            if rect.collidepoint(pos):
                if name == 'close':
                    self.config_overlay_open = False
                    return
                elif name == 'save_settings':
                    save_world_settings(self.world_settings)
                    print("Settings saved to world_settings.json")
                    return
                elif name.startswith('tab_'):
                    self.config_tab = name[4:]
                    return
                elif name == 'edit_full_details':
                    # Contextually launch Tkinter editors from the config overlay
                    if self.config_tab == 'physics':
                        self.edit_elevation_settings()
                    elif self.config_tab == 'calendar':
                        self.edit_calendar_settings()
                    elif self.config_tab == 'entities':
                        self.edit_factions_settings()
                    elif self.config_tab == 'rules':
                        self.edit_resources_recipes_settings()
                    # Re-read settings
                    self.world_settings = load_world_settings()
                    return
                    
                # Physics tab controls
                settings = self.world_settings
                wt = settings.get('winds_and_temps', {})
                zones = wt.get('zones', [])
                
                if name == 'precip_minus':
                    wt['precipitation_multiplier'] = max(0.0, wt.get('precipitation_multiplier', 1.0) - 0.1)
                elif name == 'precip_plus':
                    wt['precipitation_multiplier'] = min(5.0, wt.get('precipitation_multiplier', 1.0) + 0.1)
                elif name == 'lat_min_minus':
                    wt['global_latitude_min'] = max(-90.0, wt.get('global_latitude_min', -90.0) - 5.0)
                elif name == 'lat_min_plus':
                    wt['global_latitude_min'] = min(wt.get('global_latitude_max', 90.0) - 5.0, wt.get('global_latitude_min', -90.0) + 5.0)
                elif name == 'lat_max_minus':
                    wt['global_latitude_max'] = max(wt.get('global_latitude_min', -90.0) + 5.0, wt.get('global_latitude_max', 90.0) - 5.0)
                elif name == 'lat_max_plus':
                    wt['global_latitude_max'] = min(90.0, wt.get('global_latitude_max', 90.0) + 5.0)
                    
                # Zone adjustments
                for zi in range(len(zones)):
                    if name == f'zone_{zi}_wind_dir':
                        curr_dir = zones[zi].get('wind_dir', 'N')
                        idx = WIND_DIRECTIONS.index(curr_dir) if curr_dir in WIND_DIRECTIONS else 0
                        zones[zi]['wind_dir'] = WIND_DIRECTIONS[(idx + 1) % len(WIND_DIRECTIONS)]
                    elif name == f'zone_{zi}_speed_minus':
                        zones[zi]['wind_speed'] = max(0.0, zones[zi].get('wind_speed', 0.5) - 0.1)
                    elif name == f'zone_{zi}_speed_plus':
                        zones[zi]['wind_speed'] = min(2.0, zones[zi].get('wind_speed', 0.5) + 0.1)
                    elif name == f'zone_{zi}_tmin_minus':
                        zones[zi]['temp_min'] = zones[zi].get('temp_min', 0.0) - 5.0
                    elif name == f'zone_{zi}_tmin_plus':
                        zones[zi]['temp_min'] = zones[zi].get('temp_min', 0.0) + 5.0
                    elif name == f'zone_{zi}_tmax_minus':
                        zones[zi]['temp_max'] = zones[zi].get('temp_max', 20.0) - 5.0
                    elif name == f'zone_{zi}_tmax_plus':
                        zones[zi]['temp_max'] = zones[zi].get('temp_max', 20.0) + 5.0
                
                # Calendar tab controls
                cal = settings.get('calendar', {})
                if name == 'days_minus':
                    cal['days_per_year'] = max(30, cal.get('days_per_year', 360) - 10)
                elif name == 'days_plus':
                    cal['days_per_year'] = cal.get('days_per_year', 360) + 10
                    
                return

    def handle_edit_action(self, action):
        """Executes detailed map edits for the selected cell, writing to SQLite in real-time."""
        if not self.selected_cell:
            return
            
        cell_id = self.selected_cell['id']
        controlling_burg_id = self.selected_cell.get('controlling_burg_id', cell_id)
        is_aquatic = self.selected_cell['elevation'] < 0
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if the controlling settlement has a row in macro_groups
        cur.execute("SELECT * FROM macro_groups WHERE cell_id = ?", (controlling_burg_id,))
        row = cur.fetchone()
        faction_row = dict(row) if row else None
        
        matching_node = next((n for n in getattr(self, 'resource_nodes', []) if n['cell_id'] == cell_id), None)
        
        if action == 'deselect':
            self.selected_cell = None
            cur.close()
            conn.close()
            return
            
        # Structure editing (Updates applied to the controlling province/settlement row)
        elif action == 'cycle_farm_plus' and faction_row:
            col = 'kelp_farms_count' if is_aquatic else 'farms_count'
            cur.execute(f"UPDATE macro_groups SET {col} = MIN(3, {col} + 1) WHERE cell_id = ?", (controlling_burg_id,))
        elif action == 'cycle_farm_minus' and faction_row:
            col = 'kelp_farms_count' if is_aquatic else 'farms_count'
            cur.execute(f"UPDATE macro_groups SET {col} = MAX(0, {col} - 1) WHERE cell_id = ?", (controlling_burg_id,))
            
        elif action == 'cycle_mine_plus' and faction_row:
            col = 'coral_mines_count' if is_aquatic else 'mines_count'
            cur.execute(f"UPDATE macro_groups SET {col} = MIN(3, {col} + 1) WHERE cell_id = ?", (controlling_burg_id,))
        elif action == 'cycle_mine_minus' and faction_row:
            col = 'coral_mines_count' if is_aquatic else 'mines_count'
            cur.execute(f"UPDATE macro_groups SET {col} = MAX(0, {col} - 1) WHERE cell_id = ?", (controlling_burg_id,))
            
        elif action == 'cycle_barracks_plus' and faction_row:
            col = 'underwater_domes_count' if is_aquatic else 'barracks_count'
            cur.execute(f"UPDATE macro_groups SET {col} = MIN(3, {col} + 1) WHERE cell_id = ?", (controlling_burg_id,))
        elif action == 'cycle_barracks_minus' and faction_row:
            col = 'underwater_domes_count' if is_aquatic else 'barracks_count'
            cur.execute(f"UPDATE macro_groups SET {col} = MAX(0, {col} - 1) WHERE cell_id = ?", (controlling_burg_id,))
            
        elif action == 'cycle_tower_plus' and faction_row:
            col = 'reef_walls_count' if is_aquatic else 'watchtowers_count'
            cur.execute(f"UPDATE macro_groups SET {col} = MIN(3, {col} + 1) WHERE cell_id = ?", (controlling_burg_id,))
        elif action == 'cycle_tower_minus' and faction_row:
            col = 'reef_walls_count' if is_aquatic else 'watchtowers_count'
            cur.execute(f"UPDATE macro_groups SET {col} = MAX(0, {col} - 1) WHERE cell_id = ?", (controlling_burg_id,))
            
        elif action == 'cycle_workshops_plus' and faction_row and not is_aquatic:
            cur.execute("UPDATE macro_groups SET workshops_count = MIN(3, workshops_count + 1) WHERE cell_id = ?", (controlling_burg_id,))
        elif action == 'cycle_workshops_minus' and faction_row and not is_aquatic:
            cur.execute("UPDATE macro_groups SET workshops_count = MAX(0, workshops_count - 1) WHERE cell_id = ?", (controlling_burg_id,))
            
        elif action == 'toggle_docks' and faction_row:
            new_val = 1 if faction_row.get('docks_count', 0) == 0 else 0
            cur.execute("UPDATE macro_groups SET docks_count = ? WHERE cell_id = ?", (new_val, controlling_burg_id))
            
        # Stats editing (Updates applied to the controlling province/settlement row)
        elif action == 'pop_plus' and faction_row:
            cur.execute("UPDATE macro_groups SET population = population + 100 WHERE cell_id = ?", (controlling_burg_id,))
        elif action == 'pop_minus' and faction_row:
            cur.execute("UPDATE macro_groups SET population = MAX(0, population - 100) WHERE cell_id = ?", (controlling_burg_id,))
            
        elif action == 'dis_plus' and faction_row:
            cur.execute("UPDATE macro_groups SET discontent = MIN(1.0, discontent + 0.05) WHERE cell_id = ?", (controlling_burg_id,))
        elif action == 'dis_minus' and faction_row:
            cur.execute("UPDATE macro_groups SET discontent = MAX(0.0, discontent - 0.05) WHERE cell_id = ?", (controlling_burg_id,))
            
        elif action == 'crime_plus' and faction_row:
            cur.execute("UPDATE macro_groups SET crime_level = MIN(1.0, crime_level + 0.05) WHERE cell_id = ?", (controlling_burg_id,))
        elif action == 'crime_minus' and faction_row:
            cur.execute("UPDATE macro_groups SET crime_level = MAX(0.0, crime_level - 0.05) WHERE cell_id = ?", (controlling_burg_id,))
            
        elif action == 'toggle_capital' and faction_row:
            new_val = 1 if faction_row.get('is_capital', 0) == 0 else 0
            cur.execute("UPDATE macro_groups SET is_capital = ? WHERE cell_id = ?", (new_val, controlling_burg_id))
            
        elif action == 'change_faction' and faction_row:
            current_fid = faction_row['faction_id']
            new_fid = (current_fid + 1) % 18
            new_name = 'Neutrals' if new_fid == 0 else FACTION_NAMES[new_fid - 1]
            cur.execute("UPDATE macro_groups SET faction_id = ?, faction_name = ?, is_capital = 0 WHERE cell_id = ?", (new_fid, new_name, controlling_burg_id))
            
        # Biome & Elevation editing (Applied to the clicked cell locally)
        elif action == 'change_biome':
            cur.execute("SELECT biome FROM cells WHERE id = ?", (cell_id,))
            current_biome = cur.fetchone()[0]
            new_idx = (BIOMES_LIST.index(current_biome) + 1) % len(BIOMES_LIST) if current_biome in BIOMES_LIST else 0
            new_biome = BIOMES_LIST[new_idx]
            new_elev = -0.5 if new_biome in ['Ocean', 'Coastal', 'Reef', 'Abyssal', 'Thermal'] else 0.1
            cur.execute("UPDATE cells SET biome = ?, elevation = ?, depth_elevation = ? WHERE id = ?", (new_biome, new_elev, new_elev, cell_id))
            
        elif action == 'elev_plus':
            cur.execute("UPDATE cells SET elevation = elevation + 0.05, depth_elevation = depth_elevation + 0.05 WHERE id = ?", (cell_id,))
        elif action == 'elev_minus':
            cur.execute("UPDATE cells SET elevation = elevation - 0.05, depth_elevation = depth_elevation - 0.05 WHERE id = ?", (cell_id,))
            
        # Resource Node editing (Applied to the clicked cell locally)
        elif action == 'cycle_node':
            cur.execute("SELECT * FROM resource_nodes WHERE cell_id = ?", (cell_id,))
            node_row = cur.fetchone()
            if not node_row:
                first_node = NODE_TYPES[0]
                cur.execute('''
                    INSERT INTO resource_nodes (cell_id, faction_id, name, icon, description, yield_remaining, is_discovered)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                ''', (cell_id, faction_row['faction_id'] if faction_row else 0, first_node["name"], first_node["icon"], first_node["desc"], first_node["yield"]))
            else:
                curr_name = node_row['name']
                curr_idx = next((i for i, nt in enumerate(NODE_TYPES) if nt["name"] == curr_name), -1)
                next_idx = (curr_idx + 1) % len(NODE_TYPES)
                next_node = NODE_TYPES[next_idx]
                cur.execute("DELETE FROM resource_nodes WHERE cell_id = ?", (cell_id,))
                cur.execute('''
                    INSERT INTO resource_nodes (cell_id, faction_id, name, icon, description, yield_remaining, is_discovered)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                ''', (cell_id, faction_row['faction_id'] if faction_row else 0, next_node["name"], next_node["icon"], next_node["desc"], next_node["yield"]))
                
        elif action == 'yield_plus' and matching_node:
            cur.execute("UPDATE resource_nodes SET yield_remaining = yield_remaining + 50.0 WHERE cell_id = ?", (cell_id,))
        elif action == 'yield_minus' and matching_node:
            cur.execute("UPDATE resource_nodes SET yield_remaining = MAX(0.0, yield_remaining - 50.0) WHERE cell_id = ?", (cell_id,))
        elif action == 'clear_node':
            cur.execute("DELETE FROM resource_nodes WHERE cell_id = ?", (cell_id,))
            
        # Cult / Fringe Adjustments (Applied to the clicked cell locally)
        elif action.startswith('cult') and (action.endswith('plus') or action.endswith('minus')):
            idx = int(action[4]) - 1
            if idx < len(getattr(self, 'top_cults_drawn', [])):
                cult_name = self.top_cults_drawn[idx]
                cur.execute("SELECT cults_json FROM cells WHERE id = ?", (cell_id,))
                cults_inf = json.loads(cur.fetchone()[0])
                current_val = cults_inf.get(cult_name, 0.0)
                new_val = min(1.0, max(0.0, current_val + 0.05 if action.endswith('plus') else current_val - 0.05))
                cults_inf[cult_name] = round(new_val, 2)
                cur.execute("UPDATE cells SET cults_json = ? WHERE id = ?", (json.dumps(cults_inf), cell_id))
                
        elif action.startswith('fringe') and (action.endswith('plus') or action.endswith('minus')):
            idx = int(action[6]) - 1
            if idx < len(getattr(self, 'top_fringe_drawn', [])):
                fringe_name = self.top_fringe_drawn[idx]
                cur.execute("SELECT fringe_json FROM cells WHERE id = ?", (cell_id,))
                fringe_inf = json.loads(cur.fetchone()[0])
                current_val = fringe_inf.get(fringe_name, 0.0)
                new_val = min(1.0, max(0.0, current_val + 0.05 if action.endswith('plus') else current_val - 0.05))
                fringe_inf[fringe_name] = round(new_val, 2)
                cur.execute("UPDATE cells SET fringe_json = ? WHERE id = ?", (json.dumps(fringe_inf), cell_id))
                
        elif action == 'inject_cult':
            prisons = self.world_settings.get('cult_names', PRISON_NAMES) + ["Wardens"]
            cur.execute("SELECT cults_json FROM cells WHERE id = ?", (cell_id,))
            cults_inf = json.loads(cur.fetchone()[0])
            for p in prisons:
                if cults_inf.get(p, 0.0) == 0.0:
                    cults_inf[p] = 0.10
                    break
            cur.execute("UPDATE cells SET cults_json = ? WHERE id = ?", (json.dumps(cults_inf), cell_id))
            
        elif action == 'inject_fringe':
            fringe_list = [fg['name'] for fg in self.world_settings.get('entities', {}).get('fringe_groups', [])]
            cur.execute("SELECT fringe_json FROM cells WHERE id = ?", (cell_id,))
            fringe_inf = json.loads(cur.fetchone()[0])
            for f in fringe_list:
                if fringe_inf.get(f, 0.0) == 0.0:
                    fringe_inf[f] = 0.10
                    break
            cur.execute("UPDATE cells SET fringe_json = ? WHERE id = ?", (json.dumps(fringe_inf), cell_id))
            
        conn.commit()
        cur.close()
        conn.close()
        
        # Sync and restore selections
        self.sync_data()
        for cell in self.cells:
            if cell['id'] == cell_id:
                self.selected_cell = cell
                break

    def handle_click(self, pos):
        """Processes button clicks in the sidebar and routes editor clicks."""
        # 1. Check config overlay first
        if self.config_overlay_open:
            self.handle_config_click(pos)
            return
        
        # 2. Check Tab Clicks (cell details tabs)
        if self.selected_cell and not self.edit_mode and hasattr(self, 'tabs'):
            for t_name, rect in self.tabs.items():
                if rect.collidepoint(pos):
                    self.active_tab = t_name
                    return
                    
        # 3. Check selected cell editor actions
        if self.selected_cell and not self.edit_mode and hasattr(self, 'edit_buttons'):
            for name, rect in self.edit_buttons.items():
                if rect.collidepoint(pos):
                    self.handle_edit_action(name)
                    return
                    
        # 4. Check main sidebar buttons
        for name, rect in self.buttons.items():
            if rect.collidepoint(pos):
                if name == 'tick':
                    if self.model:
                        try:
                            self.model.step()
                            self.sync_data()
                        except Exception as e:
                            print(f"Error running tick: {e}")
                    else:
                        print("Warning: Simulation Model not running.")
                elif name == 'auto':
                    self.autoplay = not self.autoplay
                    self.last_tick_time = pygame.time.get_ticks()
                    print(f"Autoplay toggled: {self.autoplay}")
                elif name == 'edit_toggle':
                    self.edit_mode = not self.edit_mode
                    if self.edit_mode:
                        self.selected_cell = None  # Deselect cell when entering edit mode
                    print(f"Edit mode: {'ON' if self.edit_mode else 'OFF'}")
                elif name == 'sync':
                    self.sync_data()
                    print("Data synchronized from database.")
                elif name == 'save_json':
                    save_world_settings(self.world_settings)
                    print("Settings saved to world_settings.json")
                elif name == 'push_db':
                    self.push_settings_to_db()
                    
                # Layer button clicks
                elif name.startswith('lay_'):
                    lay = name[4:]
                    # Calendar is not a paint layer, so click does nothing but select calendar active
                    if lay == 'calendar':
                        self.active_layer = 'biomes'
                        self.brush_tool = 'paint_biome'
                        self.edit_mode = False
                        self.edit_calendar_settings()
                        return
                        
                    self.active_layer = lay
                    if lay == 'biomes':
                        self.brush_tool = 'paint_biome'
                    elif lay == 'elevation':
                        self.brush_tool = 'elev_up'
                    elif lay == 'factions':
                        self.brush_tool = 'paint_faction'
                    elif lay == 'settlements':
                        self.brush_tool = 'paint_faction'
                    elif lay == 'cults':
                        self.brush_tool = 'paint_cult'
                    elif lay == 'fringe':
                        self.brush_tool = 'paint_fringe'
                    elif lay == 'ecology':
                        self.brush_tool = 'paint_ecology'
                    elif lay == 'resources':
                        self.brush_tool = 'place_resource'
                    self.edit_mode = True
                    self.selected_cell = None
                    self.sync_data()
                    print(f"Switched active visual layer to: {lay} and enabled paint brush.")
                    
                # Context-sensitive active settings edit buttons in the row
                elif name.startswith('edit_settings_'):
                    action_type = name[14:]
                    if action_type == 'biomes':
                        self.edit_biomes_settings()
                    elif action_type == 'elevation':
                        self.edit_elevation_settings()
                    elif action_type == 'calendar':
                        self.edit_calendar_settings()
                    elif action_type == 'factions':
                        self.edit_factions_settings()
                    elif action_type == 'settlements':
                        self.edit_settlements_settings()
                    elif action_type == 'cults':
                        self.edit_cults_prisons_settings()
                    elif action_type == 'fringe':
                        self.edit_fringe_settings()
                    elif action_type == 'ecology':
                        self.edit_ecology_settings()
                    elif action_type == 'resources':
                        self.edit_resources_recipes_settings()
                    
                # Editor tool modes (within elevation)
                elif name.startswith('tool_'):
                    tool_id = name[5:]
                    if tool_id in self.brush_tools_list:
                        self.brush_tool = tool_id
                elif name == 'radius_minus':
                    self.brush_radius = max(1, self.brush_radius - 1)
                elif name == 'radius_plus':
                    self.brush_radius = min(20, self.brush_radius + 1)
                elif name == 'power_minus':
                    self.brush_power = max(1, self.brush_power - 1)
                elif name == 'power_plus':
                    self.brush_power = min(10, self.brush_power + 1)
                elif name == 'palette_prev':
                    if self.brush_tool == 'paint_biome' or self.brush_tool == 'paint_ecology':
                        self.selected_biome_idx = (self.selected_biome_idx - 1) % len(BIOMES_LIST)
                    elif self.brush_tool == 'paint_faction':
                        self.selected_faction_idx = (self.selected_faction_idx - 1) % len(FACTION_NAMES)
                    elif self.brush_tool == 'paint_cult':
                        cult_list = self.world_settings.get('cult_names', PRISON_NAMES) + ["Wardens"]
                        self.selected_cult_idx = (self.selected_cult_idx - 1) % len(cult_list)
                    elif self.brush_tool == 'paint_fringe':
                        self.selected_fringe_idx = (self.selected_fringe_idx - 1) % len(FRINGE_NAMES)
                    elif self.brush_tool == 'place_resource':
                        self.selected_resource_idx = (self.selected_resource_idx - 1) % len(NODE_TYPES)
                elif name == 'palette_next':
                    if self.brush_tool == 'paint_biome' or self.brush_tool == 'paint_ecology':
                        self.selected_biome_idx = (self.selected_biome_idx + 1) % len(BIOMES_LIST)
                    elif self.brush_tool == 'paint_faction':
                        self.selected_faction_idx = (self.selected_faction_idx + 1) % len(FACTION_NAMES)
                    elif self.brush_tool == 'paint_cult':
                        cult_list = self.world_settings.get('cult_names', PRISON_NAMES) + ["Wardens"]
                        self.selected_cult_idx = (self.selected_cult_idx + 1) % len(cult_list)
                    elif self.brush_tool == 'paint_fringe':
                        self.selected_fringe_idx = (self.selected_fringe_idx + 1) % len(FRINGE_NAMES)
                    elif self.brush_tool == 'place_resource':
                        self.selected_resource_idx = (self.selected_resource_idx + 1) % len(NODE_TYPES)
                return

    # ============ CONFIG OVERLAY DRAWING ============
    def draw_config_overlay(self):
        """Draws a fullscreen dark overlay with tabbed settings editor for world configuration."""
        if not self.config_overlay_open:
            return
            
        # Transparent background
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((20, 24, 30, 240))
        self.screen.blit(overlay, (0, 0))
        
        # Center container
        cw, ch = 800, 600
        cx = (self.screen_width - cw) // 2
        cy = (self.screen_height - ch) // 2
        pygame.draw.rect(self.screen, (35, 40, 50), (cx, cy, cw, ch), border_radius=8)
        pygame.draw.rect(self.screen, (80, 90, 100), (cx, cy, cw, ch), 2, border_radius=8)
        
        font_large = pygame.font.SysFont("arial", 20, bold=True)
        font_medium = pygame.font.SysFont("arial", 14, bold=True)
        font_small = pygame.font.SysFont("arial", 12)
        font_small_bold = pygame.font.SysFont("arial", 11, bold=True)
        font_tiny = pygame.font.SysFont("arial", 10)
        
        # Title
        title_lbl = font_large.render("Advanced Simulation Constants Settings", True, (255, 255, 255))
        self.screen.blit(title_lbl, (cx + 20, cy + 15))
        
        # Close button
        self.config_buttons = {
            'close': pygame.Rect(cx + cw - 100, cy + 15, 80, 24),
            'save_settings': pygame.Rect(cx + cw - 220, cy + 15, 110, 24),
            'edit_full_details': pygame.Rect(cx + 20, cy + ch - 45, 200, 30), # Launch Tkinter helper
        }
        pygame.draw.rect(self.screen, (150, 70, 70), self.config_buttons['close'], border_radius=4)
        txt = font_small_bold.render("Close Tab", True, (255, 255, 255))
        self.screen.blit(txt, txt.get_rect(center=self.config_buttons['close'].center))
        
        pygame.draw.rect(self.screen, (70, 120, 80), self.config_buttons['save_settings'], border_radius=4)
        txt = font_small_bold.render("Save Changes", True, (255, 255, 255))
        self.screen.blit(txt, txt.get_rect(center=self.config_buttons['save_settings'].center))
        
        pygame.draw.rect(self.screen, (100, 80, 120), self.config_buttons['edit_full_details'], border_radius=4)
        txt = font_medium.render("Edit All Settings (Interactive)", True, (255, 255, 255))
        self.screen.blit(txt, txt.get_rect(center=self.config_buttons['edit_full_details'].center))
        
        # Tabs bar Y = cy + 50
        tab_y = cy + 50
        tabs = ['physics', 'calendar', 'entities', 'rules']
        tab_labels = {
            'physics': '1. Climate / Prevailing Winds',
            'calendar': '2. Calendar & Moons',
            'entities': '3. Entities & Factions',
            'rules': '4. Rules, Unlocks & Costs'
        }
        
        for ti, tab in enumerate(tabs):
            tx = cx + 20 + ti * 185
            rect = pygame.Rect(tx, tab_y, 180, 26)
            self.config_buttons[f'tab_{tab}'] = rect
            
            is_active = (self.config_tab == tab)
            bg = (55, 62, 78) if is_active else (40, 44, 52)
            pygame.draw.rect(self.screen, bg, rect, border_top_left_radius=4, border_top_right_radius=4)
            if is_active:
                pygame.draw.rect(self.screen, (100, 150, 255), rect, 1, border_top_left_radius=4, border_top_right_radius=4)
            
            txt_surf = font_small_bold.render(tab_labels[tab], True, (255, 255, 255) if is_active else (160, 160, 160))
            self.screen.blit(txt_surf, txt_surf.get_rect(center=rect.center))
            
        # Content frame background
        pygame.draw.rect(self.screen, (55, 62, 78), (cx + 20, tab_y + 26, cw - 40, ch - 130), border_radius=4)
        pygame.draw.rect(self.screen, (80, 90, 100), (cx + 20, tab_y + 26, cw - 40, ch - 130), 1, border_radius=4)
        
        # Render tab content
        ccx, ccy = cx + 30, tab_y + 36
        ccw, cch = cw - 60, ch - 150
        
        if self.config_tab == 'physics':
            self._draw_config_physics(ccx, ccy, ccw, cch, self.world_settings, font_medium, font_small, font_small_bold, font_tiny)
        elif self.config_tab == 'calendar':
            self._draw_config_calendar(ccx, ccy, ccw, cch, self.world_settings, font_medium, font_small, font_small_bold, font_tiny)
        elif self.config_tab == 'entities':
            self._draw_config_entities(ccx, ccy, ccw, cch, self.world_settings, font_medium, font_small, font_small_bold, font_tiny)
        elif self.config_tab == 'rules':
            self._draw_config_rules(ccx, ccy, ccw, cch, self.world_settings, font_medium, font_small, font_small_bold, font_tiny)

    def _draw_config_physics(self, cx, cy, cw, ch, settings, font_medium, font_small, font_small_bold, font_tiny):
        """Draws the Climate & Physics tab content with interactive winds adjustment."""
        wt = settings.get('winds_and_temps', {})
        p_mult = wt.get('precipitation_multiplier', 1.0)
        lat_min = wt.get('global_latitude_min', -90.0)
        lat_max = wt.get('global_latitude_max', 90.0)
        zones = wt.get('zones', [])
        
        y = cy + 10
        self.screen.blit(font_medium.render("Climate Settings & Prevailing Winds", True, (255, 200, 100)), (cx + 15, y))
        y += 26
        
        # Precipitation Multiplier
        self.screen.blit(font_small.render(f"Global Precipitation Multiplier: {p_mult:.2f}x", True, (200, 210, 230)), (cx + 15, y))
        self.config_buttons['precip_minus'] = pygame.Rect(cx + 250, y, 30, 16)
        self.config_buttons['precip_plus'] = pygame.Rect(cx + 285, y, 30, 16)
        pygame.draw.rect(self.screen, (100, 70, 70), self.config_buttons['precip_minus'], border_radius=3)
        pygame.draw.rect(self.screen, (70, 100, 70), self.config_buttons['precip_plus'], border_radius=3)
        self.screen.blit(font_small_bold.render("-", True, (255,255,255)), font_small_bold.render("-", True, (255,255,255)).get_rect(center=self.config_buttons['precip_minus'].center))
        self.screen.blit(font_small_bold.render("+", True, (255,255,255)), font_small_bold.render("+", True, (255,255,255)).get_rect(center=self.config_buttons['precip_plus'].center))
        y += 24
        
        # Latitude range
        self.screen.blit(font_small.render(f"Global Latitude Range: {lat_min:.0f}° to {lat_max:.0f}°", True, (200, 210, 230)), (cx + 15, y))
        self.config_buttons['lat_min_minus'] = pygame.Rect(cx + 250, y, 22, 16)
        self.config_buttons['lat_min_plus'] = pygame.Rect(cx + 274, y, 22, 16)
        self.config_buttons['lat_max_minus'] = pygame.Rect(cx + 310, y, 22, 16)
        self.config_buttons['lat_max_plus'] = pygame.Rect(cx + 334, y, 22, 16)
        
        pygame.draw.rect(self.screen, (100, 70, 70), self.config_buttons['lat_min_minus'], border_radius=2)
        pygame.draw.rect(self.screen, (70, 100, 70), self.config_buttons['lat_min_plus'], border_radius=2)
        pygame.draw.rect(self.screen, (100, 70, 70), self.config_buttons['lat_max_minus'], border_radius=2)
        pygame.draw.rect(self.screen, (70, 100, 70), self.config_buttons['lat_max_plus'], border_radius=2)
        
        self.screen.blit(font_tiny.render("-", True, (255,255,255)), font_tiny.render("-", True, (255,255,255)).get_rect(center=self.config_buttons['lat_min_minus'].center))
        self.screen.blit(font_tiny.render("+", True, (255,255,255)), font_tiny.render("+", True, (255,255,255)).get_rect(center=self.config_buttons['lat_min_plus'].center))
        self.screen.blit(font_tiny.render("-", True, (255,255,255)), font_tiny.render("-", True, (255,255,255)).get_rect(center=self.config_buttons['lat_max_minus'].center))
        self.screen.blit(font_tiny.render("+", True, (255,255,255)), font_tiny.render("+", True, (255,255,255)).get_rect(center=self.config_buttons['lat_max_plus'].center))
        y += 30
        
        # Wind zones table
        pygame.draw.line(self.screen, (80, 80, 80), (cx + 15, y), (cx + cw - 30, y), 1)
        y += 6
        self.screen.blit(font_small_bold.render("Zone Name", True, (180, 190, 210)), (cx + 15, y))
        self.screen.blit(font_small_bold.render("Wind Dir", True, (180, 190, 210)), (cx + 200, y))
        self.screen.blit(font_small_bold.render("Wind Speed", True, (180, 190, 210)), (cx + 290, y))
        self.screen.blit(font_small_bold.render("Min Temp", True, (180, 190, 210)), (cx + 410, y))
        self.screen.blit(font_small_bold.render("Max Temp", True, (180, 190, 210)), (cx + 530, y))
        
        y += 20
        pygame.draw.line(self.screen, (80, 80, 80), (cx + 15, y), (cx + cw - 30, y), 1)
        y += 5
        
        # Draw each zone row with adjust buttons
        for zi, zone in enumerate(zones):
            zone_name = zone.get('name', f'Zone {zi}')
            wind_dir = zone.get('wind_dir', 'N')
            wind_speed = zone.get('wind_speed', 0.5)
            temp_min = zone.get('temp_min', 0.0)
            temp_max = zone.get('temp_max', 20.0)
            
            self.screen.blit(font_small.render(zone_name[:18], True, (200, 200, 200)), (cx + 15, y))
            
            # Wind direction cycle button
            wd_rect = pygame.Rect(cx + 200, y, 60, 18)
            self.config_buttons[f'zone_{zi}_wind_dir'] = wd_rect
            pygame.draw.rect(self.screen, (60, 70, 85), wd_rect, border_radius=3)
            self.screen.blit(font_small_bold.render(wind_dir, True, (255, 230, 150)), font_small_bold.render(wind_dir, True, (255, 230, 150)).get_rect(center=wd_rect.center))
            
            # Wind speed +/-
            self.screen.blit(font_small.render(f"{wind_speed:.1f}", True, (200, 200, 200)), (cx + 310, y))
            self.config_buttons[f'zone_{zi}_speed_minus'] = pygame.Rect(cx + 350, y, 22, 16)
            self.config_buttons[f'zone_{zi}_speed_plus'] = pygame.Rect(cx + 376, y, 22, 16)
            pygame.draw.rect(self.screen, (100, 70, 70), self.config_buttons[f'zone_{zi}_speed_minus'], border_radius=2)
            pygame.draw.rect(self.screen, (70, 100, 70), self.config_buttons[f'zone_{zi}_speed_plus'], border_radius=2)
            self.screen.blit(font_tiny.render("-", True, (255,255,255)), font_tiny.render("-", True, (255,255,255)).get_rect(center=self.config_buttons[f'zone_{zi}_speed_minus'].center))
            self.screen.blit(font_tiny.render("+", True, (255,255,255)), font_tiny.render("+", True, (255,255,255)).get_rect(center=self.config_buttons[f'zone_{zi}_speed_plus'].center))
            
            # Temp min +/-
            self.screen.blit(font_small.render(f"{temp_min:.0f}°", True, (200, 200, 200)), (cx + 420, y))
            self.config_buttons[f'zone_{zi}_tmin_minus'] = pygame.Rect(cx + 465, y, 22, 16)
            self.config_buttons[f'zone_{zi}_tmin_plus'] = pygame.Rect(cx + 491, y, 22, 16)
            pygame.draw.rect(self.screen, (100, 70, 70), self.config_buttons[f'zone_{zi}_tmin_minus'], border_radius=2)
            pygame.draw.rect(self.screen, (70, 100, 70), self.config_buttons[f'zone_{zi}_tmin_plus'], border_radius=2)
            self.screen.blit(font_tiny.render("-", True, (255,255,255)), font_tiny.render("-", True, (255,255,255)).get_rect(center=self.config_buttons[f'zone_{zi}_tmin_minus'].center))
            self.screen.blit(font_tiny.render("+", True, (255,255,255)), font_tiny.render("+", True, (255,255,255)).get_rect(center=self.config_buttons[f'zone_{zi}_tmin_plus'].center))
            
            # Temp max +/-
            self.screen.blit(font_small.render(f"{temp_max:.0f}°", True, (200, 200, 200)), (cx + 540, y))
            self.config_buttons[f'zone_{zi}_tmax_minus'] = pygame.Rect(cx + 585, y, 22, 16)
            self.config_buttons[f'zone_{zi}_tmax_plus'] = pygame.Rect(cx + 611, y, 22, 16)
            pygame.draw.rect(self.screen, (100, 70, 70), self.config_buttons[f'zone_{zi}_tmax_minus'], border_radius=2)
            pygame.draw.rect(self.screen, (70, 100, 70), self.config_buttons[f'zone_{zi}_tmax_plus'], border_radius=2)
            self.screen.blit(font_tiny.render("-", True, (255,255,255)), font_tiny.render("-", True, (255,255,255)).get_rect(center=self.config_buttons[f'zone_{zi}_tmax_minus'].center))
            self.screen.blit(font_tiny.render("+", True, (255,255,255)), font_tiny.render("+", True, (255,255,255)).get_rect(center=self.config_buttons[f'zone_{zi}_tmax_plus'].center))
            
            y += 24

    def _draw_config_calendar(self, cx, cy, cw, ch, settings, font_medium, font_small, font_small_bold, font_tiny):
        """Draws the Calendar tab: days per year, months, seasons, moons."""
        cal = settings.get('calendar', {})
        days = cal.get('days_per_year', 360)
        months = cal.get('months', [])
        seasons = cal.get('seasons', [])
        moons = cal.get('moons', [])
        
        y = cy + 10
        self.screen.blit(font_medium.render("Calendar Configuration", True, (255, 200, 100)), (cx + 15, y))
        y += 26
        
        # Days per year
        self.screen.blit(font_small.render(f"Days Per Year: {days}", True, (200, 210, 230)), (cx + 15, y))
        self.config_buttons['days_minus'] = pygame.Rect(cx + 200, y, 30, 16)
        self.config_buttons['days_plus'] = pygame.Rect(cx + 235, y, 30, 16)
        pygame.draw.rect(self.screen, (100, 70, 70), self.config_buttons['days_minus'], border_radius=3)
        pygame.draw.rect(self.screen, (70, 100, 70), self.config_buttons['days_plus'], border_radius=3)
        self.screen.blit(font_small_bold.render("-10", True, (255,255,255)), font_small_bold.render("-10", True, (255,255,255)).get_rect(center=self.config_buttons['days_minus'].center))
        self.screen.blit(font_small_bold.render("+10", True, (255,255,255)), font_small_bold.render("+10", True, (255,255,255)).get_rect(center=self.config_buttons['days_plus'].center))
        y += 24
        
        # Months list (display up to 15)
        self.screen.blit(font_small_bold.render(f"Months ({len(months)}):", True, (180, 190, 210)), (cx + 15, y))
        y += 18
        for mi, month in enumerate(months[:15]):
            self.screen.blit(font_tiny.render(f"  {mi+1}. {month}", True, (180, 180, 180)), (cx + 15, y))
            y += 14
        y += 8
        
        # Seasons
        self.screen.blit(font_small_bold.render("Seasons:", True, (180, 190, 210)), (cx + 15, y))
        y += 18
        for si, season in enumerate(seasons):
            s_name = season.get('name', f'Season {si}')
            s_start = season.get('start_day', 0)
            s_end = season.get('end_day', 90)
            growth = season.get('growth_mod', 1.0)
            travel = season.get('travel_cost_mod', 1.0)
            self.screen.blit(font_tiny.render(f"  {s_name}: Days {s_start}-{s_end} | Growth: {growth:.1f}x | Travel: {travel:.1f}x", True, (180, 180, 180)), (cx + 15, y))
            y += 14
        y += 8
        
        # Moons
        self.screen.blit(font_small_bold.render("Moons:", True, (180, 190, 210)), (cx + 15, y))
        y += 18
        for moon in moons:
            m_name = moon.get('name', 'Moon')
            m_cycle = moon.get('cycle_days', 30)
            self.screen.blit(font_tiny.render(f"  {m_name}: {m_cycle}-day cycle", True, (180, 180, 180)), (cx + 15, y))
            y += 14

    def _draw_config_entities(self, cx, cy, cw, ch, settings, font_medium, font_small, font_small_bold, font_tiny):
        """Draws the Entities tab: factions, fringe groups, flora, fauna."""
        entities = settings.get('entities', {})
        factions = entities.get('factions', [])
        fringe = entities.get('fringe_groups', [])
        flora = entities.get('flora', [])
        fauna = entities.get('fauna', [])
        
        y = cy + 10
        self.screen.blit(font_medium.render("Entity Configuration", True, (255, 200, 100)), (cx + 15, y))
        y += 26
        
        # Two-column layout
        col1_x = cx + 15
        col2_x = cx + cw // 2 + 10
        
        # Left column: Factions
        self.screen.blit(font_small_bold.render(f"Factions ({len(factions)}):", True, (180, 190, 210)), (col1_x, y))
        fy = y + 18
        for fi, fac in enumerate(factions[:17]):
            color_hex = fac.get('color', '#888888')
            try:
                r = int(color_hex[1:3], 16)
                g = int(color_hex[3:5], 16)
                b = int(color_hex[5:7], 16)
                pygame.draw.rect(self.screen, (r, g, b), (col1_x, fy + 2, 10, 10), border_radius=2)
            except Exception:
                pass
            self.screen.blit(font_tiny.render(f" {fac.get('name', '?')[:20]}", True, (180, 180, 180)), (col1_x + 14, fy))
            fy += 14
        
        # Right column: Fringe Groups
        self.screen.blit(font_small_bold.render(f"Fringe Groups ({len(fringe)}):", True, (180, 190, 210)), (col2_x, y))
        fy2 = y + 18
        for fri, fg in enumerate(fringe[:9]):
            color_hex = fg.get('color', '#888888')
            try:
                r = int(color_hex[1:3], 16)
                g = int(color_hex[3:5], 16)
                b = int(color_hex[5:7], 16)
                pygame.draw.rect(self.screen, (r, g, b), (col2_x, fy2 + 2, 10, 10), border_radius=2)
            except Exception:
                pass
            self.screen.blit(font_tiny.render(f" {fg.get('name', '?')[:20]}", True, (180, 180, 180)), (col2_x + 14, fy2))
            fy2 += 14
        
        y = max(fy, fy2) + 10
        
        # Flora
        self.screen.blit(font_small_bold.render(f"Flora ({len(flora)}):", True, (180, 190, 210)), (col1_x, y))
        fy = y + 18
        for fl in flora[:5]:
            self.screen.blit(font_tiny.render(f"  {fl.get('name', '?')} (rate: {fl.get('growth_rate', 0):.1f})", True, (180, 180, 180)), (col1_x, fy))
            fy += 14
        
        # Fauna
        self.screen.blit(font_small_bold.render(f"Fauna ({len(fauna)}):", True, (180, 190, 210)), (col2_x, y))
        fy2 = y + 18
        for fa in fauna[:5]:
            self.screen.blit(font_tiny.render(f"  {fa.get('name', '?')} (spawn: {fa.get('spawn_rate', 0):.1f})", True, (180, 180, 180)), (col2_x, fy2))
            fy2 += 14

    def _draw_config_rules(self, cx, cy, cw, ch, settings, font_medium, font_small, font_small_bold, font_tiny):
        """Draws the Rules tab: travel costs, building types, military units, production recipes."""
        travel = settings.get('travel_costs', {})
        buildings = settings.get('building_types', [])
        military = settings.get('military_units', [])
        recipes = settings.get('production_recipes', [])
        
        y = cy + 10
        self.screen.blit(font_medium.render("Rules & Costs Configuration", True, (255, 200, 100)), (cx + 15, y))
        y += 26
        
        col1_x = cx + 15
        col2_x = cx + cw // 2 + 10
        
        # Left: Travel Costs
        self.screen.blit(font_small_bold.render("Travel Costs by Biome:", True, (180, 190, 210)), (col1_x, y))
        fy = y + 18
        for biome_name, costs in travel.items():
            walking = costs.get('walking', 1.0)
            riding = costs.get('riding', 1.0)
            boating = costs.get('boating', 1.0)
            self.screen.blit(font_tiny.render(f"  {biome_name}: W:{walking:.1f} R:{riding:.1f} B:{boating:.1f}", True, (180, 180, 180)), (col1_x, fy))
            fy += 14
        
        # Right: Buildings
        self.screen.blit(font_small_bold.render(f"Building Types ({len(buildings)}):", True, (180, 190, 210)), (col2_x, y))
        fy2 = y + 18
        for bld in buildings[:8]:
            cost_str = ", ".join(f"{k}:{v}" for k, v in bld.get('cost', {}).items())
            self.screen.blit(font_tiny.render(f"  {bld.get('label', '?')}: {cost_str[:30]}", True, (180, 180, 180)), (col2_x, fy2))
            fy2 += 14
        
        y = max(fy, fy2) + 10
        
        # Military
        self.screen.blit(font_small_bold.render(f"Military Units ({len(military)}):", True, (180, 190, 210)), (col1_x, y))
        fy = y + 18
        for unit in military[:5]:
            self.screen.blit(font_tiny.render(f"  {unit.get('name', '?')}: Might {unit.get('might', 0)} / End {unit.get('endurance', 0)}", True, (180, 180, 180)), (col1_x, fy))
            fy += 14
        
        # Production Recipes
        self.screen.blit(font_small_bold.render(f"Production Recipes ({len(recipes)}):", True, (180, 190, 210)), (col2_x, y))
        fy2 = y + 18
        for rec in recipes[:5]:
            inputs_str = ", ".join(f"{k}:{v}" for k, v in rec.get('inputs', {}).items())
            self.screen.blit(font_tiny.render(f"  {rec.get('name', '?')}: {inputs_str[:28]}", True, (180, 180, 180)), (col2_x, fy2))
            fy2 += 14

    def run(self):
        """Main Pygame Loop with WASD/Arrows and Middle Click navigation support."""
        clock = pygame.time.Clock()
        running = True
        last_paint_time = 0
        paint_interval = 100  # milliseconds between paint strokes
        
        while running:
            # Panning via WASD/Arrows (Check held keys)
            keys = pygame.key.get_pressed()
            pan_speed = 15.0 / self.zoom
            if not self.config_overlay_open:
                if keys[pygame.K_w] or keys[pygame.K_UP]:
                    self.pan_y += pan_speed * self.zoom
                if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                    self.pan_y -= pan_speed * self.zoom
                if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                    self.pan_x += pan_speed * self.zoom
                if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                    self.pan_x -= pan_speed * self.zoom
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # Left click
                        if self.config_overlay_open:
                            self.handle_config_click(event.pos)
                        elif event.pos[0] >= 960: # Sidebar click
                            self.handle_click(event.pos)
                        elif self.edit_mode:
                            # Start painting
                            self.painting = True
                            self.apply_brush(event.pos)
                            last_paint_time = pygame.time.get_ticks()
                        else:
                            # Drag start (panning)
                            self.dragging = True
                            self.dragged = False
                            self.drag_start_x, self.drag_start_y = event.pos
                    elif event.button == 2: # Middle click - always pan
                        self.dragging = True
                        self.dragged = False
                        self.drag_start_x, self.drag_start_y = event.pos
                    elif event.button == 3: # Right click
                        if event.pos[0] < 960:
                            # Select cell for details
                            self.selected_cell = self.get_cell_at_pos(event.pos)
                            self.edit_mode = False
                            if self.selected_cell:
                                print(f"Selected cell {self.selected_cell['id']} (Biome: {self.selected_cell['biome']})")
                    elif event.button == 4: # Mouse wheel scroll up
                        self.zoom = min(40.0, self.zoom + 0.5)
                    elif event.button == 5: # Mouse wheel scroll down
                        self.zoom = max(1.5, self.zoom - 0.5)
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button in [1, 2]:
                        if event.button == 1 and self.painting:
                            self.painting = False
                            self.sync_data()  # Full database re-read when stroke ends
                        elif self.dragging:
                            self.dragging = False
                            # Left-click select if not dragged
                            if event.button == 1 and not self.dragged and not self.edit_mode and event.pos[0] < 960:
                                self.selected_cell = self.get_cell_at_pos(event.pos)
                                if self.selected_cell:
                                    print(f"Selected cell {self.selected_cell['id']} (Biome: {self.selected_cell['biome']})")
                elif event.type == pygame.MOUSEMOTION:
                    if self.painting and self.edit_mode:
                        now = pygame.time.get_ticks()
                        if now - last_paint_time >= paint_interval:
                            self.apply_brush(event.pos)
                            last_paint_time = now
                    elif self.dragging:
                        mx, my = event.pos
                        dx = mx - self.drag_start_x
                        dy = my - self.drag_start_y
                        if abs(dx) > 2 or abs(dy) > 2:
                            self.dragged = True
                        self.pan_x += dx
                        self.pan_y += dy
                        self.drag_start_x, self.drag_start_y = mx, my
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_TAB:
                        self.world_settings = load_world_settings()
                        self.config_overlay_open = not self.config_overlay_open
                    elif event.key == pygame.K_e:
                        self.edit_mode = not self.edit_mode
                        if self.edit_mode:
                            self.selected_cell = None
                        print(f"Edit mode: {'ON' if self.edit_mode else 'OFF'}")
                    elif event.key == pygame.K_ESCAPE:
                        if self.config_overlay_open:
                            self.config_overlay_open = False
                        elif self.edit_mode:
                            self.edit_mode = False
                        elif self.selected_cell:
                            self.selected_cell = None
            
            # Autoplay simulation advance (ticks run every 3 seconds to keep UI responsive)
            if self.autoplay and self.model:
                now = pygame.time.get_ticks()
                if now - self.last_tick_time >= 3000:
                    try:
                        self.model.step()
                        self.sync_data()
                    except Exception as e:
                        print(f"Autoplay tick error: {e}")
                    self.last_tick_time = now
                
            # Render frame
            self.screen.fill((20, 20, 20))
            self.draw_map()
            if not self.config_overlay_open:
                self.draw_tooltip()
            self.draw_sidebar()
            self.draw_config_overlay()
            pygame.display.flip()
            
            clock.tick(30)
            
        pygame.quit()
