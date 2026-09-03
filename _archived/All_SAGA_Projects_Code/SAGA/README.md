# S.A.G.A. B.R.U.T.A.L. Engine (Bloat-Free Edition)

Welcome to the **S.A.G.A. (Simulation & AI Game Architecture)** engine. This is the official, bloat-free, decoupled architecture version built strictly around the **B.R.U.T.A.L. Biological Chassis** mechanics.

## 1. Quick Start

To run the game, simply double click the `start_saga.bat` file in this directory. 
- The script will automatically check if the local AI service (**Ollama**) is running. 
- If not, it will boot Ollama in the background.
- It will then launch the main PyQt6 desktop application.

## 2. Architectural Overview

Unlike early prototypes, this engine is **fully decoupled** using an Event-Driven Architecture (`SagaMessageBus` inside `main_controller.py`). 

The system is separated into strict domains:
- **`frontend/`**: Contains the PyQt6 user interface (`app.py`, `char_creation.py`). The frontend only draws pixels and emits intents; it does *no* game logic.
- **`rules_engine/`**: The deterministic heart of the system. Handles the math, Character Sheets, Action resolution, and the Functional Effects pipeline.
- **`main_controller.py`**: The nervous system. It receives UI intents, routes them to the `rules_engine` or `ai_director`, and sends the processed results back to the screen.

## 3. The Functional Skills System

The engine no longer parses text descriptions of abilities. It relies on a hard-coded **Functional Physics Engine**.

### Where is the data?
- `rules_engine/skills_data.py`: Contains the master list of all *Passive Hardware*, *Subconscious Magic*, and *Anomalies*. 
- `rules_engine/effects.py`: Contains the actual code logic for what happens when a skill is triggered.

### How do Skills work?
Every skill in the game is defined by a JSON structure consisting of a cost and an array of `effects`.

**Example:**
```python
"T9": {
    "name": "Orbital Drop",
    "type": "ACTIVE",
    "cost": {"stamina": 5, "focus": 5},
    "effects": [
        {"type": "DAMAGE", "base": "might", "tags": ["impact", "brutal", "lethal"]},
        {"type": "APPLY_TAG", "target": "enemy", "tag": "prone"}
    ]
}
```

### Core Verbs (`effects.py`)
To add a new skill to the game, you map it using these verbs:
1. **`DAMAGE`**: Rolls against the target's defense. Incorporates Tags to override math (e.g., `brutal` auto-shatters `brittle` targets). Handles the Trauma Pipeline (Adrenaline Shock and Bleeding Out).
2. **`HEAL`**: Restores HP, Composure, etc.
3. **`APPLY_TAG`**: Adds persistent statuses like `prone`, `exposed`, `rooted`, or `fire` to an entity's `tags` set.
4. **`MOVE`**: Alters physical positioning on a grid/zone system.
5. **`MODIFY_RULE`**: A persistent engine override attached to a character (e.g., `immune_to_crit_fails`).

## 4. Character Initialization

The engine features a strict PyQt6 Wizard for Character Creation (`frontend/char_creation.py`). It algorithmically enforces the B.R.U.T.A.L. manual:
1. **Core Matrices**: Calculates T0-T4 base stats by combining Kingdom and Sub-Type.
2. **Genetic Variation**: Handles Size Shifting modifiers (+1 Finesse/Reflex or +1 Might/Endurance).
3. **Biological Ceiling**: Enforces an absolute stat cap of 8. If a player allocates points over 8, the system automatically redirects the overflow into the next available stat in the Body/Mind category.
4. **Derived Stats**: Calculates final HP, Composure, Stamina, and Focus.

## 5. Adding New Skills

To flesh out the remaining skills in the game, open `rules_engine/skills_data.py`. 
Simply translate the descriptive tier from the manual into the JSON format provided in the file, utilizing the verbs defined in `effects.py`.

The `ClashCalculator` will automatically parse the player's intent string during combat (e.g. "I use Orbital Drop"), find the corresponding skill JSON, deduct the battery cost, and route it to the physics engine.
