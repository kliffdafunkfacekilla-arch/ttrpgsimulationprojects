# Walkthrough: Data-Driven Refactoring of Fractal Core Simulation

I have successfully refactored the metabolic loop in `fractal_core.py` to be modular, testable, and data-driven by integrating structured lookup tables in SQLite.

## Changes Made

### 1. Database Schema Updates & Migrations
- **File modified:** [db_setup.py](file:///c:/Users/krazy/Documents/antigravity/serene-shannon/shatterlands_simulator/core_engine/db_setup.py)
  - Created a new `apply_migrations(conn)` function to safely upgrade existing databases without wiping active world states.
  - Added the `integrity` column (default 100.0) to the `farms` table schema.
  - Added new `structure_costs` and `production_recipes` tables, seeding them with initial structure costs, upkeeps, and refinement recipes.

### 2. Decoupled and Modular Metabolic Loop
- **File modified:** [fractal_core.py](file:///c:/Users/krazy/Documents/antigravity/serene-shannon/shatterlands_simulator/core_engine/fractal_core.py)
  - Split the monolith `process_cluster_fidelity` loop into five distinct, specialized system functions:
    1. `process_guards_upkeep`: Calculates guards based on population, handles wealth and resource equipping, updates security, and processes desertions.
    2. `process_maintenance_phase`: Applies structure upkeep costs dynamically retrieved from the `structure_costs` table. Insufficient wealth results in integrity decay and eventual demolition.
    3. `process_production_phase`: Manages node gathering, structures harvesting, rare resource discovery, and recipe refinement (e.g. Ore -> Ingot) using the `production_recipes` table.
    4. `process_population_phase`: Decouples population math from gathering, dealing with food consumption, surplus growth, and starvation/riots/anarchy.
    5. `process_construction_ai_phase`: Upgrades and constructs structures based on costs dynamically retrieved from `structure_costs`.

### 3. Backups Maintained
- Saved the original engine database setup script to `backups/db_setup_backup/db_setup.py`.
- Saved the original metabolic loop code to `backups/fractal_core_backup/fractal_core.py`.

---

## Verification Results

- Executed `apply_migrations` on the active `world_state.db` database and verified the lookup tables (`structure_costs` and `production_recipes`) were correctly created and seeded.
- Ran `python autopilot.py` to advance the simulation successfully from tick 729 to 759.
- Verified that all systems operate correctly, logging guard upkeep desertions and discovering rare Mithril deposits on schedule.
