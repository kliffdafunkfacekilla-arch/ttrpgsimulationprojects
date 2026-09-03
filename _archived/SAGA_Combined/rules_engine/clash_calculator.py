import random
from rules_engine.character_sheet import CharacterSheet

# Opposed Roll Clash Matrix based on Tactic choices
CLASH_MATRIX = {
    "press": {
        "press": "Both take increased damage.",
        "maneuver": "Maneuver wins: Move behind and strike.",
        "feint": "Press wins: Pushes through the feint.",
        "disengage": "Press wins: Push back."
    },
    "maneuver": {
        "press": "Maneuver wins: Move behind and strike.",
        "maneuver": "Both stumble and lose footing.",
        "feint": "Feint wins: Disarms the maneuvering opponent.",
        "disengage": "Maneuver wins: Intercepts the retreat."
    },
    "feint": {
        "press": "Press wins: Pushes through the feint.",
        "maneuver": "Feint wins: Disarms the maneuvering opponent.",
        "feint": "Both are stunned by mutual bluffs.",
        "disengage": "Feint wins: Disarms before retreat."
    },
    "disengage": {
        "press": "Press wins: Push back.",
        "maneuver": "Maneuver wins: Intercepts the retreat.",
        "feint": "Feint wins: Disarms before retreat.",
        "disengage": "Both step back safely."
    }
}

