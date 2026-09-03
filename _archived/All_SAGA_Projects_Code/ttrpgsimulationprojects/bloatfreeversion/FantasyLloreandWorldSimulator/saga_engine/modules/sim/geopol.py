import random
from typing import List, Dict, Set
from saga_engine.core.simulation import SimulationOrgan
from saga_engine.core.bus import EventBus
from saga_engine.core.state import CampaignState
from saga_engine.core.chronicler import Chronicler
from saga_engine.core.world_loader import WorldLoader

class SovereignAI(SimulationOrgan):
    """
    Geopolitical Simulation Organ.
    Handles faction expansion, borders, and territorial friction.
    """

    def __init__(self, bus: EventBus, state: CampaignState, chronicler: Chronicler, loader: WorldLoader):
        super().__init__(bus, state, chronicler, loader)
        self.expansion_threshold = 0.7  # Chance to expand per day

    def run_daily(self):
        """Simulates geopolitical shifts across the Shatterlands."""
        # 1. Map current territories
        current_territories: Dict[int, List[str]] = {}
        for coord_key, hex_data in self.loader.hex_data.items():
            faction_id = hex_data.get("faction_id", 0)
            if faction_id != 0:
                if faction_id not in current_territories:
                    current_territories[faction_id] = []
                current_territories[faction_id].append(coord_key)

        # 2. Process Expansion for each faction
        for faction_id, owned_hexes in current_territories.items():
            self._process_faction_expansion(faction_id, owned_hexes)

    def _process_faction_expansion(self, faction_id: int, owned_hexes: List[str]):
        """Attempts to claim adjacent hexes for a faction."""
        # Biome expansion difficulty (Wasteland is harder, Grassland easier)
        biome_difficulty = {
            0: 1.0,  # Ocean (Impossible for ground factions, maybe)
            1: 0.8,  # Tundra
            2: 0.3,  # Grassland
            3: 0.4,  # Forest
            4: 0.6,  # Desert
            8: 0.9,  # Wasteland
            18: 1.0  # Chaos Zone (Unclaimable)
        }

        # Find potential hexes to claim (neighbors of owned hexes)
        candidates: Set[str] = set()
        for hex_key in owned_hexes:
            # hex_key is "[q, r]"
            q_r = eval(hex_key) # Simple way to get [q, r]
            neighbors = self.loader.get_neighbor_coords(q_r[0], q_r[1])
            for nq, nr in neighbors:
                n_key = f"[{nq}, {nr}]"
                if n_key not in owned_hexes:
                    candidates.add(n_key)

        # Attempt to claim candidates
        claims_made = 0
        for cand_key in candidates:
            cand_data = self.loader.hex_data.get(cand_key)
            if not cand_data or cand_data.get("faction_id", 0) != 0:
                continue
            
            biome_id = cand_data.get("biome_id", 0)
            difficulty = biome_difficulty.get(biome_id, 0.5)
            
            # Expansion check
            if random.random() > difficulty and random.random() < self.expansion_threshold:
                # SUCCESS: Claim the hex
                cand_data["faction_id"] = faction_id
                claims_made += 1
        
        if claims_made > 0:
            self.chronicler.log_event("FACTION", "EXPANSION", 
                                     f"Faction {faction_id} has claimed {claims_made} new hexes.", 
                                     game_time=str(self.state.time))
