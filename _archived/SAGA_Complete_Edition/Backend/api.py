import sys
import os
import random
from typing import Optional, List, Dict, Any

# Setup path imports
backend_dir = os.path.dirname(__file__)
bloatfree_dir = os.path.join(backend_dir, "SAGA_bloatfree_rules")
sys.path.append(bloatfree_dir)

ai_director_dir = os.path.abspath(os.path.join(backend_dir, "..", "AI_Director", "saga_director"))
sys.path.append(ai_director_dir)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Rules Engine (Stage 3)
from rules_engine.clash_calculator import ClashCalculator
from rules_engine.character_sheet import CharacterSheet
from rules_engine.inventory import Item

# World Simulation & Dynamic Memory (Stage 1 & 5)
from world_manager.simulation import WorldSimulator
from world_manager.map_generator import ClusterManager

# Story Generator (Stage 2)
from story_manager.quest_weaver import QuestWeaver, GruntPack

# AI Director / Narrator (Stage 4)
try:
    from director import saga_director_app
    DIRECTOR_AVAILABLE = True
except Exception as e:
    print(f"[API Boot] Note on AI Director import: {e}")
    DIRECTOR_AVAILABLE = False


app = FastAPI(
    title="SAGA Unified Engine API", 
    description="Full 4-Stage TTRPG closed-loop engine: World Simulation -> Story Generation -> Rules Math -> AI DM Narration -> World Memory Mutation."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# ENGINE STATE INITIALIZATION
# ==============================================================================
world_sim = WorldSimulator()
cluster_mgr = ClusterManager()
story_gen = QuestWeaver()
rules_engine = ClashCalculator()

# Initialize starting region & campaign
PLAYER_START_CX = 12
PLAYER_START_CY = 12
cluster_mgr.generate_cluster(region_id=1, base_biome="Ancient Forest", poi_coords=[[14, 22], [10, 15]], poi_context="Crumbling Obsidian Keep")
story_gen.initialize_campaign(PLAYER_START_CX, PLAYER_START_CY)

# Register default player
player_character = CharacterSheet("Player", {
    "might": 7, "finesse": 6, "vitality": 6, 
    "reflexes": 5, "endurance": 6, "awareness": 6,
    "logic": 5, "presence": 5, "composure": 5
}, origin="Exiled Duelist")
player_character.inventory.equip(Item("Iron Longsword", "weapon", "might", 3, 1))
rules_engine.register_entity(player_character)

current_player_coords = {"cx": PLAYER_START_CX, "cy": PLAYER_START_CY, "px": 50, "py": 50}


# ==============================================================================
# PYDANTIC DATA CONTRACTS
# ==============================================================================
class ActionRequest(BaseModel):
    actor_id: str = "Player"
    action_type: str = Field(..., description="Action intent, e.g., 'attack with Longsword', 'cast fire spark', 'sneak forward'")
    target_id: Optional[str] = None
    target_stats: Optional[Dict[str, int]] = None
    action_params: Dict[str, Any] = {}

class ActionResponse(BaseModel):
    success: bool
    stage1_world_context: Dict[str, Any]
    stage2_story_context: Dict[str, Any]
    stage3_math_resolution: Dict[str, Any]
    stage4_ai_dm_narration: str
    stage5_world_mutations_applied: List[str]
    # Full application state for UI sync (includes world snapshot, entities, tags, etc.)
    world_state: Dict[str, Any] = Field(default_factory=dict)

class MoveRequest(BaseModel):
    direction: str = Field(..., description="north, south, east, west, or specific cx, cy")
    steps: int = 1

class WorldStateResponse(BaseModel):
    coordinates: Dict[str, int]
    biome: str
    weather: str
    active_world_tags: List[str]
    historical_scars: List[str]
    faction_influence: Dict[str, int]
    active_quests: str
    entities_present: List[str]


# ==============================================================================
# API ENDPOINTS (THE 4-STAGE CLOSED LOOP)
# ==============================================================================

@app.get("/api/v1/world/state", response_model=WorldStateResponse)
async def get_world_state():
    """Fetches the ground truth world state, current hex tags, and simulation history."""
    cx, cy = current_player_coords["cx"], current_player_coords["cy"]
    battlemap = cluster_mgr.get_battlemap(cx, cy)
    journal_summary = story_gen.journal.get_journal_summary(cx, cy)
    
    return WorldStateResponse(
        coordinates=current_player_coords,
        biome=battlemap.get("biome", "Wilderness"),
        weather=battlemap.get("weather", "Clear"),
        active_world_tags=battlemap.get("global_tags", []),
        historical_scars=battlemap.get("scars", []),
        faction_influence=battlemap.get("faction_influence", {}),
        active_quests=journal_summary,
        entities_present=list(rules_engine.entities.keys())
    )

@app.post("/api/v1/world/move")
async def move_player(move: MoveRequest):
    """Moves the player across the simulated world grid, triggering world ticks & memory."""
    d = move.direction.lower()
    if d == "north": current_player_coords["cy"] = max(0, current_player_coords["cy"] - move.steps)
    elif d == "south": current_player_coords["cy"] = min(24, current_player_coords["cy"] + move.steps)
    elif d == "east": current_player_coords["cx"] = min(24, current_player_coords["cx"] + move.steps)
    elif d == "west": current_player_coords["cx"] = max(0, current_player_coords["cx"] - move.steps)
    
    # Tick simulation & weather
    sim_messages = cluster_mgr.tick_simulation(hours=1)
    
    cx, cy = current_player_coords["cx"], current_player_coords["cy"]
    battlemap = cluster_mgr.get_battlemap(cx, cy)
    story_node = story_gen.check_for_story_node(cx, cy, party_level=player_character.level)
    
    return {
        "coordinates": current_player_coords,
        "biome": battlemap.get("biome"),
        "weather": battlemap.get("weather"),
        "tags": battlemap.get("global_tags"),
        "simulation_ticks": sim_messages,
        "story_node_discovered": story_node
    }

@app.post("/api/v1/action", response_model=ActionResponse)
async def process_action(request: ActionRequest):
    """
    Executes the Complete 4-Stage SAGA Loop:
    1. World Simulation Context (Hex, Biome, Dynamic Tags, Historical Scars)
    2. Story Generator Context (Campaign Objectives, Local Hooks, NPC Profiles)
    3. Rules Engine Math (Deterministic 1d20 Margin of Success, HP/Composure, Trauma)
    3.5 Dynamic World Memory Mutation (Tags, Scars, Faction shifts)
    4. AI DM Narration (Synthesizes facts into immersive storytelling)
    """
    cx, cy = current_player_coords["cx"], current_player_coords["cy"]
    
    # --------------------------------------------------------------------------
    # STAGE 1: SIMULATED WORLD CONTEXT
    # --------------------------------------------------------------------------
    battlemap = cluster_mgr.get_battlemap(cx, cy)
    world_biome = battlemap.get("biome", "Wasteland")
    world_weather = battlemap.get("weather", "Clear")
    world_tags = battlemap.get("global_tags", [])
    world_scars = battlemap.get("scars", [])
    faction_influence = battlemap.get("faction_influence", {})
    
    # --------------------------------------------------------------------------
    # STAGE 2: STORY GENERATION (CAMPAIGN WEAVER)
    # --------------------------------------------------------------------------
    active_story_hook = story_gen.check_for_story_node(cx, cy, party_level=player_character.level)
    quest_directive = story_gen.journal.get_journal_summary(cx, cy)
    
    story_context = {
        "quest_summary": quest_directive,
        "story_hook": active_story_hook,
        "location_context": f"Region ({cx}, {cy}) [{world_biome}] under {world_weather} skies."
    }

    # --------------------------------------------------------------------------
    # STAGE 3: RULES ENGINE (DETERMINISTIC MATH CHASSIS)
    # --------------------------------------------------------------------------
    target_name = request.target_id or "Environment"
    
    # Ensure target exists in mathematical registry
    if target_name not in rules_engine.entities and target_name != "Environment":
        stats = request.target_stats or {"might": 4, "reflexes": 4, "endurance": 4, "composure": 3}
        target_sheet = CharacterSheet(target_name, stats, origin="Spawned Entity")
        rules_engine.register_entity(target_sheet)
        
    math_result = rules_engine.resolve_action(
        intent=request.action_type,
        actor_name=request.actor_id,
        target_name=target_name,
        weather=world_weather,
        global_tags=world_tags
    )
    
    # --------------------------------------------------------------------------
    # STAGE 3.5: DYNAMIC WORLD SIMULATION MUTATIONS & MEMORY FEEDBACK
    # --------------------------------------------------------------------------
    mutations_applied = []
    
    # Check if combat or elemental actions mutate the terrain / world state
    intent_lower = request.action_type.lower()
    if any(k in intent_lower for k in ["fire", "burn", "ignite", "flame"]):
        cluster_mgr.apply_world_mutation(cx, cy, tag_add=["Scorched", "Smoke-Filled"], scar_description=f"Wildfire scorched the terrain during combat with {target_name}.")
        mutations_applied.append("Added world tags: [Scorched, Smoke-Filled]")
    elif any(k in intent_lower for k in ["kill", "strike", "slash", "cleave", "bleed", "attack"]):
        cluster_mgr.apply_world_mutation(cx, cy, tag_add=["Bloodstained"], scar_description=f"Violent clash between {request.actor_id} and {target_name}.")
        mutations_applied.append("Added world tag: [Bloodstained]")
        
    if math_result.get("success") and target_name != "Environment":
        # Shift faction influence away from hostile control
        cluster_mgr.apply_world_mutation(cx, cy, faction_delta={"Settlers Guild": +5, "Outlaws": -10})
        mutations_applied.append("Shifted faction balance: Settlers Guild (+5), Outlaws (-10)")

    # Log beat to story memory
    story_gen.log_beat(request.action_type, str(math_result))

    # --------------------------------------------------------------------------
    # STAGE 4: AI DM NARRATOR (SYNTHESIZE TRUTH INTO PROSE)
    # --------------------------------------------------------------------------
    mechanical_summary = (
        f"Action: {request.action_type} by {request.actor_id} against {target_name}. "
        f"Outcome: {'SUCCESS' if math_result.get('success') else 'FAILURE'}. "
        f"Details: {math_result.get('narrative_hint', 'Action concluded.')}"
    )
    
    world_summary = f"Environment: {world_biome}, Weather: {world_weather}. Active Tags: {', '.join(world_tags)}. Past Scars: {'; '.join(world_scars[-2:]) if world_scars else 'None'}."
    
    dm_narration = None
    
    if DIRECTOR_AVAILABLE:
        director_payload = {
            "player_id": request.actor_id,
            "player_data": {
                "name": player_character.name,
                "vitals": {"hp": player_character.current_hp, "max_hp": player_character.max_hp},
                "stamina": player_character.active_stamina,
                "focus": player_character.active_focus
            },
            "current_hex": {"biome": world_biome, "faction_owner": "Local Faction"},
            "weather": world_weather,
            "active_quest": {"narrative_objective": quest_directive},
            "war_events": world_scars,
            "tension": 20,
            "event_trigger": mechanical_summary,
            "narrative_output": ""
        }
        try:
            director_result = await saga_director_app.ainvoke(director_payload)
            dm_narration = director_result.get("narrative_output")
        except Exception as e:
            print(f"[AI DM Narrator Fallback]: {e}")
            
    if not dm_narration or "LLM offline" in dm_narration:
        # High quality algorithmic DM narrator fallback
        dm_narration = (
            f"Under the {world_weather.lower()} canopy of the {world_biome.lower()}, the air hangs heavy with the scent of "
            f"{'smoke and fresh blood' if 'Bloodstained' in world_tags else 'damp earth'}. "
            f"{player_character.name} lunges forward with precision. {math_result.get('narrative_hint', '')} "
            f"The environment reverberates as the struggle leaves its mark upon the land."
        )

    return ActionResponse(
        success=math_result.get("success", True),
        stage1_world_context={
            "coordinates": (cx, cy),
            "biome": world_biome,
            "weather": world_weather,
            "tags": world_tags,
            "scars": world_scars,
            "faction_influence": faction_influence
        },
        stage2_story_context=story_context,
        stage3_math_resolution=math_result,
        stage4_ai_dm_narration=dm_narration,
        stage5_world_mutations_applied=mutations_applied,
        world_state={
            "coordinates": (cx, cy),
            "biome": world_biome,
            "weather": world_weather,
            "tags": world_tags,
            "scars": world_scars,
            "faction_influence": faction_influence,
            "entities": list(rules_engine.entities.keys()),
            "active_quests": story_gen.journal.get_journal_summary(cx, cy)
        }
    )

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
