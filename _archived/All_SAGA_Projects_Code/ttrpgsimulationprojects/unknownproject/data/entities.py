import random
import re

# --- INVENTORY MANAGEMENT ---
def add_to_inventory(entity, item_name):
    if "inventory" not in entity: entity["inventory"] = []
    entity["inventory"].append(item_name)
    return True

def remove_from_inventory(entity, item_name):
    if "inventory" in entity and item_name in entity["inventory"]:
        entity["inventory"].remove(item_name)
        return True
    return False

# --- RPG MATH & STATS ---
def get_stat_mod(entity, stat_name):
    """Calculates D&D style stat modifiers (10 = 0, 12 = +1, 14 = +2)"""
    stats = entity.get("stats", {})
    val = stats.get(stat_name, 10) # Default to 10 if the entity has no stats
    return (val - 10) // 2

def get_armor_class(entity):
    """Calculates defense. Defaults to 10 + DEX mod."""
    base_ac = entity.get("base_ac", 10) # Monsters can have a hardcoded base_ac in templates later
    return base_ac + get_stat_mod(entity, "DEX")

def roll_damage(damage_string, bonus=0):
    """Parses strings like '1d8' or '2d6' and rolls the dice."""
    match = re.match(r"(\d+)d(\d+)", damage_string)
    if not match: return 1 + bonus # Fallback punch
    
    num_dice = int(match.group(1))
    die_sides = int(match.group(2))
    
    total = sum(random.randint(1, die_sides) for _ in range(num_dice))
    return total + bonus

# --- COMBAT & HEALTH ---
def apply_damage(entity, amount):
    if "hp" not in entity: return False
    entity["hp"] -= amount
    if entity["hp"] <= 0:
        entity["hp"] = 0
        if "hostile" in entity.get("tags", []): entity["tags"].remove("hostile")
        if "dead" not in entity.get("tags", []): entity["tags"].append("dead")
        return True
    return False

# --- NPC AI ---
def process_npc_turn(npc, player, map_data):
    if "dead" in npc.get("tags", []) or "player" in npc.get("tags", []):
        return None
        
    if "hostile" in npc.get("tags", []):
        dx = player["pos"][0] - npc["pos"][0]
        dy = player["pos"][1] - npc["pos"][1]
        
        distance = max(abs(dx), abs(dy)) 
        
        if distance <= 1:
            return {"action": "attack", "target": player["name"]}
            
        elif distance < 6:
            move_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
            move_y = 1 if dy > 0 else (-1 if dy < 0 else 0)
            new_pos = [npc["pos"][0] + move_x, npc["pos"][1] + move_y]
            
            collision = any(e["pos"] == new_pos and ("solid" in e.get("tags", []) or e.get("hp", 0) > 0) for e in map_data.get("entities", []))
            if new_pos == player["pos"]: collision = True
            
            if not collision:
                npc["pos"] = new_pos
                return {"action": "move", "target": new_pos}
                
    return None
