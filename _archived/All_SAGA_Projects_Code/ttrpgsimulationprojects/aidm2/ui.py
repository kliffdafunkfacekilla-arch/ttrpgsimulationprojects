import pygame

# Colors
COLOR_TEXT = (220, 220, 220)
COLOR_TEXT_DIM = (160, 160, 160)
COLOR_BTN = (60, 60, 70)
COLOR_BTN_HOVER = (90, 90, 110)
COLOR_ACCENT = (100, 200, 255)

class UIManager:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.width, self.height = screen.get_size()

    def draw_menu(self, engine):
        title = self.font.render("Character Creation: Select Your Tags", True, COLOR_TEXT)
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 30))
        
        col_width = self.width // 3
        categories = ["Origin", "Motivation", "Specialization"]
        tag_lists = [
            ["Nobility", "Street_Urchin", "Outlander", "Scholar"],
            ["Revenge", "Debt", "Curiosity", "Survival"],
            ["Martial", "Arcane", "Subterfuge", "Diplomatic"]
        ]
        
        for col, cat in enumerate(categories):
            cat_text = self.font.render(cat, True, COLOR_TEXT)
            self.screen.blit(cat_text, (col_width * col + 20, 70))
            
            for i, tag in enumerate(tag_lists[col]):
                selected = engine.character_tags[cat] == tag
                color = COLOR_BTN_HOVER if selected else COLOR_BTN
                rect = pygame.Rect(col_width * col + 20, 100 + i * 50, 200, 40)
                pygame.draw.rect(self.screen, color, rect)
                tag_text = self.font.render(tag, True, COLOR_TEXT)
                self.screen.blit(tag_text, (rect.x + 10, rect.y + 5))

    def draw_story_beat(self, engine):
        # BEAT Constants from engine
        from engine import BEAT_HOOK, BEAT_STRIVE, BEAT_CLIMAX
        
        # Draw Event Stack (The Deck)
        stack_title = self.font.render("Event Stack (Deck):", True, COLOR_TEXT_DIM)
        self.screen.blit(stack_title, (20, self.height - 150))
        for i, tag in enumerate(engine.event_stack):
            tag_surf = self.font.render(f"[{tag}]", True, COLOR_ACCENT)
            self.screen.blit(tag_surf, (20 + i * 120, self.height - 120))
            
        if engine.current_beat == BEAT_HOOK or engine.current_beat == BEAT_CLIMAX:
            text = engine.hook_text
            lines = text.split(". ")
            for i, line in enumerate(lines):
                hook_surf = self.font.render(line, True, COLOR_TEXT)
                self.screen.blit(hook_surf, (self.width // 2 - hook_surf.get_width() // 2, self.height // 2 - 100 + i * 40))
                
            prompt_str = "Press SPACE to advance" if engine.current_beat == BEAT_HOOK else "Press SPACE to enter the room"
            prompt = self.font.render(prompt_str, True, COLOR_ACCENT)
            self.screen.blit(prompt, (self.width // 2 - prompt.get_width() // 2, self.height - 60))
            
        elif engine.current_beat == BEAT_STRIVE:
            # Draw Prompt
            prompt_surf = self.font.render(engine.strive_prompt, True, COLOR_TEXT)
            self.screen.blit(prompt_surf, (self.width // 2 - prompt_surf.get_width() // 2, 100))
            
            # Draw Choices
            for i, choice in enumerate(engine.choices):
                rect = pygame.Rect(self.width // 2 - 200, 250 + i * 80, 400, 60)
                pygame.draw.rect(self.screen, COLOR_BTN, rect)
                choice_text = self.font.render(f"{i+1}. {choice['text']}", True, COLOR_TEXT)
                self.screen.blit(choice_text, (rect.x + 20, rect.y + 15))
