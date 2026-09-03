import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "world_state.db")

def get_calendar_info(tick):
    total_days = tick
    year = 1650 + (total_days // 539)
    day_of_year = (total_days % 539) + 1

    months = [("Nexar", 35), ("Massis", 28), ("Motom", 21), ("Fluxen", 42), ("Vitan", 49), ("Lexis", 28), ("Ration", 28), ("Ordis", 28), ("Luxen", 49), ("Omin", 63), ("Aurum", 35), ("Anum", 42), ("Maelen", 84), ("Shadowfall", 7)]
    current_month = ""
    day_of_month = day_of_year
    for m_name, m_days in months:
        if day_of_month <= m_days:
            current_month = m_name
            break
        day_of_month -= m_days

    seasons = [("Shadowburn", 84), ("Dryspell", 42), ("Frostin", 49), ("GreenSpan", 84), ("Highreach", 112), ("Spurium", 77), ("Dimfreeze", 84), ("Shadowfall", 7)]
    current_season = ""
    day_in_season = day_of_year
    for s_name, s_days in seasons:
        if day_in_season <= s_days:
            current_season = s_name
            break
        day_in_season -= s_days

    return year, current_month, day_of_month, current_season

class MacroStateTracker:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.tick = 0
        conn = sqlite3.connect(self.db_path)
        
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM metadata WHERE key='current_tick'")
        row = cursor.fetchone()
        if row: self.tick = int(row[0])
        else:
            cursor.execute("INSERT INTO metadata (key, value) VALUES ('current_tick', '0')")
            conn.commit()

        self.year, self.month, self.day, self.season = get_calendar_info(self.tick)
        cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('current_year', ?)", (str(self.year),))
        cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('current_month', ?)", (self.month,))
        cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('current_day', ?)", (str(self.day),))
        cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('current_season', ?)", (self.season,))
        conn.commit()
        conn.close()

    def save_metadata(self, conn):
        conn.execute("UPDATE metadata SET value=? WHERE key='current_tick'", (str(self.tick),))
        conn.execute("UPDATE metadata SET value=? WHERE key='current_year'", (str(self.year),))
        conn.execute("UPDATE metadata SET value=? WHERE key='current_month'", (self.month,))
        conn.execute("UPDATE metadata SET value=? WHERE key='current_day'", (str(self.day),))
        conn.execute("UPDATE metadata SET value=? WHERE key='current_season'", (self.season,))

    def log_event(self, category, msg, conn, q=None, r=None):
        cursor = conn.cursor()
        cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (self.tick, category, msg, q, r))

    def trigger_tick(self):
        self.tick += 1
        self.year, self.month, self.day, self.season = get_calendar_info(self.tick)

        conn = sqlite3.connect(self.db_path)
        
        # In the new abstract engine, the 'tick' primarily advances time.
        # Deep simulation is replaced by LLM narrative injection.
        # This function acts as the hook for any time-based passive progression if needed in the future.

        self.save_metadata(conn)
        conn.commit()
        conn.close()
        
        return {
            "tick": self.tick,
            "year": self.year,
            "month": self.month,
            "day": self.day,
            "season": self.season
        }

if __name__ == "__main__":
    tracker = MacroStateTracker()
    print(f"Current State: Year {tracker.year}, {tracker.month} {tracker.day} ({tracker.season}) - Tick {tracker.tick}")
    tracker.trigger_tick()
    print(f"Advanced to Tick {tracker.tick}")
