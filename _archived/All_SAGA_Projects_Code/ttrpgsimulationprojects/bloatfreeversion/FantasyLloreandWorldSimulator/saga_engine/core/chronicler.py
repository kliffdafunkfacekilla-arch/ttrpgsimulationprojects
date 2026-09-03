import sqlite3
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

class Chronicler:
    """
    The persistent memory of the S.A.G.A. Engine.
    Uses SQLite to store world events, player actions, and simulation heartbeats.
    Designed for high performance and efficient recall.
    """
    
    def __init__(self, db_path: str = "saga_history.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initializes the SQLite schema if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Events Table: Tracks everything that happens
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    game_time TEXT,
                    category TEXT, -- 'WORLD', 'PLAYER', 'QUEST', 'SYSTEM'
                    event_type TEXT,
                    hex_coord TEXT, -- '[q, r]' format
                    payload TEXT,   -- JSON data
                    summary TEXT    -- Human-readable short summary
                )
            """)
            
            # World State Snapshots: For efficient "rewind" functionality
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    game_time TEXT,
                    campaign_state TEXT -- Compressed JSON of CampaignState
                )
            """)
            
            # Indices for fast recall
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON events(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hex ON events(hex_coord)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)")
            
            conn.commit()

    def log_event(self, category: str, event_type: str, summary: str, 
                  payload: Dict[str, Any] = None, hex_coord: str = None, 
                  game_time: str = None):
        """Records a new event into the database."""
        timestamp = time.time()
        payload_json = json.dumps(payload) if payload else "{}"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO events (timestamp, game_time, category, event_type, hex_coord, payload, summary)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, game_time, category, event_type, hex_coord, payload_json, summary))
            conn.commit()

    def query_hex_history(self, hex_coord: str, limit: int = 10) -> List[Dict]:
        """Recalls the last N events that occurred in a specific location."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM events 
                WHERE hex_coord = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (hex_coord, limit))
            
            return [dict(row) for row in cursor.fetchall()]

    def search_events(self, query: str, category: str = None) -> List[Dict]:
        """Full-text search through event summaries and payloads."""
        sql = "SELECT * FROM events WHERE (summary LIKE ? OR payload LIKE ?)"
        params = [f"%{query}%", f"%{query}%"]
        
        if category:
            sql += " AND category = ?"
            params.append(category)
            
        sql += " ORDER BY timestamp DESC LIMIT 50"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def take_snapshot(self, game_time: str, state_dict: Dict[str, Any]):
        """Saves a full state snapshot for recovery or long-term analysis."""
        timestamp = time.time()
        state_json = json.dumps(state_dict)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO snapshots (timestamp, game_time, campaign_state)
                VALUES (?, ?, ?)
            """, (timestamp, game_time, state_json))
            conn.commit()
            
    def get_latest_snapshot(self) -> Optional[Dict]:
        """Returns the most recent state snapshot."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM snapshots ORDER BY timestamp DESC LIMIT 1")
            row = cursor.fetchone()
            return dict(row) if row else None
