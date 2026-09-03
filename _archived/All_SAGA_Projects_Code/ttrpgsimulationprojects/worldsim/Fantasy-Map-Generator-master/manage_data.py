# manage_data.py
import streamlit as st
import pandas as pd
import sys
import os
import glob
import random
import geopandas as gpd
import matplotlib.pyplot as plt

# Ensure modules directory is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'modules')))

from sqlalchemy import create_engine, text
from simulation_lore import FACTIONS, SPECIES, WILDLIFE, FLORA
from rules_engine import calculate_tech_level, get_unlocked_transport, get_unlocked_buildings, process_well_being_tick, process_living_world_tick, generate_paragon, calculate_alignment
from calendar_manager import CalendarManager
from magistar_plugin import calculate_reality_spike
from weather_system import calculate_weather

def ingest_azgaar_map(azgaar_data):
    """
    Called by server.py when the user clicks 'Sync Map to Python'.
    Parses Azgaar's native states and burgs to update our 17 Lore Factions.
    """
    states = azgaar_data.get("states", [])
    burgs = azgaar_data.get("burgs", [])
    
    # Create a mapping of State ID -> Faction Name
    state_id_to_name = {s["id"]: s["name"] for s in states}
    
    # Map Burgs to their State ID
    burgs_by_state = {}
    for b in burgs:
        sid = b["state"]
        if sid not in burgs_by_state:
            burgs_by_state[sid] = []
        burgs_by_state[sid].append(b["population"])
        
    import streamlit as st
    
    # Update the macro_groups if they match by name
    updated_count = 0
    if "macro_groups" in st.session_state:
        for group in st.session_state.macro_groups:
            # Find matching state by name
            matched_state_id = next((sid for sid, name in state_id_to_name.items() if name.lower() == group["name"].lower()), None)
            
            if matched_state_id is not None:
                # We found the faction on the map!
                # Update its settlements and population
                faction_burgs = burgs_by_state.get(matched_state_id, [])
                if faction_burgs:
                    # Azgaar population is abstract, usually x1000 or similar. We'll just take it as is.
                    # Or we calculate scale based on our lore. Let's just set the array.
                    group["settlements"] = [p * 1000 for p in faction_burgs] 
                    group["population"] = sum(group["settlements"])
                    updated_count += 1
    
    return updated_count

st.set_page_config(page_title="Ostraka Simulator Console", layout="wide")

st.title("🛡️ Ostraka Shatterlands Management Console")
st.markdown("A streamlined control panel to manage Simulation States, Species/Cultures, Wildlife, and Map Ingestions.")

# Setup DB connection status
DB_URI = 'postgresql://user:password@localhost:5432/ostraka_world'
db_active = False

try:
    engine = create_engine(DB_URI, connect_args={'connect_timeout': 2})
    with engine.connect() as conn:
        conn.execute(text("SELECT 1;"))
    db_active = True
    st.sidebar.success("🟢 Connected to live PostgreSQL DB")
except Exception:
    st.sidebar.warning("🟡 Offline Mode (Using Session State)")