class ClashCalculator:
    def __init__(self):
        self.entities = {}
        
    def register_entity(self, sheet: CharacterSheet):
        self.entities[sheet.name] = sheet

    def get_attack_stats(self, weapon_name: str, is_ranged: bool) -> tuple:
        """Returns (body_stat, mind_stat) based on the weapon."""
        name = weapon_name.lower()
        if is_ranged:
            if "bow" in name and "cross" not in name: return ("might", "awareness") # Bows
            if "crossbow" in name: return ("finesse", "logic")
            if "javelin" in name or "axe" in name or "throw" in name: return ("vitality", "willpower") # Thrown
            if "gun" in name or "powder" in name or "musket" in name or "flintlock" in name: return ("endurance", "knowledge") # Black Powder
            if "grenade" in name or "siege" in name or "cannon" in name or "ballista" in name: return ("fortitude", "charm") # Alchemical/Siege
            return ("reflexes", "intuition") # Exotic (Boomerangs/Bolas) fallback
        else:
            if "great" in name or "claymore" in name or "two-hand" in name or "heavy" in name: return ("might", "willpower") # 2-Handed
            if "hammer" in name or "mace" in name or "blunt" in name: return ("fortitude", "logic")
            if "spear" in name or "halberd" in name or "pole" in name: return ("endurance", "awareness")
            if "dagger" in name or "rapier" in name or "finesse" in name or "sword" in name: return ("finesse", "intuition")
            if "whip" in name or "flail" in name: return ("reflexes", "charm")
            return ("vitality", "knowledge") # unarmed fallback

    def get_defense_stats(self, armor_name: str) -> tuple:
        """Returns (body_stat, mind_stat) based on armor."""
        name = armor_name.lower()
        if "plate" in name or "heavy" in name: return ("fortitude", "willpower")
        if "mail" in name or "medium" in name: return ("endurance", "logic")
        if "leather" in name or "light" in name: return ("reflexes", "awareness")
        if "robe" in name or "cloth" in name: return ("finesse", "intuition")
        if "tower" in name or "heavy shield" in name: return ("might", "knowledge")
        if "buckler" in name or "shield" in name: return ("vitality", "charm") # Light shields
        return ("reflexes", "awareness") # unarmored fallback

    def resolve_attack(self, attacker_name: str, defender_name: str, intent: str, is_ranged: bool = False) -> dict:
        attacker = self.entities.get(attacker_name)
        defender = self.entities.get(defender_name)

        if not attacker or not defender:
            return {"action": intent, "success": False, "narrative_hint": "Combatants not found."}

        # 1. Calculate Attacker Score
        weapon = attacker.inventory.slots.get("weapon")
        weapon_name = weapon.name if weapon else "Fists"
        weapon_mod = weapon.modifier if weapon else 0
        b_stat, m_stat = self.get_attack_stats(weapon_name, is_ranged)
        
        # Determine if it's a mind or body variant based on stat_type, defaulting to body
        active_att_stat = m_stat if (weapon and getattr(weapon, "stat_type", "") == m_stat) else b_stat
        att_stat_val = attacker.stats.get(active_att_stat, 0)
        
        att_roll = random.randint(1, 20)
        att_total = att_roll + att_stat_val + weapon_mod

        # 2. Calculate Defender Score
        armor = defender.inventory.slots.get("body")
        armor_name = armor.name if armor else "Clothing"
        armor_mod = armor.armor_mod if armor else 0
        db_stat, dm_stat = self.get_defense_stats(armor_name)
        
        # Determine if it's a mind or body variant based on stat_type, defaulting to body
        active_def_stat = dm_stat if (armor and getattr(armor, "stat_type", "") == dm_stat) else db_stat
        def_stat_val = defender.stats.get(active_def_stat, 0)
        
        # Check active defense limit
        if not defender.has_active_defended:
            def_roll = random.randint(1, 20)
            defender.has_active_defended = True
            is_active_defense = True
        else:
            def_roll = 0 # Passive defense
            is_active_defense = False
            
        def_total = def_roll + def_stat_val + armor_mod

        narrative = f"{attacker.name} attacks with {weapon_name} [{active_att_stat}] (Roll: {att_roll}+{att_stat_val}+{weapon_mod} = {att_total}). "
        narrative += f"{defender.name} defends with {armor_name} [{active_def_stat}] ({'Active Roll: ' + str(def_roll) if is_active_defense else 'Passive'} + {def_stat_val}+{armor_mod} = {def_total})."

        # 3. Resolution
        if att_total == def_total:
            if is_active_defense:
                return {
                    "action": intent,
                    "is_clash": True,
                    "clash_target": defender.name,
                    "narrative_hint": narrative + " BLADES LOCK! A Clash is triggered! Declare your tactic (Press, Maneuver, Feint, Disengage)."
                }
            else:
                return {
                    "action": intent,
                    "success": False,
                    "is_clash": False,
                    "narrative_hint": narrative + " The passive defense holds. Glancing blow, no damage."
                }
                
        elif att_total > def_total:
            threshold = att_total - def_total
            if threshold <= 4:
                dmg = 1
                outcome = "Minor injury / Glancing blow."
            elif threshold <= 9:
                dmg = 3
                outcome = "Major injury! Solid strike."
            else:
                dmg = 5
                outcome = "CRITICAL HIT! Devastating blow."
                
            defender.take_damage(dmg)
            return {
                "action": intent,
                "success": True,
                "is_clash": False,
                "damage": dmg,
                "narrative_hint": narrative + f" {outcome} ({dmg} damage)"
            }
        else:
            threshold = def_total - att_total
            if threshold >= 10:
                outcome = "FUMBLE! The attacker leaves themselves completely open."
                attacker.has_disadvantage = True
            else:
                outcome = "Miss. The defender easily deflects or evades."
            
            return {
                "action": intent,
                "success": False,
                "is_clash": False,
                "damage": 0,
                "narrative_hint": narrative + f" {outcome}"
            }

    def resolve_clash_tactic(self, player_tactic: str, ai_tactic: str) -> dict:
        """Resolves the 4-way RPS matrix for a clash."""
        p_tactic = player_tactic.lower().strip()
        a_tactic = ai_tactic.lower().strip()
        
        if p_tactic not in CLASH_MATRIX or a_tactic not in CLASH_MATRIX:
            return {"error": "Invalid tactics."}
            
        outcome = CLASH_MATRIX[p_tactic][a_tactic]
        return {
            "narrative_hint": f"Player used {p_tactic}, Enemy used {a_tactic}. {outcome}",
            "is_clash": False # Ends the clash
        }

    def get_social_attack_stats(self, augment_name: str) -> str:
        """Returns the mind stat used for the social augment."""
        name = augment_name.lower()
        if "toxin" in name or "trophy" in name or "spore" in name: return "knowledge" # Disgust
        if "mirror" in name or "whistle" in name or "paradox" in name: return "logic" # Confusion
        if "powder" in name or "flute" in name or "ricochet" in name: return "awareness" # Distraction
        if "token" in name or "omen" in name or "curse" in name: return "intuition" # Self-Doubt
        if "mask" in name or "incense" in name or "radiant" in name: return "charm" # Awe
        if "execution" in name or "aura" in name or "judgment" in name: return "willpower" # Intimidation
        return "charm" # Fallback

    def resolve_social_attack(self, attacker_name: str, defender_name: str, intent: str, augment_name: str) -> dict:
        """Resolves Composure damage against Mental Defense."""
        attacker = self.entities.get(attacker_name)
        defender = self.entities.get(defender_name)

        if not attacker or not defender:
            return {"action": intent, "success": False, "narrative_hint": "Combatants not found."}
            
        att_stat = self.get_social_attack_stats(augment_name)
        att_val = attacker.stats.get(att_stat, 0)
        att_roll = random.randint(1, 20)
        att_total = att_roll + att_val
        
        def_total = defender.get_derived_stat("mental defense") + random.randint(1, 20)
        
        narrative = f"{attacker.name} uses {augment_name} [{att_stat}] (Roll: {att_roll}+{att_val} = {att_total}). "
        narrative += f"{defender.name} resists with Mental Defense (Roll + {defender.get_derived_stat('mental defense')} = {def_total})."
        
        if att_total > def_total:
            threshold = att_total - def_total
            if threshold <= 4:
                dmg = 1
                outcome = "Minor psychological distress."
            elif threshold <= 9:
                dmg = 3
                outcome = "Major psychological shock!"
            else:
                dmg = 5
                outcome = "CRITICAL PSYCHOLOGICAL BREAK!"
                
            defender.take_damage(dmg, is_composure=True)
            return {
                "action": intent,
                "success": True,
                "damage": dmg,
                "narrative_hint": narrative + f" {outcome} ({dmg} Composure damage)"
            }
        else:
            return {
                "action": intent,
                "success": False,
                "damage": 0,
                "narrative_hint": narrative + " The defender anchors their mind and ignores the assault."
            }
