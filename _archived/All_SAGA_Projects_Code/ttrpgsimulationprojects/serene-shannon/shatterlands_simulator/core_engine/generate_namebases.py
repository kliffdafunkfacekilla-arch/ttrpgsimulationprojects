import sqlite3
import os
import requests

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "world_state.db")
LORE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "lore")
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "namebases")
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:latest"

def load_world_lore():
    lore_texts = []
    if not os.path.exists(LORE_DIR):
        return ""
    for filename in os.listdir(LORE_DIR):
        if filename.endswith(".md") or filename.endswith(".txt"):
            filepath = os.path.join(LORE_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                lore_texts.append(f.read())
    return "\n".join(lore_texts)[:4000] # truncate to avoid massive context for simple names

def generate_names_for_faction(faction_name, lore_text):
    prompt = f"""You are a world-building linguist AI.
Here is some foundational lore context about the world of Shatterlands:
{lore_text}

I need you to invent exactly 50 unique names for the faction known as "{faction_name}".
These should be culturally and thematically appropriate for whatever that faction represents in this dark fantasy/sci-fantasy setting (e.g. if Avian, sound bird-like; if Ursine, heavy and guttural; if Insectoid, clicking/chittering).

RULES:
1. ONLY return a single comma-separated list of 50 names. 
2. NO bullet points, NO numbering, NO markdown formatting, NO extra text or explanations.
3. Example output: Name1,Name2,Name3,Name4...
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.8
        }
    }

    print(f"Asking AI for {faction_name} names...")
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        output = response.json().get("response", "").strip()
        
        # Strip out any potential markdown code blocks if the AI misbehaves
        output = output.replace("```text", "").replace("```csv", "").replace("```", "").strip()
        
        return output
    except Exception as e:
        print(f"Error generating for {faction_name}: {e}")
        return ""

def main():
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)
        
    print("Loading world lore...")
    lore_text = load_world_lore()
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT DISTINCT name FROM factions WHERE name IS NOT NULL AND name != ''")
    factions = [row[0] for row in c.fetchall()]
    conn.close()
    
    print(f"Found {len(factions)} factions.")
    
    for faction in factions:
        out_file = os.path.join(OUT_DIR, f"{faction}.txt")
        if os.path.exists(out_file):
            print(f"Skipping {faction}, namebase already exists.")
            continue
            
        names_csv = generate_names_for_faction(faction, lore_text)
        if names_csv:
            # Clean up the output to make sure it's just comma separated
            names = [n.strip() for n in names_csv.split(",") if n.strip()]
            clean_csv = ",".join(names)
            
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(clean_csv)
            print(f"Saved {len(names)} names for {faction} to {out_file}")

if __name__ == "__main__":
    main()
