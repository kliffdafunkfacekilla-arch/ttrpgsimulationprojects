import random
import math

class MapGenerator:
    def __init__(self, width=100, height=100):
        self.width = width
        self.height = height
        self.grid = []

    def generate_base_grid(self, land_mass_percent=0.4):
        """Generates a random noise grid, then smooths it using Cellular Automata rules to form continents."""
        # 1. Initial random noise (1 = land, 0 = water)
        self.grid = [[1 if random.random() < land_mass_percent else 0 for _ in range(self.width)] for _ in range(self.height)]
        
        # 2. Smooth (Cellular Automata) 4 passes
        for _ in range(4):
            new_grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
            for y in range(self.height):
                for x in range(self.width):
                    neighbors = self._get_neighbors(x, y)
                    wall_count = sum(neighbors)
                    if wall_count > 4:
                        new_grid[y][x] = 1
                    elif wall_count < 4:
                        new_grid[y][x] = 0
                    else:
                        new_grid[y][x] = self.grid[y][x]
            self.grid = new_grid

        # 3. Assign Biomes based on Latitude (Y) and Elevation (Distance from coast)
        final_map = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                is_land = self.grid[y][x] == 1
                if not is_land:
                    # Determine if Deep Ocean or Coastal
                    if self._count_land_neighbors(x, y, radius=2) > 0:
                        biome = "coastal"
                        color = "#1e3a8a" # Blue
                    else:
                        biome = "deep_ocean"
                        color = "#0f172a" # Dark slate blue
                else:
                    # Calculate Latitude Temp (0 at poles, 1 at equator)
                    equator = self.height / 2
                    latitude_factor = 1 - (abs(y - equator) / equator)
                    
                    # Distance from coast (Elevation mock)
                    inland_dist = self._count_land_neighbors(x, y, radius=3)
                    
                    if inland_dist >= 20: # Mountain
                        biome = "mountain"
                        color = "#94a3b8" # Slate 400
                    elif latitude_factor > 0.7:
                        # Hot
                        if random.random() > 0.5:
                            biome = "desert"
                            color = "#fcd34d" # Amber 300
                        else:
                            biome = "savanna"
                            color = "#fde047" # Yellow 300
                    elif latitude_factor < 0.3:
                        # Cold
                        biome = "tundra"
                        color = "#e2e8f0" # Slate 200
                    else:
                        # Temperate
                        if random.random() > 0.4:
                            biome = "forest"
                            color = "#15803d" # Green 700
                        else:
                            biome = "plains"
                            color = "#84cc16" # Lime 500

                row.append({
                    "x": x,
                    "y": y,
                    "is_land": is_land,
                    "biome": biome,
                    "color": color
                })
            final_map.append(row)
        return final_map

    def _get_neighbors(self, x, y):
        neighbors = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    neighbors.append(self.grid[ny][nx])
                else:
                    neighbors.append(0) # Treat borders as water
        return neighbors

    def _count_land_neighbors(self, x, y, radius=1):
        count = 0
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    count += self.grid[ny][nx]
        return count
