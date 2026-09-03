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

print("\n--- ANALYSIS RESULTS ---")
print(f"Total Settlements: {len(settlements)}")
print(f"Dead Settlements: {len(dead_settlements)}")
print(f"Starving Settlements: {len(starving_settlements)}")
print(f"Low Security Settlements: {len(low_sec_settlements)}")
print(f"Active Wars: {war_count}")
print(f"Weather Storms: {weather_count}")
print(f"Active Entities: {entity_count}")

# 3. Propose and Implement Fixes
patches_applied = []

# Fix Starvation
if starving_settlements:
    print("\nApplying Starvation Patches...")
    for s_id, name, ticks, health, composure in starving_settlements:
        # Boost food stockpile by 500
        cursor.execute("SELECT inventory_json FROM settlements WHERE id=?", (s_id,))
        inv_str = cursor.fetchone()[0]
        inv = json.loads(inv_str)
        inv["Survival"]["Food"] = inv["Survival"].get("Food", 0.0) + 500.0
        inv["Survival"]["StarvationTicks"] = 0
        inv["Survival"]["Health"] = 100.0
        inv["Survival"]["Composure"] = 100.0
        cursor.execute("UPDATE settlements SET inventory_json=? WHERE id=?", (json.dumps(inv), s_id))
        
        # Build an emergency food farm if none exists in the farms table for this settlement
        cursor.execute("SELECT COUNT(*) FROM farms WHERE settlement_id=? AND structure_type='Farm'", (s_id,))
        if cursor.fetchone()[0] == 0:
            # Find center hex
            cursor.execute("SELECT global_hex_id, micro_q, micro_r FROM settlements WHERE id=?", (s_id,))
            g_hex, m_q, m_r = cursor.fetchone()
            # Insert a Farm at the center or near it (we'll use center micro_q, micro_r + 1)
            cursor.execute("""
                INSERT OR IGNORE INTO farms (global_hex_id, micro_q, micro_r, settlement_id, output_rate, maintenance_cost, level, structure_type)
                VALUES (?, ?, ?, ?, 3.0, 1.0, 1, 'Farm')
            """, (g_hex, m_q, m_r + 1, s_id))
            patches_applied.append(f"Starvation Fix: Built Emergency food Farm at ({m_q}, {m_r+1}) and added 500 food for {name}")
        else:
            # Upgrade existing Farm level
            cursor.execute("UPDATE farms SET level = level + 1, output_rate = output_rate + 1.0 WHERE settlement_id=? AND structure_type='Farm'", (s_id,))
            patches_applied.append(f"Starvation Fix: Upgraded existing food Farm level and added 500 food for {name}")

# Fix Low Security
if low_sec_settlements:
    print("\nApplying Security Patches...")
    for s_id, name, sec in low_sec_settlements:
        cursor.execute("UPDATE settlements SET security_points = 50.0 WHERE id=?", (s_id,))
        patches_applied.append(f"Morale/Security Fix: Reset security points to 50.0 for {name}")

# Fix Wars
if war_count > 5:
    print("\nApplying Diplomatic Patches...")
    cursor.execute("UPDATE faction_relations SET status='Neutral', trust_level=0")
    patches_applied.append(f"Diplomacy Fix: Calmed global wars back to Neutral due to excessive war count ({war_count})")

# Fix Weather
if weather_count > 10:
    print("\nApplying Weather Patches...")
    cursor.execute("DELETE FROM weather_systems WHERE id IN (SELECT id FROM weather_systems ORDER BY energy ASC LIMIT ?)", (weather_count - 8,))
    patches_applied.append(f"Weather Fix: Cleared {weather_count - 8} low energy storms to stabilize atmospheric density")

# Fix Dead Settlements (respawn population if extinct)
if dead_settlements:
    print("\nApplying Resurrection Patches...")
    for s_id, name in dead_settlements:
        cursor.execute("UPDATE settlements SET population=50, wealth=100.0 WHERE id=?", (s_id,))
        patches_applied.append(f"Resurrection Fix: Reseeded settlement {name} with 50 population after collapse")

conn.commit()
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
    if patches_applied:
        for patch in patches_applied:
            f.write(f"- [x] {patch}\n")
    else:
        f.write("- No critical issues found. Simulation stable.\n")
    f.write("\n---\n\n")

print(f"=== Autopilot Run Complete. Report updated at {REPORT_PATH} ===")
