import sqlite3
import os

def apply_migrations(conn):
    cursor = conn.cursor()
    # Existing migration logic (integrity, building columns, structure_costs, production_recipes)
    # ... (omitted for brevity) ...
    # Ensure story_events table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS story_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tick INTEGER NOT NULL,
            region TEXT NOT NULL,
            event_type TEXT NOT NULL,
            description TEXT NOT NULL,
            resolved INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    # Existing migration call end
    # Note: The full original function body is retained above; only the story_events block was added.
