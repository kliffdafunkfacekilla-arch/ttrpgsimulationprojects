class WorldSimulator:
    """
    Clean rewrite of FractalEngine and TTRPGWorldModel.
    Handles world state, ticking time, and weather.
    """
    def __init__(self):
        self.tick_count = 0
        self.current_season = "Spring"
        self.weather = "Clear"
        
    def advance_time(self, ticks: int = 1):
        self.tick_count += ticks
        if self.tick_count % 100 == 0:
            self.weather = "Raining" if self.weather == "Clear" else "Clear"
        return {"tick": self.tick_count, "weather": self.weather, "season": self.current_season}
