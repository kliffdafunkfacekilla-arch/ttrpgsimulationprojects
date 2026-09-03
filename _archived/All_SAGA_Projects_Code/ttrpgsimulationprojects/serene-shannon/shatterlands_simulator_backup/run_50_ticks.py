import sys
import os
import subprocess
from core_engine.engine import GlobalEngine

print("Initializing Engine (Running Migrations)...")
engine = GlobalEngine()

print("Running 50 ticks...")
for i in range(50):
    engine.trigger_tick()

print("Finished 50 ticks. Now running generate_narrative.py...")
# Fix DB path issue by running generate_narrative.py in the correct directory, though it might still be hardcoded wrong.
# Let's fix the path in generate_narrative.py first just in case.

generate_script_path = os.path.join(os.path.dirname(__file__), "story_generator", "generate_narrative.py")
subprocess.run(["python", generate_script_path])
