import sqlite3
import shutil
import os
from core_engine.db_setup import apply_migrations

src = r'c:\Users\krazy\Desktop\serene-shannon\shatterlands_simulator\backups\autopilot_backups\run_20260621_184303\world_state.db'
dst = r'c:\Users\krazy\Desktop\serene-shannon\shatterlands_simulator\core_engine\world_state.db'

print("Copying DB...")
shutil.copyfile(src, dst)

conn = sqlite3.connect(dst)
cursor = conn.cursor()

# Remove world_ended flag if it exists
cursor.execute("DELETE FROM metadata WHERE key='world_ended'")
# Reset tick if necessary, but we can just continue from where it is
conn.commit()

print("Applying migrations (to add active_stages)...")
apply_migrations(conn)
print("Done.")
conn.close()
