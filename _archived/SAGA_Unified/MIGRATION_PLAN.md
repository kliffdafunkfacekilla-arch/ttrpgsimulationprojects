# SAGA Unified Migration Plan

## Phase 1: Core Beta Build Foundation (High Priority)

### 1.1 Core Engine Components
- [ ] `beta_build_backup/core/models.py` → `core/models/character_sheet.py`
- [ ] `beta_build_backup/core/skills_data.py` → `core/models/skills_data.py`
- [ ] `beta_build_backup/core/command_parser.py` → `core/mechanics/command_parser.py`
- [ ] `beta_build_backup/core/turn_manager.py` → `core/mechanics/turn_manager.py`
- [ ] `beta_build_backup/core/zone_manager.py` → `core/combat/zone_manager.py`
- [ ] `beta_build_backup/core/combat_manager.py` → `core/combat/combat_manager.py`
- [ ] `beta_build_backup/core/action_resolver.py` → `core/combat/action_resolver.py`
- [ ] `beta_build_backup/core/world_gen.py` → `core/world_gen/world_gen.py`
- [ ] `beta_build_backup/core/world_gen_worker.py` → `core/world_gen/world_gen_worker.py`
- [ ] `beta_build_backup/core/save_manager.py` → `data/sqlite/save_manager.py`

### 1.2 UI Components
- [ ] `beta_build_backup/ui/event_bus.py` → `ui/components/event_bus.py`
- [ ] `beta_build_backup/ui/async_app.py` → `main.py` (entry point)
- [ ] `beta_build_backup/ui/main_window.py` → `ui/screens/main_window.py`
- [ ] `beta_build_backup/ui/screens.py` → `ui/screens/game_screens.py`
- [ ] `beta_build_backup/ui/map_view.py` → `ui/views/map_view.py`
- [ ] `beta_build_backup/ui/char_creation.py` → `ui/screens/char_creation.py`

### 1.3 AI Services
- [ ] `beta_build_backup/ai_services/director.py` → `ai/director/llm_director.py`
- [ ] `beta_build_backup/ai_services/llm_worker.py` → `ai/director/llm_worker.py`

### 1.4 Audio Services
- [ ] `beta_build_backup/audio/audio_manager.py` → `audio/audio_manager.py`

### 1.5 Data Layer
- [ ] `beta_build_backup/data/memory_store.py` → `data/chromadb/memory_store.py`
- [ ] `beta_build_backup/data/campaigns/core_campaign.json` → `data/sqlite/campaigns/core_campaign.json`

## Phase 2: SAGA_Voice Enhancements (Medium Priority)

### 2.1 Audio Improvements
- [ ] `SAGA_Voice/audio/tts_handler.py` → `audio/tts/edge_tts_handler.py` (NEW - enhanced TTS)
- [ ] `SAGA_Voice/audio/stt_handler.py` → `audio/stt/stt_handler.py` (enhanced STT)

### 2.2 Character System
- [ ] `SAGA_Voice/rules_engine/character_sheet.py` → `core/models/character_sheet_enhanced.py` (merge with existing)
- [ ] `SAGA_Voice/rules_engine/inventory.py` → `core/models/inventory.py` (NEW - better inventory)
- [ ] `SAGA_Voice/rules_engine/clash_calculator.py` → `core/combat/clash_calculator.py` (NEW - RPS combat)
- [ ] `SAGA_Voice/rules_engine/anomaly_parser.py` → `core/mechanics/anomaly_parser.py` (NEW - magic system)

### 2.3 UI Enhancements
- [ ] `SAGA_Voice/frontend/char_creation.py` → Merge into `ui/screens/char_creation.py` (better wizard)
- [ ] `SAGA_Voice/frontend/asset_mapper.py` → `ui/components/asset_mapper.py` (NEW)
- [ ] `SAGA_Voice/frontend/app.py` → `ui/views/scene_viewer.py` (NEW - tag-driven UI)

