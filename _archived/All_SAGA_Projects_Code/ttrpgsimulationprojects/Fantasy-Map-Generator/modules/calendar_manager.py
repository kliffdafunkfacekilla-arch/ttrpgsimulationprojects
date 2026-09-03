# calendar_manager.py

class CalendarManager:
    def __init__(self, days_per_year=360, months=12):
        self.days_per_year = days_per_year
        self.months = months
        self.days_per_month = days_per_year // months

    def get_season(self, current_day):
        # 0-89 Spring, 90-179 Summer, 180-269 Autumn, 270-359 Winter
        d = current_day % self.days_per_year
        if d < 90: return "Spring"
        if d < 180: return "Summer"
        if d < 270: return "Autumn"
        return "Winter"

    def apply_seasonal_modifier(self, biome_type, current_day):
        season = self.get_season(current_day)
        # Scaling travel cost and growth rate based on lore-rot
        modifiers = {
            "Spring": {"growth": 1.2, "travel_cost": 1.0},
            "Summer": {"growth": 1.5, "travel_cost": 1.0},
            "Autumn": {"growth": 0.8, "travel_cost": 1.2},
            "Winter": {"growth": 0.1, "travel_cost": 2.5} # Winter Travel Rot
        }
        return modifiers[season]
