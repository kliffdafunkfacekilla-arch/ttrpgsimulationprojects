import random
from saga_engine.core.simulation import SimulationOrgan
from saga_engine.core.bus import EventBus
from saga_engine.core.state import CampaignState
from saga_engine.core.chronicler import Chronicler
from saga_engine.core.world_loader import WorldLoader

class Biosphere(SimulationOrgan):
    """
    Ecological and Biological Simulation Organ.
    Manages population growth, resource depletion, and regional fertility.
    """

    def __init__(self, bus: EventBus, state: CampaignState, chronicler: Chronicler, loader: WorldLoader):
        super().__init__(bus, state, chronicler, loader)
        # Biome Fertility % (Daily growth bonus)
        self.fertility = {
            2: 0.05,  # Grassland
            3: 0.03,  # Forest
            6: 0.02,  # Swamp
            7: 0.02,  # Hills
            4: -0.05, # Desert
            1: -0.02, # Tundra
            8: -0.10, # Wasteland
        }

    def run_daily(self):
        """Processes ecological shifts across the Shatterlands."""
        meta = self.state.dynamic_world.hex_metadata
        total_growth = 0
        
        for coord_key, hex_data in self.loader.hex_data.items():
            q_r = eval(coord_key)
            hex_id = f"{q_r[0]},{q_r[1]}"
            
            # 1. Get current population
            pop = hex_data.get("population", 0)
            biome_id = hex_data.get("biome_id", 0)
            
            # 2. Base Growth Logic
            # If population is zero, have a tiny chance to settle in fertile lands
            if pop == 0:
                if biome_id in [2, 3] and random.random() < 0.001:
                    new_pop = random.randint(10, 50)
                    hex_data["population"] = new_pop
                    total_growth += new_pop
                    self.chronicler.log_event("ECOLOGY", "SETTLEMENT", 
                                             f"New settlers have arrived in Hex {hex_id}", 
                                             game_time=str(self.state.time))
                continue

            # Existing population growth
            bonus = self.fertility.get(biome_id, 0.0)
            
            # Modifier based on moisture (from AetherFlow)
            h_meta = meta.get(hex_id, {})
            moisture = h_meta.get("moisture", 0.5)
            # Ideal moisture is 0.6 to 0.8
            moisture_mod = 1.0 - abs(moisture - 0.7) * 2.0
            
            net_growth_rate = bonus * max(0.1, moisture_mod)
            pop_change = int(pop * net_growth_rate)
            
            # Natural attrition if resources are low (hypothetical tension check)
            if h_meta.get("tension", 0.0) > 0.8:
                pop_change -= int(pop * 0.1)

            if pop_change != 0:
                hex_data["population"] = max(0, pop + pop_change)
                total_growth += pop_change

        if total_growth > 0:
            self.chronicler.log_event("ECOLOGY", "GROWTH", 
                                     f"Global population has shifted by {total_growth} units.", 
                                     game_time=str(self.state.time))