# Initialize session state for mock database if offline
if "macro_groups" not in st.session_state:
    # Restructured: Only Primary Factions (17 territorial states/countries)
    st.session_state.macro_groups = [
        {"id": 1, "name": "Ursine Hegemony", "population": 5000.0, "chaos_level": 0.20, "pressure": 0.30, "magistar_id": "Stagus", "is_active": True, "physical_well_being": 0.85, "mental_well_being": 0.80, "crime_level": 0.10, "discontent": 0.05, "camps_count": 2, "mines_count": 1, "docks_count": 1, "farms_count": 2, "watchtowers_count": 3, "walls_count": 2, "barracks_count": 2, "settlements": [4000, 900, 100], "cult_infiltration": 0.05, "cult_population": 250.0, "cult_devoted": 50.0, "distance_to_chaos_structure": 0.7, "distance_to_convergence": 0.8, "flora_ghost_flower": 100.0, "flora_stone_root": 100.0, "fauna_sky_grazer": 50.0, "fauna_timber_wolf": 10.0, "domestic_greenhouses": 0, "domestic_orchards": 0, "domestic_pens": 0, "domestic_kennels": 0, "churches_count": 0, "theatres_count": 0, "arenas_count": 0, "gambling_dens_count": 0, "black_markets_count": 0, "paragon": None},
        {"id": 2, "name": "River Folk", "population": 8000.0, "chaos_level": 0.30, "pressure": 0.40, "magistar_id": "Tiraton", "is_active": True, "physical_well_being": 0.80, "mental_well_being": 0.85, "crime_level": 0.15, "discontent": 0.10, "camps_count": 1, "mines_count": 1, "docks_count": 3, "farms_count": 3, "watchtowers_count": 1, "walls_count": 0, "barracks_count": 1, "settlements": [6000, 1500, 500], "cult_infiltration": 0.08, "cult_population": 640.0, "cult_devoted": 128.0, "distance_to_chaos_structure": 0.2, "distance_to_convergence": 0.5, "flora_ghost_flower": 100.0, "flora_stone_root": 100.0, "fauna_sky_grazer": 50.0, "fauna_timber_wolf": 10.0, "domestic_greenhouses": 0, "domestic_orchards": 0, "domestic_pens": 0, "domestic_kennels": 0, "churches_count": 0, "theatres_count": 0, "arenas_count": 0, "gambling_dens_count": 0, "black_markets_count": 0, "paragon": None},
        {"id": 3, "name": "Sump-Kin", "population": 6200.0, "chaos_level": 0.50, "pressure": 0.60, "magistar_id": "Gavusrix", "is_active": True, "physical_well_being": 0.55, "mental_well_being": 0.50, "crime_level": 0.40, "discontent": 0.30, "camps_count": 2, "mines_count": 3, "docks_count": 2, "farms_count": 0, "watchtowers_count": 1, "walls_count": 0, "barracks_count": 2, "settlements": [5000, 1000, 200], "cult_infiltration": 0.15, "cult_population": 930.0, "cult_devoted": 186.0, "distance_to_chaos_structure": 0.1, "distance_to_convergence": 0.3, "flora_ghost_flower": 100.0, "flora_stone_root": 100.0, "fauna_sky_grazer": 50.0, "fauna_timber_wolf": 10.0, "domestic_greenhouses": 0, "domestic_orchards": 0, "domestic_pens": 0, "domestic_kennels": 0, "churches_count": 0, "theatres_count": 0, "arenas_count": 0, "gambling_dens_count": 0, "black_markets_count": 0, "paragon": None},
        {"id": 4, "name": "Iron Caladrea", "population": 9000.0, "chaos_level": 0.40, "pressure": 0.50, "magistar_id": "Aurgenas", "is_active": True, "physical_well_being": 0.75, "mental_well_being": 0.70, "crime_level": 0.20, "discontent": 0.15, "camps_count": 1, "mines_count": 4, "docks_count": 0, "farms_count": 1, "watchtowers_count": 2, "walls_count": 3, "barracks_count": 3, "settlements": [7000, 1500, 500], "cult_infiltration": 0.05, "cult_population": 450.0, "cult_devoted": 90.0, "distance_to_chaos_structure": 0.4, "distance_to_convergence": 0.6, "flora_ghost_flower": 100.0, "flora_stone_root": 100.0, "fauna_sky_grazer": 50.0, "fauna_timber_wolf": 10.0, "domestic_greenhouses": 0, "domestic_orchards": 0, "domestic_pens": 0, "domestic_kennels": 0, "churches_count": 0, "theatres_count": 0, "arenas_count": 0, "gambling_dens_count": 0, "black_markets_count": 0, "paragon": None},
        {"id": 5, "name": "Vaneer Concord", "population": 9800.0, "chaos_level": 0.35, "pressure": 0.45, "magistar_id": "Lophex", "is_active": True, "physical_well_being": 0.88, "mental_well_being": 0.75, "crime_level": 0.12, "discontent": 0.10, "camps_count": 2, "mines_count": 4, "docks_count": 1, "farms_count": 3, "watchtowers_count": 2, "walls_count": 3, "barracks_count": 4, "settlements": [9000, 500, 300], "cult_infiltration": 0.04, "cult_population": 392.0, "cult_devoted": 78.4, "distance_to_chaos_structure": 0.6, "distance_to_convergence": 0.6, "flora_ghost_flower": 100.0, "flora_stone_root": 100.0, "fauna_sky_grazer": 50.0, "fauna_timber_wolf": 10.0, "domestic_greenhouses": 0, "domestic_orchards": 0, "domestic_pens": 0, "domestic_kennels": 0, "churches_count": 0, "theatres_count": 0, "arenas_count": 0, "gambling_dens_count": 0, "black_markets_count": 0, "paragon": None},
        {"id": 6, "name": "Hive Collective", "population": 15000.0, "chaos_level": 0.25, "pressure": 0.35, "magistar_id": "Tyrustis", "is_active": True, "physical_well_being": 0.90, "mental_well_being": 0.90, "crime_level": 0.05, "discontent": 0.05, "camps_count": 3, "mines_count": 2, "docks_count": 0, "farms_count": 6, "watchtowers_count": 2, "walls_count": 4, "barracks_count": 3, "settlements": [12000, 2000, 1000], "cult_infiltration": 0.02, "cult_population": 300.0, "cult_devoted": 60.0, "distance_to_chaos_structure": 0.8, "distance_to_convergence": 0.6, "flora_ghost_flower": 100.0, "flora_stone_root": 100.0, "fauna_sky_grazer": 50.0, "fauna_timber_wolf": 10.0, "domestic_greenhouses": 0, "domestic_orchards": 0, "domestic_pens": 0, "domestic_kennels": 0, "churches_count": 0, "theatres_count": 0, "arenas_count": 0, "gambling_dens_count": 0, "black_markets_count": 0, "paragon": None},
        {"id": 7, "name": "Avians", "population": 8500.0, "chaos_level": 0.30, "pressure": 0.40, "magistar_id": "Opecten", "is_active": True, "physical_well_being": 0.92, "mental_well_being": 0.85, "crime_level": 0.08, "discontent": 0.08, "camps_count": 1, "mines_count": 1, "docks_count": 2, "farms_count": 2, "watchtowers_count": 4, "walls_count": 1, "barracks_count": 2, "settlements": [8000, 400, 100], "cult_infiltration": 0.06, "cult_population": 510.0, "cult_devoted": 102.0, "distance_to_chaos_structure": 0.3, "distance_to_convergence": 0.5, "flora_ghost_flower": 100.0, "flora_stone_root": 100.0, "fauna_sky_grazer": 50.0, "fauna_timber_wolf": 10.0, "domestic_greenhouses": 0, "domestic_orchards": 0, "domestic_pens": 0, "domestic_kennels": 0, "churches_count": 0, "theatres_count": 0, "arenas_count": 0, "gambling_dens_count": 0, "black_markets_count": 0, "paragon": None},
        {"id": 8, "name": "Flower Valwey", "population": 4500.0, "chaos_level": 0.20, "pressure": 0.25, "magistar_id": "Vecelo", "is_active": True, "physical_well_being": 0.85, "mental_well_being": 0.88, "crime_level": 0.10, "discontent": 0.05, "camps_count": 2, "mines_count": 1, "docks_count": 1, "farms_count": 4, "watchtowers_count": 1, "walls_count": 1, "barracks_count": 1, "settlements": [3000, 1000, 500], "cult_infiltration": 0.05, "cult_population": 225.0, "cult_devoted": 45.0, "distance_to_chaos_structure": 0.9, "distance_to_convergence": 0.9, "flora_ghost_flower": 100.0, "flora_stone_root": 100.0, "fauna_sky_grazer": 50.0, "fauna_timber_wolf": 10.0, "domestic_greenhouses": 0, "domestic_orchards": 0, "domestic_pens": 0, "domestic_kennels": 0, "churches_count": 0, "theatres_count": 0, "arenas_count": 0, "gambling_dens_count": 0, "black_markets_count": 0, "paragon": None},
        {"id": 9, "name": "Sylvian", "population": 7200.0, "chaos_level": 0.35, "pressure": 0.40, "magistar_id": "Termhill", "is_active": True, "physical_well_being": 0.82, "mental_well_being": 0.80, "crime_level": 0.15, "discontent": 0.10, "camps_count": 3, "mines_count": 1, "docks_count": 0, "farms_count": 4, "watchtowers_count": 2, "walls_count": 1, "barracks_count": 2, "settlements": [6000, 1000, 200], "cult_infiltration": 0.07, "cult_population": 504.0, "cult_devoted": 100.8, "distance_to_chaos_structure": 0.5, "distance_to_convergence": 0.7, "flora_ghost_flower": 100.0, "flora_stone_root": 100.0, "fauna_sky_grazer": 50.0, "fauna_timber_wolf": 10.0, "domestic_greenhouses": 0, "domestic_orchards": 0, "domestic_pens": 0, "domestic_kennels": 0, "churches_count": 0, "theatres_count": 0, "arenas_count": 0, "gambling_dens_count": 0, "black_markets_count": 0, "paragon": None},
        {"id": 10, "name": "Sciute", "population": 5500.0, "chaos_level": 0.30, "pressure": 0.35, "magistar_id": "Carulkem", "is_active": True, "physical_well_being": 0.80, "mental_well_being": 0.78, "crime_level": 0.12, "discontent": 0.08, "camps_count": 1, "mines_count": 2, "docks_count": 1, "farms_count": 2, "watchtowers_count": 2, "walls_count": 3, "barracks_count": 1, "settlements": [4000, 1000, 500], "cult_infiltration": 0.05, "cult_population": 275.0, "cult_devoted": 55.0, "distance_to_chaos_structure": 0.5, "distance_to_convergence": 0.7, "flora_ghost_flower": 100.0, "flora_stone_root": 100.0, "fauna_sky_grazer": 50.0, "fauna_timber_wolf": 10.0, "domestic_greenhouses": 0, "domestic_orchards": 0, "domestic_pens": 0, "domestic_kennels": 0, "churches_count": 0, "theatres_count": 0, "arenas_count": 0, "gambling_dens_count": 0, "black_markets_count": 0, "paragon": None},
        {"id": 11, "name": "Meridian Chain", "population": 8500.0, "chaos_level": 0.40, "pressure": 0.50, "magistar_id": "Virantor", "is_active": True, "physical_well_being": 0.88, "mental_well_being": 0.82, "crime_level": 0.18, "discontent": 0.12, "camps_count": 2, "mines_count": 1, "docks_count": 4, "farms_count": 1, "watchtowers_count": 1, "walls_count": 1, "barracks_count": 3, "settlements": [8000, 500], "cult_infiltration": 0.10, "cult_population": 850.0, "cult_devoted": 170.0, "distance_to_chaos_structure": 0.3, "distance_to_convergence": 0.6, "flora_ghost_flower": 100.0, "flora_stone_root": 100.0, "fauna_sky_grazer": 50.0, "fauna_timber_wolf": 10.0, "domestic_greenhouses": 0, "domestic_orchards": 0, "domestic_pens": 0, "domestic_kennels": 0, "churches_count": 0, "theatres_count": 0, "arenas_count": 0, "gambling_dens_count": 0, "black_markets_count": 0, "paragon": None},
        {"id": 12, "name": "Prism Lizards", "population": 6800.0, "chaos_level": 0.45, "pressure": 0.50, "magistar_id": "Metrion", "is_active": True, "physical_well_being": 0.84, "mental_well_being": 0.80, "crime_level": 0.16, "discontent": 0.14, "camps_count": 1, "mines_count": 2, "docks_count": 1, "farms_count": 1, "watchtowers_count": 2, "walls_count": 2, "barracks_count": 2, "settlements": [5000, 1500, 300], "cult_infiltration": 0.08, "cult_population": 544.0, "cult_devoted": 108.8, "distance_to_chaos_structure": 0.2, "distance_to_convergence": 0.5, "flora_ghost_flower": 100.0, "flora_stone_root": 100.0, "fauna_sky_grazer": 50.0, "fauna_timber_wolf": 10.0, "domestic_greenhouses": 0, "domestic_orchards": 0, "domestic_pens": 0, "domestic_kennels": 0, "churches_count": 0, "theatres_count": 0, "arenas_count": 0, "gambling_dens_count": 0, "black_markets_count": 0, "paragon": None},
        {"id": 13, "name": "Canopy Clans", "population": 3400.0, "chaos_level": 0.60, "pressure": 0.40, "magistar_id": "Metrion", "is_active": True, "physical_well_being": 0.70, "mental_well_being": 0.65, "crime_level": 0.35, "discontent": 0.25, "camps_count": 5, "mines_count": 1, "docks_count": 0, "farms_count": 2, "watchtowers_count": 2, "walls_count": 0, "barracks_count": 1, "settlements": [3000, 400], "cult_infiltration": 0.12, "cult_population": 408.0, "cult_devoted": 81.6, "distance_to_chaos_structure": 0.2, "distance_to_convergence": 0.5, "flora_ghost_flower": 100.0, "flora_stone_root": 100.0, "fauna_sky_grazer": 50.0, "fauna_timber_wolf": 10.0, "domestic_greenhouses": 0, "domestic_orchards": 0, "domestic_pens": 0, "domestic_kennels": 0, "churches_count": 0, "theatres_count": 0, "arenas_count": 0, "gambling_dens_count": 0, "black_markets_count": 0, "paragon": None},
        {"id": 14, "name": "East Hounds", "population": 4200.0, "chaos_level": 0.55, "pressure": 0.45, "magistar_id": "Termhill", "is_active": True, "physical_well_being": 0.65, "mental_well_being": 0.70, "crime_level": 0.28, "discontent": 0.20, "camps_count": 3, "mines_count": 0, "docks_count": 0, "farms_count": 2, "watchtowers_count": 2, "walls_count": 0, "barracks_count": 2, "settlements": [3000, 1000, 200], "cult_infiltration": 0.14, "cult_population": 588.0, "cult_devoted": 117.6, "distance_to_chaos_structure": 0.5, "distance_to_convergence": 0.7, "flora_ghost_flower": 100.0, "flora_stone_root": 100.0, "fauna_sky_grazer": 50.0, "fauna_timber_wolf": 10.0, "domestic_greenhouses": 0, "domestic_orchards": 0, "domestic_pens": 0, "domestic_kennels": 0, "churches_count": 0, "theatres_count": 0, "arenas_count": 0, "gambling_dens_count": 0, "black_markets_count": 0, "paragon": None},
        {"id": 15, "name": "Guirrilla Clans", "population": 2500.0, "chaos_level": 0.65, "pressure": 0.55, "magistar_id": "Tiraton", "is_active": True, "physical_well_being": 0.58, "mental_well_being": 0.62, "crime_level": 0.38, "discontent": 0.28, "camps_count": 4, "mines_count": 1, "docks_count": 0, "farms_count": 1, "watchtowers_count": 1, "walls_count": 0, "barracks_count": 1, "settlements": [1500, 800, 200], "cult_infiltration": 0.18, "cult_population": 450.0, "cult_devoted": 90.0, "distance_to_chaos_structure": 0.1, "distance_to_convergence": 0.4, "flora_ghost_flower": 100.0, "flora_stone_root": 100.0, "fauna_sky_grazer": 50.0, "fauna_timber_wolf": 10.0, "domestic_greenhouses": 0, "domestic_orchards": 0, "domestic_pens": 0, "domestic_kennels": 0, "churches_count": 0, "theatres_count": 0, "arenas_count": 0, "gambling_dens_count": 0, "black_markets_count": 0, "paragon": None},
        {"id": 16, "name": "Theocracy", "population": 7800.0, "chaos_level": 0.50, "pressure": 0.55, "magistar_id": "Virantor", "is_active": True, "physical_well_being": 0.72, "mental_well_being": 0.68, "crime_level": 0.22, "discontent": 0.18, "camps_count": 1, "mines_count": 1, "docks_count": 3, "farms_count": 2, "watchtowers_count": 2, "walls_count": 1, "barracks_count": 2, "settlements": [6000, 1500, 300], "cult_infiltration": 0.11, "cult_population": 858.0, "cult_devoted": 171.6, "distance_to_chaos_structure": 0.3, "distance_to_convergence": 0.6, "flora_ghost_flower": 100.0, "flora_stone_root": 100.0, "fauna_sky_grazer": 50.0, "fauna_timber_wolf": 10.0, "domestic_greenhouses": 0, "domestic_orchards": 0, "domestic_pens": 0, "domestic_kennels": 0, "churches_count": 0, "theatres_count": 0, "arenas_count": 0, "gambling_dens_count": 0, "black_markets_count": 0, "paragon": None},
        {"id": 17, "name": "The Reliance", "population": 3000.0, "chaos_level": 0.15, "pressure": 0.20, "magistar_id": "Gavusrix", "is_active": True, "physical_well_being": 0.95, "mental_well_being": 0.90, "crime_level": 0.05, "discontent": 0.02, "camps_count": 1, "mines_count": 2, "docks_count": 0, "farms_count": 1, "watchtowers_count": 1, "walls_count": 1, "barracks_count": 1, "settlements": [300], "cult_infiltration": 0.01, "cult_population": 30.0, "cult_devoted": 6.0, "distance_to_chaos_structure": 0.9, "distance_to_convergence": 0.4, "flora_ghost_flower": 100.0, "flora_stone_root": 100.0, "fauna_sky_grazer": 50.0, "fauna_timber_wolf": 10.0, "domestic_greenhouses": 0, "domestic_orchards": 0, "domestic_pens": 0, "domestic_kennels": 0, "churches_count": 0, "theatres_count": 0, "arenas_count": 0, "gambling_dens_count": 0, "black_markets_count": 0, "paragon": None}
    ]

