import re
import math
import logging
from typing import Dict, Any
from beta_build.core.fov_calculator import calculate_fov

logger = logging.getLogger("CommandParser")

class CommandParser:
    def __init__(self, bus, zone_manager, turn_manager):
        self.bus = bus
        self.zone_manager = zone_manager
        self.turn_manager = turn_manager
        
        # Regex mappings for cardinal movement
        self.dir_map = {
            "north": (0, -1),
            "up": (0, -1),
            "south": (0, 1),
            "down": (0, 1),
            "east": (1, 0),
            "right": (1, 0),
            "west": (-1, 0),
            "left": (-1, 0),
        }
        
        self.move_pattern = re.compile(
            r"\b(?:walk|run|move|go|step|head)\s+(north|south|east|west|up|down|left|right)\b", 
            re.IGNORECASE
        )
        
        self.attack_pattern = re.compile(
            r"\b(?:strike|attack|shoot|hit|kill)\s+(.*)\b",
            re.IGNORECASE
        )
        
        self.mental_attack_pattern = re.compile(
            r"\b(?:intimidate|charm|deceive|mindblast|taunt|cast)\s+(.*)\b",
            re.IGNORECASE
        )
        
        self.interact_pattern = re.compile(
            r"\b(?:open|loot|search|hack|inspect)\s+(.*)\b",
            re.IGNORECASE
        )
        
        self.end_turn_pattern = re.compile(
            r"\b(?:end turn|pass|done)\b",
            re.IGNORECASE
        )
        
        self.equip_pattern = re.compile(r"\bequip\s+(.*)\b", re.IGNORECASE)
        self.unequip_pattern = re.compile(r"\bunequip\s+(.*)\b", re.IGNORECASE)
        
        self.save_pattern = re.compile(r"^/save$", re.IGNORECASE)
        self.load_pattern = re.compile(r"^/load$", re.IGNORECASE)

    def parse_intent(self, intent: str, player_uuid: str = "player_1", player_character=None) -> Dict[str, Any]:
        """
        Interprets the player intent string.
        Returns a dictionary detailing the action to take.
        """
        intent_lower = intent.lower()
        
        # Check for Save/Load commands
        if self.save_pattern.search(intent_lower):
            self.bus.publish("UI_SAVE_GAME", {})
            return {"type": "system", "system_prompt": "System: Game state saved."}
            
        if self.load_pattern.search(intent_lower):
            self.bus.publish("UI_LOAD_GAME", {})
            return {"type": "system", "system_prompt": "System: Game state loaded."}
        
        # 0. Check for End Turn
        if self.end_turn_pattern.search(intent_lower):
            if self.turn_manager.end_turn(player_uuid):
                # Trigger AI to narrate enemies taking their turn (stub for now)
                return {
                    "type": "turn_ended",
                    "system_prompt": "System: Player ended their turn. Narrate the tension as enemies prepare to act."
                }
            else:
                return {
                    "type": "error",
                    "system_prompt": "System Error: It is not currently your turn."
                }
                
        # 1. Check for Movement
        move_match = self.move_pattern.search(intent_lower)
        if move_match:
            if not self.turn_manager.can_act(player_uuid, "move"):
                return {
                    "type": "movement_failed",
                    "system_prompt": "System: Player attempted to move, but they have already exhausted their movement this turn. Narrate their hesitation."
                }
                
            direction = move_match.group(1)
            dx, dy = self.dir_map[direction]
            
            curr_x, curr_y = self.zone_manager.get_entity_pos(player_uuid)
            if curr_x == -1:
                return {
                    "type": "error",
                    "system_prompt": "System Error: Player token not found on the physical board."
                }
                
            new_x = curr_x + dx
            new_y = curr_y + dy
            
            return self._resolve_movement(direction, new_x, new_y, player_uuid)
            
        # 2. Check for Combat
        attack_match = self.attack_pattern.search(intent_lower)
        if attack_match:
            target_str = attack_match.group(1).strip()
            
            curr_x, curr_y = self.zone_manager.get_entity_pos(player_uuid)
            if curr_x == -1:
                return {"type": "error", "system_prompt": "System Error: Player token not found on the physical board."}
                
            return self._resolve_combat(target_str, curr_x, curr_y, player_uuid, is_mental=False, player_character=player_character)
            
        # 3. Check for Mental Combat
        mental_match = self.mental_attack_pattern.search(intent_lower)
        if mental_match:
            target_str = mental_match.group(1).strip()
            
            curr_x, curr_y = self.zone_manager.get_entity_pos(player_uuid)
            if curr_x == -1:
                return {"type": "error", "system_prompt": "System Error: Player token not found on the physical board."}
                
            return self._resolve_combat(target_str, curr_x, curr_y, player_uuid, is_mental=True, player_character=player_character)
            
        # 4. Check for Interaction
        interact_match = self.interact_pattern.search(intent_lower)
        if interact_match:
            if not self.turn_manager.can_act(player_uuid, "focus"):
                return {
                    "type": "interaction_failed",
                    "system_prompt": "System: Player attempted to interact, but they have already exhausted their focus action this turn. Narrate their inability to focus."
                }
                
            target_str = interact_match.group(1).strip()
            
            curr_x, curr_y = self.zone_manager.get_entity_pos(player_uuid)
            if curr_x == -1:
                return {"type": "error", "system_prompt": "System Error: Player token not found on the physical board."}
                
            return self._resolve_interaction(target_str, curr_x, curr_y, player_uuid, player_character=player_character)
            
        # 5. Check for Equipment
        equip_match = self.equip_pattern.search(intent_lower)
        if equip_match:
            item_name = equip_match.group(1).strip()
            if not player_character:
                return {"type": "error", "system_prompt": "System Error: No player character loaded."}
                
            bag = player_character.inventory.bag
            for i, item in enumerate(bag):
                if item_name.lower() in item.name.lower():
                    self.bus.publish("UI_INVENTORY_EQUIP", {"index": i})
                    return {"type": "interaction_success", "system_prompt": f"System: Player successfully equipped {item.name}. Narrate."}
            
            return {"type": "error", "system_prompt": f"System Error: Item '{item_name}' not found in bag."}
            
        unequip_match = self.unequip_pattern.search(intent_lower)
        if unequip_match:
            item_name = unequip_match.group(1).strip()
            if not player_character:
                return {"type": "error", "system_prompt": "System Error: No player character loaded."}
                
            for slot_name, item in player_character.inventory.slots.items():
                if item and item_name.lower() in item.name.lower():
                    self.bus.publish("UI_INVENTORY_UNEQUIP", {"slot": slot_name})
                    return {"type": "interaction_success", "system_prompt": f"System: Player successfully unequipped {item.name}. Narrate."}
                    
            return {"type": "error", "system_prompt": f"System Error: Item '{item_name}' not currently equipped."}
            
        # Fallback to generic unhandled (let AI handle it)
        return {
            "type": "generic",
            "message": intent
        }
        
    def _resolve_movement(self, direction: str, new_x: int, new_y: int, player_uuid: str) -> Dict[str, Any]:
        """Validates movement against the grid."""
        
        is_passable, reason, target_node = self.zone_manager.is_tile_passable(new_x, new_y)
        
        if not is_passable:
            if reason == "edge_of_map":
                self.bus.publish("EDGE_TRANSITION_REQUESTED", {"direction": direction})
                return {
                    "type": "movement_failed",
                    "reason": reason,
                    "direction": direction,
                    "system_prompt": f"System: Player attempted to move {direction} and is traveling to the adjacent region. Narrate their departure.",
                    "dx": 0, "dy": 0
                }
            else:
                return {
                    "type": "movement_failed",
                    "reason": reason,
                    "direction": direction,
                    "system_prompt": f"System: Player attempted to move {direction} but collided with a {target_node.get('tile_type', 'wall')}. Narrate their failure.",
                    "dx": 0, "dy": 0
                }
            
        # Success
        
        self.turn_manager.consume_beat(player_uuid, "move")
        
        # We fire the physical move here in the parser so the main_window doesn't have to
        self.bus.publish("MOVE_ENTITY", {
            "uuid": player_uuid,
            "x": new_x,
            "y": new_y
        })
        
        visible_context = self.zone_manager.get_visible_context(new_x, new_y)
        sys_prompt = f"System: Player successfully moved {direction} onto a {target_node.get('tile_type', 'floor')}. Stamina cost applied. {visible_context} Narrate what they see."
        
        return {
            "type": "movement_success",
            "direction": direction,
            "new_pos": (new_x, new_y),
            "system_prompt": sys_prompt,
            "dx": new_x, "dy": new_y
        }
        
    def _resolve_combat(self, target_str: str, curr_x: int, curr_y: int, player_uuid: str, is_mental: bool = False, player_character=None) -> Dict[str, Any]:
        beat_to_consume = "focus" if is_mental else "stamina"
        action_name = "mental attack" if is_mental else "attack"
        
        if not self.turn_manager.can_act(player_uuid, beat_to_consume):
            return {
                "type": "combat_failed",
                "system_prompt": f"System: Player attempted to {action_name} '{target_str}', but they have already exhausted their {beat_to_consume} action this turn. Narrate their fatigue."
            }
            
        target_uuid = self.zone_manager.get_entity_by_name_heuristic(target_str)
        if not target_uuid:
            return {
                "type": "combat_failed",
                "system_prompt": f"System: Player attempted to attack '{target_str}', but no such entity exists nearby. Narrate their confusion."
            }
            
        tx, ty = self.zone_manager.get_entity_pos(target_uuid)
        
        # Check FOV
        if self.zone_manager.grid_data:
            visible_coords = calculate_fov(self.zone_manager.grid_data, curr_x, curr_y, 7)
            if (tx, ty) not in visible_coords:
                return {
                    "type": "combat_failed",
                    "system_prompt": f"System: Player attempted to attack '{target_str}', but they do not have line of sight. Narrate their failure."
                }
                
        # Check Range
        dist = math.hypot(tx - curr_x, ty - curr_y)
        range_limit = 5.0 if is_mental else 1.5
        
        if dist > range_limit: # Simple range
            return {
                "type": "combat_failed",
                "system_prompt": f"System: Player attempted to {action_name} '{target_str}', but they are out of range (distance {dist:.1f}). Narrate their failure."
            }
            
        # Instead of returning success, we publish to ActionResolver
        # and let it handle the math and AI intent dispatch!
        
        target_name = self.zone_manager.entities[target_uuid].get("name", target_str)
        target_tags = self.zone_manager.entities[target_uuid].get("tags", [])
        
        # Dynamic Stats Extraction
        attacker_name = "player_1"
        attacker_tags = []
        offense_stat = 5
        weapon_mod = 0
        
        if player_character:
            attacker_name = player_character.name
            attacker_tags = player_character.tags
            if is_mental:
                offense_stat = player_character.stats.get("willpower", 5)
            else:
                offense_stat = player_character.stats.get("might", 5)
                if player_character.inventory.slots.get("weapon"):
                    weapon_mod += player_character.inventory.slots["weapon"].modifier
                    
        # Defender stats extracted dynamically if it's an entity
        defense_stat = 5
        armor_mod = 0
        enemy_data = self.zone_manager.entities.get(target_uuid, {})
        if "stats" in enemy_data:
            if is_mental:
                defense_stat = enemy_data["stats"].get("logic", 5)
            else:
                defense_stat = enemy_data["stats"].get("reflexes", 5)
                # enemy armor logic here if applicable
        
        payload = {
            "attacker": attacker_name, 
            "defender": target_uuid,
            "offense_stat": offense_stat, 
            "defense_stat": defense_stat,
            "weapon_mod": weapon_mod,
            "armor_mod": armor_mod,
            "is_physical": not is_mental,
            "attacker_tags": attacker_tags,
            "defender_tags": target_tags,
            "technique": action_name.capitalize(),
            "effort": 1
        }
        
        self.turn_manager.consume_beat(player_uuid, beat_to_consume)
        self.bus.publish("COMBAT_ACTION_DECLARED", payload)
        
        return {
            "type": "handled_by_resolver"
        }
        
    def _resolve_interaction(self, target_str: str, curr_x: int, curr_y: int, player_uuid: str, player_character=None) -> Dict[str, Any]:
        """Validates interaction with grid nodes (chests, doors)."""
        target_lower = target_str.lower()
        
        # Scan adjacent tiles for the interactable object
        found_node = None
        found_x, found_y = -1, -1
        
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                ny = curr_y + dy
                nx = curr_x + dx
                
                if ny >= 0 and ny < len(self.zone_manager.grid_data) and nx >= 0 and nx < len(self.zone_manager.grid_data[0]):
                    node = self.zone_manager.grid_data[ny][nx]
                    tile_type = node.get("tile_type", "").lower()
                    
                    if target_lower in tile_type or any(target_lower in tag.lower() for tag in node.get("tags", [])):
                        found_node = node
                        found_x, found_y = nx, ny
                        break
            if found_node:
                break
                
        if not found_node:
            return {
                "type": "interaction_failed",
                "system_prompt": f"System: Player attempted to interact with '{target_str}', but nothing matching that description is within reach. Narrate their failure."
            }
            
        tags = found_node.get("tags", [])
        
        if "interactable" not in tags:
            return {
                "type": "interaction_failed",
                "system_prompt": f"System: Player attempted to interact with '{target_str}', but it is not interactable. Narrate."
            }
            
        # Dispatch Interaction
        self.bus.publish("INTERACTION_DECLARED", {
            "player_uuid": player_uuid,
            "player_character": player_character.model_dump() if player_character else None,
            "target_str": target_str,
            "found_node": found_node,
            "found_x": found_x,
            "found_y": found_y
        })
                
        self.turn_manager.consume_beat(player_uuid, "focus")
        return {
            "type": "interaction_success",
            "system_prompt": f"System: Player successfully interacted with {target_str}. Narrate."
        }
