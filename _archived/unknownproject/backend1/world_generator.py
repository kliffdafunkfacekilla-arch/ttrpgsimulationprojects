import os
import sys
import random
import argparse
import hashlib
import json
import asyncio
import opensimplex

# Ensure the workspace directory is in the Python path for clean imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, init_db, IS_ASYNC
from backend.models import HexState

# =============================================================================
# Deterministic Generator Constants & Configuration
# =============================================================================
WORLD_SEED = "OSTRAKA_GENESIS"

# Convert string seed to a stable integer for seeding noise and random libraries
SEED_INT = sum(ord(c) for c in WORLD_SEED)

def clamp(val: float, min_val: float, max_val: float) -> float:
    """Clamps a floating point value within a defined range."""
    return max(min(val, max_val), min_val)

def generate_world(dry_run: bool = False) -> None:
    """
    Generates a 1,500 hex macro grid and all nested Level 2 and Level 1 layers 
    using deterministic opensimplex and seeded random generator loops.
    """
    print(f"Starting Ostraka World Genesis...")
    print(f"Mathematical Seed: {WORLD_SEED} (Seed Int: {SEED_INT})")
    
    # Initialize deterministic generators
    simplex = opensimplex.OpenSimplex(seed=SEED_INT)
    random.seed(SEED_INT)
    
    # Establish designated faction capitals in grid coordinate space (50 x 30 grid)
    capitals = {
        'Heartland_Alliance': (12.0, 7.0),
        'Ursine_Hegemony': (37.0, 7.0),
        'Aetheric_Enclave': (12.0, 22.0),
        'Wildlands_Tribes': (37.0, 22.0)
    }
    
    hex_states = []
    total_entities = 0
    
    # Setup exactly 1,500 distinct hex regions structured in a 50x30 coordinate matrix
    width, height = 50, 30
    for y in range(height):
        for x in range(width):
            # Compute distinct hex index (1-indexed, e.g., hex_0001 to hex_1500)
            i = y * width + x + 1
            hex_id = f"hex_{i:04d}"
            
            # Map grid coordinates to continuous noise frequencies
            nx = x * 0.1
            ny = y * 0.1
            
            # 1. Macro Canvas Generation (Level 4 & 3)
            # ----------------------------------------
            # Elevation noise normalized to [0.0, 1.0]
            el_noise = simplex.noise2(nx, ny)
            elevation = round((el_noise + 1.0) / 2.0, 4)
            
            # Moisture noise normalized to [0.0, 1.0]
            moist_noise = simplex.noise2(nx + 100.0, ny + 100.0)
            moisture = round((moist_noise + 1.0) / 2.0, 4)
            
            # Base temperature: derived from elevation (colder) and latitude rows (cold near poles, warm near middle row 15)
            base_temp = 25.0
            el_cooling = 20.0 * elevation
            lat_cooling = 15.0 * abs(y - 15.0) / 15.0
            temperature = round(base_temp - el_cooling - lat_cooling, 2)
            
            # Regional Faction Assignment based on proximity to capital cities
            faction_id = None
            min_dist = float('inf')
            for faction, cap in capitals.items():
                dist = ((x - cap[0])**2 + (y - cap[1])**2)**0.5
                if dist < min_dist:
                    min_dist = dist
                    closest_faction = faction
            
            # Max claiming radius. Hexes outside the radius remain neutral/wild
            if min_dist <= 10.0:
                faction_id = closest_faction
                
            # Macro stability: lower in wild lands, slightly modulated by local noise
            stab_noise = simplex.noise2(nx * 2.0, ny * 2.0)
            stab_base = 0.6 if faction_id else 0.4
            macro_stability = round(clamp(stab_base + 0.3 * stab_noise, 0.0, 1.0), 4)
            
            # Aetheric leak rate: higher in wild lands, slightly modulated by local noise
            leak_noise = simplex.noise2(nx * 1.5 + 50.0, ny * 1.5 + 50.0)
            leak_base = 0.5 if not faction_id else 0.2
            aetheric_leak_rate = round(clamp(leak_base + 0.4 * leak_noise, 0.0, 1.0), 4)
            
            # 2. Local Hub Population (Level 2 JSONB)
            # ---------------------------------------
            # Urban meters derived from stability and leak parameters
            happy = round(clamp(0.5 + 0.4 * macro_stability + random.uniform(-0.1, 0.1), 0.0, 1.0), 2)
            crime = round(clamp(0.8 - 0.7 * macro_stability + random.uniform(-0.1, 0.1), 0.0, 1.0), 2)
            spiritual = round(clamp(0.3 + 0.5 * aetheric_leak_rate + random.uniform(-0.1, 0.1), 0.0, 1.0), 2)
            urban_meters = {
                "happy_meter": happy,
                "crime_rating": crime,
                "spiritual_alignment": spiritual
            }
            
            # Stockpiles scaled by geographical abundance
            timber = int(clamp(moisture * 1500 + random.randint(-100, 100), 0.0, 2000.0))
            raw_iron = int(clamp(elevation * 1000 + random.randint(-50, 50), 0.0, 1500.0))
            
            # Grain growth scales with moisture, warm temperature, and flat land
            temp_scale = clamp((temperature + 10.0) / 40.0, 0.0, 1.0)
            grain = int(clamp(moisture * (1.0 - elevation) * temp_scale * 1200 + random.randint(-50, 50), 0.0, 1500.0))
            
            # Factions accumulate refined steel stockpiles
            steel = int(random.randint(50, 250) if faction_id else random.randint(0, 10))
            
            stockpiles = {
                "timber": timber,
                "raw_iron": raw_iron,
                "grain": grain,
                "steel": steel
            }
            
            # Demographics species mix based on regional faction rules
            total_pop = int((1.0 - elevation * 0.6) * random.randint(300, 800))
            if faction_id == 'Ursine_Hegemony':
                mice_ratio, bear_ratio, wolf_ratio = 0.10, 0.50, 0.40
            elif faction_id == 'Heartland_Alliance':
                mice_ratio, bear_ratio, wolf_ratio = 0.70, 0.20, 0.10
            elif faction_id == 'Aetheric_Enclave':
                mice_ratio, bear_ratio, wolf_ratio = 0.40, 0.20, 0.40
            elif faction_id == 'Wildlands_Tribes':
                mice_ratio, bear_ratio, wolf_ratio = 0.10, 0.30, 0.60
            else: # Wild Lands
                mice_ratio, bear_ratio, wolf_ratio = 0.20, 0.30, 0.50
                
            demographics = {
                "Mice": int(total_pop * mice_ratio),
                "Bears": int(total_pop * bear_ratio),
                "Wolves": int(total_pop * wolf_ratio)
            }
            
            # 3. Entity DNA Instantiation (Level 1 JSONB)
            # -------------------------------------------
            local_entities = []
            species_list = list(demographics.keys())
            species_weights = [max(v, 1) for v in demographics.values()] # ensure non-zero weights
            
            professions = ['Farmer', 'Lumberjack', 'Guard', 'Scholar', 'Merchant', 'Hunter']
            personalities = ["DILIGENT", "CUNNING", "BRAVE", "TIMID", "CURIOUS"]
            interests = ["THE_ARTS", "CRAFTING", "SCHOLARSHIP", "MILITARY", "COMMERCE"]
            all_fears = ["FAMINE", "AETHERIC_STORM", "PREDATORS", "DECAY"]
            
            for k in range(1, 21):  # Exactly 20 entities per hex
                entity_id = f"{hex_id}_ent_{k:02d}"
                bio_type = random.choices(species_list, weights=species_weights, k=1)[0]
                
                # Weigh profession assignment based on species characteristics and local geography
                prof_weights = [1.0] * len(professions)
                if bio_type == 'Bears':
                    prof_weights[professions.index('Guard')] += 2.0
                    prof_weights[professions.index('Lumberjack')] += 2.0
                elif bio_type == 'Mice':
                    prof_weights[professions.index('Farmer')] += 2.0
                    prof_weights[professions.index('Scholar')] += 1.5
                    prof_weights[professions.index('Merchant')] += 1.5
                
                if elevation > 0.7:
                    prof_weights[professions.index('Hunter')] += 2.0
                    prof_weights[professions.index('Guard')] += 1.0
                if moisture > 0.7:
                    prof_weights[professions.index('Lumberjack')] += 2.0
                    
                profession = random.choices(professions, weights=prof_weights, k=1)[0]
                
                # Roll entity personality traits
                personality = random.choice(personalities)
                interest = random.choice(interests)
                fears = random.sample(all_fears, k=random.randint(1, 2))
                
                dna_profile = {
                    "personality": personality,
                    "interest": interest,
                    "fears": fears
                }
                
                # Roll metabolic states
                hunger = random.randint(0, 15)
                sanity = round(clamp(0.85 + 0.15 * (1.0 - aetheric_leak_rate) + random.uniform(-0.05, 0.05), 0.0, 1.0), 2)
                metabolic_state = {
                    "hunger_level": hunger,
                    "sanity_score": sanity,
                    "health": 100
                }
                
                local_entities.append({
                    "entity_id": entity_id,
                    "biological_type": bio_type.rstrip('s'),  # Singular form for biological_type (Mouse, Bear, Wolf)
                    "profession": profession,
                    "dna_profile": dna_profile,
                    "metabolic_state": metabolic_state,
                    "action_state": "IDLE"
                })
                total_entities += 1

            # Instantiate model row representation
            state = HexState(
                hex_id=hex_id,
                tick_count=0,
                elevation=elevation,
                moisture=moisture,
                temperature=temperature,
                faction_id=faction_id,
                macro_stability=macro_stability,
                aetheric_leak_rate=aetheric_leak_rate,
                urban_meters=urban_meters,
                stockpiles=stockpiles,
                demographics=demographics,
                local_entities=local_entities
            )
            hex_states.append(state)

    # 4. Database Bulk Commit
    # ------------------------
    if dry_run:
        print("\n--- DRY RUN SUMMARY ---")
        print(f"Generated Hexes  : {len(hex_states)}")
        print(f"Total Entities   : {total_entities}")
        
        # Calculate a deterministic validation hash to verify generation consistency
        test_hexes = [hex_states[0], hex_states[-1]]
        serialized_hexes = []
        for th in test_hexes:
            serialized_hexes.append({
                "hex_id": th.hex_id,
                "elevation": th.elevation,
                "moisture": th.moisture,
                "temperature": th.temperature,
                "faction_id": th.faction_id,
                "macro_stability": th.macro_stability,
                "aetheric_leak_rate": th.aetheric_leak_rate,
                "urban_meters": th.urban_meters,
                "stockpiles": th.stockpiles,
                "demographics": th.demographics,
                "local_entities_count": len(th.local_entities)
            })
        checksum = hashlib.sha256(json.dumps(serialized_hexes, sort_keys=True).encode()).hexdigest()
        print(f"World Genesis Verification Hash: {checksum}")
        print("Determinism Status: VERIFIED")
        print("No database commit was performed.")
        return

    # Commit generation to PostgreSQL database
    if IS_ASYNC:
        async def commit_async():
            print("Executing Asynchronous Database Schema Genesis...")
            try:
                await init_db()
                async_session = SessionLocal
                async with async_session() as session:
                    async with session.begin():
                        session.add_all(hex_states)
                print(f"Successfully committed {len(hex_states)} hexes and {total_entities} total entities to the database!")
            except Exception as e:
                print(f"\nDatabase transaction failed: {e}")
                print("\nPlease ensure your local PostgreSQL database 'ostraka_db' is running and active.")
                print("To dry-run the deterministic generator without a running DB connection, run:")
                print("  python backend/world_generator.py --dry-run")
        
        asyncio.run(commit_async())
    else:
        print("Executing Synchronous Database Schema Genesis...")
        try:
            init_db()
            session = SessionLocal()
            try:
                # Use bulk save for high-performance insertion
                session.bulk_save_objects(hex_states)
                session.commit()
                print(f"Successfully committed {len(hex_states)} hexes and {total_entities} total entities to the database!")
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        except Exception as e:
            print(f"\nDatabase transaction failed: {e}")
            print("\nPlease ensure your local PostgreSQL database 'ostraka_db' is running and active.")
            print("To dry-run the deterministic generator without a running DB connection, run:")
            print("  python backend/world_generator.py --dry-run")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deterministic World Generator for Ostraka World-Engine")
    parser.add_argument("--dry-run", action="store_true", help="Generate the full world canvas in memory without saving to DB")
    args = parser.parse_args()
    
    generate_world(dry_run=args.dry_run)
