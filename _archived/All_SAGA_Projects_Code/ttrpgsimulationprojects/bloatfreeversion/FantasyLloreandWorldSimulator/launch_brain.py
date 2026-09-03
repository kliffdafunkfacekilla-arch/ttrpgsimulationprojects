import arcade
import os
from saga_engine.core.bus import EventBus
from saga_engine.core.chronicler import Chronicler
from saga_engine.core.world_loader import WorldLoader
from saga_engine.core.state import CampaignState, PlayerCharacter, WealthState
from saga_engine.core.rules import RulesetManager
from saga_engine.core.chronos import ChronosManager
from saga_engine.core.simulation import SimulationDirector
from saga_engine.modules.sim.atmos import AetherFlow
from saga_engine.modules.sim.geopol import SovereignAI
from saga_engine.modules.sim.biosphere import Biosphere
from saga_engine.modules.quest_weaver import QuestWeaver
from saga_engine.modules.director import DirectorBrain
from saga_engine.modules.rules_engine import RulesEngine
from saga_engine.modules.forgers import EntityForger
from saga_engine.ui.dashboard import DashboardView, SCREEN_WIDTH, SCREEN_HEIGHT

def main():
    print("[SYSTEM] Initializing S.A.G.A. Brain Engine...")
    
    # 1. Foundation
    bus = EventBus()
    chronicler = Chronicler("saga_brain.db")
    
    # 2. World Data
    loader = WorldLoader("saga_engine/data/Master_World.json")
    if not loader.load_world():
        print("[CRITICAL] Failed to load macro-world data. Exiting.")
        return

    # 3. Ruleset Hub
    rules_manager = RulesetManager("saga_engine/data/rulesets/shatterlands_rules.json")
    if not rules_manager.load():
        print("[CRITICAL] Failed to load ruleset. Exiting.")
        return

    # 4. Campaign State (The Spine)
    # Initialize a player with dynamic stats
    base_stats = {
        "might": 10, "endurance": 10, "vitality": 10, 
        "reflexes": 10, "finesse": 10, "awareness": 10, 
        "intuition": 10, "knowledge": 10, "willpower": 10
    }
    
    # Calculate Max HP and Stamina from ruleset
    max_hp = rules_manager.calculate_vital("hp", base_stats)
    max_stm = rules_manager.calculate_vital("stamina", base_stats)
    max_foc = rules_manager.calculate_vital("focus", base_stats)

    player = PlayerCharacter(
        id="PC_01",
        name="The Wanderer",
        attributes=base_stats,
        wealth=WealthState(),
        location_hex="[0, 0]"
    )
    # Set current/max vitals
    player.vitals.maxima = {"hp": max_hp, "stamina": max_stm, "focus": max_foc}
    player.vitals.current = {"hp": max_hp, "stamina": max_stm, "focus": max_foc}
    
    state = CampaignState(
        campaign_id="BRAIN_SIM_001",
        active_player=player,
        active_ruleset_id="shatterlands_rules"
    )
    loader.sync_to_state(state)
    
    # 4. Simulation Organs
    chronos = ChronosManager(bus, state, chronicler)
    
    # Sovereign Simulation Engine
    sim_director = SimulationDirector(bus, state, chronicler, loader)
    aether_flow = AetherFlow(bus, state, chronicler, loader)
    sovereign_ai = SovereignAI(bus, state, chronicler, loader)
    biosphere = Biosphere(bus, state, chronicler, loader)
    
    sim_director.register_organ(aether_flow)
    sim_director.register_organ(sovereign_ai)
    sim_director.register_organ(biosphere)
    
    weaver = QuestWeaver(bus, state, chronicler)
    
    # 5. The Cerebral Organs (Rules & Narration)
    rules_engine = RulesEngine(bus, state, rules_manager)
    director = DirectorBrain(bus, state, rules_manager)
    
    # Entity Forger would be used by JIT triggers
    
    # 5. Dashboard (Visuals)
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "S.A.G.A. Brain - GM Dashboard")
    dash_view = DashboardView(bus, state, chronicler, loader, chronos)
    window.show_view(dash_view)
    
    print("[SYSTEM] S.A.G.A. Brain Active. Launching Dashboard...")
    arcade.run()

if __name__ == "__main__":
    main()
