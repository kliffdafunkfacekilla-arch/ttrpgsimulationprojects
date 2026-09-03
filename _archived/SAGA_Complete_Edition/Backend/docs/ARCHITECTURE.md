# SAGA Unified Architecture

## Overview

SAGA Unified represents the convergence of three SAGA project iterations into a single, event-driven architecture that combines the best features from each:

- **SAGA Beta**: Advanced event-driven architecture with VTT features
- **SAGA_Voice**: Voice-first enhancements with neural TTS
- **SAGA_Combined**: External data integration and quest systems

## Core Principles

### 1. Event-Driven Architecture
All communication between components flows through the central EventBus, enabling complete decoupling of subsystems. This allows for:

- Easy testing and mocking of components
- Flexible component replacement
- Clear data flow traceability
- Non-blocking async operations

### 2. Forge vs Game Master Pattern
- **Forge (Python Engine)**: Handles all deterministic mechanics - physics, math, combat resolution, stat calculations. Never invents narrative.
- **Game Master (AI Director)**: Handles all creative narrative generation. Never calculates mechanics.

This separation prevents AI hallucinations while maintaining rich storytelling.

### 3. Async-First Design
Heavy operations (LLM inference, TTS/STT, world generation) run in QThread workers to maintain UI responsiveness. The qasync library bridges asyncio with PyQt6's event loop.

### 4. Local-First Execution
100% local execution with no cloud dependencies:
- Local LLM via llama-cpp-python
- Local vector database via ChromaDB
- Local SQLite for persistence
- Optional external world simulation integration

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Main Entry Point                        │
│                           main.py                               │
│                    (async + qasync bootstrap)                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      EventBus (Central Nervous System)          │
│                   ui/components/event_bus.py                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│     UI       │  │    Core      │  │     AI       │
│   Layer      │  │   Engine     │  │  Services    │
│              │  │              │  │              │
│ • Screens    │  │ • Models     │  │ • Director   │
│ • Views      │  │ • Mechanics  │  │ • Memory     │
│ • Components │  │ • Combat     │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  ChromaDB    │  │   SQLite     │  │   Config     │        │
│  │  (Vector DB) │  │  (Persist)   │  │  (Settings)  │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

## Module Responsibilities

### Core Engine (`core/`)
**Purpose**: Deterministic game mechanics and physics

- `models/`: Pydantic data models (CharacterSheet, Inventory, Items)
- `mechanics/`: Command parsing, turn management, action economy
- `combat/`: Combat resolution, clash calculator, effects system
- `world_gen/`: Procedural world generation, terrain tiles

**Key Principle**: Never invents narrative. Only calculates mechanics.

### UI Layer (`ui/`)
**Purpose**: User interface and visualization

- `components/`: Reusable UI components (EventBus, AssetMapper)
- `screens/`: Game screens (MainMenu, CharCreation, GameScreen)
- `views/`: Visual views (MapView, SceneViewer, HUD)

**Key Principle**: Subscribes to events, renders state, never modifies game logic.

### AI Services (`ai/`)
**Purpose**: Creative narrative generation

- `director/`: LLM narrative generation (AIDirector, LLMWorker)
- `memory/`: ChromaDB memory management (MemoryStore)

**Key Principle**: Never calculates mechanics. Only translates mechanical results into narrative.

### Audio (`audio/`)
**Purpose**: Voice input/output

- `tts/`: Text-to-speech using edge-tts (neural voices)
- `stt/`: Speech-to-text using speech_recognition

**Key Principle**: Non-blocking async operations via QThread workers.

### Data (`data/`)
**Purpose**: Data persistence and memory

- `chromadb/`: Vector database for long-term memory and RAG
- `sqlite/`: SQLite databases for structured data

### World (`world/`)
**Purpose**: World state and generation

- `external/`: External world simulation integration (Omnis DB)
- `procedural/`: Procedural generation algorithms

### Quest (`quest/`)
**Purpose**: Quest and campaign management

- `journal/`: Quest journal and tracking (QuestJournal, QuestWeaver)
- `templates/`: Quest generation templates

## Data Flow Example

### User Action: "I attack the goblin with my sword"

1. **UI Layer** captures input → publishes `USER_COMMAND` event
2. **Core Engine** (`command_parser`) subscribes → parses intent → publishes `ACTION_PARSED` event
3. **Core Engine** (`turn_manager`) validates action economy → publishes `ACTION_VALIDATED` event
4. **Core Engine** (`action_resolver`) calculates combat math → publishes `COMBAT_RESULT` event
5. **AI Services** (`director`) subscribes → generates narrative → publishes `NARRATIVE_READY` event
6. **Audio** (`tts`) subscribes → converts to speech → publishes `AUDIO_READY` event
7. **UI Layer** updates map and displays narration

## Event Types

### Core Events
- `USER_COMMAND`: Player input (text or voice)
- `ACTION_PARSED`: Parsed command intent
- `ACTION_VALIDATED`: Action economy validation result
- `COMBAT_RESULT`: Mechanical combat resolution
- `STATE_CHANGED`: General game state change

### AI Events
- `NARRATIVE_REQUEST`: Request for narrative generation
- `NARRATIVE_READY`: Generated narrative text
- `MEMORY_STORE`: Store event in ChromaDB
- `MEMORY_RECALL`: Retrieve context from ChromaDB

### UI Events
- `SCREEN_CHANGE`: Navigate between screens
- `MAP_UPDATE`: Update VTT map
- `HUD_UPDATE`: Update HUD elements
- `ASSET_LOADED`: Asset loading complete

### Audio Events
- `TTS_REQUEST`: Request text-to-speech
- `TTS_COMPLETE`: TTS playback complete
- `STT_RESULT`: Speech-to-text result

## Configuration

Configuration is managed via JSON files in `config/profiles/`:

- `default_config.json`: Default settings
- `dev_config.json`: Development overrides
- `prod_config.json`: Production settings

Key configuration sections:
- `audio`: TTS/STT engine settings
- `ai`: LLM model and prompt settings
- `data`: Database paths and settings
- `world`: External integration settings
- `game`: Gameplay settings (difficulty, filters)

## Migration Strategy

The unified architecture maintains compatibility with the original beta build while incorporating enhancements:

1. **Preserve EventBus**: Keep as central communication mechanism
2. **Maintain Async Pattern**: Continue using qasync + QThread workers
3. **Enhance Models**: Add SAGA_Voice improvements to existing Pydantic models
4. **Add Quest System**: Integrate SAGA_Combined quest system via events
5. **Upgrade Audio**: Replace pyttsx3 with edge-tts while maintaining QThread pattern

## Testing Strategy

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test event flow between components
3. **UI Tests**: Test screen navigation and user interactions
4. **Performance Tests**: Profile critical paths and async operations

## Future Enhancements

Potential areas for expansion:
- Multiplayer support via network events
- Plugin system for custom rules modules
- Advanced world simulation integration
- Mobile UI adaptation
- Cloud save synchronization (optional)