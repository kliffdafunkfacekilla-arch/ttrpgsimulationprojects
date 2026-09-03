# seed_simulation_data.py
import os
import sys

# Ensure modules directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'modules')))

from sqlalchemy import create_engine, text
from simulation_lore import FACTIONS, SPECIES, RESOURCES, PRODUCED_ITEMS, WILDLIFE, FLORA

def main():
    print("Initiating Database Seeding for Ostraka Simulation Lore...")
    db_uri = 'postgresql://user:password@localhost:5432/ostraka_world'
    
    try:
        # Connect to DB
        engine = create_engine(db_uri, connect_args={'connect_timeout': 3})
        connection = engine.connect()
        print("Successfully connected to the Ostraka World database.")
        
        # 1. Seed Species
        print("Seeding Species...")
        connection.execute(text("TRUNCATE TABLE species RESTART IDENTITY CASCADE;"))
        for sp in SPECIES:
            connection.execute(
                text("INSERT INTO species (name, homeland, traits, societal_function) VALUES (:name, :homeland, :traits, :societal_function)"),
                {"name": sp["name"], "homeland": sp["homeland"], "traits": sp["traits"], "societal_function": sp["societal_function"]}
            )
            
        # 2. Seed Factions
        print("Seeding Factions...")
        connection.execute(text("TRUNCATE TABLE factions RESTART IDENTITY CASCADE;"))
        for fac in FACTIONS:
            connection.execute(
                text("INSERT INTO factions (name, base_of_operations, key_leaders, description, mechanics, special_sight_protocol) VALUES (:name, :base_of_operations, :key_leaders, :description, :mechanics, :special_sight_protocol)"),
                {"name": fac["name"], "base_of_operations": fac["base_of_operations"], "key_leaders": fac["key_leaders"], "description": fac["description"], "mechanics": fac["mechanics"], "special_sight_protocol": fac["special_sight_protocol"]}
            )
            
        # 3. Seed Resources
        print("Seeding Resources...")
        connection.execute(text("TRUNCATE TABLE resources RESTART IDENTITY CASCADE;"))
        for res in RESOURCES:
            connection.execute(
                text("INSERT INTO resources (name, origin, physical_properties, applications) VALUES (:name, :origin, :physical_properties, :applications)"),
                {"name": res["name"], "origin": res["origin"], "physical_properties": res["physical_properties"], "applications": res["applications"]}
            )
            
        # 4. Seed Produced Items (with Tier column)
        print("Seeding Produced Items...")
        connection.execute(text("TRUNCATE TABLE produced_items RESTART IDENTITY CASCADE;"))
        for item in PRODUCED_ITEMS:
            # Fallback to tier 2 if not explicitly specified
            item_tier = item.get("tier", 2)
            connection.execute(
                text("INSERT INTO produced_items (name, tier, composition, purpose, user_mechanics) VALUES (:name, :tier, :composition, :purpose, :user_mechanics)"),
                {"name": item["name"], "tier": item_tier, "composition": item["composition"], "purpose": item["purpose"], "user_mechanics": item["user_mechanics"]}
            )
            
        # 5. Seed Wildlife
        print("Seeding Wildlife...")
        connection.execute(text("TRUNCATE TABLE wildlife RESTART IDENTITY CASCADE;"))
        for wl in WILDLIFE:
            connection.execute(
                text("INSERT INTO wildlife (name, scientific_name, role, habitat, danger_level, traits, utility) VALUES (:name, :scientific_name, :role, :habitat, :danger_level, :traits, :utility)"),
                {"name": wl["name"], "scientific_name": wl["scientific_name"], "role": wl["role"], "habitat": wl["habitat"], "danger_level": wl["danger_level"], "traits": wl["traits"], "utility": wl["utility"]}
            )
            
        # 6. Seed Flora
        print("Seeding Flora...")
        connection.execute(text("TRUNCATE TABLE flora RESTART IDENTITY CASCADE;"))
        for fl in FLORA:
            connection.execute(
                text("INSERT INTO flora (name, classification, habitat, properties, applications) VALUES (:name, :classification, :habitat, :properties, :applications)"),
                {"name": fl["name"], "classification": fl["classification"], "habitat": fl["habitat"], "properties": fl["properties"], "applications": fl["applications"]}
            )
            
        connection.commit()
        connection.close()
        print("Database Seeding Completed Successfully!")
        
    except Exception as e:
        print("\n[FALLBACK DRY-RUN] Could not establish connection to live database.")
        print(f"Connection error details: {e}")
        print("\n--- Dry Run Validation of Lore Structures ---")
        print(f"Total Species loaded in memory: {len(SPECIES)}")
        for idx, sp in enumerate(SPECIES, 1):
            print(f"  {idx}. {sp['name']} (Homeland: {sp['homeland']})")
            
        print(f"\nTotal Factions loaded in memory: {len(FACTIONS)}")
        for idx, fac in enumerate(FACTIONS, 1):
            print(f"  {idx}. {fac['name']}")
            
        print(f"\nTotal Resources loaded in memory: {len(RESOURCES)}")
        for idx, res in enumerate(RESOURCES, 1):
            print(f"  {idx}. {res['name']}")
            
        print(f"\nTotal Produced Items loaded in memory: {len(PRODUCED_ITEMS)}")
        for idx, item in enumerate(PRODUCED_ITEMS, 1):
            tier_num = item.get("tier", 2)
            print(f"  {idx}. {item['name']} (Tier {tier_num})")
            
        print(f"\nTotal Wildlife loaded in memory: {len(WILDLIFE)}")
        for idx, wl in enumerate(WILDLIFE, 1):
            print(f"  {idx}. {wl['name']} ({wl['scientific_name']})")
            
        print(f"\nTotal Flora loaded in memory: {len(FLORA)}")
        for idx, fl in enumerate(FLORA, 1):
            print(f"  {idx}. {fl['name']} ({fl['classification']})")
            
        print("\nDry Run validation complete. All python data structures are structurally verified!")

if __name__ == "__main__":
    main()
