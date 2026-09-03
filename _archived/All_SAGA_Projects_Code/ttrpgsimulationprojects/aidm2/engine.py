import pygame
import random

# State Constants
STATE_MENU = 0        # Character Creation (Tag Selection)
STATE_STORY_BEAT = 1  # The "Mad Libs" Narrative Screen
STATE_INTERACTION = 2 # The 2D Grid / Tactical Interaction
STATE_JOURNAL = 3     # Reviewing the Chronicle

# Beat Constants
BEAT_HOOK = 0
BEAT_STRIVE = 1
BEAT_CLIMAX = 2

class GameEngine:
    def __init__(self):
        self.state = STATE_MENU
        self.current_beat = BEAT_HOOK
        
        self.world_tags = []  # Persistent memory
        self.character_tags = {
            "Origin": None,
            "Motivation": None,
            "Specialization": None
        }
        self.event_stack = [] # The "Deck"
        
        self.current_room = None
        self.hook_text = ""
        self.strive_prompt = ""
        self.choices = []
        
        # Room Manifest (Data-driven handoff)
        self.manifest = None

    def set_character_tag(self, category, tag):
        self.character_tags[category] = tag
        if all(self.character_tags.values()):
            self.generate_hook()
            self.state = STATE_STORY_BEAT
            self.current_beat = BEAT_HOOK

    def generate_hook(self):
        origin = self.character_tags["Origin"]
        motivation = self.character_tags["Motivation"]
        specialization = self.character_tags["Specialization"]
        
        hooks = {
            "Debt": f"Coming from {origin}, your {motivation} has led you to a shadowy contract.",
            "Revenge": f"As a {specialization}, your quest for {motivation} brings you to these ruins.",
            "Curiosity": f"Despite your {origin} roots, {motivation} pulls you toward the unknown.",
            "Survival": f"In the path of {specialization}, {motivation} is your only companion."
        }
        self.hook_text = hooks.get(motivation, f"A {specialization} from {origin} seeking {motivation}.")
        
    def advance_beat(self):
        if self.current_beat == BEAT_HOOK:
            self.setup_strive()
            self.current_beat = BEAT_STRIVE
        elif self.current_beat == BEAT_STRIVE:
            # Beat 2 transition is triggered by player choice
            pass
        elif self.current_beat == BEAT_CLIMAX:
            self.generate_manifest()
            self.state = STATE_INTERACTION

    def setup_strive(self):
        # Generate a situational prompt based on tags
        spec = self.character_tags["Specialization"]
        prompts = {
            "Martial": ("A heavy iron gate blocks the path. Guards patrol the walls.", [
                {"text": "Charge the gate", "tags": [("Ambush", 0.7), ("Success", 0.3)]},
                {"text": "Scout for a breach", "tags": [("Short_Cut", 0.6), ("Alerted", 0.4)]}
            ]),
            "Arcane": ("The air hums with unstable energy. A sealed library lies ahead.", [
                {"text": "Siphon the energy", "tags": [("Arcane_Boost", 0.5), ("Entropy", 0.5)]},
                {"text": "Decipher the seal", "tags": [("Intel", 0.8), ("Slow_Progress", 0.2)]}
            ]),
            "Subterfuge": ("A ventilation shaft overhead whispers of secrets. Guards are below.", [
                {"text": "Sneak through vents", "tags": [("Hidden", 0.7), ("Clumsy", 0.3)]},
                {"text": "Pick the lock", "tags": [("Easy_Entry", 0.6), ("Broken_Tool", 0.4)]}
            ]),
            "Diplomatic": ("A group of local scavengers blocks the road, looking hungry.", [
                {"text": "Negotiate passage", "tags": [("Allies", 0.5), ("Hefty_Fee", 0.5)]},
                {"text": "Intimidate them", "tags": [("Fear", 0.6), ("Resentment", 0.4)]}
            ])
        }
        self.strive_prompt, self.choices = prompts.get(spec, ("The road ahead is uncertain.", []))

    def make_choice(self, choice_index):
        choice = self.choices[choice_index]
        # Roll for outcome
        outcome_tags = choice["tags"]
        # For simplicity, pick one tag based on probability
        r = random.random()
        cumulative = 0
        for tag, prob in outcome_tags:
            cumulative += prob
            if r <= cumulative:
                self.event_stack.append(tag)
                break
        
        self.current_beat = BEAT_CLIMAX
        self.hook_text = f"Result of {choice['text']}: Added {self.event_stack[-1]} to the event stack."

    def generate_manifest(self):
        spec = self.character_tags["Specialization"]
        entities = [
            {"name": "Player", "pos": (2, 2), "tags": ["player", spec.lower()]}
        ]
        
        # Add entities/modifiers based on Event Stack
        room_modifier = "None"
        if "Alerted" in self.event_stack:
            entities.append({"name": "Guard", "pos": (4, 4), "tags": ["hostile", "alert"]})
            entities.append({"name": "Guard", "pos": (6, 2), "tags": ["hostile", "alert"]})
        elif "Hidden" in self.event_stack:
            entities.append({"name": "Guard", "pos": (7, 7), "tags": ["hostile", "sleeping"]})
        else:
            entities.append({"name": "Guard", "pos": (5, 5), "tags": ["hostile"]})
            
        if "Darkness" in self.event_stack or "Entropy" in self.event_stack:
            room_modifier = "Low_Visibility"
            
        self.manifest = {
            "biome": "Dungeon",
            "faction": "Unknown",
            "entities": entities,
            "room_modifier": room_modifier
        }

    def update(self):
        pass

    def transition_to_interaction(self):
        if self.current_beat == BEAT_CLIMAX:
            self.generate_manifest()
            self.state = STATE_INTERACTION
