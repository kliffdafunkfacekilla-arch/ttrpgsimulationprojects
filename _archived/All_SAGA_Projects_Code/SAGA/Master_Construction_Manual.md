# SAGA - Master Construction Manual

This document details the architectural structure and integration logic for the unified **SAGA Application**, combining the visual Qt/PyGame interface with the STT/TTS Voice Engine and AI Director.

## Core Folders & Sub-systems

### `/ai_dm/`
Contains the AI Director integration that connects the local logic to the LLM (via Unsloth and Llama.cpp).
- **`director.py`**: The `AIDirector` class. Parses user intents, generates environmental prompts using world context, and interfaces with `llama_cpp` for ultra-fast local inference.

### `/audio/`
Handles all auditory input and output for the CLI Voice loop.
- **`stt_handler.py`**: Speech-to-Text engine using `speech_recognition` and the system microphone.
- **`tts_handler.py`**: Text-to-Speech engine using `pyttsx3` for real-time AI narration.

### `/frontend/`
Contains the graphical Qt-based UI logic.
- **`main_menu.py`**: The boot Launcher and Character Creator. Writes user preferences to `campaign_settings.json` and the `CharacterSheet` to `player_save.json`.
- **`app.py`**: The main `SceneViewer` visual interface. Contains a polling loop that reads `scene_state.json` to dynamically render backgrounds, character stats, and subtitles.
- **`asset_mapper.py`**: Resolves `scene_state.json` tags to specific image files located in `/assets/`.

### `/rules_engine/`
Houses the mechanical RPG framework (The Brutal Chassis).
- **`chassis_data.py`**: Contains the skill track definitions (Offense, Defense, Power) and character creation validation rules (1/1/2 track limits).
- **`character_sheet.py`**: The overarching Player entity class that calculates derived stats based on selected chassis options.
- **`inventory.py`**: Logic for equipping items and calculating modifiers.
- **`anomaly_parser.py`**: Utilities for parsing AI intent strings for mechanical triggers.

### `/story_manager/`
Connects the local application state to the world databases.
- **`world_db.py`**: Handles a dual SQLite connection:
  - Local: `world_state.db` (Campaign progress, Reactive Seeds).
  - Omnis: `ttrpg_world.db` (The massive 250,000 Cell world map, Factions, Biomes).
- **`campaign_weaver.py`**: Logic for driving the macro-narrative and story acts.
- **`reactive_seeds.py`**: Tracks unresolved player actions and escalates them into threats over time.

### `/assets/` & `/processed_sprites/` & `/models/`
Static resource directories.
- `assets/`: Contains audio, background images, and icon sprites for rendering.
- `models/`: The home for local `.gguf` weights (e.g., `phi-3-mini-4k-instruct-q4.gguf`).

## Root Application Files

- **`main_controller.py`**: The application orchestrator. 
  1. Bootstraps the PyQt application.
  2. Spawns the `SagaLauncher` (`main_menu.py`).
  3. When "Start Game" is pressed, it kicks the `VoiceEngine` loop into a background thread and replaces the active window with the visual `SceneViewer` (`app.py`).
- **`voice_engine.py`**: The main game loop running in the background. It listens to the mic, parses commands via `AIDirector`, updates character stats, and serializes the visual outcome to `scene_state.json`.
- **`start_saga.bat`**: The one-click executable that invokes `main_controller.py`.
- **`scene_state.json`**: The IPC (Inter-Process Communication) file that links the background `voice_engine.py` logic to the foreground `app.py` GUI.
- **`campaign_settings.json` & `player_save.json`**: Created by the launcher and ingested by the voice engine to define starting variables.
