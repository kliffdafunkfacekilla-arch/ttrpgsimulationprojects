import json
import random
import os
import map_generator
import entities

def load_state():
    if not os.path.exists("local_map_state.json"): map_generator.generate_local_map([0,0], [25,25])
    try:
        with open("local_map_state.json", "r") as f:
            data = json.load(f)
            if "entities" not in data:
                map_generator.generate_local_map([0,0], [25,25])
                with open("local_map_state.json", "r") as f2: return json.load(f2)
            return data
    except:
        map_generator.generate_local_map([0,0], [25,25])
        with open("local_map_state.json", "r") as f: return json.load(f)

def save_state(state):
    with open("local_map_state.json", "w") as f: json.dump(state, f, indent=2)

def start_new_game():
    map_generator.generate_local_map([0,0], [25,25])
    return "New game initialized."

def execute_world_turn(state):
    player = next((e for e in state.get("entities", []) if e.get("type") == "player"), None)
    if not player or "dead" in player.get("tags", []): return
    
    npc_actions = []
    for npc in state.get("entities", []):
        if npc.get("type") == "hostile":
            action = entities.process_npc_turn(npc, player, state)
            if action:
                if action["action"] == "attack":
                    # NPC Attacks use their STR mod and a basic 1d4 damage die for now
                    npc_str_mod = entities.get_stat_mod(npc, "STR")
                    attack_roll = random.randint(1, 20) + npc_str_mod
                    player_ac = entities.get_armor_class(player)
                    
                    if attack_roll >= player_ac:
                        damage = entities.roll_damage("1d4", npc_str_mod)
                        entities.apply_damage(player, damage)
                        log_msg = f"{npc['name']} hit Valerius for {damage} damage!"
                    else:
                        log_msg = f"{npc['name']}'s attack missed Valerius!"
                        
                    print(f"[World Turn] {log_msg} (Valerius HP: {player['hp']}/{player['max_hp']})")
                    npc_actions.append(log_msg)
                elif action["action"] == "move":
                    print(f"[World Turn] {npc['name']} creeps closer... (Moved to {action['target']})")
                
    if npc_actions:
        state["latest_action"]["mechanical_result"] += " " + " ".join(npc_actions)

def execute_attack(actor_id, target_id):
    state = load_state()
    actor = next((e for e in state.get("entities", []) if e.get("id") == actor_id or e.get("name") == actor_id), None)
    target = next((e for e in state.get("entities", []) if e.get("id") == target_id or e.get("name") == target_id), None)
    
    if not actor or not target: return "ERROR: Combatants not found."
    
    actor_name = actor["name"]
    target_name = target["name"]
    
    # Range Check
    dx = abs(actor["pos"][0] - target["pos"][0])
    dy = abs(actor["pos"][1] - target["pos"][1])
    if max(dx, dy) > 1:
        mech_result = f"{actor_name} swung at the air! {target_name} is out of melee range."
        print(f"\n[Combat] {mech_result}")
        state["latest_action"] = {"actor": actor_name, "action": "Melee Attack", "target": target_name, "mechanical_result": mech_result}
        execute_world_turn(state)
        save_state(state)
        return mech_result

    # --- THE TRUE RPG MATH ---
    # 1. Get Actor's Strength Modifier
    str_mod = entities.get_stat_mod(actor, "STR")
    
    # 2. Get Target's Armor Class
    target_ac = entities.get_armor_class(target)
    
    # 3. Roll to Hit
    attack_roll = random.randint(1, 20) + str_mod
    print(f"\n[Combat] {actor_name} rolled {attack_roll} to hit {target_name} (AC: {target_ac}).")
    
    if attack_roll >= target_ac: 
        # 4. Roll Damage (Using a Longsword 1d8 as placeholder until we link weapons)
        damage = entities.roll_damage("1d8", str_mod)
        is_dead = entities.apply_damage(target, damage)
        
        if is_dead: 
            mech_result = f"CRITICAL HIT! {damage} damage dealt. {target_name} is DEAD."
            print(f"[Combat] SUCCESS! {damage} damage dealt. {target_name} died.")
        else: 
            mech_result = f"HIT. {damage} damage dealt. {target_name} has {target['hp']} HP left."
            print(f"[Combat] SUCCESS! {damage} damage dealt. {target_name} has {target['hp']} HP remaining.")
    else: 
        mech_result = f"MISS. Armor deflected the blow."
        print(f"[Combat] MISS! The attack was deflected.")
                
    state["latest_action"] = {"actor": actor_name, "action": "Melee Attack", "target": target_name, "mechanical_result": mech_result}
    state["ai_directive"] = "NARRATOR MODE: Describe the combat action vividly based on the mechanics."
    
    execute_world_turn(state)
    save_state(state)
    return mech_result

