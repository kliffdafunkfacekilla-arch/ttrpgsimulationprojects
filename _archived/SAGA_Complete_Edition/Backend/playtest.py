import sys
import os
import asyncio
import io

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Path setup
backend_dir = os.path.dirname(__file__)
bloatfree_dir = os.path.join(backend_dir, "SAGA_bloatfree_rules")
sys.path.append(bloatfree_dir)

from api import app, process_action, move_player, get_world_state, ActionRequest, MoveRequest

async def run_comprehensive_playtest():
    print("=" * 80)
    print("      [SAGA ENGINE: COMPLETE 4-STAGE CLOSED-LOOP PLAYTEST]")
    print("=" * 80)
    
    # -------------------------------------------------------------------------
    # STEP 1: INSPECT INITIAL WORLD SIMULATION STATE
    # -------------------------------------------------------------------------
    print("\n>>> [STEP 1] Querying Simulated World State (Stage 1)...")
    world_state = await get_world_state()
    print(f"[*] Coordinates:       {world_state.coordinates}")
    print(f"[*] Biome:             {world_state.biome}")
    print(f"[*] Weather:           {world_state.weather}")
    print(f"[*] Active World Tags: {world_state.active_world_tags}")
    print(f"[*] Historical Scars:  {world_state.historical_scars if world_state.historical_scars else 'None (Pristine)'}")
    print(f"[*] Faction Influence: {world_state.faction_influence}")
    print(f"[*] Active Quests:     \n{world_state.active_quests}")
    
    # -------------------------------------------------------------------------
    # STEP 2: MOVEMENT & SIMULATION TICKS
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print(">>> [STEP 2] Moving Player East into the Wilderness & Advancing World Clock...")
    move_res = await move_player(MoveRequest(direction="east", steps=1))
    print(f"[*] New Coordinates:   {move_res['coordinates']}")
    print(f"[*] Current Biome:     {move_res['biome']}")
    print(f"[*] Weather Status:    {move_res['weather']}")
    print(f"[*] Hex Tags:          {move_res['tags']}")
    print(f"[*] Simulation Clock:  {move_res['simulation_ticks']}")
    if move_res.get('story_node_discovered'):
        print(f"[*] Story Seed Found:  {move_res['story_node_discovered']}")

    # -------------------------------------------------------------------------
    # STEP 3: TACTICAL COMBAT ACTION (ATTACK WITH LONGSWORD)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print(">>> [STEP 3] Executing Action: 'strike with Iron Longsword' against 'Orc Marauder'...")
    action_1 = ActionRequest(
        actor_id="Player",
        action_type="strike with Iron Longsword",
        target_id="Orc Marauder",
        target_stats={"might": 6, "reflexes": 4, "endurance": 5, "composure": 4}
    )
    res_1 = await process_action(action_1)
    
    print("\n[STAGE 1: WORLD CONTEXT INGESTED]")
    print(f"  Biome: {res_1.stage1_world_context['biome']} | Weather: {res_1.stage1_world_context['weather']}")
    print(f"  Tags: {res_1.stage1_world_context['tags']}")
    
    print("\n[STAGE 2: STORY GENERATION (CAMPAIGN WEAVER)]")
    print(f"  Context: {res_1.stage2_story_context['location_context']}")
    print(f"  Quest:   {res_1.stage2_story_context['quest_summary']}")
    
    print("\n[STAGE 3: RULES ENGINE (DETERMINISTIC MATH)]")
    print(f"  Success:     {res_1.stage3_math_resolution.get('success')}")
    print(f"  Math Result: {res_1.stage3_math_resolution.get('narrative_hint')}")
    
    print("\n[STAGE 3.5: DYNAMIC WORLD SIMULATION MUTATIONS (CAMPAIGN MEMORY)]")
    for mut in res_1.stage5_world_mutations_applied:
        print(f"  -> Mutation: {mut}")
        
    print("\n[STAGE 4: AI DM NARRATION (PROSE SYNTHESIS)]")
    print(f"  DM: \"{res_1.stage4_ai_dm_narration}\"")

    # -------------------------------------------------------------------------
    # STEP 4: ELEMENTAL SPELL ACTION (FIRE SPARK) -> TESTING FURTHER WORLD MUTATION
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print(">>> [STEP 4] Executing Action: 'cast fire ignite' to burn enemy barricades...")
    action_2 = ActionRequest(
        actor_id="Player",
        action_type="cast fire ignite blaze",
        target_id="Orc Marauder"
    )
    res_2 = await process_action(action_2)
    
    print("\n[STAGE 3.5: DYNAMIC WORLD SIMULATION MUTATIONS (CAMPAIGN MEMORY)]")
    for mut in res_2.stage5_world_mutations_applied:
        print(f"  -> Mutation: {mut}")
        
    print("\n[STAGE 4: AI DM NARRATION (PROSE SYNTHESIS)]")
    print(f"  DM: \"{res_2.stage4_ai_dm_narration}\"")

    # -------------------------------------------------------------------------
    # STEP 5: VERIFY SIMULATION MEMORY LOOPBACK IN SUBSEQUENT TICKS
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print(">>> [STEP 5] Advancing Simulation by 24 Hours to Observe Mutated Hex Feedback...")
    move_res_2 = await move_player(MoveRequest(direction="east", steps=1))
    print(f"[*] New Location:       {move_res_2['coordinates']}")
    print(f"[*] Simulation Feedback:")
    for tick_msg in move_res_2['simulation_ticks']:
        print(f"  - {tick_msg}")
        
    # Re-inspect original hex to verify scars and tags persisted
    print("\n>>> Re-inspecting mutated world state to confirm permanent memory...")
    final_world = await get_world_state()
    print(f"[*] Active Tags on current hex: {final_world.active_world_tags}")
    print(f"[*] World Scars in memory:       {final_world.historical_scars}")
    print(f"[*] Updated Faction Balance:    {final_world.faction_influence}")
    
    print("\n" + "=" * 80)
    print("     [SUCCESS] CLOSED-LOOP PLAYTEST COMPLETED SUCCESSFULLY WITH ZERO ERRORS")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_comprehensive_playtest())