if "fringe_groups" not in st.session_state:
    # Non-state actor syndicates and guilds
    st.session_state.fringe_groups = [
        {"name": "Obsidian Cartel and Sister Org", "description": "Brokers illegal assets and runs the black market/smuggling pipelines."},
        {"name": "Freesky Barons", "description": "Independent aeronauts mining dragonstone crystals in volatile rifts."},
        {"name": "Ghost Wind Raiders", "description": "Clandestine sky pirates masking their operations in high-altitude currents."},
        {"name": "Gilded Compass", "description": "High-power financial syndicate controlling trade maps and banking channels."},
        {"name": "Crimson Coursairs", "description": "Smuggler fleets breaking shipping monopolies across high-velocity streams."},
        {"name": "Silent Current", "description": "Deep-sea marine smuggling network operating out of ocean trenches."},
        {"name": "The Black Label", "description": "Elite mercenary company dealing in high-risk cargo and safety contracts."},
        {"name": "The Otter Syndicate", "description": "Riverine black market krewes moving cargo under city locks and bridges."},
        {"name": "The Spring Ghosts", "description": "Clandestine spy network executing political sabotage during high-static storm weeks."}
    ]

if "prisons" not in st.session_state:
    # 12 Dragon stone prison seals corresponding to the 12 Magistar domains
    st.session_state.prisons = {
        "Tiraton": 1.0,
        "Stagus": 1.0,
        "Metrion": 1.0,
        "Aurgenas": 1.0,
        "Vecelo": 1.0,
        "Lophex": 1.0,
        "Tyrustis": 1.0,
        "Opecten": 1.0,
        "Carulkem": 1.0,
        "Termhill": 1.0,
        "Virantor": 1.0,
        "Gavusrix": 1.0,
        "warden_population": 1500.0,
        "warden_recruits_accumulated": 0.0
    }

# Ensure all macro groups have default inventories
for group in st.session_state.macro_groups:
    if "inventory" not in group:
        group["inventory"] = {
            "Lumber": 50.0,
            "Stone": 50.0,
            "Iron Ore": 10.0,
            "Copper Ore": 5.0,
            "Coal": 10.0,
            "Grain": 30.0,
            "Leather": 10.0,
            "Dragonstone": 2.0,
            "Voltaic Fleece": 0.0,
            "Ozone-Milk": 0.0,
            "Ghost Flower": 0.0,
            "Night-Nectar": 0.0,
            "Flour": 0.0,
            "Peak-Cheese": 0.0,
            "Smelted Steel": 0.0,
            "Copper Wire": 0.0,
            "Refined Aether Battery": 0.0,
            "Tanned Strips": 0.0,
            "Ostrakan Hardtack": 5.0,
            "Caldera Spark-Bread": 0.0,
            "Basic Weapons": 0.0,
            "Aether-Wright PPE": 0.0,
            "Silk-Steel Cables": 0.0,
            "Leather Armor": 0.0,
            "Rope": 0.0
        }

if "cultures" not in st.session_state:
    st.session_state.cultures = [
        {"name": "Beavers", "traits": "geomancers of infrastructure with trowel tails.", "tech_score": 10},
        {"name": "Hippos", "traits": "siege engines reading unspoken intent and expressions.", "tech_score": 11},
        {"name": "Owls", "traits": "feathered bird-kin who cannot speak a direct lie.", "tech_score": 11},
        {"name": "Horses", "traits": "noble knights maintaining warnings and grid defense.", "tech_score": 12},
        {"name": "Wolves", "traits": "fierce canine pack defenders and boundary keepers.", "tech_score": 9},
        {"name": "Bears", "traits": "Ursine guarding roads and keeping winter stasis.", "tech_score": 8},
        {"name": "Sloths", "traits": "slow Bradypods harvesting high-tension silk cables.", "tech_score": 12},
        {"name": "Toads", "traits": "amphibians immune to alchemical swamp runoff.", "tech_score": 9},
        {"name": "Mice", "traits": "auditing bookkeeping clerks weaponizing reports.", "tech_score": 12},
        {"name": "Bats", "traits": "nocturnal echolocator scouts mapping air waves.", "tech_score": 7},
        {"name": "Porcupines", "traits": "surgeon-kin using scalpel-sharp quills.", "tech_score": 8},
        {"name": "Otters", "traits": "smugglers running delta transport channels.", "tech_score": 8},
        {"name": "Deer", "traits": "common farm growers harvesting storm edges.", "tech_score": 8},
        {"name": "Mongooses", "traits": "bodyguards dodging physical gravity shifts.", "tech_score": 7},
        {"name": "Cactus-Kin", "traits": "symbiotic succulents acting as airship ballast.", "tech_score": 8},
        {"name": "Mushroom-Kin", "traits": "archivists immune to raw dragon mind bleed.", "tech_score": 12}
    ]

