import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from story_generator.ollama_director import generate_summary, process_player_action
from core_engine.llm_interface import get_world_context

def main():
    print("Fetching world context...")
    context = get_world_context()
    
    print("\n--- Testing World Summary ---")
    summary = generate_summary(context)
    print("NARRATIVE SUMMARY:\n", summary)
    
    print("\n--- Testing Player Action ---")
    action = "The Free Cities launch a surprise blockade on Kingdom of Arcanum's main trade route."
    print(f"Action: {action}")
    
    result = process_player_action(context, action)
    print("Result Narrative:\n", result.get("narrative", "None"))
    print("\nState Shifts:\n", result.get("state_shifts", {}))
    
if __name__ == "__main__":
    main()
