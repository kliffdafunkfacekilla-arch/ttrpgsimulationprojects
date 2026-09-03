import sqlite3
import os

def create_story_events_table(conn):
    cursor = conn.cursor()
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

# Extend the existing apply_migrations to also ensure the story_events table exists.
# This function will be called during engine initialization.

# NOTE: This file is a backup of the original db_setup.py before modification.
"
