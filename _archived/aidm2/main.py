import pygame
import sys
from engine import GameEngine, STATE_MENU, STATE_STORY_BEAT, STATE_INTERACTION, BEAT_HOOK, BEAT_STRIVE, BEAT_CLIMAX
from ui import UIManager
from grid import GridRenderer

# Configuration
WIDTH, HEIGHT = 800, 600
FPS = 60
COLOR_BG = (20, 20, 25)

class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Recursive Narrative Engine")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 22)
        
        self.engine = GameEngine()
        self.ui = UIManager(self.screen, self.font)
        self.grid = GridRenderer(self.screen)
        
        self.running = True

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if self.engine.state == STATE_MENU:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_menu_click(event.pos)
            elif self.engine.state == STATE_STORY_BEAT:
                if self.engine.current_beat == BEAT_STRIVE:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_1:
                            self.engine.make_choice(0)
                        elif event.key == pygame.K_2:
                            self.engine.make_choice(1)
                else:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            if self.engine.current_beat == BEAT_HOOK:
                                self.engine.advance_beat()
                            elif self.engine.current_beat == BEAT_CLIMAX:
                                self.engine.transition_to_interaction()

    def handle_menu_click(self, pos):
        col_width = WIDTH // 3
        tag_lists = [
            ["Nobility", "Street_Urchin", "Outlander", "Scholar"],
            ["Revenge", "Debt", "Curiosity", "Survival"],
            ["Martial", "Arcane", "Subterfuge", "Diplomatic"]
        ]
        categories = ["Origin", "Motivation", "Specialization"]
        
        for col, cat in enumerate(categories):
            for i, tag in enumerate(tag_lists[col]):
                rect = pygame.Rect(col_width * col + 20, 100 + i * 50, 200, 40)
                if rect.collidepoint(pos):
                    self.engine.set_character_tag(cat, tag)

    def update(self):
        self.engine.update()

    def draw(self):
        self.screen.fill(COLOR_BG)
        
        if self.engine.state == STATE_MENU:
            self.ui.draw_menu(self.engine)
        elif self.engine.state == STATE_STORY_BEAT:
            self.ui.draw_story_beat(self.engine)
        elif self.engine.state == STATE_INTERACTION:
            self.grid.draw(self.engine.manifest)
            
        pygame.display.flip()

if __name__ == "__main__":
    app = App()
    app.run()