if "sim_logs" not in st.session_state:
    st.session_state.sim_logs = ["Simulation initialized. Ready for ticks."]

if "metric_history" not in st.session_state:
    st.session_state.metric_history = {
        "ticks": [0],
        "factions": {
            g["name"]: {
                "population": [float(g["population"])],
                "discontent": [float(g["discontent"])],
                "crime_level": [float(g["crime_level"])]
            } for g in st.session_state.macro_groups
        }
    }

if "current_tick" not in st.session_state:
    st.session_state.current_tick = 0

if "current_day" not in st.session_state:
    st.session_state.current_day = 150

# Load GeoJSON layers
if "map_gdf" not in st.session_state:
    try:
        st.session_state.map_gdf = gpd.read_file("OSTRAKA Cells 2026-06-01-07-50.geojson")
    except Exception:
        st.session_state.map_gdf = None

if "rivers_gdf" not in st.session_state:
    try:
        st.session_state.rivers_gdf = gpd.read_file("OSTRAKA Rivers 2026-06-01-07-50.geojson")
    except Exception:
        st.session_state.rivers_gdf = None

if "routes_gdf" not in st.session_state:
    try:
        st.session_state.routes_gdf = gpd.read_file("OSTRAKA Routes 2026-06-01-07-50 (1).geojson")
    except Exception:
        st.session_state.routes_gdf = None

def run_simulation_tick_in_state():
    cal = CalendarManager()
    st.session_state.current_day += 1
    current_day = st.session_state.current_day
    st.session_state.current_tick += 1
    tick_num = st.session_state.current_tick
    
    st.session_state.metric_history["ticks"].append(tick_num)
    
    # Simulate Primary Factions (17)
    for g in st.session_state.macro_groups:
        season_mod = cal.apply_seasonal_modifier("Forest", current_day)
        reality_mod = calculate_reality_spike(g["magistar_id"], g["is_active"])
        is_oceanic = g["name"] in ["Theocracy", "Meridian Chain", "Sciute"]
        weather = calculate_weather(g["chaos_level"], g["pressure"], g["magistar_id"], is_oceanic)

        if "inventory" not in g:
            g["inventory"] = {r: 0.0 for r in ["Lumber", "Stone", "Iron Ore", "Coal", "Grain", "Leather", "Dragonstone", "Ostrakan Hardtack"]}
        
        tick_result = process_living_world_tick(
            g, 
            g["inventory"], 
            current_day, 
            season_mod, 
            reality_mod, 
            weather, # pass full weather dictionary
            prisons=st.session_state.prisons
        )

        # Update stats
        g["population"] = tick_result["population"]
        g["physical_well_being"] = tick_result["physical_well_being"]
        g["mental_well_being"] = tick_result["mental_well_being"]
        g["crime_level"] = tick_result["crime_level"]
        g["discontent"] = tick_result["discontent"]
        g["inventory"] = tick_result["inventory"]
        g["cult_infiltration"] = tick_result["cult_infiltration"]
        g["cult_population"] = tick_result["cult_population"]
        g["cult_devoted"] = tick_result.get("cult_devoted", g.get("cult_devoted", g["cult_population"] * 0.20))
        g["allocated_patrols"] = tick_result.get("allocated_patrols", 0.0)
        g["allocated_hunters"] = tick_result.get("allocated_hunters", 0.0)
        
        # Ecology updates
        g["flora_ghost_flower"] = tick_result["flora_ghost_flower"]
        g["flora_stone_root"] = tick_result["flora_stone_root"]
        g["fauna_sky_grazer"] = tick_result["fauna_sky_grazer"]
        g["fauna_timber_wolf"] = tick_result["fauna_timber_wolf"]

        # Domestic structure updates
        g["domestic_greenhouses"] = tick_result["domestic_greenhouses"]
        g["domestic_orchards"] = tick_result["domestic_orchards"]
        g["domestic_pens"] = tick_result["domestic_pens"]
        g["domestic_kennels"] = tick_result["domestic_kennels"]

        # Sync active interaction tags
        g["active_tags"] = tick_result.get("active_tags", [])
        
        # Infrastructure sync in case of weather damage
        g["farms_count"] = tick_result.get("farms_count", g["farms_count"])
        g["watchtowers_count"] = tick_result.get("watchtowers_count", g["watchtowers_count"])
        g["barracks_count"] = tick_result.get("barracks_count", g["barracks_count"])
        g["mines_count"] = tick_result.get("mines_count", g["mines_count"])
        g["walls_count"] = tick_result.get("walls_count", g["walls_count"])
        g["camps_count"] = tick_result.get("camps_count", g["camps_count"])
        g["docks_count"] = tick_result.get("docks_count", g["docks_count"])
        g["churches_count"] = tick_result.get("churches_count", g.get("churches_count", 0))
        g["theatres_count"] = tick_result.get("theatres_count", g.get("theatres_count", 0))
        g["arenas_count"] = tick_result.get("arenas_count", g.get("arenas_count", 0))
        g["gambling_dens_count"] = tick_result.get("gambling_dens_count", g.get("gambling_dens_count", 0))
        g["black_markets_count"] = tick_result.get("black_markets_count", g.get("black_markets_count", 0))
        
        # Paragon Leader Sync
        g["paragon"] = tick_result.get("paragon", g.get("paragon"))
        
        st.session_state.prisons = tick_result["prisons"]
        
        # Handle Secret Cult Network spread to adjacent factions
        if tick_result.get("spread_target"):
            target_name, amount = tick_result["spread_target"]
            for target_g in st.session_state.macro_groups:
                if target_g["name"] == target_name:
                    target_g["cult_population"] = min(target_g["population"], target_g.get("cult_population", 0.0) + amount)
                    target_g["cult_infiltration"] = target_g["cult_population"] / max(1.0, target_g["population"])
                    target_g["cult_devoted"] = min(target_g["cult_population"], target_g.get("cult_devoted", 0.0) + amount * 0.15)
                    st.session_state.sim_logs.append(f"[Tick {tick_num}] 🕸️ CULT NETWORK SPREAD: Cultists spread from {g['name']} to {target_name}, seeding {amount} members.")
        
        # Log faction details
        for log_msg in tick_result["logs"]:
            st.session_state.sim_logs.append(f"[Tick {tick_num}] {log_msg}")

        # Scale settlements
        scale_ratio = g["population"] / max(1.0, sum(g["settlements"]))
        g["settlements"] = [pop * scale_ratio for pop in g["settlements"]]
        
        if tick_result["event"] == "Rioting":
            st.session_state.sim_logs.append(f"[Tick {tick_num}] ⚠️ CIVIL UNREST: Rioting in {g['name']} has slowed population growth!")
        elif tick_result["event"] == "Revolution":
            st.session_state.sim_logs.append(f"[Tick {tick_num}] 🚨 REVOLUTION: Revolution in {g['name']} has halted all population growth!")

        if weather['type'] != "Stable":
            st.session_state.sim_logs.append(f"[Tick {tick_num}] 🌀 WEATHER: {g['name']} experiences {weather['type']} weather ({weather['description']}).")
            if weather.get('is_chaos_charged'):
                st.session_state.sim_logs.append(f"[Tick {tick_num}] ⚡ CHAOS CHARGE: Storm converging towards nearest {weather.get('destination_prison')} Prison!")
            
        st.session_state.metric_history["factions"][g["name"]]["population"].append(float(g["population"]))
        st.session_state.metric_history["factions"][g["name"]]["discontent"].append(float(g["discontent"]))
        st.session_state.metric_history["factions"][g["name"]]["crime_level"].append(float(g["crime_level"]))

    # Simulate Fringe Groups Operations (Guilds and Syndicates)
    for fg in st.session_state.fringe_groups:
        host = random.choice(st.session_state.macro_groups)
        if fg["name"] == "Obsidian Cartel and Sister Org":
            host["crime_level"] = min(1.0, host["crime_level"] + 0.02)
            host["inventory"]["Lumber"] = max(0.0, host["inventory"]["Lumber"] - 3.0)
            host["inventory"]["Smelted Steel"] = host["inventory"].get("Smelted Steel", 0.0) + 1.0
            st.session_state.sim_logs.append(f"[Tick {tick_num}] 🕶️ UNDERWORLD: Obsidian Cartel ran smuggling in {host['name']}: exchanged raw Lumber for Smelted Steel, raising crime.")
        elif fg["name"] == "Freesky Barons":
            host["inventory"]["Dragonstone"] = host["inventory"].get("Dragonstone", 0.0) + 1.0
            st.session_state.sim_logs.append(f"[Tick {tick_num}] ⚓ SKY-TRADE: Freesky Barons sold 1 Dragonstone crystal to {host['name']} to refuel skiffs.")
        elif fg["name"] == "Gilded Compass":
            host["discontent"] = max(0.0, host["discontent"] - 0.03)
            host["inventory"]["Stone"] = max(0.0, host["inventory"]["Stone"] - 4.0)
            st.session_state.sim_logs.append(f"[Tick {tick_num}] 🏦 BANKING: Gilded Compass audited {host['name']}'s ledger, stabilizing discontent.")

    # Model global Convergence Void Drain of Moon Chaos Leakage
    avg_seal = sum(st.session_state.prisons[name] for name in [
        "Tiraton", "Stagus", "Metrion", "Aurgenas", "Vecelo", "Lophex", 
        "Tyrustis", "Opecten", "Carulkem", "Termhill", "Virantor", "Gavusrix"
    ]) / 12.0
    if avg_seal < 0.75:
        # Convergence is overwhelmed
        for g in st.session_state.macro_groups:
            proximity_mult = 1.0 - g.get("distance_to_chaos_structure", 0.5)
            g["chaos_level"] = min(1.0, g["chaos_level"] + 0.04 * proximity_mult)
            g["pressure"] = min(1.0, g["pressure"] + 0.04 * proximity_mult)
        st.session_state.sim_logs.append(f"[Tick {tick_num}] 🌀 CONVERGENCE SURGE: Prison seal integrity average dropped to {avg_seal * 100:.0f}%. The Convergence is overwhelmed, surging chaos globally!")
    else:
        # Convergence void drain operates cleanly
        st.session_state.sim_logs.append(f"[Tick {tick_num}] 🌌 CONVERGENCE: Void drain operating cleanly at {avg_seal * 100:.0f}% efficiency, draining Shattered Moon leakage.")

    # Warden natural selection decay & recruitment step
    warden_recruits = st.session_state.prisons.get("warden_recruits_accumulated", 0.0)
    warden_decay = st.session_state.prisons.get("warden_population", 1500.0) * 0.08
    st.session_state.prisons["warden_population"] = max(0.0, st.session_state.prisons.get("warden_population", 1500.0) - warden_decay + warden_recruits)
    st.session_state.prisons["warden_recruits_accumulated"] = 0.0

    st.session_state.sim_logs.append(f"[Tick {tick_num}] 🛡️ WARDEN TELEMETRY: Grey Warden Population: {st.session_state.prisons['warden_population']:.1f} (-{warden_decay:.1f} decay, +{warden_recruits:.1f} recruits)")
    st.session_state.sim_logs.append(f"[Tick {tick_num}] Tick complete. Day {current_day} has ended.")

