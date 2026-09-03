class Pathfinder:
    @staticmethod
    def plan_regional_path(grid_data: dict, start: tuple, end: tuple):
        """
        Calculates a path across the Tier 2 Regional Grid.
        Currently returns a direct line (breadth-first placeholder).
        """
        # grid_data is expected to be a 20x20 grid
        return {
            "path": [start, end], 
            "travel_time_hours": 2.0,
            "stamina_cost": 5
        }

    @staticmethod
    def plan_local_path(grid_data: dict, start: tuple, end: tuple):
        """
        Calculates a path across the Tier 3 Local Grid.
        Currently returns a direct line.
        """
        # grid_data is expected to be a 100x100 grid
        return {
            "path": [start, end],
            "travel_time_hours": 0.5,
            "stamina_cost": 2
        }
