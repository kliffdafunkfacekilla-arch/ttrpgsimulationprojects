# SAGA Unified - AI-Powered TTRPG Engine

A unified, event-driven tabletop RPG engine combining the best features from SAGA Beta, SAGA_Voice, and SAGA_Combined projects.

## Architecture

SAGA Unified implements a sophisticated event-driven architecture with clear separation of concerns:

- **Core Engine**: Deterministic game mechanics, physics, and math
- **AI Services**: Creative narrative generation via local LLM
- **UI Layer**: PyQt6 desktop application with VTT features
- **Audio System**: Enhanced voice I/O with neural TTS
- **Data Layer**: ChromaDB vector memory + SQLite persistence
- **World System**: Procedural generation + external simulation data
- **Quest System**: Structured campaign progression

## Key Features

### From SAGA Beta (Core Foundation)
- Event-driven architecture with EventBus
- 2D VTT map with token rendering
- Tactical combat with turn-based system
- Line of sight calculations
- ChromaDB vector database for long-term memory
- Pydantic models for data validation
- Async operations with qasync + QThread workers

### From SAGA_Voice (Enhancements)
- Neural TTS via edge-tts (Microsoft Azure voices)
- Advanced voice command processing
- Improved character creation wizard
- Asset mapper system
- Enhanced inventory and equipment system
- RPS clash calculator for tactical combat

### From SAGA_Combined (Integration)
- Quest system with journal management
- Effects engine with tag interactions
- External world simulation integration
- Database import utilities
- Asset migration patterns

## Project Structure

```
SAGA_Unified/
├── core/                    # Game mechanics and physics
│   ├── models/             # Pydantic data models
│   ├── mechanics/          # Command parsing, turn management
│   ├── combat/             # Combat resolution, clash calculator
│   └── world_gen/          # Procedural world generation
├── ui/                      # PyQt6 desktop application
│   ├── components/         # Reusable UI components
│   ├── screens/            # Game screens (char creation, etc.)
│   └── views/              # Map view, HUD, scene viewer
├── ai/                      # AI services
│   ├── director/           # LLM narrative generation
│   └── memory/              # ChromaDB memory management
├── audio/                   # Voice I/O
│   ├── tts/                # Text-to-speech (edge-tts)
│   └── stt/                # Speech-to-text
├── data/                    # Data persistence
│   ├── chromadb/           # Vector database storage
│   └── sqlite/             # SQLite databases
├── world/                   # World management
│   ├── external/           # External simulation integration
│   └── procedural/         # Procedural generation algorithms
├── quest/                   # Quest system
│   ├── journal/            # Quest journal and tracking
│   └── templates/         # Quest generation templates
├── assets/                  # Visual assets
│   ├── biomes/             # Background and terrain assets
│   ├── entities/           # Character and creature sprites
│   ├── props/              # Interactive objects
│   └── ui/                 # UI elements and icons
├── config/                  # Configuration files
│   └── profiles/           # User settings and profiles
├── utils/                   # Utility modules
│   ├── logging/            # Logging configuration
│   └── validation/        # Data validation utilities
├── tests/                   # Test suite
├── docs/                    # Documentation
└── scripts/                 # Utility scripts
```

## Installation

### Prerequisites
- Python 3.13+
- PyQt6
- llama-cpp-python
- ChromaDB
- edge-tts
- pygame

### Setup

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure settings in `config/default_config.json`

4. Run the application:
```powershell
python main.py
```

## Usage

### Starting a New Game
1. Launch the application
2. Create a character using the improved wizard
3. Select campaign settings and starting plot
4. Begin voice-driven or mouse-driven gameplay

### Voice Features
- Use natural language commands: "I attack the goblin with my sword"
- Ask questions: "What do I have?", "Where am I?"
- Cast spells: "Cast a fireball at the enemy"

### VTT Features
- 2D tactical map with token movement
- Line of sight calculations
- Turn-based combat with action economy
- Real-time stat tracking

## Development

### Architecture Principles
- **Event-Driven**: All communication via EventBus
- **Forge vs Game Master**: Core = mechanics, AI = narrative
- **Async-First**: Heavy operations in QThread workers
- **Local-First**: 100% local execution, no cloud dependencies

### Adding New Features
1. Core mechanics → `core/`
2. UI components → `ui/`
3. AI improvements → `ai/`
4. Quest content → `quest/`

## License

[Your License Here]

## Credits

Built from the SAGA project family:
- SAGA Beta (Advanced event-driven architecture)
- SAGA_Voice (Voice-first enhancements)
- SAGA_Combined (External data integration)