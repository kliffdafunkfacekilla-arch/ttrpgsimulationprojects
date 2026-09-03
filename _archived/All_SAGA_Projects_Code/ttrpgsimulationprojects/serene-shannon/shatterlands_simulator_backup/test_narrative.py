import sqlite3
import json
import os
from core_engine.engine import GlobalEngine, DB_PATH
from ai_director.npc_behavior import NarrativeStageManager

print("Initializing Engine (Running Migrations)...")
engine = GlobalEngine()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Find a valid normal settlement to act as our test subject
cursor.execute("""
    SELECT s.id, g.q, g.r, s.name 
    FROM settlements s
    JOIN global_hexes g ON s.global_hex_id = g.id
    WHERE s.name NOT LIKE 'Prison of%' AND s.name != 'The Warden Spire'
    LIMIT 1
""")
row = cursor.fetchone()
if not row:
    print("No suitable settlement found!")
    exit(1)

s_id, q, r, s_name = row
print(f"Testing with Settlement: {s_name} at ({q}, {r})")

# Force low security
cursor.execute("UPDATE settlements SET security_points = 5 WHERE id=?", (s_id,))
conn.commit()

# Player moves to this coordinate
print("Initializing Narrative Bubble...")
manager = NarrativeStageManager(db_path=DB_PATH, player_pos=(q, r), radius=2)

# Step 1: Initialize Stage (Generates NPCs based on < 20 security)
manager.update_stage()
print("\n[After Initial update_stage]")
cursor.execute("SELECT settlement_id, npcs_json, conflict_signal FROM active_stages")
for st in cursor.fetchall():
    print(st)

# Step 2: Global Tick triggers Anarchy
print("\nRunning Global Tick...")
engine.trigger_tick()

print("\n[After trigger_tick]")
cursor.execute("SELECT settlement_id, npcs_json, conflict_signal FROM active_stages")
for st in cursor.fetchall():
    print(st)

# Step 3: Process the Anarchy signal
print("\nUpdating Stage again to process conflict signal...")
manager.update_stage()

print("\n[After second update_stage]")
cursor.execute("SELECT settlement_id, npcs_json, conflict_signal FROM active_stages")
for st in cursor.fetchall():
    print(st)

conn.close()
