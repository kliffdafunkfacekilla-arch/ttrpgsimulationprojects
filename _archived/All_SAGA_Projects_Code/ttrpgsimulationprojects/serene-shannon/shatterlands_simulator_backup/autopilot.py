import sys
import os
import shutil
import sqlite3
import json
from datetime import datetime

# Add root directory to python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)

from core_engine.engine import GlobalEngine

DB_PATH = os.path.join(ROOT_DIR, "core_engine", "world_state.db")
BACKUP_DIR = os.path.join(ROOT_DIR, "backups", "autopilot_backups")
REPORT_PATH = os.path.join(ROOT_DIR, "autopilot_report.md")

os.makedirs(BACKUP_DIR, exist_ok=True)

# 1. Create a unique timestamped folder for backups
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
run_backup_dir = os.path.join(BACKUP_DIR, f"run_{timestamp}")
os.makedirs(run_backup_dir, exist_ok=True)

print(f"=== Starting Autopilot Run: {timestamp} ===")

# Back up database and engine files
shutil.copy2(DB_PATH, os.path.join(run_backup_dir, "world_state.db"))
shutil.copy2(os.path.join(ROOT_DIR, "core_engine", "engine.py"), os.path.join(run_backup_dir, "engine.py"))
shutil.copy2(os.path.join(ROOT_DIR, "core_engine", "fractal_core.py"), os.path.join(run_backup_dir, "fractal_core.py"))
shutil.copy2(os.path.join(ROOT_DIR, "dashboard.py"), os.path.join(run_backup_dir, "dashboard.py"))

print(f"Backups created in: {run_backup_dir}")

# Initialize Engine
engine = GlobalEngine(DB_PATH)
start_tick = engine.tick

# Run 30 ticks
print("Simulating 30 ticks...")
for _ in range(30):
    engine.trigger_tick()

end_tick = engine.tick
print(f"Ticks simulated: {start_tick} -> {end_tick}")

# 2. Analyze DB State
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Query settlements
cursor.execute("SELECT id, name, population, wealth, security_points, inventory_json, global_hex_id, micro_q, micro_r FROM settlements")
settlements = cursor.fetchall()

starving_settlements = []
dead_settlements = []
low_sec_settlements = []

for row in settlements:
    s_id, name, pop, wealth, sec, inv_str, g_hex_id, m_q, m_r = row
    try:
        inv = json.loads(inv_str)
    except:
        inv = {}
    
    starvation_ticks = inv.get("Survival", {}).get("StarvationTicks", 0)
    health = inv.get("Survival", {}).get("Health", 100.0)
    composure = inv.get("Survival", {}).get("Composure", 100.0)
    
    if pop <= 0:
        dead_settlements.append((s_id, name))
    elif starvation_ticks > 0:
        starving_settlements.append((s_id, name, starvation_ticks, health, composure))
        
    if sec < 20.0:
        low_sec_settlements.append((s_id, name, sec))

# Query wars
cursor.execute("SELECT COUNT(*) FROM faction_relations WHERE status='War'")
war_count = cursor.fetchone()[0] // 2 # Divided by 2 since relations are bidirectional

# Query weather & entities
cursor.execute("SELECT COUNT(*) FROM weather_systems")
weather_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM world_entities")
entity_count = cursor.fetchone()[0]

# Query recent events during this run
cursor.execute("SELECT tick, category, message FROM event_log WHERE tick > ? AND tick <= ? ORDER BY tick ASC, id ASC", (start_tick, end_tick))
recent_events = cursor.fetchall()

print("\n--- ANALYSIS RESULTS ---")
print(f"Total Settlements: {len(settlements)}")
print(f"Dead Settlements: {len(dead_settlements)}")
print(f"Starving Settlements: {len(starving_settlements)}")
print(f"Low Security Settlements: {len(low_sec_settlements)}")
print(f"Active Wars: {war_count}")
print(f"Weather Storms: {weather_count}")
print(f"Active Entities: {entity_count}")
print(f"Events Logged: {len(recent_events)}")

# No patches are applied directly. Only report on state.
patches_applied = []

conn.close()

# 4. Generate Report
report_exists = os.path.exists(REPORT_PATH)
with open(REPORT_PATH, "a") as f:
    if not report_exists:
        f.write("# Autopilot Simulation Analysis & Fixes Report\n\n")
    
    f.write(f"## Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Tick: {start_tick} -> {end_tick})\n")
    f.write(f"- **Backup Folder:** `backups/autopilot_backups/run_{timestamp}`\n")
    f.write(f"- **Total Settlements:** {len(settlements)}\n")
    f.write(f"- **Dead Settlements Found:** {len(dead_settlements)}\n")
    f.write(f"- **Starving Settlements Found:** {len(starving_settlements)}\n")
    f.write(f"- **Low Security Settlements Found:** {len(low_sec_settlements)}\n")
    f.write(f"- **Active Wars:** {war_count}\n")
    f.write(f"- **Weather Storms:** {weather_count}\n")
    f.write(f"- **Active Entities:** {entity_count}\n\n")
    
    f.write("### Actions & Patches Applied:\n")
    f.write("- Pure Diagnostic Mode: No database patches/resources injected. Simulation is allowed to run naturally.\n\n")
    
    f.write("### Chronicle of Simulation Events:\n")
    if recent_events:
        for ev_tick, ev_cat, ev_msg in recent_events:
            f.write(f"- **[Tick {ev_tick}]** *{ev_cat}*: {ev_msg}\n")
    else:
        f.write("- No specific chronicle events were logged during this 30-tick run.\n")
    
    f.write("\n---\n\n")

print(f"=== Autopilot Run Complete. Report updated at {REPORT_PATH} ===")
