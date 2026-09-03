from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os
import sys
import random
import json

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from core_engine.llm_interface import get_world_context, apply_narrative_shift
from story_generator.ollama_director import generate_campaign_intro, process_player_action, resolve_skill_check

app = FastAPI(title="AI RPG Hub", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "core_engine", "world_state.db")

# --- Pydantic Models ---
class Character(BaseModel):
    name: str
    kingdom: str
    species: str
    passive_trait: str
    power_track: str
    survival_track: str
    crew_talent: str
    background: str
    might: int
    fortitude: int
    finesse: int
    vitality: int
    reflex: int
    endurance: int
    willpower: int
    intuition: int
    logic: int
    knowledge: int
    awareness: int
    charm: int

class CharacterCreationRequest(BaseModel):
    characters: List[Character]

class ActionRequest(BaseModel):
    action: str
    model: str = "qwen2.5:latest"


# --- DB Helpers ---
def get_db_connection():
    return sqlite3.connect(DB_PATH)

def get_active_characters():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, kingdom, species, passive_trait, power_track, survival_track, crew_talent, background, might, fortitude, finesse, vitality, reflex, endurance, willpower, intuition, logic, knowledge, awareness, charm, current_hp, max_hp FROM characters")
    rows = c.fetchall()
    conn.close()
    
    chars = []
    for r in rows:
        chars.append({
            "id": r[0], "name": r[1], "kingdom": r[2], "species": r[3],
            "passive_trait": r[4], "power_track": r[5], "survival_track": r[6], "crew_talent": r[7], "background": r[8],
            "might": r[9], "fortitude": r[10], "finesse": r[11], "vitality": r[12], "reflex": r[13], "endurance": r[14],
            "willpower": r[15], "intuition": r[16], "logic": r[17], "knowledge": r[18], "awareness": r[19], "charm": r[20],
            "hp": f"{r[21]}/{r[22]}"
        })
    return chars

def get_campaign_state():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT story_framework, current_quest, current_location_id FROM campaign_state ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    if row:
        return {"story_framework": row[0], "current_quest": row[1], "location_id": row[2]}
    return {}

def update_campaign_state(framework: str, location_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE campaign_state SET story_framework = ?, current_location_id = ? WHERE id = (SELECT MAX(id) FROM campaign_state)", (framework, location_id))
    conn.commit()
    conn.close()

def save_new_npcs(npcs, location_id):
    if not npcs: return
    conn = get_db_connection()
    c = conn.cursor()
    for npc in npcs:
        c.execute("INSERT INTO npcs (name, location_id, personality, memory) VALUES (?, ?, ?, '')",
                  (npc.get("name", "Unknown"), location_id, npc.get("personality", "")))
    conn.commit()
    conn.close()


# --- Endpoints ---

@app.post("/create_characters")
def create_characters(req: CharacterCreationRequest):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM characters") # Reset for new game
    for char in req.characters:
        c.execute("""
            INSERT INTO characters (name, kingdom, species, passive_trait, power_track, survival_track, crew_talent, background, might, fortitude, finesse, vitality, reflex, endurance, willpower, intuition, logic, knowledge, awareness, charm, current_hp, max_hp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 20, 20)
        """, (char.name, char.kingdom, char.species, char.passive_trait, char.power_track, char.survival_track, char.crew_talent, char.background, char.might, char.fortitude, char.finesse, char.vitality, char.reflex, char.endurance, char.willpower, char.intuition, char.logic, char.knowledge, char.awareness, char.charm))
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"{len(req.characters)} characters saved."}

@app.post("/start_campaign")
def start_campaign(model: str = "qwen2.5:latest"):
    chars = get_active_characters()
    if not chars:
        raise HTTPException(status_code=400, detail="No characters created yet.")
        
    world_context = get_world_context()
    
    # Let AI generate intro
    result = generate_campaign_intro(chars, world_context, model=model)
    
    framework = result.get("story_framework", "")
    narrative = result.get("narrative", "")
    npcs = result.get("new_npcs", [])
    
    # Update DB
    update_campaign_state(framework, 1) # Default location 1 for now
    save_new_npcs(npcs, 1)
    
    return {
        "narrative": narrative,
        "story_framework": framework,
        "npcs_spawned": npcs
    }

@app.post("/action")
def submit_action(req: ActionRequest):
    world_context = get_world_context()
    campaign_state = get_campaign_state()
    
    # 1. Ask AI for resolution
    result = process_player_action(world_context, json.dumps(campaign_state), req.action, model=req.model)
    
    skill_check = result.get("skill_check")
    state_shifts = result.get("state_shifts", {})
    new_npcs = result.get("new_npcs", [])
    
    if state_shifts:
        apply_narrative_shift(state_shifts)
        
    save_new_npcs(new_npcs, campaign_state.get("location_id", 1))
    
    # 2. Check if AI requested a skill check
    if skill_check:
        stat_name = skill_check.get("stat", "brawn").lower()
        # Find highest stat among party for the roll
        chars = get_active_characters()
        best_mod = max([c.get(stat_name, 0) for c in chars]) if chars else 0
        
        die_roll = random.randint(1, 20)
        total = die_roll + best_mod
        
        # 3. Resolve the skill check with AI
        final_result = resolve_skill_check(world_context, req.action, skill_check, best_mod, die_roll, total, model=req.model)
        
        # Combine narratives
        combined_narrative = result.get("narrative", "") + f"\n\n[System: Rolled {stat_name.upper()} -> {die_roll} + {best_mod} = {total} vs DC {skill_check.get('dc', 10)}]\n\n" + final_result.get("narrative", "")
        
        if final_result.get("state_shifts"):
            apply_narrative_shift(final_result["state_shifts"])
            
        return {
            "narrative": combined_narrative,
            "skill_check_executed": True,
            "roll": total
        }
    
    return {
        "narrative": result.get("narrative", "The AI was silent."),
        "skill_check_executed": False
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
