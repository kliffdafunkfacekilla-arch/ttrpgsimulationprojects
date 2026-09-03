import os
import shutil

DCSS_DIR = r"C:\Users\krazy\Desktop\SAGA\assets\Dungeon Crawl Stone Soup Full\Dungeon Crawl Stone Soup Full"
TARGET_DIR = r"C:\Users\krazy\Desktop\SAGA_Voice\frontend\assets"

def migrate():
    print("Starting asset migration for diverse biomes...")
    
    os.makedirs(os.path.join(TARGET_DIR, "backgrounds"), exist_ok=True)
    os.makedirs(os.path.join(TARGET_DIR, "structural"), exist_ok=True)
    os.makedirs(os.path.join(TARGET_DIR, "interactive_props"), exist_ok=True)
    os.makedirs(os.path.join(TARGET_DIR, "entities"), exist_ok=True)

    # 1. Backgrounds (Diverse Biomes)
    floor_map = {
        "grey_dirt0.png": "biome_underground.png",
        "sand_1.png": "biome_desert.png",
        "grass_1.png": "biome_forest.png",
        "ice_0.png": "biome_tundra.png",
        "lava0.png": "biome_volcanic.png",
        "water_1.png": "biome_aquatic.png",
        "crypt_floor_1.png": "biome_crypt.png",
        "swamp_0.png": "biome_swamp.png"
    }
    
    for src_name, dst_name in floor_map.items():
        src = os.path.join(DCSS_DIR, "dungeon", "floor", src_name)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(TARGET_DIR, "backgrounds", dst_name))
            
    # Also add "Drift Anomaly" alias
    src_drift = os.path.join(DCSS_DIR, "dungeon", "floor", "purple_crystal.png") # hypothetical or fallback
    if not os.path.exists(src_drift): src_drift = os.path.join(DCSS_DIR, "dungeon", "floor", "grey_dirt0.png")
    if os.path.exists(src_drift):
        shutil.copy(src_drift, os.path.join(TARGET_DIR, "backgrounds", "biome_drift_anomaly.png"))
        
    # 2. Structural
    wall_map = {
        "brick_brown0.png": "barricade_steel.png",
        "tree_pine.png": "obstacle_tree.png",
        "rock_wall0.png": "obstacle_boulder.png",
        "ice_wall0.png": "obstacle_ice.png"
    }
    for src_name, dst_name in wall_map.items():
        src = os.path.join(DCSS_DIR, "dungeon", "wall", src_name)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(TARGET_DIR, "structural", dst_name))
            
    # 3. Props
    prop_map = {
        ("dungeon", "altars", "sif_munin.png"): "prop_console.png",
        ("dungeon", "altars", "vehumet.png"): "prop_core_regulator.png",
        ("item", "misc", "box.png"): "prop_crate_heavy.png",
        ("item", "potion", "ruby.png"): "prop_health_potion.png"
    }
    for src_tuple, dst_name in prop_map.items():
        src = os.path.join(DCSS_DIR, *src_tuple)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(TARGET_DIR, "interactive_props", dst_name))

    # 4. Entities
    entity_map = {
        ("misc", "human.png"): "npc_cultist.png",
        ("misc", "draconian_red.png"): "npc_dragon.png",
        ("misc", "goblin.png"): "npc_goblin.png",
        ("misc", "orc.png"): "npc_orc.png"
    }
    for src_tuple, dst_name in entity_map.items():
        src = os.path.join(DCSS_DIR, *src_tuple)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(TARGET_DIR, "entities", dst_name))

    print("Migration complete. Assets pulled for varied biome types.")

if __name__ == "__main__":
    migrate()
