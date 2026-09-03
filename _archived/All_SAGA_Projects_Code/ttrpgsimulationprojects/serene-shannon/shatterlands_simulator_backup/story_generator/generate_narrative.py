import sqlite3
import os
import re
from datetime import datetime

# Path to the simulation database (relative to this script)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "core_engine", "world_state.db")


def fetch_latest_tick(conn):
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT value FROM metadata WHERE key='current_tick'")
        row = cursor.fetchone()
        return int(row[0]) if row else 0
    except sqlite3.OperationalError:
        return 0


def fetch_events_for_tick(conn, tick):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT category, message, global_q, global_r FROM event_log WHERE tick=?",
        (tick,)
    )
    return cursor.fetchall()


def generate_narratives():
    conn = sqlite3.connect(DB_PATH)
    latest_tick = fetch_latest_tick(conn)
    # We'll generate narratives for the last 5 ticks
    narratives = []
    
    for t in range(max(1, latest_tick - 4), latest_tick + 1):
        events = fetch_events_for_tick(conn, t)
        if not events:
            continue
            
        # Group events by (category, message) to prevent spam
        grouped_events = {}
        for category, message, q, r in events:
            key = (category, message)
            if key not in grouped_events:
                grouped_events[key] = {'count': 0, 'coords': set()}
            
            grouped_events[key]['count'] += 1
            if q is not None and r is not None:
                grouped_events[key]['coords'].add(f"({q}, {r})")
                
        for (category, message), data in grouped_events.items():
            count = data['count']
            
            # Format locations
            coords_str = ""
            if data['coords']:
                c_list = list(data['coords'])
                coords_str = " near " + ", ".join(c_list[:3])
                if len(c_list) > 3:
                    coords_str += f" and {len(c_list) - 3} other locations"
                    
            # Build the core narrative string
            if category == "WORLD_END":
                text = f"The world shattered: {message}"
            else:
                # Most messages from the engine are already full sentences.
                text = message
                
            # Append coordinates only if the message doesn't already have them
            if coords_str and not re.search(r'\(-?\d+,\s*-?\d+\)', message):
                text += coords_str
                
            # Append the occurrence count if it happened multiple times
            if count > 1:
                text += f" (occurred {count} times)"
                
            narratives.append(f"Tick {t} | [{category}] {text}")
            
    conn.close()
    return narratives


def main():
    narratives = generate_narratives()
    if not narratives:
        print("No recent events to narrate.")
        return
        
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Narrative report generated at {timestamp}\n")
    for line in narratives:
        print(f"- {line}")


if __name__ == "__main__":
    main()
