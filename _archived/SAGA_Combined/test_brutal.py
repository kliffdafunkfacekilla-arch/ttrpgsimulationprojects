import json
from rules_engine.character_sheet import CharacterSheet
from rules_engine.anomaly_parser import AnomalyParser

def test_brutal_engine():
    # 1. Create a character with strict baseline stats (all 5s)
    player = CharacterSheet("Mage-Knight", stats={})
    
    # 2. Test Derived Stat Accuracy
    print("--- 1. Testing Derived Stats ---")
    assert player.max_hp == 15, f"Expected 15 HP (5+5+5), got {player.max_hp}"
    assert player.max_stamina == 15, f"Expected 15 Stamina, got {player.max_stamina}"
    assert player.max_focus == 15, f"Expected 15 Focus, got {player.max_focus}"
    assert player.max_composure == 15, f"Expected 15 Composure, got {player.max_composure}"
    
    print(f"Health: {player.max_hp} | Stamina: {player.max_stamina} | Focus: {player.max_focus} | Composure: {player.max_composure}")
    print(f"Phys Def: {player.get_derived_stat('phys_def')} | Speed: {player.get_derived_stat('speed')} | Percep: {player.get_derived_stat('perception')} | Ment Def: {player.get_derived_stat('ment_def')}")
    print("All derived stats correctly calculated using 2:1 formula!\n")

    # 3. Test Action Battery & Turn Start
    print("--- 2. Testing 3-Beat Pulse & Loadout Tax ---")
    player.active_stamina = 5
    player.active_focus = 5
    
    # Fake a high loadout tax (> 7.5 capacity)
    class MockInventory:
        def get_physical_tax(self): return 5
        def get_mental_tax(self): return 3
        def get_total_modifier(self, stat): return 0
    player.inventory = MockInventory()
    
    player.start_turn()
    print(f"After heavy loadout tax turn start -> Stamina: {player.active_stamina}/15, Focus: {player.active_focus}/15")
    assert player.active_stamina == 6, f"Expected penalized regen to 6, got {player.active_stamina}"
    print("Heavy loadout correctly penalized regeneration!\n")

    # 4. Test Modular Magic System
    print("--- 3. Testing Modular Magic Parsing ---")
    player.active_stamina = 10
    player.active_focus = 10
    player.beats["focus"] = 2 # Give extra beat to afford the cone
    
    # Mock LLM JSON output for: "I cast a Rank 4 Cone of Fire at Power Scale 6"
    llm_json = '''
    {
        "shape": "cone",
        "school": "Nexus",
        "effect_rank": 4,
        "power_scale": 6
    }
    '''
    
    result = AnomalyParser.parse_spell(player, llm_json)
    print(result["narrative_hint"])
    
    # Costs for Cone (Shape=2 Focus). Rank 4 (+4 Focus). Scale 6 (+6 Stamina).
    # Total Focus Cost: 6. Total Stamina Cost: 6.
    print(f"Remaining Pools -> Stamina: {player.active_stamina}, Focus: {player.active_focus}")
    assert player.active_focus == 4, f"Expected 4 Focus remaining, got {player.active_focus}"
    assert player.active_stamina == 4, f"Expected 4 Stamina remaining, got {player.active_stamina}"
    assert player.beats["focus"] == 0, f"Expected 0 Focus beats left, got {player.beats['focus']}"
    
    print("\nBRUTAL Engine implementation verified.")

if __name__ == "__main__":
    test_brutal_engine()
