# Implementation Plan: Advanced Resource Types, Sub-Structures, and Refinement Workflows

We will expand the simulation engine with a high-fidelity economy, introducing sub-types of food and materials, biome-specific plant/animal resource outputs, internal sub-structures (contained inside settlements/farms rather than taking expansion rings), and advanced processing pipelines.

## User Review Required

> [!IMPORTANT]
> - **Extended Resource Taxonomy:**
>   - **Survival:** `Fruits`, `Grains`, `Vegetables`, `Roots`, `Greens`, `Spices`, `Juice`, `Poultry`, `Red Meat`, `White Meat`, `Milk`, `Eggs`, `Beer`, `Wine`, `Liquor`, `Steak`, `Chuck`, `Sausage`, `Bread`, `Cake`, `Pie`, `Water`.
>   - **Materials:** `Ore`, `Ingot`, `Leather`, `Treated_Hide`, `Wool`, `Bone`, `Fur`, `Crystal`, `Obsidian`.
>   - **Building:** `Clay`, `Hardwood`, `Softwood`, `Granite`, `Sandstone`, `Bamboo`, `Grass Fiber`, `Raw Silk`, `Flagstone`, `River Rock`, `Planks`, `Bricks`, `Paving Stone`.
> - **Biome-Specific Outputs:** Plant/animal gathering outputs will dynamically depend on the hex biome (e.g. Jungle yields Fruits/Spices, Plains yields Grains/Grass Fiber, Mountains yield Granite/Crystal/Wool).
> - **Internal Sub-Structures:**
>   - Settlements house up to **2 internal buildings per level**.
>   - Hub-villages house up to **1 internal building per level**.
>   - Level 2+ resource structures (Farms/Mines) can house **1 matching building** (e.g. Mill on a Grain Farm, Smelter on a Mine).
>   - Internal buildings include: `Mill`, `Brewery`, `Butcher`, `Bakery`, `Smelter`, `Forge`, `Workshop`, and `Apothecary`.
> - **Database Migrations:** We will add `associated_farm_id INTEGER` to the `buildings` table schema.

## Open Questions

> [!NOTE]
> - Are there specific refined food recipe requirements you want? We will implement:
>   - **Mill:** Grains -> Flour, Plants -> Oil.
>   - **Brewery:** Grains/Fruits -> Beer/Wine/Liquor.
>   - **Butcher:** Red/White Meat -> Steak/Chuck/Sausage.
>   - **Bakery:** Flour + Eggs + Milk + Spices -> Bread/Cake/Pie.

## Proposed Changes

### Core Engine

---

#### [MODIFY] [db_setup.py](file:///c:/Users/krazy/Documents/antigravity/serene-shannon/shatterlands_simulator/core_engine/db_setup.py)
1. Add `associated_farm_id INTEGER` to the `buildings` table schema.
2. In `apply_migrations(conn)`, check if `associated_farm_id` exists in the `buildings` table, and add it via `ALTER TABLE` if missing.
3. Seed construction costs for the new internal production buildings.

---

#### [MODIFY] [fractal_core.py](file:///c:/Users/krazy/Documents/antigravity/serene-shannon/shatterlands_simulator/core_engine/fractal_core.py)
1. Update `process_production_phase` to:
   - Identify the hex biome and map it to specific wild plant/animal outputs (e.g. Grains, Fruits, Red Meat).
   - Feed raw materials into active internal sub-structures (Mills, Smelters, etc.) to perform processing.
2. Update `process_population_phase` to support consuming various types of food, applying health/composure bonuses for refined foods (Steaks, Cakes, Bread).
3. Update `process_construction_ai_phase` to check internal building limits and build matching sub-structures inside Farms/Mines or Settlements/Hubs.

## Verification Plan

### Automated Tests
- Run `python autopilot.py` to simulate 30 ticks and verify:
  - Biome-specific resources are harvested correctly.
  - Sub-structures process refined materials.
  - Refined foods are consumed and apply health/composure buffs.
