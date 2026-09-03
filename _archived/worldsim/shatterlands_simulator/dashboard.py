# dashboard.py
# Streamlit verification dashboard for the Shatterlands Simulator

import streamlit as st
import sqlite3
import pandas as pd
import os
from engine import ShatterlandsEngine
from codec import BIOMES, FACTIONS, RESOURCES, OVERLAYS, unpack_micro_hex

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "world_state.db")

st.set_page_config(page_title="Shatterlands Simulation Dashboard", layout="wide")

# Persistent Engine Initialization in Streamlit Session State
if "engine" not in st.session_state:
    st.session_state.engine = ShatterlandsEngine(DB_PATH)

engine = st.session_state.engine

st.title("📂 Shatterlands Headless Simulation Engine Dashboard")

# Top Metrics Row
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Global Clock Tick", engine.global_tick)
with col2:
    st.metric("Active Event Queue Size", len(engine.event_queue))
with col3:
    st.metric("Active Overlays Floating", len(engine.overlays))

# Verification Controls
st.subheader("⚙️ Verification Controls")
btn_col1, btn_col2, btn_col3 = st.columns(3)

with btn_col1:
    if st.button("Trigger Simulation Tick (+1)"):
        res = engine.trigger_tick()
        st.success(f"Tick {res['tick']} completed! Events processed: {len(res['processed_events'])}")

with btn_col2:
    if st.button("Schedule Test Caravan Event"):
        # Schedule caravan arrival event 5 ticks from now
        arrival = engine.global_tick + 5
        engine.add_event(arrival, "caravan_arrive", {"dest_x": 0, "dest_y": 0, "iron": 50})
        st.info(f"Caravan scheduled to arrive at tick {arrival} at center hex (0,0)")

with btn_col3:
    if st.button("Schedule Test Scout Spark Event"):
        arrival = engine.global_tick + 2
        engine.add_event(arrival, "scout_spark", {"x": 5, "y": 5})
        st.info(f"Scout team scheduled to spark coordinate (5,5) at tick {arrival}")

# Event Queue Display
st.subheader("⏳ Event Queue Tasks")
if engine.event_queue:
    queue_df = pd.DataFrame(engine.event_queue, columns=["Arrival Tick", "Event Type", "Payload"])
    st.dataframe(queue_df, use_container_width=True)
else:
    st.info("No pending events in the priority queue.")

# Active Overlays Display
st.subheader("🌌 Active Floating Overlays (Drifting)")
overlays_data = []
for o in engine.overlays:
    overlays_data.append({
        "Overlay Name": OVERLAYS[o.overlay_id],
        "X Coord": round(o.x, 2),
        "Y Coord": round(o.y, 2),
        "Velocity X": o.vx,
        "Velocity Y": o.vy
    })
st.table(pd.DataFrame(overlays_data))

# Map Snapshot Viewer
st.subheader("🗺️ Map coordinate view (Snapshot Extraction)")
snap_col1, snap_col2 = st.columns(2)
with snap_col1:
    min_x = st.number_input("Min X Coordinate", value=-5)
    max_x = st.number_input("Max X Coordinate", value=5)
with snap_col2:
    min_y = st.number_input("Min Y Coordinate", value=-5)
    max_y = st.number_input("Max Y Coordinate", value=5)

if st.button("Query Hex Coordinates"):
    raw_snapshot = engine.extract_snapshot(min_x, max_x, min_y, max_y)
    if raw_snapshot:
        snapshot_df = pd.DataFrame(raw_snapshot)
        st.dataframe(snapshot_df, use_container_width=True)
    else:
        st.warning("No hex data found in the coordinate range.")

# Data Tables (verification of db contents)
tab1, tab2 = st.tabs(["Meso Hexes Data Verification", "Micro Hexes Data Verification"])

with tab1:
    st.write("Top 100 rows of `meso_hexes` database table:")
    conn = sqlite3.connect(DB_PATH)
    meso_df = pd.read_sql_query("SELECT * FROM meso_hexes LIMIT 100", conn)
    conn.close()
    st.dataframe(meso_df, use_container_width=True)

with tab2:
    st.write("Top 100 rows of raw `micro_hexes` database table:")
    conn = sqlite3.connect(DB_PATH)
    micro_df = pd.read_sql_query("SELECT * FROM micro_hexes LIMIT 100", conn)
    conn.close()
    st.dataframe(micro_df, use_container_width=True)

# TTRPG Event Injection Section
st.subheader("💉 Direct Data Injection (TTRPG Results)")
inj_col1, inj_col2, inj_col3 = st.columns(3)
with inj_col1:
    inj_x = st.number_input("Target Coordinate X", value=0, key="inj_x")
    inj_y = st.number_input("Target Coordinate Y", value=0, key="inj_y")
with inj_col2:
    inj_biome = st.selectbox("Update Biome", list(BIOMES.values()))
    inj_faction = st.selectbox("Update Faction", list(FACTIONS.values()))
with inj_col3:
    inj_resource = st.selectbox("Update Resource", list(RESOURCES.values()))
    inj_dev = st.slider("Development Level", min_value=0, max_value=7, value=0)
    inj_spark = st.checkbox("Spark Anomaly Active")

if st.button("Inject Map Update"):
    mod_dict = {
        "biome_id": [k for k, v in BIOMES.items() if v == inj_biome][0],
        "faction_id": [k for k, v in FACTIONS.items() if v == inj_faction][0],
        "resource_id": [k for k, v in RESOURCES.items() if v == inj_resource][0],
        "dev_level": inj_dev,
        "spark": 1 if inj_spark else 0
    }
    try:
        engine.inject_event(inj_x, inj_y, mod_dict)
        st.success(f"Injected modifications at ({inj_x}, {inj_y}) successfully!")
    except Exception as e:
        st.error(f"Failed to inject event: {e}")
