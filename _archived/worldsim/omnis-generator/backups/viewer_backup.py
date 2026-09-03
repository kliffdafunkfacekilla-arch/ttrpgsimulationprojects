# ui/viewer.py
import pygame
import os
from shapely.wkt import loads
from database import get_db_connection

class MapViewer:
    def __init__(self, screen_width=1280, screen_height=720):
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("TTRPG World Builder & Simulator")
        
        # Navigation
        self.zoom = 7.0  # Default zoom factor
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # Simulation model connection
        self.model = None
        self.autoplay = False
        
        # Visual Layers: 'biomes', 'elevation', 'factions', 'food', 'chaos'
        self.active_layer = 'biomes'
        
        # Data caches
        self.cells = []
        self.edges = []
        self.factions = {}  # cell_id -> faction_data
        self.faction_colors = {
            1: (180, 50, 50),    # Red - Ursine Hegemony
            2: (50, 180, 50),    # Green - River Folk
            3: (100, 100, 180),  # Purple/Blue - Sump-Kin
            4: (180, 150, 50),   # Orange/Yellow - Iron Caladrea
            5: (180, 50, 180)    # Pink - Vaneer Concord
        }
        self.logs = []
        
        # Load assets
        self.sprites = {}
        self.textures = {}  # Store original-size cleaned textures for tiling
        self.map_surface = None
        
        self.load_spritesheet()
        self.sync_data()

    def remove_checkerboard(self, surface):
        """Removes the white/grey checkerboard background of a sprite using an optimized BFS flood-fill from edges."""
        w, h = surface.get_size()
        visited = [[False] * h for _ in range(w)]
        queue = []
        
        # Seed BFS from all border pixels
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
            
            # Checkerboard white & grey detection
            is_white = color.r >= 240 and color.g >= 240 and color.b >= 240
            is_grey = (210 <= color.r <= 235 and 
                       210 <= color.g <= 235 and 
                       210 <= color.b <= 235 and 
                       abs(color.r - color.g) <= 5 and 
                       abs(color.g - color.b) <= 5)
                       
            if is_white or is_grey:
                surface.set_at((x, y), (0, 0, 0, 0))
                # Add 4-way neighbors
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
            
            # Irregular y-boundaries detected on the grid
            y_bounds = [0, 127, 255, 383, 511, 639, 768, 891, 1010, 1126, 1253, 1393, 1534]
            tile_w = 176
            cols = 16
            
            # Slice tiles and store them indexed by (row_1indexed, col_1indexed)
            for r in range(12):
                y_start = y_bounds[r]
                y_end = y_bounds[r + 1]
                h = y_end - y_start
                for c in range(cols):
                    x_start = c * tile_w
                    # Slice with a 2-pixel trim on all sides to avoid black grid lines
                    rect = pygame.Rect(x_start + 2, y_start + 2, tile_w - 4, h - 4)
                    sub = sheet.subsurface(rect).copy()
                    
                    # Remove the checkerboard background to make the sprite truly transparent
                    self.remove_checkerboard(sub)
                    
                    # Store original cleaned texture for tiling
                    self.textures[(r + 1, c + 1)] = sub
                    
                    # Scale down to 32x23 to preserve aspect ratio (11:8) and store for overlay stamps
                    scaled = pygame.transform.smoothscale(sub, (32, 23))
                    self.sprites[(r + 1, c + 1)] = scaled
            print(f"Successfully loaded, sliced, and trimmed spritesheet: {len(self.sprites)} sprites cached.")
        except Exception as e:
            print(f"Error loading spritesheet: {e}")

    def sync_data(self):
        """Queries the current cells, edges, factions, and logs from SQLite database."""
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Fetch cells
        cur.execute('SELECT * FROM cells')
        cell_rows = cur.fetchall()
        self.cells = []
        for row in cell_rows:
            try:
                poly = loads(row['geom_wkt'])
                coords = list(poly.exterior.coords)
                centroid_x, centroid_y = poly.centroid.x, poly.centroid.y
                self.cells.append({
                    'id': row['id'],
                    'biome': row['biome'],
                    'elevation': row['elevation'],
                    'depth_elevation': row['depth_elevation'],
                    'food_supply': row['food_supply'],
                    'chaos_saturation': row['chaos_saturation'],
                    'weather': row['weather'],
                    'coords': coords,
                    'center': (centroid_x, centroid_y)
                })
            except Exception as e:
                print(f"Error loading polygon WKT for cell {row['id']}: {e}")
                
        # 2. Fetch edges
        cur.execute('SELECT cell_a, cell_b FROM cell_edges')
        self.edges = [dict(r) for r in cur.fetchall()]
        
        # 3. Fetch macro groups (factions)
        cur.execute('SELECT * FROM macro_groups')
        self.factions = {r['cell_id']: dict(r) for r in cur.fetchall()}
        
        # 4. Fetch logs
        cur.execute('SELECT * FROM simulation_logs ORDER BY id DESC LIMIT 8')
        self.logs = [dict(r) for r in cur.fetchall()]
        
        cur.close()
        conn.close()
        
        # Pre-render the background map with updated cells
        self.render_background_map()

    def draw_textured_polygon(self, surface, coords, scaled_tex, tile_w, tile_h, base_color):
        """Fills a polygon with a solid base color, then tiles a textured image across it."""
        # 1. Fill polygon with base color
        pygame.draw.polygon(surface, base_color, coords)
        
        # 2. Get local bounding box of the coords
        xs = [p[0] for p in coords]
        ys = [p[1] for p in coords]
        min_x, max_x = int(min(xs)), int(max(xs))
        min_y, max_y = int(min(ys)), int(max(ys))
        
        w = max_x - min_x
        h = max_y - min_y
        if w <= 0 or h <= 0:
            return
            
        # 3. Create a temporary surface for the tiled texture
        temp_texture = pygame.Surface((w, h), pygame.SRCALPHA)
        
        # Align the tiling grid with absolute screen space coordinates to ensure seamless tiling
        start_x = - (min_x % tile_w)
        start_y = - (min_y % tile_h)
        
        for x in range(start_x, w, tile_w):
            for y in range(start_y, h, tile_h):
                temp_texture.blit(scaled_tex, (x, y))
                
        # 4. Create mask surface for the polygon shape
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        local_coords = [(p[0] - min_x, p[1] - min_y) for p in coords]
        pygame.draw.polygon(mask, (255, 255, 255, 255), local_coords)
        
        # 5. Mask the tiled texture so it only keeps pixels inside the polygon
        temp_texture.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        
        # 6. Blit the textured cell onto the main map surface
        surface.blit(temp_texture, (min_x, min_y))

    def render_background_map(self):
        """Pre-renders the cell polygons onto a single high-performance map surface."""
        map_size = int(100 * self.zoom)
        if map_size <= 0:
            return
            
        # Create a surface representing the entire map at the current zoom level
        self.map_surface = pygame.Surface((map_size, map_size), pygame.SRCALPHA)
        self.map_surface.fill((30, 30, 30, 0))
        
        def to_surface(val):
            return val * self.zoom
            
        # Pre-scale all textures once for this render pass to optimize performance
        zoom_ratio = self.zoom / 7.0
        tile_w = max(8, min(256, int(48 * zoom_ratio)))
        tile_h = max(8, min(256, int(34 * zoom_ratio)))
        
        scaled_textures = {}
        for key, tex in self.textures.items():
            scaled_textures[key] = pygame.transform.smoothscale(tex, (tile_w, tile_h))
            
        # Draw cells
        for cell in self.cells:
            surface_coords = [(to_surface(x), to_surface(y)) for x, y in cell['coords']]
            if len(surface_coords) < 3:
                continue
                
            color = self.get_cell_color(cell)
            biome = cell['biome']
            elevation = cell['elevation']
            
            # If biomes layer, tile the terrain sprite, else draw flat colors
            if self.active_layer == 'biomes':
                row, col = self.get_biome_sprite_coords(biome, elevation)
                texture = scaled_textures.get((row, col))
                if texture:
                    self.draw_textured_polygon(self.map_surface, surface_coords, texture, tile_w, tile_h, color)
                else:
                    pygame.draw.polygon(self.map_surface, color, surface_coords)
            else:
                pygame.draw.polygon(self.map_surface, color, surface_coords)
                
            # Draw cell borders
            pygame.draw.polygon(self.map_surface, (50, 50, 50), surface_coords, 1)

    def to_screen(self, x, y):
        """Converts map coordinates (0-100) to viewport screen coordinates."""
        # Viewport width is 960 (leaving 320 for sidebar)
        viewport_w = 960
        viewport_h = 720
        screen_x = int((x - 50.0) * self.zoom + (viewport_w / 2) + self.pan_x)
        screen_y = int((y - 50.0) * self.zoom + (viewport_h / 2) + self.pan_y)
        return screen_x, screen_y

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
            # Highlight cells owned by factions
            faction_info = self.factions.get(cell['id'])
            if faction_info:
                fid = faction_info['faction_id']
                return self.faction_colors.get(fid, (150, 150, 150))
            return (220, 220, 220) if cell['elevation'] >= 0 else (40, 60, 90)
            
        elif self.active_layer == 'food':
            # Green gradient based on food_supply
            val = int(cell['food_supply'] * 200)
            return (40, 50 + val, 40)
            
        elif self.active_layer == 'chaos':
            # Purple gradient based on chaos_saturation
            val = int(cell['chaos_saturation'] * 200)
            return (50 + val, 30, 50 + val)
            
        else: # 'biomes' layer (default)
            # Check for high chaos overlay first
            if cell['chaos_saturation'] > 0.8:
                return (139, 0, 0) # Deep red for chaos storm
            biome = cell['biome']
            # Standard colors from updated guide Svelte Map component
            biome_colors = {
                'Forest': (45, 106, 45),
                'Plains': (168, 201, 110),
                'Desert': (212, 168, 67),
                'Mountain': (138, 138, 138),
                'Swamp': (74, 122, 74),
                'Ocean': (26, 95, 138)
            }
            return biome_colors.get(biome, (200, 200, 200))

    def get_biome_sprite_coords(self, biome, elevation):
        """Maps biomes and depth to spritesheet grid rows/columns (1-indexed)."""
        if elevation < 0: # Underwater
            if biome == 'Ocean':
                # Subaquatic mapping based on depth (R4-R6, C9 is open water)
                if elevation < -0.6:
                    return 6, 3 # R6, C3 - Abyssal Chasm
                elif elevation < -0.3:
                    return 5, 9 # R5, C9 - Rippling Open Water
                else:
                    return 4, 9 # R4, C9 - Open Water
            # Default underwater
            return 4, 1
        else: # Land biomes
            # Row 1 has base terrains
            biome_map = {
                'Plains': (1, 1),
                'Forest': (1, 2),
                'Desert': (1, 4),
                'Mountain': (1, 7),
                'Swamp': (1, 8),
            }
            return biome_map.get(biome, (1, 1))

    def draw_map(self):
        """Draws cells, borders, edges, and sprites."""
        # Fill map viewport background
        pygame.draw.rect(self.screen, (30, 30, 30), (0, 0, 960, 720))
        
        # 1. Blit the pre-rendered background map surface
        if hasattr(self, 'map_surface') and self.map_surface:
            viewport_w = 960
            viewport_h = 720
            # Centered around (50, 50) in map coords
            screen_x = int((viewport_w / 2) - 50.0 * self.zoom + self.pan_x)
            screen_y = int((viewport_h / 2) - 50.0 * self.zoom + self.pan_y)
            self.screen.blit(self.map_surface, (screen_x, screen_y))
            
        # 2. Draw Sprite Overlays (Capitals, Units)
        for cell in self.cells:
            cx, cy = cell['center']
            scx, scy = self.to_screen(cx, cy)
            
            # Skip if cell is off-viewport
            if not (0 <= scx < 960 and 0 <= scy < 720):
                continue
                
            sprite = None
            
            # Check for Faction Capital Keep (POI R10, C13 for intact Castle/Keep)
            faction_info = self.factions.get(cell['id'])
            if faction_info and faction_info['cell_id'] == cell['id']:
                # Capital cell - Draw Keep Castle (POI intact keep is Col 13)
                sprite = self.sprites.get((10, 13))
            elif faction_info:
                # Normal faction cell - Draw Faction-specific Unit
                fid = faction_info['faction_id']
                # Factions 1 to 5 map to specific columns in Row 11:
                # 1: Ursine Hegemony -> Badger Guard (Col 1)
                # 2: River Folk -> Fox Ranger (Col 2)
                # 3: Sump-Kin -> Mole Sapper (Col 3)
                # 4: Iron Caladrea -> Rodent Caravan (Col 5)
                # 5: Vaneer Concord -> Seed-pod Airship (Col 7)
                faction_unit_cols = {
                    1: 1,
                    2: 2,
                    3: 3,
                    4: 5,
                    5: 7
                }
                unit_col = faction_unit_cols.get(fid)
                if unit_col:
                    sprite = self.sprites.get((11, unit_col))
                    
            if sprite:
                # Centered blitting (offset by half-width=16, half-height=11 for 32x23 sprite)
                self.screen.blit(sprite, (scx - 16, scy - 11))

            # 3. Draw Weather Overlays (Row 12 Effects)
            if cell['weather'] == 'Chaos Storm':
                # Blit Storm effect (R12, C5 Magic Surge/Fog Effect A)
                effect = self.sprites.get((12, 5))
                if effect:
                    self.screen.blit(effect, (scx - 16, scy - 11))

    def draw_sidebar(self):
        """Draws the control panel and logs."""
        sidebar_x = 960
        # Draw background panel
        pygame.draw.rect(self.screen, (40, 44, 52), (sidebar_x, 0, 320, 720))
        # Draw border line
        pygame.draw.line(self.screen, (80, 80, 80), (sidebar_x, 0), (sidebar_x, 720), 2)
        
        # Load font
        font_large = pygame.font.SysFont("arial", 20, bold=True)
        font_medium = pygame.font.SysFont("arial", 14, bold=True)
        font_small = pygame.font.SysFont("arial", 12)
        
        # Render Title
        title = font_large.render("TTRPG World Conductor", True, (255, 255, 255))
        self.screen.blit(title, (sidebar_x + 20, 20))
        
        # Simulation stats
        tick_val = self.model.current_tick if self.model else 0
        tick_text = font_medium.render(f"Simulation Tick: {tick_val}", True, (170, 220, 255))
        self.screen.blit(tick_text, (sidebar_x + 20, 60))
        
        layer_text = font_medium.render(f"Active Layer: {self.active_layer.upper()}", True, (255, 255, 150))
        self.screen.blit(layer_text, (sidebar_x + 20, 85))
        
        autoplay_status = "PLAYING" if self.autoplay else "PAUSED"
        color = (100, 255, 100) if self.autoplay else (255, 100, 100)
        auto_text = font_medium.render(f"Autoplay: {autoplay_status}", True, color)
        self.screen.blit(auto_text, (sidebar_x + 20, 110))
        
        # Render Action Buttons
        self.buttons = {
            'gen': pygame.Rect(sidebar_x + 20, 150, 280, 35),
            'tick': pygame.Rect(sidebar_x + 20, 195, 280, 35),
            'auto': pygame.Rect(sidebar_x + 20, 240, 280, 35),
            'layer': pygame.Rect(sidebar_x + 20, 285, 280, 35),
            'sync': pygame.Rect(sidebar_x + 20, 330, 280, 35),
        }
        
        btn_labels = {
            'gen': "Generate New World (Seed 42)",
            'tick': "Run 1 Simulation Tick",
            'auto': "Toggle Autoplay Tick Loop",
            'layer': "Switch Visual Layer",
            'sync': "Force Database Sync"
        }
        
        for name, rect in self.buttons.items():
            # Draw rounded button
            pygame.draw.rect(self.screen, (60, 70, 85), rect, border_radius=5)
            # Text inside button
            txt = font_medium.render(btn_labels[name], True, (230, 240, 255))
            txt_rect = txt.get_rect(center=rect.center)
            self.screen.blit(txt, txt_rect)
            
        # Draw Logs Area
        logs_title = font_medium.render("Simulation Event Logs (psql sync):", True, (255, 200, 100))
        self.screen.blit(logs_title, (sidebar_x + 20, 390))
        
        log_y = 420
        for entry in self.logs:
            desc = entry['description']
            tick = entry['tick_number']
            ev_type = entry['event_type']
            
            # Format text
            text_str = f"[{tick}] [{ev_type}] {desc}"
            # Truncate if too long to fit
            if len(text_str) > 42:
                text_str = text_str[:40] + "..."
                
            color_map = {1: (200, 200, 200), 3: (255, 255, 180), 5: (255, 150, 150)}
            log_color = color_map.get(entry.get('severity', 1), (200, 200, 200))
            
            log_lbl = font_small.render(text_str, True, log_color)
            self.screen.blit(log_lbl, (sidebar_x + 20, log_y))
            log_y += 22

    def handle_click(self, pos):
        """Processes button clicks in the sidebar."""
        for name, rect in self.buttons.items():
            if rect.collidepoint(pos):
                if name == 'gen':
                    from map_generator import generate_world
                    generate_world(seed=42, num_cells=1000)
                    if self.model:
                        # Reinitialize model to load new graph
                        from simulation_engine import TTRPGWorldModel
                        self.model = TTRPGWorldModel()
                    self.sync_data()
                    print("Generated and synced fresh world.")
                elif name == 'tick':
                    if self.model:
                        self.model.step()
                        self.sync_data()
                    else:
                        print("Warning: Simulation Model not running. Start main.py with Mesa engine.")
                elif name == 'auto':
                    self.autoplay = not self.autoplay
                    print(f"Autoplay toggled: {self.autoplay}")
                elif name == 'layer':
                    layers = ['biomes', 'elevation', 'factions', 'food', 'chaos']
                    idx = layers.index(self.active_layer)
                    self.active_layer = layers[(idx + 1) % len(layers)]
                    self.sync_data()  # Redraw with fresh colors/values
                    print(f"Visual layer switched to: {self.active_layer}")
                elif name == 'sync':
                    self.sync_data()
                    print("Data synchronized from database.")

    def run(self):
        """Main Pygame Loop."""
        clock = pygame.time.Clock()
        running = True
        
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # Left click
                        if event.pos[0] >= 960: # Sidebar click
                            self.handle_click(event.pos)
                        else: # Drag start
                            self.dragging = True
                            self.drag_start_x, self.drag_start_y = event.pos
                    elif event.button == 4: # Mouse wheel scroll up
                        self.zoom = min(30.0, self.zoom + 0.5)
                        self.render_background_map()
                    elif event.button == 5: # Mouse wheel scroll down
                        self.zoom = max(2.0, self.zoom - 0.5)
                        self.render_background_map()
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.dragging = False
                elif event.type == pygame.MOUSEMOTION:
                    if self.dragging:
                        mx, my = event.pos
                        self.pan_x += mx - self.drag_start_x
                        self.pan_y += my - self.drag_start_y
                        self.drag_start_x, self.drag_start_y = mx, my
            
            # Autoplay ticks
            if self.autoplay and self.model:
                self.model.step()
                self.sync_data()
                
            # Render frame
            self.screen.fill((20, 20, 20))
            self.draw_map()
            self.draw_sidebar()
            pygame.display.flip()
            
            # Cap frame rate
            clock.tick(30)
            
        pygame.quit()
