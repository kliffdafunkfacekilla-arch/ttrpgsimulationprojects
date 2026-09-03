import pygame

# Colors
COLOR_PLAYER = (50, 200, 50)
COLOR_GUARD = (200, 50, 50)
COLOR_GRID = (40, 40, 50)

class GridRenderer:
    def __init__(self, screen, grid_size=40):
        self.screen = screen
        self.grid_size = grid_size
        self.width, self.height = screen.get_size()

    def draw(self, manifest):
        # Draw grid lines
        for x in range(0, self.width, self.grid_size):
            pygame.draw.line(self.screen, COLOR_GRID, (x, 0), (x, self.height))
        for y in range(0, self.height, self.grid_size):
            pygame.draw.line(self.screen, COLOR_GRID, (0, y), (self.width, y))
            
        # Draw entities
        if manifest:
            for entity in manifest["entities"]:
                color = COLOR_PLAYER if "player" in entity["tags"] else COLOR_GUARD
                px, py = entity["pos"]
                rect = pygame.Rect(px * self.grid_size, py * self.grid_size, self.grid_size, self.grid_size)
                pygame.draw.rect(self.screen, color, rect)
