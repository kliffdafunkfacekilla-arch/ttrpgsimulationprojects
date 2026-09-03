import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from python_fmg.core.db_manager import DatabaseManager
from python_fmg.core.ingestor import LoreIngestor
from python_fmg.core.tick_sequencer import WorldKernel
from python_fmg.core.resolution_referee import ResolutionReferee

def run_worldsmith():
    # Setup paths relative to project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    db_path = os.path.join(project_root, "lore_forge_world.db")
    docs_path = os.path.join(project_root, "docs")
    
    # Create docs folder if it doesn't exist
    if not os.path.exists(docs_path):
        os.makedirs(docs_path)

    # 1. Initialize Reality
    print(f"Initializing Reality at {db_path}...")
    db = DatabaseManager(db_path)
    db.init_tables()
    
    # 2. Hydrate Lore (Ingest Markdown)
    print(f"Hydrating Lore from {docs_path}...")
    ingestor = LoreIngestor(db_path)
    ingestor.ingest_all(docs_path)
    
    # 3. Setup Simulation Kernel
    print("Setting up Simulation Kernel...")
    kernel = WorldKernel(db_path)
    referee = ResolutionReferee(db_path)
    
    # 4. The Live Loop
    print("--- Worldsmith Simulation Online ---")
    while True:
        try:
            cmd_input = input("Command (tick/attack/travel [target_id]): ")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting Simulation.")
            break
            
        cmd = cmd_input.split()
        if not cmd: continue
        
        action = cmd[0].upper()
        if action == "EXIT" or action == "QUIT":
            print("Exiting Simulation.")
            break
            
        if action == "TICK":
            kernel.process_tick()
            print("Tick processed.")
        elif action in ["ATTACK", "TRAVEL"]:
            target = int(cmd[1]) if len(cmd) > 1 else None
            if target is None:
                print("Missing target ID.")
                continue
            # For testing, we assume entity ID 1
            result = referee.execute_command(1, action.capitalize(), target)
            print(result)
        else:
            print(f"Unknown command: {action}")

if __name__ == "__main__":
    run_worldsmith()
