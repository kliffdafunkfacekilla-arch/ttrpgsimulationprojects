import logging
import random
from typing import Dict, Any

from core.models.skills_data import get_skill_flavor

logger = logging.getLogger("ActionResolver")

class ActionResolver:
    """
    The BRUTAL Combat Engine.
    Collapses Hit & Damage into a single opposed d20 calculation.
    """
    def __init__(self, bus):
        self.bus = bus
        self.bus.subscribe("COMBAT_ACTION_DECLARED", self._on_combat_action)
        self.bus.subscribe("INTERACTION_DECLARED", self._on_interaction)
        
    def _on_interaction(self, payload: Dict[str, Any]):
        found_node = payload.get("found_node", {})
        tags = found_node.get("tags", [])
        
        if found_node.get("tile_type") == "chest":
            if "closed" in tags:
                tags.remove("closed")
                tags.append("open")
                
                # We could spawn a loot item here via the EventBus
                import random
                from beta_build.core.loot_data import LOOT_TABLES
                
                item_data = {"name": "Health Potion", "type": "consumable"} # default
                if "default" in LOOT_TABLES:
                    item_data = random.choice(LOOT_TABLES["default"])
                    
                self.bus.publish("SPAWN_LOOT", {
                    "x": payload.get("found_x"),
                    "y": payload.get("found_y"),
                    "item_data": item_data
                })
        
    def _on_combat_action(self, payload: Dict[str, Any]):
        attacker = payload.get("attacker", "Attacker")
        defender = payload.get("defender", "Defender")
        
        offense_stat = payload.get("offense_stat", 5)
        weapon_mod = payload.get("weapon_mod", 0)
        armor_mod = payload.get("armor_mod", 0)
        
        defense_stat = payload.get("defense_stat", 5)
        is_physical = payload.get("is_physical", True)
        
        attacker_tags = payload.get("attacker_tags", [])
        defender_tags = payload.get("defender_tags", [])
        cover_bonus = payload.get("cover_bonus", 0)
        
        # Tactical Equation
        technique = payload.get("technique", "Strike")
        effort = payload.get("effort", 1)
        effort_pool = "Stamina" if is_physical else "Focus"
        
        # Apply terrain/tag logic — Defender
        if "cover" in defender_tags and is_physical:
            armor_mod += cover_bonus
        
        # Apply terrain/tag logic — Attacker
        if "flanking" in attacker_tags:
            weapon_mod += 2
        if "elevated" in attacker_tags:
            weapon_mod += 1
        if "prone" in attacker_tags:
            weapon_mod -= 2
            
        # Roll the dice (1d20 system)
        att_roll = random.randint(1, 20)
        
        att_total = att_roll + offense_stat + weapon_mod
        def_total = 10 + defense_stat + armor_mod
        
        margin = att_total - def_total
        
        # Formatting narrative string
        damage_type = "Physical" if is_physical else "Mental"
        
        log_string = f"{attacker} used {technique} (Effort: {effort} {effort_pool}).\n"
        log_string += f"{attacker} rolled {att_total} (d20:{att_roll} + Stat:{offense_stat} + Mod:{weapon_mod}). "
        if "cover" in defender_tags and is_physical:
            log_string += f"{defender} defense is {def_total} (Base:10 + Stat:{defense_stat} + Armor:{armor_mod} [includes +{cover_bonus} Cover]). "
        else:
            log_string += f"{defender} defense is {def_total} (Base:10 + Stat:{defense_stat} + Armor:{armor_mod}). "
        
        flavor_text = get_skill_flavor(technique)
        if flavor_text:
            log_string += f"\nSkill Flavor: {flavor_text}\n"

        if margin < 0:
            log_string += "The attack missed or was completely absorbed!"
            self._notify_hud_and_narrator(payload, 0, False, log_string, flavor_text, margin)
        elif margin == 0:
            # The 4-Way Clash Matrix simulation
            tactics = ["PRESS", "DISENGAGE", "MANEUVER", "FEINT"]
            att_tactic = random.choice(tactics)
            def_tactic = random.choice(tactics)
            
            clash_att = random.randint(1, 20) + offense_stat + weapon_mod
            clash_def = random.randint(1, 20) + defense_stat + weapon_mod # Assuming defender weapon mod
            
            clash_winner = attacker if clash_att >= clash_def else defender
            clash_loser = defender if clash_att >= clash_def else attacker
            winning_tactic = att_tactic if clash_att >= clash_def else def_tactic
            
            log_string += f"EXACT TIE! A Clash occurs! Both lose 1 {effort_pool}.\n"
            log_string += f"{attacker} chose {att_tactic}, {defender} chose {def_tactic}.\n"
            log_string += f"{clash_winner} wins the clash using {winning_tactic}!"
            
            if winning_tactic == "PRESS":
                log_string += f" {clash_winner} pushes {clash_loser} back 1 Zone. {clash_loser} is Prone!"
            elif winning_tactic == "DISENGAGE":
                log_string += f" {clash_winner} steps back. {clash_loser} is Staggered!"
            elif winning_tactic == "MANEUVER":
                log_string += f" Combatants swap Zones. {clash_loser} suffers Minor Injury + Bleed and is Confused!"
            elif winning_tactic == "FEINT":
                log_string += f" Combatants lock weapons. {clash_loser} is Disarmed and Vulnerable!"
            
            self.bus.publish("COMBAT_CLASH", {"attacker": attacker, "defender": defender, "log": log_string})
            self._notify_hud_and_narrator(payload, 0, False, log_string, flavor_text, margin)
        else:
            # Threshold Engine
            threshold = defense_stat if defense_stat > 0 else 1
            
            capacity_dmg = 0
            is_trauma = False
            
            if margin < threshold:
                log_string += f"{attacker} hits! Minor {damage_type} Injury. (-1 Capacity)."
                capacity_dmg = 1
            elif margin >= (2 * threshold):
                perm_loss = "Limb/Mutation" if is_physical else "Mind-Fracture"
                log_string += f"APOCALYPTIC CRITICAL! {attacker} shatters {defender}! Critical {damage_type} Injury! (-5 Capacity, Permanent Loss: {perm_loss}, Staggered)."
                capacity_dmg = 5
                is_trauma = True
            elif margin >= threshold:
                penalty = "Bleeding/Hobbled" if is_physical else "Shaken/Confused"
                log_string += f"DEVASTATING BLOW! {attacker} breaches {defender}'s threshold! Major {damage_type} Injury! (-3 Capacity, Persistent Penalty: {penalty})."
                capacity_dmg = 3
                is_trauma = True
                
            self._notify_hud_and_narrator(payload, capacity_dmg, is_trauma, log_string, flavor_text, margin)
            
    def _notify_hud_and_narrator(self, payload, damage, trauma, log_string, flavor_text, margin):
        logger.info(log_string)
        
        target = payload.get("defender")
        
        # We bounce this event to the UI so it can apply damage if the target is the player
        self.bus.publish("COMBAT_RESOLVED", {
            "attacker": payload.get("attacker"),
            "target": target,
            "damage": damage,
            "trauma": trauma,
            "is_physical": payload.get("is_physical", True),
            "log": log_string,
            "intent_raw": payload.get("intent_raw", ""),
            "action_flavor": flavor_text,
            "margin": margin
        })
        
        # Visual Map Events
        if damage > 0:
            self.bus.publish("ENTITY_DAMAGED", {"uuid": target})
            
        # For the demo: Critical strikes (trauma=True) on NPCs kill them outright
        if trauma and target != payload.get("attacker"): 
            import random
            from beta_build.core.loot_data import LOOT_TABLES
            defender_tags = payload.get("defender_tags", [])
            
            loot_pool = "default"
            for t in defender_tags:
                if t in LOOT_TABLES:
                    loot_pool = t
                    break
                    
            item_data = random.choice(LOOT_TABLES[loot_pool])
            
            self.bus.publish("ENTITY_DIED", {"uuid": target, "loot_data": item_data})
        
        # Finally, pass the mathematical truth and the tags to the AI Director
        intent_prompt = f"COMBAT RESOLUTION: {log_string} Attacker Tags: {payload.get('attacker_tags', [])}. Defender Tags: {payload.get('defender_tags', [])}. Generate a 1-2 sentence brutal, visceral narrative description of this outcome."
        self.bus.publish("EXECUTE_INTENT", {"intent": intent_prompt})
