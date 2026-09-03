from rules_engine.character_sheet import CharacterSheet
from rules_engine.clash_calculator import ClashCalculator

def test_combat():
    # Setup Player
    player = CharacterSheet("Ael Thorne")
    player.stats["finesse"] = 8
    player.stats["intuition"] = 4
    # Mock a finesse weapon (Body Variant)
    class MockWeapon:
        def __init__(self):
            self.name = "Rapier of the Wind"
            self.modifier = 2
            self.stat_type = "finesse" # Body variant
    player.inventory.slots["weapon"] = MockWeapon()

    # Setup Enemy
    enemy = CharacterSheet("Cultist Guard")
    enemy.stats["endurance"] = 5
    enemy.stats["logic"] = 3
    # Mock medium armor (Mind Variant)
    class MockArmor:
        def __init__(self):
            self.name = "Cultist Mail"
            self.armor_mod = 1
            self.stat_type = "logic" # Mind variant
    enemy.inventory.slots["body"] = MockArmor()

    calc = ClashCalculator()
    calc.register_entity(player)
    calc.register_entity(enemy)

    print("--- FIRST ATTACK (Enemy gets Active Defense) ---")
    res1 = calc.resolve_attack("Ael Thorne", "Cultist Guard", "attack")
    print(res1["narrative_hint"])
    
    print("\n--- SECOND ATTACK (Enemy is out of Active Defenses) ---")
    res2 = calc.resolve_attack("Ael Thorne", "Cultist Guard", "attack")
    print(res2["narrative_hint"])

if __name__ == "__main__":
    test_combat()
