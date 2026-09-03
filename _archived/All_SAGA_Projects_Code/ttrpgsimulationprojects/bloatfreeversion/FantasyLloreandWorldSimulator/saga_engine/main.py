import arcade
import json
import threading

# Import the Spine (Memory & Bus)
from saga_engine.core.state import CampaignState, PlayerCharacter, WealthState
from saga_engine.core.bus import EventBus
from saga_engine.core.rules import RulesetManager

# Import the Organs (Logic, World, Brain)
from saga_engine.modules.lore_vault import LoreVaultDB
from saga_engine.modules.content_generators import WorldGenerator
from saga_engine.modules.director import DirectorBrain
from saga_engine.modules.rules_engine import RulesEngine

# Import the Skin (VTT)
from saga_engine.ui.arcade_views import VTTView, SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE

def load_static_databases() -> dict:
    """Bootstraps all JSON rulesets into memory at startup."""
    db = {}
    paths = {
        "weapons": "saga_engine/data/base_weapons.json",
        "charms": "saga_engine/data/hedge_charms.json",
        "hazards": "saga_engine/data/hazard_templates.json",
        "npcs": "saga_engine/data/npc_archetypes.json",
        "magic": "saga_engine/data/spell_grids.json",
        "world": "saga_engine/data/Master_World.json",
        "loot": "saga_engine/data/loot_tables.json",
        "sounds": "saga_engine/data/sound_manifest.json",
        "ui": "saga_engine/data/ui_manifest.json"
    }
    for key, path in paths.items():
        try:
            with open(path, "r") as f:
                db[key] = json.load(f)
        except FileNotFoundError:
            db[key] = [] if key != "world" else {}
            print(f"[BOOT WARNING] {path} not found. Using empty data.")
    return db

def initialize_new_campaign(rules_manager: RulesetManager) -> CampaignState:
    """Builds the Player Chassis and sets the initial World State."""
    base_stats = {
        "might": 12, "endurance": 11, "finesse": 11, "reflexes": 10, "vitality": 9, "fortitude": 9,
        "knowledge": 10, "logic": 9, "charm": 10, "willpower": 11, "awareness": 12, "intuition": 11
    }
    
    # Calculate Max HP from ruleset
    max_hp = rules_manager.calculate_vital("hp", base_stats)
    max_stm = rules_manager.calculate_vital("stamina", base_stats)
    max_foc = rules_manager.calculate_vital("focus", base_stats)

    player = PlayerCharacter(
        id="PC_01",
        name="Kaelen",
        attributes=base_stats,
        wealth=WealthState(aetherium_coins=50, d_dust_grams=0.0)
    )
    player.vitals.maxima = {"hp": max_hp, "stamina": max_stm, "focus": max_foc}
    player.vitals.current = {"hp": max_hp, "stamina": max_stm, "focus": max_foc}
    
    return CampaignState(
        campaign_id="CAMP_001",
        active_player=player,
        active_ruleset_id="shatterlands_rules",
        chaos_level=1
    )

def main():
    print("[SYSTEM] Bootstrapping S.A.G.A. Engine...")
    
    # 1. Load Static Data and Rules
    static_db = load_static_databases()
    rules_manager = RulesetManager("saga_engine/data/rulesets/shatterlands_rules.json")
    if not rules_manager.load():
        print("[CRITICAL] Failed to load ruleset. Exiting.")
        return
    
    # 2. Forge the Spine
    global_state = initialize_new_campaign(rules_manager)
    bus = EventBus()
    
    # 3. Spin up the Lore Vault as a Background Thread
    lore_vault = LoreVaultDB(bus=bus)
    lore_thread = threading.Thread(target=lore_vault.start_daemon, daemon=True)
    lore_thread.start()
    
    # 4. Attach the Organs to the Bus
    rules = RulesEngine(bus=bus, global_state=global_state, rules_manager=rules_manager, magic_db=static_db.get("magic"))
    world_gen = WorldGenerator(bus=bus, global_state=global_state, static_db=static_db)
    director = DirectorBrain(bus=bus, global_state=global_state, rules_manager=rules_manager)
    
    # 5. Initialize the Skin (The Arcade Window)
    # The UI receives the bus to publish clicks, and the state to render health bars.
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=False)
    vtt_view = VTTView(bus=bus, global_state=global_state, static_db=static_db)
    
    window.show_view(vtt_view)
    
    print("[SYSTEM] S.A.G.A. Engine successfully launched.")
    print("[SYSTEM] Awaiting player input on the Event Bus...")
    
    # 6. Run the 60 FPS Engine Loop
    arcade.run()

if __name__ == "__main__":
    main()