def execute_move(actor_id, dest_x, dest_y):
    state = load_state()
    actor = next((e for e in state.get("entities", []) if e.get("id") == actor_id or e.get("name") == actor_id), None)
    if not actor or "dead" in actor.get("tags", []): return "Action failed."
    
    actor["pos"] = [dest_x, dest_y]
    actor_name = actor["name"]
    
    state["latest_action"] = {"actor": actor_name, "action": "Movement", "target": f"[{dest_x}, {dest_y}]", "mechanical_result": f"{actor_name} moved."}
    execute_world_turn(state)
    save_state(state)
    return f"{actor_name} moved to {dest_x}, {dest_y}."

def execute_transition(dest_x, dest_y):
    state = load_state()
    player_data = next((e for e in state.get("entities", []) if e.get("type") == "player"), None)
    grid_w, grid_h = state["meta"]["grid_size"]
    global_pos = state["meta"].get("global_pos", [0, 0])
    new_g_x, new_g_y = global_pos[0], global_pos[1]
    entry_x, entry_y = dest_x, dest_y

    if dest_x >= grid_w - 1: new_g_x += 1; entry_x = 1
    elif dest_x <= 0: new_g_x -= 1; entry_x = grid_w - 2
    if dest_y >= grid_h - 1: new_g_y += 1; entry_y = 1
    elif dest_y <= 0: new_g_y -= 1; entry_y = grid_h - 2

    map_generator.generate_local_map([new_g_x, new_g_y], [entry_x, entry_y], player_data=player_data)
    return "Transition complete."

def execute_examine(actor_id, target_id):
    state = load_state()
    actor = next((e for e in state.get("entities", []) if e.get("id") == actor_id or e.get("name") == actor_id), None)
    target = next((e for e in state.get("entities", []) if e.get("id") == target_id or e.get("name") == target_id), None)
    
    if not actor or not target: return "Error"
    actor_name = actor["name"]
    target_name = target["name"]
    target_tags = target.get("tags", [])
    
    state["latest_action"] = {"actor": actor_name, "action": "Examine Entity", "target": target_name, "target_current_tags": target_tags, "mechanical_result": "Player is studying the target."}
    state["ai_directive"] = f"NARRATOR MODE: Describe the target visually. YOU MUST FACTOR IN THESE TAGS: {target_tags}. If 'dead' is present, describe a lifeless corpse."
    save_state(state)
    return f"{actor_name} is examining {target_name}."

def execute_examine_area(actor_id, dest_x, dest_y):
    state = load_state()
    actor = next((e for e in state.get("entities", []) if e.get("id") == actor_id or e.get("name") == actor_id), None)
    if not actor: return "Error"
    
    map_tags = state.get("meta", {}).get("map_tags", [])
    state["latest_action"] = {"actor": actor["name"], "action": "Examine Environment", "target": f"[{dest_x}, {dest_y}]", "map_tags": map_tags, "mechanical_result": "Player is scanning the terrain."}
    state["ai_directive"] = f"NARRATOR MODE: Describe the atmospheric environment here using tags: {map_tags}."
    save_state(state)
    return f"{actor['name']} is examining the area."
