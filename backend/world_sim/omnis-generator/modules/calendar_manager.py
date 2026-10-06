# calendar_manager.py
import json
import os

# Resolve project root (two levels up from this module file)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def load_settings():
    """
    Load calendar settings from JSON files.
    Priority: world_settings.json > default_settings.json > hardcoded defaults.
    """
    # Try world_settings.json first (user-customized)
    world_path = os.path.join(_PROJECT_ROOT, 'world_settings.json')
    if os.path.isfile(world_path):
        try:
            with open(world_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if 'calendar' in data:
                return data['calendar']
        except (json.JSONDecodeError, IOError):
            pass

    # Fall back to default_settings.json
    default_path = os.path.join(_PROJECT_ROOT, 'default_settings.json')
    if os.path.isfile(default_path):
        try:
            with open(default_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if 'calendar' in data:
                return data['calendar']
        except (json.JSONDecodeError, IOError):
            pass

    # Final fallback: hardcoded defaults
    return {
        "days_per_year": 360,
        "months": [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ],
        "seasons": [
            {"name": "Spring", "start_day": 0, "end_day": 89, "growth_mod": 1.2, "travel_cost_mod": 1.0},
            {"name": "Summer", "start_day": 90, "end_day": 179, "growth_mod": 1.5, "travel_cost_mod": 1.0},
            {"name": "Autumn", "start_day": 180, "end_day": 269, "growth_mod": 0.8, "travel_cost_mod": 1.2},
            {"name": "Winter", "start_day": 270, "end_day": 359, "growth_mod": 0.1, "travel_cost_mod": 2.5}
        ],
        "moons": [
            {
                "name": "Aether-Moon",
                "cycle_days": 30,
                "phases": ["New", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
                           "Full", "Waning Gibbous", "Third Quarter", "Waning Crescent"]
            }
        ]
    }


class CalendarManager:
    def __init__(self, days_per_year=None, months=None, settings=None):
        # If a settings dict is passed, use it; otherwise call load_settings()
        if settings is None:
            settings = load_settings()

        self.days_per_year = settings.get('days_per_year', 360)
        self.months = settings.get('months', [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ])
        self.seasons = settings.get('seasons', [
            {"name": "Spring", "start_day": 0, "end_day": 89, "growth_mod": 1.2, "travel_cost_mod": 1.0},
            {"name": "Summer", "start_day": 90, "end_day": 179, "growth_mod": 1.5, "travel_cost_mod": 1.0},
            {"name": "Autumn", "start_day": 180, "end_day": 269, "growth_mod": 0.8, "travel_cost_mod": 1.2},
            {"name": "Winter", "start_day": 270, "end_day": 359, "growth_mod": 0.1, "travel_cost_mod": 2.5}
        ])
        self.moons = settings.get('moons', [
            {"name": "Aether-Moon", "cycle_days": 30,
             "phases": ["New", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
                        "Full", "Waning Gibbous", "Third Quarter", "Waning Crescent"]}
        ])

        # Allow explicit overrides via constructor for backwards compatibility
        if days_per_year is not None:
            self.days_per_year = days_per_year
        if months is not None:
            self.months = months

        self.days_per_month = self.days_per_year // max(1, len(self.months))

    def get_season(self, current_day):
        """Return the season name for the given day, using loaded season bounds."""
        d = current_day % self.days_per_year
        for season in self.seasons:
            if season['start_day'] <= d <= season['end_day']:
                return season['name']
        # If no season matched (shouldn't happen with proper config), return last season
        return self.seasons[-1]['name'] if self.seasons else "Unknown"

    def apply_seasonal_modifier(self, biome_type, current_day):
        """Return growth and travel_cost modifiers from the matching season data."""
        season_name = self.get_season(current_day)
        for season in self.seasons:
            if season['name'] == season_name:
                return {
                    "growth": season.get('growth_mod', 1.0),
                    "travel_cost": season.get('travel_cost_mod', 1.0)
                }
        # Fallback if season not found in list
        return {"growth": 1.0, "travel_cost": 1.0}

    def get_month_name(self, current_day):
        """Return the month name based on the loaded months list and days_per_year."""
        if not self.months:
            return "Unknown"
        d = current_day % self.days_per_year
        month_index = d // max(1, self.days_per_month)
        # Clamp to valid index range
        month_index = min(month_index, len(self.months) - 1)
        return self.months[month_index]

    def get_moon_phase(self, current_day):
        """
        Return a dict of moon phase info for each moon at the given day.
        Each entry has the moon name and the current phase string.
        """
        results = {}
        for moon in self.moons:
            name = moon.get('name', 'Unknown Moon')
            cycle_days = moon.get('cycle_days', 30)
            phases = moon.get('phases', ["Full"])
            # Determine which phase index we are in
            day_in_cycle = current_day % cycle_days
            phase_length = cycle_days / max(1, len(phases))
            phase_index = int(day_in_cycle / phase_length)
            phase_index = min(phase_index, len(phases) - 1)
            results[name] = phases[phase_index]
        return results
