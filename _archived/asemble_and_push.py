# assemble_and_push.py
import os
import shutil
import subprocess

# Define the target project name
PROJECT_NAME = "shatterlands_simulator"

# 1. Define the directories to create
STRUCTURE = [
    f"{PROJECT_NAME}/data",
    f"{PROJECT_NAME}/core_engine",
    f"{PROJECT_NAME}/taleweaver_chronicle",
    f"{PROJECT_NAME}/ai_director",
    f"{PROJECT_NAME}/client_vtt/public",
    f"{PROJECT_NAME}/client_vtt/src"
]

print("Initializing clean architecture directory layout...")
for folder in STRUCTURE:
    os.makedirs(folder, exist_ok=True)

# 2. Define harvesting mapping (Source file -> Target destination)
# The script checks if these exist locally and migrates them safely
MIGRATION_MAP = {
    # Move your current optimized simulation core files
    "codec.py": f"{PROJECT_NAME}/core_engine/codec.py",
    "engine.py": f"{PROJECT_NAME}/core_engine/engine.py",
    "fractal_core.py": f"{PROJECT_NAME}/core_engine/fractal_core.py",
    "db_setup.py": f"{PROJECT_NAME}/core_engine/db_setup.py",
    
    # Harvest targets from your previous narrative code repositories
    "TALEWEAVERS/event_parser.py": f"{PROJECT_NAME}/taleweaver_chronicle/event_parser.py",
    "TaleWeaver/history_ledger.py": f"{PROJECT_NAME}/taleweaver_chronicle/history_ledger.py",
    "lore-formatter/prompt_templates.py": f"{PROJECT_NAME}/taleweaver_chronicle/prompt_templates.py",
    
    # Harvest targets from automated GM and assistant DM scripts
    "GMAI/oracle.py": f"{PROJECT_NAME}/ai_director/oracle.py",
    "DMAI/npc_behavior.py": f"{PROJECT_NAME}/ai_director/npc_behavior.py",
}

print("Harvesting modules from legacy codebases...")
for source, destination in MIGRATION_MAP.items():
    if os.path.exists(source):
        shutil.copy4(source, destination) if hasattr(shutil, "copy4") else shutil.copy(source, destination)
        print(f"  [HARVESTED] {source} -> {destination}")
    else:
        # If a specific module doesn't exist yet, seed a clean placeholder file
        with open(destination, 'w') as f:
            f.write(f"# Placeholder for {os.path.basename(destination)}\n")
        print(f"  [SEEDED PLACEHOLDER] {destination}")

# 3. Create structural file touchpoints
with open(f"{PROJECT_NAME}/requirements.txt", "w") as f:
    f.write("flask\n")
with open(f"{PROJECT_NAME}/.gitignore", "w") as f:
    f.write("*.db\n__pycache__/\n.env\n")
with open(f"{PROJECT_NAME}/core_engine/__init__.py", "w") as f: f.write("")
with open(f"{PROJECT_NAME}/taleweaver_chronicle/__init__.py", "w") as f: f.write("")
with open(f"{PROJECT_NAME}/ai_director/__init__.py", "w") as f: f.write("")

# Write an INSTRUCTIONS file directly inside the folder for your agents to read
with open(f"{PROJECT_NAME}/INSTRUCTIONS.md", "w") as f:
    f.write("""# Agent Instructions
You are an assembly agent. The code files in `core_engine/` must be finalized to support the strict nested geometry:
- Tier 1: L=14 frequency (10,570 Global Hexes)
- Tier 2: get_hexes_in_radius(5) loop (91 Regional Hexes)
""")

print("\nStructure completely assembled locally. Commencing GitHub integration...")

# 4. Automate local Git setup and push using GitHub CLI (gh)
try:
    os.chdir(PROJECT_NAME)
    subprocess.run(["git", "init"], check=True)
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit: Headless Nested Geodesic Engine Structure"], check=True)
    subprocess.run(["git", "branch", "-M", "main"], check=True)
    
    # Programmatically create the repo on your GitHub account and push it
    print(f"Creating new GitHub repository: '{PROJECT_NAME}'...")
    subprocess.run(["gh", "repo", "create", PROJECT_NAME, "--public", "--source=.", "--remote=origin", "--push"], check=True)
    print("\nSUCCESS: Your clean, consolidated simulation engine repository is live on GitHub!")
except Exception as e:
    print(f"\nGit Integration Error: {e}")
    print("Ensure you have installed the GitHub CLI (`gh`) and run `gh auth login` in your terminal first.")