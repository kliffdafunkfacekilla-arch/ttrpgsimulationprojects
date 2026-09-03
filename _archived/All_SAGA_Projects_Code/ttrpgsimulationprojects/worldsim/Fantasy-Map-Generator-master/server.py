from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import sys
import os

# Import our engine modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from scheduler import (
    run_simulation_tick, 
    get_all_macro_groups, 
    ingest_map_data, 
    get_global_grid, 
    get_global_trade_routes, 
    get_global_resource_nodes,
    get_saga_logs,
    get_and_clear_territory_changes,
    get_all_fringe_groups
)
from modules.ecology_system import ALL_FAUNA, ALL_FLORA
from modules.ecology_system import ALL_FAUNA, ALL_FLORA
from map_parser import load_azgaar_geometry
from map_generator import MapGenerator

app = FastAPI(title="Omnis World Engine API")

# Allow UI to connect locally
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class InjectPayload(BaseModel):
    location: str
    event_type: str
    amount: float

class GodModePayload(BaseModel):
    faction_id: int
    updates: Dict[str, Any]

@app.get("/api/geometry")
def get_geometry():
    """Returns the parsed Azgaar GeoJSON geometry."""
    return load_azgaar_geometry()

@app.get("/api/state")
def get_state():
    """Returns the current LIVE state of the world from memory."""
    groups = get_all_macro_groups()
    grid = get_global_grid()
    trade_routes = get_global_trade_routes()
    resource_nodes = get_global_resource_nodes()
    logs = get_saga_logs()
    territory_changes = get_and_clear_territory_changes()
    
    factions_data = []
    
    for g in groups:
        factions_data.append({
            "id": g.id,
            "name": g.name,
            "population": g.population,
            "chaos": int(g.chaos_level * 100),
            "physical": int(g.physical_well_being * 100),
            "mental": int(g.mental_well_being * 100),
            "crime": int(g.crime_level * 100),
            "discontent": int(g.discontent * 100),
            "farms": g.farms_count,
            "kelp_farms": getattr(g, "kelp_farms_count", 0),
            "cult_infiltration": getattr(g, "cult_infiltration", 0.0),
            "magistar_id": getattr(g, "magistar_id", "Unknown"),
            "paragon": g.paragon["name"] if g.paragon else "None",
            "paragon_stats": g.paragon["stats"] if g.paragon else None,
            "military_power": int(
                g.population * 0.05 + 
                g.barracks_count * 50.0 + 
                g.walls_count * 30.0 + 
                g.watchtowers_count * 20.0
            ),
            "warden_presence": min(g.chaos_level * 0.35, 0.4), # Max 40% land claimed by wardens
            "dominant_fauna": max(
                [{"name": f.replace("fauna_", "").replace("_", " ").title(), "pop": getattr(g, f, 0.0)} for f in ALL_FAUNA],
                key=lambda x: x["pop"]
            ) if any(getattr(g, f, 0.0) > 0 for f in ALL_FAUNA) else None,
            "dominant_flora": max(
                [{"name": f.replace("flora_", "").replace("_", " ").title(), "pop": getattr(g, f, 0.0)} for f in ALL_FLORA],
                key=lambda x: x["pop"]
            ) if any(getattr(g, f, 0.0) > 0 for f in ALL_FLORA) else None
        })
        
    raw_fringe = get_all_fringe_groups()
    fringe_groups_data = []
    
    color_map = {
        "criminal_syndicate": "#fb923c",
        "sky_miners": "#38bdf8",
        "sky_pirates": "#818cf8",
        "financial_syndicate": "#fbbf24",
        "smuggler_fleet": "#f43f5e",
        "deep_marine_syndicate": "#0284c7",
        "mercenary_guild": "#1f2937",
        "riverine_black_market": "#059669",
        "assassin_guild": "#10b981"
    }

    if isinstance(raw_fringe, dict):
        for name, data in raw_fringe.items():
            if data.get("population", 0) > 0:
                fringe_groups_data.append({
                    "name": name,
                    "target": data["host_faction"],
                    "color": color_map.get(data.get("type"), "#ffffff"),
                    "population": data["population"],
                    "heat": data["heat"],
                    "influence": data.get("influence", 0.1)
                })

    from scheduler import _GLOBAL_ECOLOGY_GRID
    
    # Compress the ecology grid so we don't send 10,000 massive objects.
    # We only send cells that have significant flora or fauna.
    compressed_ecology = {}
    for cid, cell in _GLOBAL_ECOLOGY_GRID.items():
        entry = {}
        if cell.get("flora_pop", 0) > 10.0:
            entry["f"] = cell["flora"]
        if cell.get("fauna_pop", 0) > 10.0:
            entry["a"] = cell["fauna"]
        if entry:
            compressed_ecology[cid] = entry

    return {
        "status": "success",
        "data": {
            "time": "Sim Day X",
            "chaos_level": 42.0,
            "factions": factions_data,
            "fringe_groups": fringe_groups_data,
            "ecology_grid": compressed_ecology,
            "grid": grid,
            "trade_routes": trade_routes,
            "resource_nodes": resource_nodes,
            "logs": logs,
            "territory_changes": territory_changes
        }
    }

@app.post("/api/tick")
def execute_tick():
    """Advances the simulation by 1 step (24 hours)."""
    try:
        run_simulation_tick(24)
        return {"message": "Tick complete. 24 hours advanced."}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/map/generate")
def generate_custom_map():
    """Procedurally generates a new Grid map."""
    generator = MapGenerator(width=100, height=100)
    grid_data = generator.generate_base_grid(land_mass_percent=0.45)
    return {"status": "success", "grid": grid_data}

@app.post("/api/db/update")
def god_mode_update(payload: GodModePayload):
    """Directly overrides live simulation state memory."""
    groups = get_all_macro_groups()
    target = next((g for g in groups if g.id == payload.faction_id), None)
    
    if not target:
        raise HTTPException(status_code=404, detail="Faction not found")

    for key, value in payload.updates.items():
        if hasattr(target, key):
            setattr(target, key, value)
        elif key in target.inventory:
            target.inventory[key] = value

    return {"message": f"Faction {target.name} successfully updated via God Mode."}

@app.post("/api/map/save")
def save_map_layout(payload: dict):
    """Saves the map data (from Grid or Native Azgaar) to the DB/Memory."""
    
    if "azgaar_data" in payload:
        az_data = payload["azgaar_data"]
        states_count = len(az_data.get("states", []))
        burgs_count = len(az_data.get("burgs", []))
        
        # Import and run the actual ingestion
        from scheduler import ingest_azgaar_data
        updated = ingest_azgaar_data(az_data)
        
        print(f"OMNIS ENGINE: Ingested {states_count} Factions and {burgs_count} Settlements. Matched & Updated {updated} Lore Factions.")
        return {"message": f"Successfully synced {updated} Factions from Azgaar into Omnis Engine!"}
        
    elif "grid" in payload:
        from scheduler import ingest_map_data
        # Fallback to the old grid parser if needed
        ingest_map_data(payload["grid"])
        return {"message": "Custom Grid Layout successfully parsed!"}
        
    return {"message": "Payload format not recognized."}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
