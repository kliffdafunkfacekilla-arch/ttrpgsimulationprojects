# Goal Description

The world-building and setup features will be integrated directly into the existing Pygame desktop application (`main.py` and `ui/viewer.py`), avoiding any separate web servers or external dashboard apps. 

The Pygame desktop application will support:
1. **Interactive Map Painting**: Clicking and dragging on cells with adjustable brush radius and power. Brush modes include:
   - **Elevation Brush**: Up (increase height), Down (decrease height), Smooth (blend with neighbors), and Level (flatten to active height).
   - **Territory & Biome Painter**: Color-palette selection to paint Factions, Biomes, Cults, Fringe Groups, and Flora/Fauna densities.
   - **Resource & Node Placer**: Click to place resource nodes, chaos nodes, and convergence locations.
   - **Elevation Heatmap Loader**: Reads a local grayscale image (e.g. `heightmap.png`), scales it to map coordinates, and samples pixel brightness to set cell elevations.
2. **Fullscreen Config Overlay (Settings Dialog)**: Pressed key (e.g. `Tab` or button click) toggles a premium modal editor panel in Pygame containing:
   - **Prevailing Winds & Temperatures**: Slider controls for the 7 latitudinal zones (Zone 0 to 6) to cycle wind direction (8 directions) and wind speed, plus min/max temperature limits.
   - **Custom Calendar**: Editable calendar settings (days per year, month names, season bounds, moon phases).
   - **Entity Manager & Simulator Rules**: Controls to add/edit factions, fringe groups, flora, fauna, building costs, travel costs per biome, military stats, and namebases.
3. **Data Storage & Syncing**: Loads initial default settings from `default_settings.json`, edits/saves custom profiles to `world_settings.json`, and commits changes directly to `ttrpg_world.db` to feed the simulation model.

---

## User Review Required

> [!IMPORTANT]
> **Pygame Native Config UI Layout**
> The Configuration Editor will render as a fullscreen dark overlay (with transparency and clean buttons) inside the Pygame main loop, bypassing map rendering while open. It will use a tabbed interface (Physics, Calendar, Entities, Rules) for clean organization.
> 
> **Brush Painting Mode**
> The left sidebar will contain an "Edit Mode" toggle. When active, mouse clicks and drags on the map viewport will execute the active brush tool (Up, Down, Smooth, Level, Paint Faction, Paint Biome, Paint Cult, etc.) based on the brush radius and power sliders.

> [!NOTE]
> **Data Fallback**
> We will create `default_settings.json` containing all default values for calendar days, seasons, moon phases, wind zones, temperatures, recipes, and paragon namebases. The simulator will load data from `world_settings.json` if it exists, falling back to `default_settings.json`. No data is hard-coded.

---

## Proposed Changes

### Configuration Data Layer

#### [NEW] [default_settings.json](file:///C:/Users/krazy/worldsim/omnis-generator/default_settings.json)
- Store all default settings (seasons, days, months, moons, 7 wind/temp zones, default entities, building requirements, travel costs, military units, namebases).

---

### Python Simulator Component

#### [MODIFY] [simulation_engine.py](file:///C:/Users/krazy/worldsim/omnis-generator/simulation_engine.py)
- Load calendar settings, prevailing winds, temp limits, and travel costs from `world_settings.json` (falling back to `default_settings.json`).
- Apply latitudinal wind zone directions and temperatures to weather calculation instead of static weather probabilities.

#### [MODIFY] [modules/calendar_manager.py](file:///C:/Users/krazy/worldsim/omnis-generator/modules/calendar_manager.py)
- Load days per year, month names, moon cycles, and season spans dynamically from JSON settings.

#### [MODIFY] [modules/weather_system.py](file:///C:/Users/krazy/worldsim/omnis-generator/modules/weather_system.py)
- Calculate cell weather factoring local wind zone direction, temperature limits, and global precipitation modifier from JSON settings.

#### [MODIFY] [modules/rules_engine.py](file:///C:/Users/krazy/worldsim/omnis-generator/modules/rules_engine.py)
- Load namebases, paragon alignment ranges, building requirements, and travel costs dynamically from JSON settings.

---

### Pygame Setup & GUI Component

#### [MODIFY] [ui/viewer.py](file:///C:/Users/krazy/worldsim/omnis-generator/ui/viewer.py)
- **Edit Mode Implementation**:
  - Add an "Editor" sidebar tab with sliders for brush radius (1 to 20 cells) and brush power/strength (1 to 10), and action buttons (Up, Down, Smooth, Level, Factions, Biomes, Cults, Fringe, Resources, Nodes).
  - Track active palette selection (e.g. which Faction/Biome/Cult/Resource is selected for painting).
  - Add a "Load heightmap.png" button. Reads `heightmap.png` using Python's `Pillow` library, scales it, samples brightness at cell centroids, and updates elevations.
- **Mouse Drag Painting**:
  - Intercept mouse clicks/moves in the viewport while in Edit Mode.
  - Implement a fast spatial query to find cells within the brush screen-radius of the mouse cursor.
  - Apply the brush operation (adjust elevation up/down, smooth heights, paint faction index, set biome name, place node).
- **Fullscreen Config Overlay**:
  - Implement `draw_config_overlay()` which renders tabbed forms (Physics, Calendar, Entities, Rules) for winds, temperatures, calendar cycles, custom factions, and travel costs.
  - Intercept mouse clicks on sliders, checkboxes, and input fields while the overlay is open.
  - Write updated settings back to `world_settings.json` and sync the database/Mesa model immediately.

#### [MODIFY] [main.py](file:///C:/Users/krazy/worldsim/omnis-generator/main.py)
- Ensure the viewer launches in standard windowed mode and immediately starts the editor tools natively, checking for `heightmap.png` if loaded.

---

## Verification Plan

### Automated Tests
- Create `scratch/test_settings_loader.py` to:
  1. Verify `default_settings.json` and `world_settings.json` parse correctly.
  2. Test that `CalendarManager` and `calculate_weather` successfully load and apply winds and custom months.
  - Command: `python scratch/test_settings_loader.py`

### Manual Verification
1. Launch `python main.py`.
2. Toggle the "Editor" sidebar tab, adjust brush radius, select "Biomes", pick "Reef", and paint a coral reef zone on the ocean.
3. Select "Elevation: Up" brush and paint a mountain ridge, verifying that the colors shift to heights.
4. Drop `heightmap.png` in the directory, click "Load Heatmap Image", and confirm elevations are imported.
5. Click "Global Settings" to open the config overlay. Change Zone 1 winds to NW and the calendar to 15 months. Click "Apply & Sync".
6. Verify ticks advance under the new calendar and winds!