# TABS DEFINITION
tab_states, tab_cultures, tab_map, tab_wildlife, tab_runner, tab_visualizer = st.tabs([
    "🏰 Manage States & Macro Groups", 
    "🎭 Manage Species / Cultures", 
    "🗺️ Map Layer Ingestion", 
    "🌲 Wildlife & Flora Registry",
    "⚙️ Simulation Runner",
    "🗺️ Interactive Map Visualizer"
])

# ==================== TAB 1: STATES & MACRO GROUPS ====================
with tab_states:
    st.header("States / Macro Groups Editor")
    
    # Selection dropdown
    group_names = [g["name"] for g in st.session_state.macro_groups]
    selected_name = st.selectbox("Select Macro Group to Edit:", group_names)
    
    # Get index of chosen group
    idx = next(i for i, g in enumerate(st.session_state.macro_groups) if g["name"] == selected_name)
    g = st.session_state.macro_groups[idx]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Core Parameters")
        g_pop = st.number_input("Population:", min_value=1.0, value=float(g["population"]), step=100.0)
        g_chaos = st.slider("Chaos Level:", 0.0, 1.0, float(g["chaos_level"]), 0.05)
        g_pressure = st.slider("Tensegrity Pressure:", 0.0, 1.0, float(g["pressure"]), 0.05)
        g_magistar = st.selectbox("Magistar Prison Entity:", ["Tiraton", "Stagus", "Metrion", "Aurgenas", "Vecelo", "Lophex", "Tyrustis", "Opecten", "Carulkem", "Termhill", "Virantor", "Gavusrix"], index=["Tiraton", "Stagus", "Metrion", "Aurgenas", "Vecelo", "Lophex", "Tyrustis", "Opecten", "Carulkem", "Termhill", "Virantor", "Gavusrix"].index(g["magistar_id"]) if g["magistar_id"] in ["Tiraton", "Stagus", "Metrion", "Aurgenas", "Vecelo", "Lophex", "Tyrustis", "Opecten", "Carulkem", "Termhill", "Virantor", "Gavusrix"] else 0)
        g_dist_chaos = st.slider("Distance to nearest Chaos Structure (Icosahedron channels):", 0.0, 1.0, float(g.get("distance_to_chaos_structure", 0.5)), 0.05)
        g_dist_conv = st.slider("Distance to Convergence Spire Base:", 0.1, 1.0, float(g.get("distance_to_convergence", 0.6)), 0.05)
        g_active = st.checkbox("Is Active Zone", value=bool(g["is_active"]))
        
        st.subheader("Social & Well-Being Indicators")
        g_phys = st.slider("Physical Well-Being:", 0.0, 1.0, float(g["physical_well_being"]), 0.05)
        g_mental = st.slider("Mental Well-Being:", 0.0, 1.0, float(g["mental_well_being"]), 0.05)
        g_crime = st.slider("Crime Level:", 0.0, 1.0, float(g["crime_level"]), 0.05)
        g_discontent = st.slider("Discontent:", 0.0, 1.0, float(g["discontent"]), 0.05)
        
    with col2:
        st.subheader("Infrastructure & Buildings")
        b_camps = st.number_input("Resource Camps:", min_value=0, value=int(g["camps_count"]))
        b_mines = st.number_input("Mines & Quarries:", min_value=0, value=int(g["mines_count"]))
        b_docks = st.number_input("Harbor Docks:", min_value=0, value=int(g["docks_count"]))
        b_farms = st.number_input("Farms:", min_value=0, value=int(g["farms_count"]))
        b_towers = st.number_input("Watchtowers:", min_value=0, value=int(g["watchtowers_count"]))
        b_walls = st.number_input("Wall Segments:", min_value=0, value=int(g["walls_count"]))
        b_barracks = st.number_input("Militia Barracks:", min_value=0, value=int(g["barracks_count"]))
        b_churches = st.number_input("Churches:", min_value=0, value=int(g.get("churches_count", 0)))
        b_theatres = st.number_input("Theatres:", min_value=0, value=int(g.get("theatres_count", 0)))
        b_arenas = st.number_input("Arenas:", min_value=0, value=int(g.get("arenas_count", 0)))
        b_gambling_dens = st.number_input("Gambling Dens:", min_value=0, value=int(g.get("gambling_dens_count", 0)))
        b_black_markets = st.number_input("Black Markets:", min_value=0, value=int(g.get("black_markets_count", 0)))
        
        # Calculate preview
        buildings_dict = {
            "farms": b_farms, "docks": b_docks, 
            "watchtowers": b_towers, "walls": b_walls, 
            "barracks": b_barracks
        }
        stats_dict = {
            "physical_well_being": g_phys, "mental_well_being": g_mental,
            "crime_level": g_crime, "discontent": g_discontent
        }
        
        preview = process_well_being_tick(stats_dict, buildings_dict, g_chaos)
        tech_level = calculate_tech_level(g["settlements"])
        transports = get_unlocked_transport(tech_level)
        buildings = get_unlocked_buildings(tech_level)
        
        st.markdown("### 📊 Rules Preview (Next Tick)")
        st.info(f"**Food Supply Rating:** {preview['food_supply']:.2f} | **Safety Rating:** {preview['safety_rating']:.2f} | **Security:** {preview['security_rating']:.2f}")
        st.warning(f"**Discontent (Next):** {preview['discontent']:.2f} | **Crime (Next):** {preview['crime_level']:.2f}")
        st.success(f"**Active Status:** {preview['event']} | **Trade Access:** {preview['trader_status']}")
        st.write(f"**Tech Level:** {tech_level} | **Unlocked Transports:** {', '.join(transports)}")
        st.write(f"**Unlocked Buildings:** {', '.join(buildings)}")
        st.markdown(f"🏷️ **Active Interaction Tags:** {', '.join(g.get('active_tags', ['calm']))}")

    st.markdown("---")
    col_inv1, col_inv2 = st.columns(2)
    with col_inv1:
        st.subheader("🎒 Resource Inventory")
        if "inventory" in g:
            inv_data = [{"Resource / Item": k, "Quantity": f"{v:.1f}"} for k, v in g["inventory"].items() if v > 0]
            if inv_data:
                df_inv = pd.DataFrame(inv_data)
                st.dataframe(df_inv, use_container_width=True, hide_index=True)
            else:
                st.write("Inventory is currently empty.")
                
    with col_inv2:
        st.subheader("😈 Cult & Warden Threat Monitor")
        g_cult_pop = st.number_input("Cultist Population:", min_value=0.0, max_value=float(g_pop), value=float(g.get("cult_population", g_pop * g.get("cult_infiltration", 0.05))))
        g_infilt = g_cult_pop / max(1.0, g_pop)
        st.metric(label="Chaos Cult Infiltration Level", value=f"{g_infilt * 100:.1f}%", delta=f"{g_cult_pop:.0f} cultists")
        
        g_devoted = st.number_input("Devoted Cultists (Based near local Prison):", min_value=0.0, max_value=float(g_cult_pop), value=float(g.get("cult_devoted", g_cult_pop * 0.20)))
        st.write(f"**Secret Network Cultists:** {g_cult_pop - g_devoted:.0f}")
        
        st.markdown("**🛡️ Warden Sentinel Deployments**")
        st.write(f"**Patrol Sentinels (stabilizing prisons/channels):** {g.get('allocated_patrols', 0.0):.0f}")
        st.write(f"**Active Hunters (tracking cultist networks):** {g.get('allocated_hunters', 0.0):.0f}")
        
        magistar = g["magistar_id"]
        seal_val = st.session_state.prisons.get(magistar, 1.0)
        st.metric(label=f"Local {magistar} Dragonstone Prison Seal", value=f"{seal_val * 100:.1f}%")
        
        st.markdown("---")
        st.markdown("✨ **Magical Affinity Demographics (50/50 Split)**")
        sparkborn_val = g_pop * 0.5
        null_val = g_pop * 0.5
        st.write(f"**Null Population (magic-blind):** {null_val:.0f}")
        st.write(f"**Sparkborn Population (magic-sensitive):** {sparkborn_val:.0f}")
        st.write(f"- Sensitive (35%): {sparkborn_val * 0.35:.0f}")
        st.write(f"- Attuned (30%): {sparkborn_val * 0.30:.0f}")
        st.write(f"- Adept (20%): {sparkborn_val * 0.20:.0f}")
        st.write(f"- Wielder (10%): {sparkborn_val * 0.10:.0f}")
        st.write(f"- Master (4%): {sparkborn_val * 0.04:.0f}")
        st.write(f"- Epic (1%): {sparkborn_val * 0.01:.0f}")
        
        # Color alerts based on threat
        if g_infilt > 0.40:
            st.error("🚨 Warning: Cult Infiltration has crossed critical threshold! Sabotage imminent.")
        if seal_val < 0.70:
            st.warning("⚠️ Warning: Dragon Prison seal weakening. Local reality stability leaking.")
            
        st.markdown("---")
        st.markdown("### 🌲 Flora & Fauna Populations")
        g_gf = st.number_input("Ghost Flower Population:", min_value=0.0, value=float(g.get("flora_ghost_flower", 100.0)))
        g_sr = st.number_input("Stone-Root Population:", min_value=0.0, value=float(g.get("flora_stone_root", 100.0)))
        g_sg = st.number_input("Sky-Grazer Population:", min_value=0.0, value=float(g.get("fauna_sky_grazer", 50.0)))
        g_tw = st.number_input("Timber Wolf Population:", min_value=0.0, value=float(g.get("fauna_timber_wolf", 10.0)))

        st.markdown("---")
        st.markdown("### 🌾 Domesticated Agriculture & Beast Training")
        g_gh = st.number_input("Domestic Greenhouses (Ghost Flower):", min_value=0, value=int(g.get("domestic_greenhouses", 0)))
        g_or = st.number_input("Domestic Orchards (Stone-Root):", min_value=0, value=int(g.get("domestic_orchards", 0)))
        g_pe = st.number_input("Domestic Pens (Sky-Grazer):", min_value=0, value=int(g.get("domestic_pens", 0)))
        g_ke = st.number_input("Wolf Kennels (Trained Wolves):", min_value=0, value=int(g.get("domestic_kennels", 0)))
 
    st.markdown("---")
    st.subheader("👑 Settlement Leader / Paragon")
    p = g.get("paragon")
    if p is None:
        # Lazy initialization
        g["paragon"] = generate_paragon(g["name"], st.session_state.sim_logs)
        p = g["paragon"]
        
    st.markdown(f"### **{p['name']}** ({p['role']})")
    
    # Alignment Badge Display
    p_align = p.get("alignment", "Pragmatic")
    if p_align == "Heroic":
        st.success("🌟 **Heroic** Alignment")
    elif p_align == "Villainous":
        st.error("😈 **Villainous** Alignment (Siphons reserves, drives crime)")
    else:
        st.warning("⚖️ **Pragmatic** Alignment")
        
    p_affinity = p.get("magic_affinity", "Null")
    if p_affinity == "Null":
        st.info("🧿 **Null** Magic Affinity (Chaos immune, stabilizes minds)")
    else:
        st.success(f"✨ **{p_affinity}** Affinity (Magical but chaos sensitive)")

    st.markdown(f"**Species / Culture:** {p['culture']}")
    st.markdown(f"**Traits:** {', '.join(p['traits'])}")
    
    # 12 stats display
    stat_cols = st.columns(6)
    stat_items = list(p["stats"].items())
    for i, (s_name, s_val) in enumerate(stat_items):
        stat_cols[i % 6].metric(label=s_name, value=s_val)
        
    st.markdown("**Recent Decisions:**")
    if p.get("recent_decisions"):
        for dec in reversed(p["recent_decisions"][-5:]):
            st.write(f"- {dec}")
    else:
        st.write("*No emergency events presented yet.*")
        
    if st.button("🔄 Appoint / Attune New Paragon Leader"):
        g["paragon"] = generate_paragon(g["name"], st.session_state.sim_logs)
        st.success(f"A new Paragon leader has taken charge: {g['paragon']['name']} ({g['paragon']['alignment']})")
        st.rerun()

    st.markdown("---")
    st.subheader("🔏 12 Chaos Dragon Prisons Grid & Grey Warden Sentinel Telemetry")
    warden_pop = st.session_state.prisons.get("warden_population", 1500.0)
    st.metric(label="🛡️ Global Grey Warden Sentinel Population (Self-managing, no manual support)", value=f"{warden_pop:.1f} sentinels")
    
    grid_cols = st.columns(6)
    prison_names = [k for k in st.session_state.prisons.keys() if k not in ["warden_population", "warden_recruits_accumulated"]]
    for index, name in enumerate(prison_names):
        col_widget = grid_cols[index % 6]
        seal_level = st.session_state.prisons[name]
        col_widget.metric(label=f"🏰 {name} Seal", value=f"{seal_level * 100:.1f}%")

    if st.button("Save Changes", key="save_state"):
        st.session_state.macro_groups[idx].update({
            "population": g_pop, "chaos_level": g_chaos, "pressure": g_pressure,
            "magistar_id": g_magistar, "is_active": g_active,
            "physical_well_being": g_phys, "mental_well_being": g_mental,
            "crime_level": g_crime, "discontent": g_discontent,
            "camps_count": b_camps, "mines_count": b_mines, "docks_count": b_docks,
            "farms_count": b_farms, "watchtowers_count": b_towers, "walls_count": b_walls,
            "barracks_count": b_barracks,
            "churches_count": b_churches,
            "theatres_count": b_theatres,
            "arenas_count": b_arenas,
            "gambling_dens_count": b_gambling_dens,
            "black_markets_count": b_black_markets,
            "cult_population": g_cult_pop,
            "cult_devoted": g_devoted,
            "cult_infiltration": g_infilt,
            "distance_to_chaos_structure": g_dist_chaos,
            "distance_to_convergence": g_dist_conv,
            "flora_ghost_flower": g_gf,
            "flora_stone_root": g_sr,
            "fauna_sky_grazer": g_sg,
            "fauna_timber_wolf": g_tw,
            "domestic_greenhouses": g_gh,
            "domestic_orchards": g_or,
            "domestic_pens": g_pe,
            "domestic_kennels": g_ke,
            "paragon": g.get("paragon")
        })
        
        if db_active:
            try:
                with engine.connect() as conn:
                    conn.execute(
                        text("""
                            UPDATE macro_groups SET 
                                population = :pop, chaos_level = :chaos, pressure = :press, 
                                magistar_id = :magistar, is_active = :act, 
                                physical_well_being = :phys, mental_well_being = :mental, 
                                crime_level = :crime, discontent = :disc,
                                camps_count = :camps, mines_count = :mines, docks_count = :docks,
                                farms_count = :farms, watchtowers_count = :towers, walls_count = :walls,
                                barracks_count = :barracks,
                                churches_count = :churches, theatres_count = :theatres, arenas_count = :arenas,
                                gambling_dens_count = :gambling_dens, black_markets_count = :black_markets
                            WHERE id = :gid
                        """),
                        {
                            "pop": g_pop, "chaos": g_chaos, "press": g_pressure, "magistar": g_magistar, "act": g_active,
                            "phys": g_phys, "mental": g_mental, "crime": g_crime, "disc": g_discontent,
                            "camps": b_camps, "mines": b_mines, "docks": b_docks, "farms": b_farms,
                            "towers": b_towers, "walls": b_walls, "barracks": b_barracks,
                            "churches": b_churches, "theatres": b_theatres, "arenas": b_arenas,
                            "gambling_dens": b_gambling_dens, "black_markets": b_black_markets,
                            "gid": g["id"]
                        }
                    )
                    conn.commit()
                st.success("Successfully saved to database!")
            except Exception as ex:
                st.error(f"Failed to update database: {ex}")
        else:
            st.success("Successfully updated session state (Dry Run mode)!")

