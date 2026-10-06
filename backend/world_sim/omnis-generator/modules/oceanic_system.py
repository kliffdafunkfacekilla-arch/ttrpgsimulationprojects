import random
import math

class OceanicSystem:
    def __init__(self):
        # Base global ocean metrics
        self.global_temperature = 12.0 # Celsius avg deep sea
        self.salinity = 35.0 # ppt
        self.water_quality_index = 1.0 # 1.0 is pristine, drops with chaos/pollution

    def calculate_tidal_tick(self, delta_time_hours):
        """Simulates currents and tide shifts, moving resources and spreading chaos underwater."""
        shifts = []

        # In a real grid iteration, we would move vectors across cells.
        # For now, we simulate the macro-effect of tides on the global water quality.
        tide_strength = random.uniform(0.5, 1.5)

        if tide_strength > 1.2:
            shifts.append("High Tides: Upwelling brings nutrients to surface reefs.")
            # Boost water quality slightly as nutrients flush
            self.water_quality_index = min(1.0, self.water_quality_index + 0.05)
        elif tide_strength < 0.8:
            shifts.append("Low Tides: Stagnant waters in shallow bays.")
            self.water_quality_index = max(0.0, self.water_quality_index - 0.02)

        return {
            "tide_strength": tide_strength,
            "water_quality": self.water_quality_index,
            "events": shifts
        }

    def process_aquatic_ecology(self, groups, water_quality):
        """Adjusts underwater ecology based on oceanic metrics rather than land weather."""
        logs = []
        for group in groups:
            # Check if this group has aquatic assets (e.g. kelp farms)
            kelp_farms = getattr(group, "kelp_farms_count", 0)
            if kelp_farms > 0:
                # Water quality heavily dictates kelp growth
                base_yield = kelp_farms * 100
                actual_yield = base_yield * water_quality

                # Update inventory if it exists
                if not hasattr(group, "inventory"):
                    group.inventory = {}

                group.inventory["Kelp"] = group.inventory.get("Kelp", 0) + actual_yield
                logs.append(f"[{group.name}] Harvested {actual_yield:.1f} Kelp (Quality Mod: {water_quality:.2f})")

            # Deep sea chaos anomalies (Reality storms leaking into thermal vents)
            if group.chaos_level > 0.8:
                if random.random() < 0.3:
                    logs.append(f"[{group.name}] ABYSSAL SURGE: High chaos ignited a thermal vent, spawning deep-sea nulls!")
                    group.population -= random.randint(50, 200) # Casualties from deep sea attack

        return logs

# Singleton instance
ocean_sim = OceanicSystem()

def run_oceanic_tick(delta_time_hours, groups):
    result = ocean_sim.calculate_tidal_tick(delta_time_hours)
    ecology_logs = ocean_sim.process_aquatic_ecology(groups, result["water_quality"])

    return {
        "metrics": result,
        "logs": ecology_logs
    }
