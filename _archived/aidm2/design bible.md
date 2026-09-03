

# Design Bible: The Recursive Narrative Engine

## I. Core Architecture: The "Great Split"
To manage complexity, the app is divided into two independent logic loops that communicate via a data handoff.

### 1. The Story Engine (The Macro)
* **Role:** Campaign management, plot-weaving, and long-term memory.
* **Method:** Uses **"Mad Libs" Templates** and **Context Tags**.
* **Output:** Generates a 3-beat scene "Manifest" for the Interaction Engine.

### 2. The Interaction Engine (The Micro)
* **Role:** Tactical room resolution and physics.
* **Method:** **Tag Collision.** It doesn't know the "Plot"; it only knows the "Entities" in the room and how their tags react to player actions.
* **Output:** Returns a "Resolution Bundle" of tags back to the Story Engine.

---

## II. The Interaction Logic (Pygame Implementation)
In Pygame, your "Room" is an object containing a list of `Entity` objects.

### 1. Entity & Tag System
Every object in a room (Guards, Torches, Crates) is an `Entity` with a `tags` list.
* **Example Entity:** `Torch` 
    * `tags = ["light_source", "fire", "fragile", "static"]`
    * `state = {"active": True}`

### 2. Tag Collision Matrix
When a player inputs an action (e.g., *"I throw water on the torch"*), the engine checks the **Action Tags** against the **Entity Tags**.
* **Logic:** `[Liquid]` vs `[Fire]` $\rightarrow$ `State: active = False`.
* **Consequence:** The room's global `environment_tags` updates from `["lit"]` to `["dark"]`.

### 3. NPC Behavior (The "If-This-Then-That" AI)
NPCs react to tag changes in the room:
* **Trigger:** `Room.tags` contains `"dark"`.
* **Action:** If NPC has `"sight_dependent"`, set state to `"searching"` and move toward the last known `"light_source"`.

---

## III. The Story Logic (The Narrative Loop)

### 1. The 3-Beat Scene Generation
The engine uses **Backstory Tags** + **Current Setting** to build a sequence:
* **Beat 1 (The Hook):** Introduces a Faction or Seed.
* **Beat 2 (The Complication):** Adds a barrier (Lock/Hazard).
* **Beat 3 (The Climax/Goal):** The resolution that creates the next Seed.

### 2. The "Event Stack" (The Striving Phase)
As players travel between beats, their actions generate **Story Points**:
* **Player Input:** *"We scout the perimeter."* (Success)
* **Result:** A `[Short_Cut]` or `[Ambush_Intel]` tag is added to the hidden stack.
* **The Reveal:** When the "Dungeon" starts, these tags are pulled to generate specific room features.

---

## IV. The World Journal & Memory
The app maintains two data files to ensure continuity.

* **The Chronicle (JSON/Text):** A human-readable log of the "Mad Libs" results for the player to read.
* **The Fact Database (Dictionary/SQLite):** A persistent list of tags that never expire (e.g., `[Killed_The_Duke]`) or have a countdown (e.g., `[Injured_Leg: 3_rooms]`).

---

## V. Technical Roadmap (Pygame Strategy)

### Phase 1: The Tag Parser
* Create a simple console-in/console-out system where you can type an action, toggle "Success/Fail," and see how the room tags change.

### Phase 2: The Grid Renderer
* Build a basic `5x5` or `10x10` grid.
* Represent Entities as colored squares (e.g., Red = Guard, Yellow = Torch).
* Implement **Fog of War**: Only show squares adjacent to the player.

### Phase 3: The Narrative Wrapper
* Connect the Story Engine. Before the grid loads, display the "Mad Libs" text beat. 
* After the grid is cleared (Goal Tag reached), update the World Journal.

---

## VI. Summary of Play Flow
1.  **Seed:** App generates narrative text based on Backstory + Setting.
2.  **Strive:** Player dictates actions to reach the goal; App banks "Story Point" tags.
3.  **Dungeon:** Pygame renders a 2D grid. The "Event Stack" populates the rooms with tagged Entities.
4.  **Interact:** Player dictates tactical moves + Success/Fail. App updates Room Tags and NPC behaviors.
5.  **Resolve:** Climax is met. Story Engine "harvests" the tags to seed the next 3-beat scene.

**Pro-Tip for Pygame:** Use a `State Machine` to swap between `NARRATIVE_MODE` (text-heavy story beats) and `TACTICAL_MODE` (the 2D grid interaction). 

VII. Backstory & Character Initialization
Instead of open-ended text, characters are defined by 3 Primary Tags. These tags act as "Global Modifiers" for the Story and Interaction engines.

1. The Starting Tag Categories
Origin (Where you're from): [Nobility], [Street_Urchin], [Outlander], [Scholar]

Motivation (Why you're here): [Revenge], [Debt], [Curiosity], [Survival]

Specialization (What you do): [Martial], [Arcane], [Subterfuge], [Diplomatic]

2. How these influence the Logic
Story Engine: If a player has the [Debt] tag, the "Mad Libs" generator will prioritize [Hostile] and [Bounty_Hunter] events in the Story Stack.

Interaction Engine: If a player has the [Arcane] tag, certain entities (like [Ancient_Runes]) will trigger a "Knowledge" prompt that a [Martial] character wouldn't see.

VIII. Pygame Implementation: The State Machine
To keep your code clean, I recommend structuring your main loop using a State Pattern. This prevents your story logic from bleeding into your grid-rendering code.

Python
import pygame

# State Constants
STATE_MENU = 0        # Character Creation (Tag Selection)
STATE_STORY_BEAT = 1  # The "Mad Libs" Narrative Screen
STATE_INTERACTION = 2 # The 2D Grid / Tactical Interaction
STATE_JOURNAL = 3     # Reviewing the Chronicle

class GameEngine:
    def __init__(self):
        self.state = STATE_MENU
        self.world_tags = [] # Persistent memory
        self.current_room = None
        
    def update(self):
        if self.state == STATE_STORY_BEAT:
            # Run Narrative Logic: Build the Manifest
            pass
        elif self.state == STATE_INTERACTION:
            # Run Tag Collision Logic: Update Entities
            pass

    def draw(self, screen):
        if self.state == STATE_STORY_BEAT:
            self.render_text_interface(screen)
        elif self.state == STATE_INTERACTION:
            self.render_grid(screen)
IX. Data Structure: The "Interaction Manifest"
When the state changes from STORY_BEAT to INTERACTION, pass a dictionary that defines the room. This makes your Pygame code very "data-driven."

Python
# Example Handoff Dictionary
manifest = {
    "biome": "Forest",
    "faction": "Bandits",
    "entities": [
        {"name": "Guard", "pos": (2, 3), "tags": ["sentient", "hostile"]},
        {"name": "Crate", "pos": (1, 1), "tags": ["cover", "flammable"]},
        {"name": "Exit",  "pos": (4, 4), "tags": ["goal"]}
    ],
    "room_modifier": "Darkness"
}
X. Development Strategy (Phase 1)
Since you're using a list for backstories, your first coding milestone should be:

The Tag Picker: A simple Pygame screen with clickable buttons for the 3 categories.

The "Mad Lib" Generator: A function that takes those 3 tags and prints a 1-sentence "Hook" to the screen.

The Grid Spawn: A function that spawns a Red Square (Guard) and a Green Square (Player) based on the "Hook."