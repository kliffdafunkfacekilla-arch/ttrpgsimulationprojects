# Task List: Faction Capitals, Terrain Tiling, and Real-time Structure Placement

- `[x]` Phase 1: Database and Schema Setup
  - `[x]` Add `is_capital` column to `macro_groups` table in `database.py`
  - `[x]` Update `generate_world` to write `is_capital` for generated capitals in `map_generator.py`
  - `[x]` Update `import_ostraka_map` to write `is_capital` for Ostraka capitals in `map_generator.py`
  - `[x]` Load `is_capital` in `FactionAgent` in `simulation_engine.py`

- `[x]` Phase 2: Pygame Viewer Updates
  - `[x]` Implement dynamic centering based on cell coordinate bounding box in `viewer.py`
  - `[x]` Modify `draw_textured_polygon` in `viewer.py` to stretch single terrain texture to cell bounding box and mask it (preventing tiling/repetition inside cell)
  - `[x]` Remove pre-scaling in `render_background_map` and pass raw textures directly to `draw_textured_polygon` in `viewer.py`
  - `[x]` Fix keep drawing check: draw castle `(10, 13)` only on cells with `is_capital == 1`, and units on other cells in `viewer.py`
  - `[x]` Render Farms, Mines, Barracks, and Watchtowers at offset positions around cell center when `zoom >= 10.0` in `viewer.py`
  - `[x]` Set `is_capital = 0` when cycling cell faction ownership in `viewer.py`

- `[x]` Phase 3: Verification
  - `[x]` Run test import script to verify database loads cells, edges, and capitals successfully
  - `[x]` Launch `main.py` and manually verify visual corrections, zooming, structure placement, and ticks