# ==================== TAB 2: SPECIES / CULTURES ====================
with tab_cultures:
    st.header("Species / Cultures Registry")
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.subheader("Species/Cultures Ledger")
        df_cul = pd.DataFrame(st.session_state.cultures)
        st.dataframe(df_cul, use_container_width=True)
        
    with col_c2:
        st.subheader("Register New Species / Culture")
        c_name = st.text_input("Species/Culture Name:")
        c_traits = st.text_area("Lore & Traits:")
        c_tech = st.number_input("Starting Tech Score:", min_value=1, value=5)
        
        if st.button("Add Species/Culture"):
            st.session_state.cultures.append({
                "name": c_name, "traits": c_traits, "tech_score": c_tech
            })
            st.success(f"Species/Culture '{c_name}' attuned successfully!")
            st.rerun()

# ==================== TAB 3: MAP INGESTION ====================
with tab_map:
    st.header("GeoJSON Map Ingestion Console")
    st.markdown("Load layers directly from Azgaar's Fantasy Map Generator into Ostraka's PostGIS spatial tables.")
    
    # Dynamically scan the directory for GeoJSON files
    project_dir = os.path.dirname(os.path.abspath(__file__))
    geojson_files = glob.glob(os.path.join(project_dir, "*.geojson"))
    geojson_filenames = [os.path.basename(f) for f in geojson_files]
    
    if geojson_filenames:
        selected_file = st.selectbox("Detected Map Files (*.geojson):", geojson_filenames)
        default_path = os.path.join(project_dir, selected_file)
    else:
        st.warning("⚠️ No GeoJSON map files detected in the project directory.")
        default_path = ""
        
    geojson_path = st.text_input("Path to GeoJSON File (Override if needed):", default_path)
    layer_type = st.selectbox("Ingestion Target Table:", ["cells", "macro_groups", "markers", "rivers", "routes"])
    
    if st.button("Trigger Ingestion"):
        if not geojson_path or not os.path.exists(geojson_path):
            st.error(f"GeoJSON file not found at: {geojson_path}")
        else:
            st.info(f"Beginning ingestion of {layer_type} from: {os.path.basename(geojson_path)}...")
            try:
                from import_map import ingest_map_data
                ingest_map_data(geojson_path, layer_type)
                st.success(f"Successfully processed and ingested {layer_type} layers.")
            except Exception as e:
                st.error(f"Error during ingestion execution: {e}")