### 2.4 Voice Commands
- [ ] `SAGA_Voice/voice_engine.py` → Extract command processing logic into `core/mechanics/voice_commands.py`

## Phase 3: SAGA_Combined Integration (Medium Priority)

### 3.1 Quest System
- [ ] `SAGA_Combined/story_manager/quest_weaver.py` → `quest/journal/quest_weaver.py` (NEW)
- [ ] `SAGA_Combined/rules_engine/effects.py` → `core/combat/effects.py` (NEW - effects engine)

### 3.2 World Integration
- [ ] `SAGA_Combined/story_manager/world_db.py` → `world/external/world_db.py` (NEW)
- [ ] `SAGA_Combined/story_manager/reactive_seeds.py` → `world/procedural/reactive_seeds.py` (NEW)
- [ ] `SAGA_Combined/story_manager/campaign_weaver.py` → `quest/journal/campaign_weaver.py` (NEW)

### 3.3 Database Tools
- [ ] `SAGA_Combined/story_manager/db_importer.py` → `scripts/db_importer.py` (utility)
- [ ] `SAGA_Combined/migrate_assets.py` → `scripts/asset_migrator.py` (utility)

## Phase 4: Configuration & Utilities (Low Priority)

### 4.1 Configuration
- [ ] `campaign_settings.json` → `config/profiles/default_config.json`
- [ ] Create unified configuration system
- [ ] Add environment-specific configs (dev, prod)

### 4.2 Utilities
- [ ] Create logging utility in `utils/logging/`
- [ ] Create validation utility in `utils/validation/`
- [ ] Create common utility functions

### 4.3 Documentation
- [ ] Update README with new structure
- [ ] Create API documentation
- [ ] Write migration guide
- [ ] Document architecture decisions

## Phase 5: Testing & Integration

### 5.1 Testing
- [ ] Create test structure in `tests/`
- [ ] Write unit tests for core components
- [ ] Write integration tests for event flow
- [ ] Test voice features

### 5.2 Integration
- [ ] Update imports throughout codebase
- [ ] Ensure event bus integration
- [ ] Test async operations
- [ ] Verify database connections

### 5.3 Performance
- [ ] Profile critical paths
- [ ] Optimize database queries
- [ ] Improve async operation handling
- [ ] Test memory usage

## Integration Notes

### Key Architectural Decisions

1. **Event-Driven Foundation**: Keep beta build's EventBus as core communication mechanism
2. **Async Operations**: Maintain qasync + QThread pattern from beta build
3. **Data Validation**: Use Pydantic models from beta build as base
4. **Memory System**: Keep ChromaDB from beta build, integrate quest/effect data

### Component Mapping

| Original | New Location | Notes |
|----------|-------------|-------|
| beta_build/core/models.py | core/models/character_sheet.py | Base + Voice enhancements |
| beta_build/ui/event_bus.py | ui/components/event_bus.py | Core communication |
| SAGA_Voice/audio/tts_handler.py | audio/tts/edge_tts_handler.py | Enhanced TTS |
| SAGA_Combined/quest_weaver.py | quest/journal/quest_weaver.py | New quest system |
| SAGA_Voice/inventory.py | core/models/inventory.py | Better inventory |

### Dependencies to Add

```
edge-tts>=6.1.0
pygame>=2.5.0
llama-cpp-python>=0.2.0
chromadb>=0.4.0
PyQt6>=6.4.0
qasync>=0.23.0
pydantic>=2.0.0
```

### Configuration Changes

1. Unified config file structure
2. Environment variable support
3. Voice settings (TTS voice selection, STT backend)
4. External database paths (Omnis DB)
5. Asset directory configuration

## Rollback Plan

If migration fails:
1. Keep `beta_build_backup` as reference
2. Document what was successfully migrated
3. Create incremental rollback script
4. Preserve working components separately