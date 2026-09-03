import sqlite3
import os
import json
import requests

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "world_state.db")
LORE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "lore")
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:latest"

def load_world_lore():
    lore_texts = []
    if not os.path.exists(LORE_DIR):
        return "No world lore available."
    
    for filename in os.listdir(LORE_DIR):
        if filename.endswith(".md") or filename.endswith(".txt"):
            filepath = os.path.join(LORE_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                lore_texts.append(f"--- {filename} ---\n{f.read()}")
    
    return "\n\n".join(lore_texts) if lore_texts else "No world lore available."

def generate_regional_data(settlement_name, faction_name, lore_text):
    prompt = f"""You are the World Builder AI for a fantasy roleplaying game. 
Here is the foundational World Lore:
{lore_text}

We are generating meso-map regional data for the territory surrounding the settlement of "{settlement_name}", which belongs to the faction "{faction_name}".

Based on the lore and the location, generate regional data. You must return a strict JSON object containing whatever details are most appropriate for this specific hex (e.g., local points of interest, a specific threat, a rumor, resources, or sub-factions). 
Ensure the JSON keys are descriptive (e.g., "points_of_interest", "local_threat", "geography", "rumors", "resources").

Return ONLY valid JSON. Do not wrap it in markdown block quotes.
Example format:
{{
    "geography": "Dense, mist-shrouded pine forests covering rolling hills.",
    "points_of_interest": ["The Ruined Spire of Aldor", "Whispering Cave"],
    "local_threat": "A pack of shadow-wolves has been hunting merchants.",
    "rumors": ["They say the old mayor buried his gold under the town square."]
}}
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }

    print(f"Generating data for {settlement_name}...")
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        output = response.json().get("response", "{}")
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            if "```json" in output:
                clean_output = output.split("```json")[1].split("```")[0].strip()
                return json.loads(clean_output)
            print(f"Warning: Failed to parse JSON for {settlement_name}.")
            return {}
    except Exception as e:
        print(f"Error contacting Ollama for {settlement_name}: {e}")
        return {}

def run_pipeline():
    print("Loading lore...")
    lore_text = load_world_lore()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Fetch all settlements to generate data for their parent hex
    cursor.execute("""
        SELECT s.id, s.name, f.name, s.global_hex_id 
        FROM settlements s
        LEFT JOIN factions f ON s.faction_id = f.id
    """)
    settlements = cursor.fetchall()
    
    if not settlements:
        print("No settlements found in the database. Are you sure the map is parsed?")
        return

    print(f"Found {len(settlements)} settlements. Beginning pre-generation pipeline...")
    
    for s_id, s_name, f_name, hex_id in settlements:
        f_name = f_name or "Independent"
        
        # Check if already generated
        cursor.execute("SELECT regional_data_json FROM global_hexes WHERE id = ?", (hex_id,))
        row = cursor.fetchone()
        if row and row[0] and row[0] != "{}" and row[0].strip() != "":
            print(f"Skipping {s_name} - data already exists.")
            continue
            
        # Generate new data
        regional_data = generate_regional_data(s_name, f_name, lore_text)
        
        if regional_data:
            cursor.execute(
                "UPDATE global_hexes SET regional_data_json = ? WHERE id = ?",
                (json.dumps(regional_data), hex_id)
            )
            conn.commit()
            print(f"Successfully saved regional data for {s_name} (Hex {hex_id}).")
            
    conn.close()
    print("Pipeline complete.")

if __name__ == "__main__":
    run_pipeline()
