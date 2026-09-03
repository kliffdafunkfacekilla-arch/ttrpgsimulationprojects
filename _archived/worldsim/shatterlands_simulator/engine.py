# engine.py
# Headless simulation engine for Shatterlands Simulator

import sqlite3
import os
import heapq
import random
from codec import pack_micro_hex, unpack_micro_hex, OVERLAYS

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "world_state.db")

class Overlay:
    def __init__(self, x: float, y: float, vx: float, vy: float, overlay_id: int):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.overlay_id = overlay_id

    def move(self):
        self.x += self.vx
        self.y += self.vy
        # Wrap around boundaries
        if self.x > 20: self.x = -20
        if self.x < -20: self.x = 20
        if self.y > 20: self.y = -20
        if self.y < -20: self.y = 20

class ShatterlandsEngine:
    __slots__ = ['global_tick', 'event_queue', 'overlays', 'db_path']

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.global_tick = 0
        self.event_queue = [] # Min-heap priority queue
        
        # Initialize floating weather and magic overlays in memory
        self.overlays = [
            Overlay(x=-5.0, y=5.0, vx=0.5, vy=0.2, overlay_id=1),  # Transmutation Mist
            Overlay(x=10.0, y=-5.0, vx=-0.3, vy=0.4, overlay_id=2), # Gravity Well
            Overlay(x=0.0, y=0.0, vx=0.1, vy=-0.5, overlay_id=3),   # Psychic Lightning
        ]

    def trigger_tick(self) -> dict:
        """Advance the simulation clock by 1 tick and run simulation phases."""
        self.global_tick += 1
        print(f"\n--- Triggering Simulation Tick {self.global_tick} ---")

        # 1. Move overlays
        for overlay in self.overlays:
            overlay.move()

        # 2. Process priority event queue
        processed_events = []
        while self.event_queue and self.event_queue[0][0] <= self.global_tick:
            event_tick, event_type, event_data = heapq.heappop(self.event_queue)
            self._execute_event(event_type, event_data)
            processed_events.append((event_type, event_data))

        # 3. Process ecology updates in SQLite
        self.process_ecology()

        # 4. Perform Data Folding (every 7 ticks)
        folded = False
        if self.global_tick % 7 == 0:
            self.fold_micro_to_meso()
            folded = True

        return {
            "tick": self.global_tick,
            "processed_events": processed_events,
            "overlays": [{"x": o.x, "y": o.y, "id": o.overlay_id, "name": OVERLAYS[o.overlay_id]} for o in self.overlays],
            "folded": folded
        }

    def _execute_event(self, event_type: str, event_data: dict):
        """Execute logic for popped events."""
        print(f"Executing event: {event_type} - {event_data}")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if event_type == "caravan_arrive":
            dest_x = event_data.get("dest_x")
            dest_y = event_data.get("dest_y")
            iron_add = event_data.get("iron", 0)
            
            # Update closest Meso hex resources
            cursor.execute("""
            UPDATE meso_hexes
            SET iron = iron + ?
            WHERE id = (
                SELECT id FROM meso_hexes 
                ORDER BY (abs(center_x - ?) + abs(center_y - ?)) LIMIT 1
            )
            """, (iron_add, dest_x, dest_y))
            conn.commit()
            print(f"Caravan successfully delivered {iron_add} iron to nearest Meso hex.")

        elif event_type == "scout_spark":
            # Set a random coordinate's spark parameter to True
            target_x = event_data.get("x")
            target_y = event_data.get("y")
            cursor.execute("SELECT state_int FROM micro_hexes WHERE x=? AND y=?", (target_x, target_y))
            row = cursor.fetchone()
            if row:
                attrs = unpack_micro_hex(row[0])
                new_state = pack_micro_hex(
                    attrs["biome_id"], attrs["faction_id"], attrs["resource_id"],
                    attrs["dev_level"], attrs["overlay_id"], spark=1
                )
                cursor.execute("UPDATE micro_hexes SET state_int=? WHERE x=? AND y=?", (new_state, target_x, target_y))
                conn.commit()
                print(f"Scout team ignited Spark anomaly at ({target_x}, {target_y})")

        conn.close()

    def add_event(self, arrival_tick: int, event_type: str, event_data: dict):
        """Push an event onto the priority queue."""
        heapq.heappush(self.event_queue, (arrival_tick, event_type, event_data))
        print(f"Event scheduled for tick {arrival_tick}: {event_type}")

    def process_ecology(self):
        """Apply mathematical rules of local ecology, taking overlays into account."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Gather all micro hexes
        cursor.execute("SELECT id, x, y, state_int FROM micro_hexes")
        rows = cursor.fetchall()

        updates = []
        for hex_id, hx, hy, state_int in rows:
            attrs = unpack_micro_hex(state_int)
            
            # Check if any overlay is directly on top of this hex (distance < 2.0)
            active_overlay_id = 0
            for overlay in self.overlays:
                dist = ((overlay.x - hx) ** 2 + (overlay.y - hy) ** 2) ** 0.5
                if dist < 2.0:
                    active_overlay_id = overlay.overlay_id
                    break

            # 1. Overlay specific transmutations or effects
            biome_id = attrs["biome_id"]
            dev_level = attrs["dev_level"]
            resource_id = attrs["resource_id"]
            spark = 1 if attrs["spark"] else 0

            if active_overlay_id == 1: # Transmutation Mist (Aurgenas)
                # Randomly transmute resources
                if random.random() < 0.3:
                    resource_id = random.randint(1, 12) # Transmute to elemental conductors
            elif active_overlay_id == 2: # Gravity Well (Tiraton)
                # Saps/crushes development levels due to weight
                if dev_level > 0:
                    dev_level -= 1

            # 2. General ecology rules
            # High dev levels boost resource extraction potential but require development maintenance
            if dev_level > 3 and random.random() < 0.05:
                # Slowly increase dev level up to max 7
                if dev_level < 7:
                    dev_level += 1

            new_state = pack_micro_hex(biome_id, attrs["faction_id"], resource_id, dev_level, active_overlay_id, spark)
            if new_state != state_int:
                updates.append((new_state, hex_id))

        if updates:
            cursor.executemany("UPDATE micro_hexes SET state_int=? WHERE id=?", updates)
            conn.commit()

        conn.close()

    def fold_micro_to_meso(self):
        """Fold Micro layer coordinates up to update Meso economy values."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Query all Meso-hex centers
        cursor.execute("SELECT id, center_x, center_y FROM meso_hexes")
        meso_rows = cursor.fetchall()

        for meso_id, cx, cy in meso_rows:
            # Query all micro-hexes within offset distance of 3
            cursor.execute("""
            SELECT state_int FROM micro_hexes
            WHERE x BETWEEN ? AND ? AND y BETWEEN ? AND ?
            """, (cx - 2, cx + 2, cy - 2, cy + 2))
            
            micro_states = cursor.fetchall()
            if not micro_states:
                continue

            total_timber = 0
            total_iron = 0
            total_food = 0
            dev_sum = 0
            
            for (state_int,) in micro_states:
                attrs = unpack_micro_hex(state_int)
                dev_sum += attrs["dev_level"]
                
                # Check for Ouroboros resources and translate to base resource units
                res = attrs["resource"]
                if "Gold" in res or "Tungsten" in res:
                    total_iron += 5
                elif "Timber" in res:
                    total_timber += 15
                elif "Food" in res:
                    total_food += 20
                else:
                    # Generic resource allocation
                    total_food += 2
                    total_timber += 2

            # Calculate average development
            avg_dev = min(10, dev_sum // len(micro_states))

            # Accumulate resources to the Meso hex
            cursor.execute("""
            UPDATE meso_hexes
            SET iron = iron + ?, timber = timber + ?, food = food + ?, development = ?
            WHERE id = ?
            """, (total_iron, total_timber, total_food, avg_dev, meso_id))

        conn.commit()
        conn.close()
        print("Meso-folding cycle complete.")

    def extract_snapshot(self, min_x: int, max_x: int, min_y: int, max_y: int) -> list:
        """Query and return descriptive snapshots of a rectangular area of the world map."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        SELECT x, y, state_int FROM micro_hexes
        WHERE x BETWEEN ? AND ? AND y BETWEEN ? AND ?
        """, (min_x, max_x, min_y, max_y))

        results = []
        for x, y, state_int in cursor.fetchall():
            attrs = unpack_micro_hex(state_int)
            attrs["x"] = x
            attrs["y"] = y
            results.append(attrs)

        conn.close()
        return results

    def inject_event(self, hex_x: int, hex_y: int, modification: dict):
        """Inject an event/change directly into a specific micro-hex coordinate (e.g. from TTRPG results)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT state_int FROM micro_hexes WHERE x=? AND y=?", (hex_x, hex_y))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"Coordinate ({hex_x}, {hex_y}) does not exist in database.")

        attrs = unpack_micro_hex(row[0])
        
        # Apply updates if provided
        biome = modification.get("biome_id", attrs["biome_id"])
        faction = modification.get("faction_id", attrs["faction_id"])
        resource = modification.get("resource_id", attrs["resource_id"])
        dev_level = modification.get("dev_level", attrs["dev_level"])
        overlay = modification.get("overlay_id", attrs["overlay_id"])
        spark = int(modification.get("spark", attrs["spark"]))

        new_state = pack_micro_hex(biome, faction, resource, dev_level, overlay, spark)
        cursor.execute("UPDATE micro_hexes SET state_int=? WHERE x=? AND y=?", (new_state, hex_x, hex_y))
        
        conn.commit()
        conn.close()
        print(f"Successfully injected update to micro-hex at ({hex_x}, {hex_y}).")
