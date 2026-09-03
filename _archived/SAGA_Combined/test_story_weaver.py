import os
import json
import sqlite3
from contextlib import closing
from story_manager.world_db import WorldDB
from story_manager.reactive_seeds import SeedManager
from story_manager.campaign_weaver import CampaignWeaver

def test_story_weaver():
    # 1. Setup DB
    print("--- 1. Testing SQLite DB and Seed Creation ---")
    db_path = "test_world.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        
    db = WorldDB(db_path)
    
    # Inject a test location
    with closing(db._get_connection()) as conn:
        conn.execute("INSERT INTO locations (id, name, base_lore) VALUES ('loc_1', 'The Sunken Market', 'A damp, claustrophobic bazaar built in a drained canal.')")
        conn.commit()
        
    manager = SeedManager(db)
    campaign = CampaignWeaver(db)
    
    # 2. Spawn a seed
    seed_id = manager.create_seed(
        location_id="loc_1", 
        origin_action="Stole a plasma coil from the junk merchant.", 
        subtle_description="A junk merchant is frantically searching his stall, muttering angrily to himself.",
        target_entity="Junk Merchant",
        urgency=2
    )
    
    seeds = manager.get_active_seeds("loc_1")
    assert len(seeds) == 1, "Failed to retrieve seed."
    print(f"Spawned Seed: {seeds[0].subtle_description} (Urgency: {seeds[0].urgency_ticks})")

    # 3. Tick Simulation (Escalation)
    print("\n--- 2. Testing Simulation Escalation ---")
    manager.tick_simulation() # Drops to 1
    manager.tick_simulation() # Drops to 0 -> Mutates to Escalated
    
    seeds = manager.get_active_seeds("loc_1")
    assert seeds[0].status == "Escalated", "Seed failed to mutate."
    print(f"Mutated Seed: {seeds[0].subtle_description} (Status: {seeds[0].status})")

    # 4. Campaign Weaver Escalation
    print("\n--- 3. Testing Campaign Weaver ---")
    # Resolve 5 seeds to trigger Act II
    for i in range(5):
        campaign.ingest_seed_resolution(
            seed_data={"title": f"Test Node {i}", "category": "Violence"},
            player_choice_outcome=f"Killed target {i}"
        )
        
    act = campaign.get_campaign_act()
    assert act == 2, f"Expected Campaign Act to shift to 2, got {act}"
    print(f"Campaign organically shifted to Act {act}!")
    
    history = campaign.get_resolved_history()
    print(f"History length: {len(history)} elements aggregated for the Director.")
    assert len(history) == 5, "History aggregation failed."

    # 5. Cleanup
    # In order to safely delete the file, ensure all instances of CampaignWeaver / SeedManager 
    # haven't left unclosed connections. 
    # They currently use `with self.db._get_connection() as conn:` which doesn't close the connection.
    # We will close the connection cleanly.
    
    del manager
    del campaign
    del db
    
    print("\nStory Weaver & Campaign Spine successfully verified!")

if __name__ == "__main__":
    test_story_weaver()