# ==================== TAB 4: WILDLIFE & FLORA ====================
with tab_wildlife:
    st.header("Wildlife & Flora Registry")
    
    # Display current simulated ecology totals
    st.subheader("📊 Live Ecosystem Monitor")
    ecology_summary = []
    for group in st.session_state.macro_groups:
        ecology_summary.append({
            "Faction": group["name"],
            "Ghost Flower": f"{group.get('flora_ghost_flower', 100.0):.1f}",
            "Stone-Root": f"{group.get('flora_stone_root', 100.0):.1f}",
            "Sky-Grazer": f"{group.get('fauna_sky_grazer', 50.0):.1f}",
            "Timber Wolf": f"{group.get('fauna_timber_wolf', 10.0):.1f}"
        })
    st.dataframe(pd.DataFrame(ecology_summary), use_container_width=True, hide_index=True)
    
    st.subheader("📊 Live Domestic Agriculture & Trained Tools Monitor")
    domestic_summary = []
    for group in st.session_state.macro_groups:
        domestic_summary.append({
            "Faction": group["name"],
            "Greenhouses (Ghost Flower)": int(group.get('domestic_greenhouses', 0)),
            "Orchards (Stone-Root)": int(group.get('domestic_orchards', 0)),
            "Pens (Sky-Grazer)": int(group.get('domestic_pens', 0)),
            "Kennels (Trained Wolves)": int(group.get('domestic_kennels', 0))
        })
    st.dataframe(pd.DataFrame(domestic_summary), use_container_width=True, hide_index=True)
    
    st.subheader("📊 Live Happiness & Syndicate Structures Monitor")
    happiness_summary = []
    for group in st.session_state.macro_groups:
        happiness_summary.append({
            "Faction": group["name"],
            "Churches": int(group.get('churches_count', 0)),
            "Theatres": int(group.get('theatres_count', 0)),
            "Arenas": int(group.get('arenas_count', 0)),
            "Gambling Dens": int(group.get('gambling_dens_count', 0)),
            "Black Markets": int(group.get('black_markets_count', 0))
        })
    st.dataframe(pd.DataFrame(happiness_summary), use_container_width=True, hide_index=True)
    
    col_w1, col_w2 = st.columns(2)
    
    with col_w1:
        st.subheader("Add Wildlife/Fauna")
        w_name = st.text_input("Name:")
        w_sci = st.text_input("Scientific Name:")
        w_role = st.text_input("Role (e.g. Scavenger, Predator):")
        w_hab = st.text_input("Habitat:")
        w_danger = st.slider("Danger Level (1-5):", 1, 5, 2)
        w_traits = st.text_area("Traits & Behaviors:")
        w_util = st.text_area("Economic Utility / Harvesting:")
        
        if st.button("Register Beast"):
            if db_active:
                try:
                    with engine.connect() as conn:
                        conn.execute(
                            text("INSERT INTO wildlife (name, scientific_name, role, habitat, danger_level, traits, utility) VALUES (:name, :sci, :role, :hab, :danger, :traits, :util)"),
                            {"name": w_name, "sci": w_sci, "role": w_role, "hab": w_hab, "danger": w_danger, "traits": w_traits, "util": w_util}
                        )
                        conn.commit()
                    st.success(f"Successfully added {w_name} to database!")
                except Exception as e:
                    st.error(f"DB Error: {e}")
            else:
                st.success(f"[DRY-RUN] Registered {w_name} in system logs!")
                
    with col_w2:
        st.subheader("Add Flora/Botanical")
        f_name = st.text_input("Plant Name:")
        f_class = st.text_input("Classification:")
        f_hab = st.text_input("Plant Habitat:")
        f_props = st.text_area("Physical/Arcane Properties:")
        f_apps = st.text_area("Alchemical/Construction Applications:")
        
        if st.button("Register Flora"):
            if db_active:
                try:
                    with engine.connect() as conn:
                        conn.execute(
                            text("INSERT INTO flora (name, classification, habitat, properties, applications) VALUES (:name, :class, :hab, :props, :apps)"),
                            {"name": f_name, "class": f_class, "hab": f_hab, "props": f_props, "apps": f_apps}
                        )
                        conn.commit()
                    st.success(f"Successfully added {f_name} to database!")
                except Exception as e:
                    st.error(f"DB Error: {e}")
            else:
                st.success(f"[DRY-RUN] Registered {f_name} in system logs!")

