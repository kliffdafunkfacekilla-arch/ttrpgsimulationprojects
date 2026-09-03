import random
from typing import Dict, Any, List
from saga_engine.core.state import CampaignState
from saga_engine.core.bus import EventBus

class RulesEngine:
    """The B.R.U.T.A.L. math processor handling Action Dice, Tags, and Clashes."""
    
    def __init__(self, bus: EventBus, global_state: CampaignState, rules_manager, static_db: Dict[str, Any] = None):
        self.bus = bus
        self.state = global_state
        self.rules_manager = rules_manager
        self.static_db = static_db or {}
        
        # Subscribe to the 3-Beat Pulse events
        self.bus.subscribe("PULSE_START", self.regenerate_action_dice)
        self.bus.subscribe("ACTION_ATTEMPT", self.validate_and_execute_action)
        self.bus.subscribe("CLASH_LOCK", self.resolve_clash_matrix)
        self.bus.subscribe("CLASH_ATTACK", self.process_attack_event)

    def regenerate_action_dice(self, payload: Dict[str, Any]):
        """Runs at the start of the round to regen vital pools."""
        if not self.state.active_player:
            return
            
        vitals = self.state.active_player.vitals
        # Regen all vitals by 1 (or based on ruleset logic if we added it)
        for v_def in self.rules_manager.vitals:
            v_id = v_def["id"]
            max_val = vitals.maxima.get(v_id, 0)
            curr_val = vitals.current.get(v_id, 0)
            if curr_val < max_val:
                vitals.current[v_id] = min(max_val, curr_val + 1)
                
        self.bus.publish("STATE_UPDATE", {"element": "VITALS", "msg": "Vitality Pools Regenerated"})

    def validate_tags(self, required_tags: list, injuries: list, trauma: list) -> bool:
        """Checks if the anatomy can support the action."""
        for tag in required_tags:
            # Physics-based restrictions
            if tag in ["[Biped]", "[Ambulatory]"] and any("Leg" in inj for inj in injuries):
                return False
            # Mental-based restrictions
            if tag == "[Logical]" and any("Enraged" in tr or "Panic" in tr for tr in trauma):
                return False
        return True

    def process_attack_event(self, payload: Dict[str, Any]):
        """Translates a UI click (Action Deck) into a validated B.R.U.T.A.L. Clash."""
        player = self.state.active_player
        
        # 1. Determine Attacker Pool (Leading Stat)
        # Look up lead stat from weapon data
        weapon_id = payload.get("weapon_id", "ITM_WP_001")
        weapon_data = self.static_db.get("weapons", {}).get(weapon_id, {})
        lead_stat = weapon_data.get("lead_stat_required", "Might").lower()
        
        # Get stat value from player
        attacker_pool = player.attributes.get(lead_stat, 10)
        
        # 2. Extract Damage Dice
        dmg_dice = weapon_data.get("damage_dice", "1d6")
        def roll_dice(dice_str):
            num, sides = map(int, dice_str.split("d"))
            return sum(random.randint(1, sides) for _ in range(num))
        
        # 3. Handle Stamina Burn (Player choice from UI)
        burn = payload.get("attacker_stamina_burn", 1)
        
        # Redefine the payload for validation and execution
        collision_payload = {
            "type": "STAMINA",
            "cost": burn,
            "tags": weapon_data.get("traits", []),
            "weapon_name": weapon_data.get("name", "Bare Hands"),
            "damage_potential": roll_dice(dmg_dice),
            "attacker_pool": attacker_pool + burn, # Burn adds direct dice to pool
            "defender_pool": payload.get("defender_pool", 10),
            "player_tactic": payload.get("action", "PRESS")
        }
        
        # Trigger validation
        self.validate_and_execute_action(collision_payload)

    def validate_and_execute_action(self, payload: Dict[str, Any]):
        """Processes the Action Cost and checks for the Zero-State Breach."""
        player = self.state.active_player
        action_cost = payload.get("cost", 1)
        action_type = payload.get("type", "STAMINA")
        
        # 1. Anatomy/Tag Validation
        if not self.validate_tags(payload.get("tags", []), player.vitals.body_injuries, player.vitals.mind_injuries):
            self.bus.publish("STATE_UPDATE", {"element": "CHAT_LOG", "text": "Action Failed: Required anatomy is compromised."})
            return

        # 2. Spend the Action Die
        v_id = "stamina" if action_type == "STAMINA" else "focus"
        current_val = player.vitals.current.get(v_id, 0)
        
        if current_val < action_cost:
            self.bus.publish("STATE_UPDATE", {"element": "CHAT_LOG", "text": f"Not enough {v_id.capitalize()}!"})
            return
            
        player.vitals.current[v_id] -= action_cost

        # 3. Determine Success (Pool Comparison)
        # SAGA uses a simple Pool vs Pool comparison plus a D10 Chaos roll
        chaos_roll = random.randint(1, 10)
        margin = payload["attacker_pool"] - payload["defender_pool"] + (chaos_roll - 5)
        
        if margin > 0:
            # Attack Success!
            res_payload = {
                "action": "CLASH_RESOLVED",
                "margin_result": "CRITICAL" if margin > 5 else "HIT",
                "damage": payload["damage_potential"] + max(0, margin // 2)
            }
            self.bus.publish("STATE_UPDATE", res_payload)
            self.bus.publish("PLAY_SOUND", {"key": "SFX_SWORD_HIT"})
        else:
            # Deflection/Miss
            self.bus.publish("STATE_UPDATE", {"element": "CHAT_LOG", "text": f"Deflected! (Margin: {margin})"})
            self.bus.publish("PLAY_SOUND", {"key": "SFX_SWORD_MISS"})
            
        # 4. Trigger Chaos Track advancement
        if chaos_roll == self.state.chaos_level:
            self.advance_chaos()

    def resolve_clash_matrix(self, payload: Dict[str, Any]):
        """Implementation of the 5-Point Tactic Loop."""
        p_tactic = payload.get("player_tactic")
        e_tactic = payload.get("enemy_tactic", random.choice(["PRESS", "HOLD", "MANEUVER", "TRICK"]))
        
        clash_logic = {
            "PRESS": {"beats": "HOLD", "result": "Pushed Back"},
            "HOLD": {"beats": "MANEUVER", "result": "Staggered"},
            "MANEUVER": {"beats": "TRICK", "result": "Side-Step"},
            "TRICK": {"beats": "PRESS", "result": "Disarm"},
            "DISENGAGE": {"beats": "ANY", "result": "Break-Away"}
        }
        
        if p_tactic == e_tactic:
            self.state.chaos_tracker += 1
            self.bus.publish("STATE_UPDATE", {"element": "CHAT_LOG", "text": "DEADLOCK! Chaos Tracker +1."})
            self.bus.publish("PLAY_SOUND", {"key": "SFX_CANCEL"})
        elif (p_tactic in clash_logic and clash_logic[p_tactic]["beats"] == e_tactic) or p_tactic == "DISENGAGE":
            self.bus.publish("STATE_UPDATE", {"element": "CHAT_LOG", "text": f"CLASH WON: {clash_logic[p_tactic]['result']}"})
        else:
            self.bus.publish("STATE_UPDATE", {"element": "CHAT_LOG", "text": f"CLASH LOST: {e_tactic} counters {p_tactic}."})

    def advance_chaos(self):
        """Advances the global Chaos tracker."""
        self.state.chaos_tracker += 1
        self.bus.publish("STATE_UPDATE", {"element": "CHAT_LOG", "text": f"The Zone trembles... Chaos Tracker: {self.state.chaos_tracker}/10"})
        if self.state.chaos_tracker >= 10:
            self.state.chaos_tracker = 0
            self.state.chaos_level = min(10, self.state.chaos_level + 1)
            self.bus.publish("STATE_UPDATE", {"element": "CHAT_LOG", "text": "CHAOS EVOLUTION! The Zone has become more volatile."})
