"""
Automated import update script for SAGA Unified.
Updates import statements to match the new directory structure.
"""
import os
import re
from pathlib import Path

def update_imports(file_path: Path):
    """Update imports in a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Import replacements mapping
        replacements = {
            # Beta Build imports
            'from beta_build.ui.event_bus': 'from ui.components.event_bus',
            'from beta_build.ui.main_window': 'from ui.screens.main_window',
            'from beta_build.ui.screens': 'from ui.screens.game_screens',
            'from beta_build.ui.map_view': 'from ui.views.map_view',
            'from beta_build.ui.char_creation': 'from ui.screens.char_creation',
            'from beta_build.core.models': 'from core.models.character_sheet',
            'from beta_build.core.skills_data': 'from core.models.skills_data',
            'from beta_build.core.command_parser': 'from core.mechanics.command_parser',
            'from beta_build.core.turn_manager': 'from core.mechanics.turn_manager',
            'from beta_build.core.zone_manager': 'from core.combat.zone_manager',
            'from beta_build.core.combat_manager': 'from core.combat.combat_manager',
            'from beta_build.core.action_resolver': 'from core.combat.action_resolver',
            'from beta_build.core.world_gen': 'from core.world_gen.world_gen',
            'from beta_build.core.world_gen_worker': 'from core.world_gen.world_gen_worker',
            'from beta_build.ai_services.director': 'from ai.director.llm_director',
            'from beta_build.ai_services.llm_worker': 'from ai.director.llm_worker',
            'from beta_build.audio.audio_manager': 'from audio.audio_manager',
            'from beta_build.data.memory_store': 'from data.chromadb.memory_store',
            
            # SAGA_Voice imports
            'from frontend.asset_mapper': 'from ui.components.asset_mapper',
            'from frontend.app': 'from ui.views.scene_viewer',
            'from frontend.char_creation': 'from ui.screens.char_creation',
            'from frontend.main_menu': 'from ui.screens.main_menu',
            'from rules_engine.character_sheet': 'from core.models.character_sheet',
            'from rules_engine.inventory': 'from core.models.inventory',
            'from rules_engine.clash_calculator': 'from core.combat.clash_calculator',
            'from rules_engine.anomaly_parser': 'from core.mechanics.anomaly_parser',
            'from rules_engine.effects': 'from core.combat.effects',
            'from audio.tts_handler': 'from audio.tts.edge_tts_handler',
            'from audio.stt_handler': 'from audio.stt.stt_handler',
            
            # SAGA_Combined imports
            'from story_manager.quest_weaver': 'from quest.journal.quest_weaver',
            'from story_manager.world_db': 'from world.external.world_db',
            'from story_manager.reactive_seeds': 'from world.procedural.reactive_seeds',
            'from story_manager.campaign_weaver': 'from quest.journal.campaign_weaver',
            'from story_manager.db_importer': 'from scripts.db_importer',
        }
        
        # Apply replacements
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated: {file_path}")
            return True
        else:
            print(f"No changes: {file_path}")
            return False
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to update all Python files."""
    print("Starting import update process...")
    
    # Get the SAGA_Unified directory
    unified_dir = Path(__file__).parent.parent
    
    # Find all Python files
    py_files = list(unified_dir.rglob('*.py'))
    
    print(f"Found {len(py_files)} Python files to process")
    
    updated_count = 0
    for py_file in py_files:
        # Skip the update script itself
        if py_file.name == 'update_imports.py':
            continue
            
        if update_imports(py_file):
            updated_count += 1
    
    print(f"\nImport update complete!")
    print(f"Updated {updated_count} files")
    print(f"Total files processed: {len(py_files)}")

if __name__ == "__main__":
    main()