# ==================== TAB 5: SIMULATION RUNNER ====================
with tab_runner:
    st.header("⚙️ Simulation Runner & Telemetry")
    st.markdown("Execute simulation turns in real-time, view detailed status logs, and visualize demographic trends.")
    
    col_r1, col_r2 = st.columns([1, 2])
    
    with col_r1:
        st.subheader("Controls")
        if st.button("▶️ Run 1 Simulation Tick"):
            run_simulation_tick_in_state()
            st.success("1 Simulation Tick executed successfully!")
            st.rerun()
            
        if st.button("⏩ Run 5 Simulation Ticks"):
            for _ in range(5):
                run_simulation_tick_in_state()
            st.success("5 Simulation Ticks executed successfully!")
            st.rerun()
            
        if st.button("🔄 Reset Simulation History"):
            st.session_state.current_tick = 0
            st.session_state.current_day = 150
            st.session_state.sim_logs = ["Simulation reset. Ready for ticks."]
            st.session_state.metric_history = {
                "ticks": [0],
                "factions": {
                    g["name"]: {
                        "population": [float(g["population"])],
                        "discontent": [float(g["discontent"])],
                        "crime_level": [float(g["crime_level"])]
                    } for g in st.session_state.macro_groups
                }
            }
            # Reset inventories & prisons
            st.session_state.prisons = {k: 1.0 for k in st.session_state.prisons.keys() if k not in ["warden_population", "warden_recruits_accumulated"]}
            st.session_state.prisons["warden_population"] = 1500.0
            st.session_state.prisons["warden_recruits_accumulated"] = 0.0
            for g in st.session_state.macro_groups:
                g["inventory"] = {
                    "Lumber": 50.0,
                    "Stone": 50.0,
                    "Iron Ore": 10.0,
                    "Copper Ore": 5.0,
                    "Coal": 10.0,
                    "Grain": 30.0,
                    "Leather": 10.0,
                    "Dragonstone": 2.0,
                    "Voltaic Fleece": 0.0,
                    "Ozone-Milk": 0.0,
                    "Ghost Flower": 0.0,
                    "Night-Nectar": 0.0,
                    "Flour": 0.0,
                    "Peak-Cheese": 0.0,
                    "Smelted Steel": 0.0,
                    "Copper Wire": 0.0,
                    "Refined Aether Battery": 0.0,
                    "Tanned Strips": 0.0,
                    "Ostrakan Hardtack": 5.0,
                    "Caldera Spark-Bread": 0.0,
                    "Basic Weapons": 0.0,
                    "Aether-Wright PPE": 0.0,
                    "Silk-Steel Cables": 0.0,
                    "Leather Armor": 0.0,
                    "Rope": 0.0
                }
                g["cult_infiltration"] = 0.05
                g["cult_population"] = g["population"] * 0.05
                g["cult_devoted"] = g["cult_population"] * 0.20
                g["allocated_patrols"] = 0.0
                g["allocated_hunters"] = 0.0
                g["flora_ghost_flower"] = 100.0
                g["flora_stone_root"] = 100.0
                g["fauna_sky_grazer"] = 50.0
                g["fauna_timber_wolf"] = 10.0
                g["domestic_greenhouses"] = 0
                g["domestic_orchards"] = 0
                g["domestic_pens"] = 0
                g["domestic_kennels"] = 0
                g["churches_count"] = 0
                g["theatres_count"] = 0
                g["arenas_count"] = 0
                g["gambling_dens_count"] = 0
                g["black_markets_count"] = 0
                g["paragon"] = None
            st.success("Simulation metrics and history reset successfully!")
            st.rerun()
            
        st.subheader("Simulation State Summary")
        st.write(f"**Current Day:** {st.session_state.current_day}")
        st.write(f"**Total Ticks Run:** {st.session_state.current_tick}")
        
        st.subheader("📜 Event Logs")
        logs_text = "\n".join(reversed(st.session_state.sim_logs))
        st.text_area("Event Feed (Latest First)", logs_text, height=350, disabled=True)
        
    with col_r2:
        st.subheader("📈 Faction Demographics & Well-Being Over Time")
        
        g_names = [g["name"] for g in st.session_state.macro_groups]
        selected_graph_faction = st.selectbox("Select Faction to Graph:", g_names, key="graph_faction")
        
        faction_metrics = st.session_state.metric_history["factions"][selected_graph_faction]
        ticks_list = st.session_state.metric_history["ticks"]
        
        df_metrics = pd.DataFrame({
            "Tick": ticks_list,
            "Population": faction_metrics["population"],
            "Discontent": faction_metrics["discontent"],
            "Crime Level": faction_metrics["crime_level"]
        }).set_index("Tick")
        
        st.markdown("**Population Trend**")
        st.line_chart(df_metrics["Population"], use_container_width=True)
        
        st.markdown("**Social Unrest Indicators (Discontent vs. Crime)**")
        st.line_chart(df_metrics[["Discontent", "Crime Level"]], use_container_width=True)

# ==================== TAB 6: INTERACTIVE MAP VISUALIZER ====================
with tab_visualizer:
    st.header("🗺️ Interactive Simulation Map Visualizer")
    st.markdown("Visualize live Ostraka simulation parameters projected directly onto the geographical cells.")
    
    if st.session_state.map_gdf is not None:
        gdf_vis = st.session_state.map_gdf.copy()
        
        state_to_group = {g["id"]: g for g in st.session_state.macro_groups}
        
        def resolve_live_metric(row, metric):
            try:
                state_idx = int(row["state"])
            except Exception:
                return 0.0
            
            if state_idx in state_to_group:
                grp = state_to_group[state_idx]
                if metric == "chaos":
                    return float(grp["chaos_level"])
                elif metric == "population":
                    return float(grp["population"])
                elif metric == "happiness":
                    return float(1.0 - grp["discontent"])
                elif metric == "crime":
                    return float(grp["crime_level"])
            return 0.0
 
        col_m1, col_m2 = st.columns([1, 3])
        
        with col_m1:
            st.subheader("Map View Settings")
            map_overlay = st.radio(
                "Filter Map Attribute:",
                ["Faction Territories", "Chaos Levels", "Population Density", "Happiness Index", "Crime Rate"]
            )
            
            # Setup layer parameters
            if map_overlay == "Faction Territories":
                gdf_vis["plot_val"] = gdf_vis["state"].astype(str)
                cmap = "tab20"
                legend_kwds = {"title": "Territory/State ID", "bbox_to_anchor": (1.05, 1), "loc": "upper left"}
                categorical_plot = True
            elif map_overlay == "Chaos Levels":
                gdf_vis["plot_val"] = gdf_vis.apply(lambda r: resolve_live_metric(r, "chaos"), axis=1).astype(float)
                cmap = "inferno"
                legend_kwds = {"label": "Chaos Level (High = Warm)", "orientation": "horizontal", "pad": 0.05}
                categorical_plot = False
            elif map_overlay == "Population Density":
                gdf_vis["plot_val"] = gdf_vis.apply(lambda r: resolve_live_metric(r, "population"), axis=1).astype(float)
                cmap = "viridis"
                legend_kwds = {"label": "Total Faction Population", "orientation": "horizontal", "pad": 0.05}
                categorical_plot = False
            elif map_overlay == "Happiness Index":
                gdf_vis["plot_val"] = gdf_vis.apply(lambda r: resolve_live_metric(r, "happiness"), axis=1).astype(float)
                cmap = "RdYlGn"
                legend_kwds = {"label": "Happiness (Green = Good, Red = Unrest)", "orientation": "horizontal", "pad": 0.05}
                categorical_plot = False
            elif map_overlay == "Crime Rate":
                gdf_vis["plot_val"] = gdf_vis.apply(lambda r: resolve_live_metric(r, "crime"), axis=1).astype(float)
                cmap = "coolwarm"
                legend_kwds = {"label": "Crime Index", "orientation": "horizontal", "pad": 0.05}
                categorical_plot = False
                
            st.subheader("Overlay Layers")
            overlay_rivers = st.checkbox("Overlay Rivers (Blue)", value=True)
            overlay_routes = st.checkbox("Overlay Trade Routes (Red Dashed)", value=True)
            
            st.info("💡 Note: The map renders live data directly matching the parameters edited in Tab 1 and Tab 5.")
            
        with col_m2:
            st.subheader("Geospatial Projection")
            fig, ax = plt.subplots(figsize=(10, 8))
            
            gdf_vis.plot(
                column="plot_val", 
                ax=ax, 
                cmap=cmap, 
                legend=True, 
                categorical=categorical_plot,
                legend_kwds=legend_kwds
            )
            
            if overlay_rivers and st.session_state.rivers_gdf is not None:
                st.session_state.rivers_gdf.plot(ax=ax, color="blue", linewidth=1.5, alpha=0.7, label="Rivers")
                
            if overlay_routes and st.session_state.routes_gdf is not None:
                st.session_state.routes_gdf.plot(ax=ax, color="red", linestyle="--", linewidth=1.2, alpha=0.8, label="Trade Routes")
                
            ax.set_axis_off()
            st.pyplot(fig)
            
    else:
        st.error("⚠️ OSTRAKA Cells map layer not found in project directory. Please check that 'OSTRAKA Cells 2026-06-01-07-50.geojson' is present.")
