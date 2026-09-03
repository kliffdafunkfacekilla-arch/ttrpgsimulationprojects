# Import Update Guide

This document outlines the import changes needed for migrated files to work with the new SAGA Unified structure.

## Common Import Patterns

### Old Imports (Beta Build)
```python
from beta_build.ui.event_bus import EventBus
from beta_build.core.models import CharacterSheet
from beta_build.ai_services.director import AIDirector
```

### New Imports (SAGA Unified)
```python
from ui.components.event_bus import EventBus
from core.models.character_sheet import CharacterSheet
from ai.director.llm_director import AIDirector
```

## Files Requiring Import Updates

### Core Components
- `ui/screens/main_window.py` - Update imports for event_bus, core components
- `ui/screens/game_screens.py` - Update imports for UI components
- `ui/views/map_view.py` - Update imports for components
- `ai/director/llm_director.py` - Update imports for models
- `ai/director/llm_worker.py` - Update imports for models
- `core/mechanics/command_parser.py` - Update imports for models
- `core/combat/action_resolver.py` - Update imports for models
- `core/world_gen/world_gen.py` - Update imports for models

### Audio Components
- `audio/audio_manager.py` - Update imports for QThread workers

### Data Components
- `data/chromadb/memory_store.py` - Update imports for models

## Update Patterns

### Pattern 1: Beta Build Imports
Replace:
```python
from beta_build.ui.event_bus import EventBus
from beta_build.core.models import CharacterSheet, Inventory, Item
from beta_build.ai_services.director import AIDirector
from beta_build.ai_services.llm_worker import preload_shared_llama
```

With:
```python
from ui.components.event_bus import EventBus
from core.models.character_sheet import CharacterSheet, Inventory, Item
from ai.director.llm_director import AIDirector
from ai.director.llm_worker import preload_shared_llama
```

### Pattern 2: SAGA_Voice Imports
Replace:
```python
from frontend.asset_mapper import AssetMapper
from rules_engine.character_sheet import CharacterSheet
from audio.tts_handler import TTSHandler
```

With:
```python
from ui.components.asset_mapper import AssetMapper
from core.models.character_sheet import CharacterSheet
from audio.tts.edge_tts_handler import TTSHandler
```

### Pattern 3: SAGA_Combined Imports
Replace:
```python
from story_manager.quest_weaver import QuestWeaver
from story_manager.world_db import WorldDB
from rules_engine.effects import execute_effects
```

With:
```python
from quest.journal.quest_weaver import QuestWeaver
from world.external.world_db import WorldDB
from core.combat.effects import execute_effects
```

## Utility Imports

For logging and validation:
```python
from utils.logging.logger import get_logger
from utils.validation.validators import validate_character_name
from utils.config import config_manager
```

## Automated Update Script

A helper script can be created to automatically update imports:

```python
import os
import re
from pathlib import Path

def update_imports(file_path: Path):
    """Update imports in a Python file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Import replacements
    replacements = {
        'from beta_build.ui.event_bus': 'from ui.components.event_bus',
        'from beta_build.core.models': 'from core.models.character_sheet',
        'from beta_build.ai_services.director': 'from ai.director.llm_director',
        'from beta_build.ai_services.llm_worker': 'from ai.director.llm_worker',
        'from beta_build.audio.audio_manager': 'from audio.audio_manager',
        'from beta_build.data.memory_store': 'from data.chromadb.memory_store',
        'from frontend.asset_mapper': 'from ui.components.asset_mapper',
        'from rules_engine.character_sheet': 'from core.models.character_sheet',
        'from rules_engine.inventory': 'from core.models.inventory',
        'from rules_engine.clash_calculator': 'from core.combat.clash_calculator',
        'from rules_engine.anomaly_parser': 'from core.mechanics.anomaly_parser',
        'from rules_engine.effects': 'from core.combat.effects',
        'from story_manager.quest_weaver': 'from quest.journal.quest_weaver',
        'from story_manager.world_db': 'from world.external.world_db',
        'from story_manager.reactive_seeds': 'from world.procedural.reactive_seeds',
        'from story_manager.campaign_weaver': 'from quest.journal.campaign_weaver',
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

# Apply to all Python files in the project
for py_file in Path('.').rglob('*.py'):
    update_imports(py_file)
```

## Testing After Updates

After updating imports, test each component:

1. **Event Bus**: Test event publishing/subscribing
2. **Models**: Test Pydantic model validation
3. **AI Director**: Test LLM integration
4. **Audio**: Test TTS/STT handlers
5. **UI**: Test screen navigation
6. **Data**: Test database connections

## Common Issues

### Issue: ModuleNotFoundError
**Solution**: Check that the import path matches the new directory structure

### Issue: Circular Imports
**Solution**: Restructure code to avoid circular dependencies, use lazy imports

### Issue: Missing Dependencies
**Solution**: Ensure all required packages are in requirements.txt

## Verification

After updates, verify:
```bash
# Check for import errors
python -m py_compile main.py

# Run basic imports test
python -c "from ui.components.event_bus import EventBus; print('OK')"
```