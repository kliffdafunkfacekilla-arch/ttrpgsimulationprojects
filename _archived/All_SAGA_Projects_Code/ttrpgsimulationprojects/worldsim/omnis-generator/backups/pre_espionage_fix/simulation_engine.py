# simulation_engine.py
import mesa
import networkx as nx
import json
import random
import os
import sys
from database import get_db_connection

# Ensure modules directory is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

from calendar_manager import CalendarManager
from weather_system import calculate_weather as calculate_aether_weather
from magistar_plugin import calculate_reality_spike
from oceanic_system import run_oceanic_tick
from expansion_system import run_expansion_tick
from ecology_system import process_global_ecology_tick
from rules_engine import (
    process_well_being_tick,
    process_living_world_tick,
    process_global_trade_and_conflict,
    calculate_tech_level,
    get_unlocked_transport,
    get_unlocked_buildings
)
from diplomacy_system import process_diplomacy_tick
from fringe_system import process_fringe_tick

def serialize_diplomacy(diplomacy):
    """Converts diplomacy dict (which has tuple keys in relations) to JSON string safely."""
    if not diplomacy:
        return "{}"
    ser_relations = {}
    for (f1, f2), val in diplomacy.get("relations", {}).items():
        ser_relations[f"{f1},{f2}"] = val
    data = dict(diplomacy)
    data["relations"] = ser_relations
    return json.dumps(data)

def deserialize_diplomacy(json_str):
    """Converts a diplomacy JSON string back to a dictionary with tuple keys for relations."""
    if not json_str:
        return {"relations": {}, "wars": [], "alliances": []}
    try:
        data = json.loads(json_str)
    except Exception:
        return {"relations": {}, "wars": [], "alliances": []}
    
    relations = {}
    for k, val in data.get("relations", {}).items():
        parts = k.split(',')
        if len(parts) == 2:
            relations[(parts[0], parts[1])] = val
        else:
            relations[k] = val
    data["relations"] = relations
    return data


class CellAgent(mesa.Agent):
    def __init__(self, unique_id, model, cell_data):
        super().__init__(unique_id, model)
        self.cell_id = cell_data['id']
        self.is_underwater = cell_data['depth_elevation'] < 0
        self.biome = cell_data['biome']
        self.elevation = cell_data['elevation']
        self.food_supply = cell_data.get('food_supply', 0.5)
        self.chaos_saturation = cell_data.get('chaos_saturation', 0.0)
        self.chaos_base_modifier = cell_data.get('chaos_base_modifier', 0.0)
        self.weather = cell_data.get('weather', 'Clear')
        self.controlling_burg_id = cell_data.get('controlling_burg_id')
        
        # JSON fields
        self.cults_influence = json.loads(cell_data['cults_json']) if cell_data.get('cults_json') else {}
        self.fringe_influence = json.loads(cell_data['fringe_json']) if cell_data.get('fringe_json') else {}
        self.flora = json.loads(cell_data['flora_json']) if cell_data.get('flora_json') else {"name": "flora_stone_root", "population": 50.0}
        self.fauna = json.loads(cell_data['fauna_json']) if cell_data.get('fauna_json') else {"name": "fauna_timber_wolf", "population": 20.0}
        
        self.has_mutated_wildlife = False
        self._changed = False

    def stage_environment(self):
        pass

    def stage_economy(self):
        pass

    def stage_diplomacy(self):
        pass


class FactionAgent(mesa.Agent):
    def __init__(self, unique_id, model, faction_data):
        super().__init__(unique_id, model)
        self.macro_group_id = faction_data['id']
        self.cell_id = faction_data['cell_id']
        self.faction_id = faction_data['faction_id']
        self.faction_name = faction_data['faction_name']
        self.is_capital = faction_data.get('is_capital', 0)
        
        # Load simulation variables
        self.chaos_level = faction_data.get('chaos_level', 0.0)
        self.population = faction_data.get('population', 100)
        self.discontent = faction_data.get('discontent', 0.0)
        self.crime_level = faction_data.get('crime_level', 0.0)
        self.food_supply = faction_data.get('food_supply', 0.5)
        self.physical_well_being = faction_data.get('physical_well_being', 1.0)
        self.mental_well_being = faction_data.get('mental_well_being', 1.0)
        self.safety_rating = faction_data.get('safety_rating', 0.5)
        self.pressure = faction_data.get('pressure', 0.0)
        self.magistar_id = faction_data.get('magistar_id')
        self.is_active = faction_data.get('is_active', 1)
        self.distance_to_chaos_structure = faction_data.get('distance_to_chaos_structure', 0.0)
        self.distance_to_convergence = faction_data.get('distance_to_convergence', 0.0)
        
        # Structure counts
        self.camps_count = faction_data.get('camps_count', 0)
        self.mines_count = faction_data.get('mines_count', 0)
        self.farms_count = faction_data.get('farms_count', 0)
        self.barracks_count = faction_data.get('barracks_count', 0)
        self.watchtowers_count = faction_data.get('watchtowers_count', 0)
        self.docks_count = faction_data.get('docks_count', 0)
        self.walls_count = faction_data.get('walls_count', 0)
        self.kelp_farms_count = faction_data.get('kelp_farms_count', 0)
        self.underwater_domes_count = faction_data.get('underwater_domes_count', 0)
        self.coral_mines_count = faction_data.get('coral_mines_count', 0)
        self.reef_walls_count = faction_data.get('reef_walls_count', 0)
        
        # Happiness & Cults
        self.cult_infiltration = faction_data.get('cult_infiltration', 0.05)
        self.cult_population = faction_data.get('cult_population', 0.0)
        self.cult_devoted = faction_data.get('cult_devoted', 0.0)
        self.flora_ghost_flower = faction_data.get('flora_ghost_flower', 100.0)
        self.flora_stone_root = faction_data.get('flora_stone_root', 100.0)
        self.fauna_sky_grazer = faction_data.get('fauna_sky_grazer', 50.0)
        self.fauna_timber_wolf = faction_data.get('fauna_timber_wolf', 10.0)
        self.domestic_greenhouses = faction_data.get('domestic_greenhouses', 0)
        self.domestic_orchards = faction_data.get('domestic_orchards', 0)
        self.domestic_pens = faction_data.get('domestic_pens', 0)
        self.domestic_kennels = faction_data.get('domestic_kennels', 0)
        self.churches_count = faction_data.get('churches_count', 0)
        self.theatres_count = faction_data.get('theatres_count', 0)
        self.arenas_count = faction_data.get('arenas_count', 0)
        self.gambling_dens_count = faction_data.get('gambling_dens_count', 0)
        self.black_markets_count = faction_data.get('black_markets_count', 0)
        self.workshops_count = faction_data.get('workshops_count', 0)
        
        # JSON-serialized fields
        self.settlements = json.loads(faction_data['settlements_json']) if faction_data.get('settlements_json') else []
        self.paragon = json.loads(faction_data['paragon_json']) if faction_data.get('paragon_json') else None
        self.inventory = json.loads(faction_data['inventory_json']) if faction_data.get('inventory_json') else {}
        self.hub_wealth = faction_data.get('hub_wealth', 0.0)
        self.ruined_hub_penalty = faction_data.get('ruined_hub_penalty', 0.0)
        
        self.active_tags = []
        self._changed = False
        self._event_logs = []

    # Map property aliases required by original modules
    @property
    def name(self):
        return self.faction_name

    @name.setter
    def name(self, value):
        self.faction_name = value
        self._changed = True

    @property
    def id(self):
        return self.macro_group_id

    @id.setter
    def id(self, value):
        self.macro_group_id = value
        self._changed = True

    @property
    def settlement_populations(self):
        return self.settlements

    @settlement_populations.setter
    def settlement_populations(self, value):
        self.settlements = value
        self._changed = True

    def stage_environment(self):
        pass

    def stage_economy(self):
        pass

    def stage_diplomacy(self):
        pass


class TTRPGWorldModel(mesa.Model):
    def __init__(self):
        super().__init__()
        self.current_tick = 0
        self._all_agents = []
        
        # Load cells and build the NetworkX graph
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('SELECT cell_a, cell_b FROM cell_edges')
        edges = [(r['cell_a'], r['cell_b']) for r in cur.fetchall()]
        
        self.G = nx.Graph()
        cur.execute('SELECT id FROM cells')
        for (cell_id,) in cur.fetchall():
            self.G.add_node(cell_id)
        self.G.add_edges_from(edges)
        
        self.grid = mesa.space.NetworkGrid(self.G)
        
        # Spawn CellAgents
        cur.execute('SELECT * FROM cells')
        cols = [desc[0] for desc in cur.description]
        cell_records = [dict(zip(cols, row)) for row in cur.fetchall()]
        
        for record in cell_records:
            agent = CellAgent(f'cell_{record["id"]}', self, record)
            self.grid.place_agent(agent, record['id'])
            self._all_agents.append(agent)
            
        # Spawn FactionAgents on cells
        cur.execute('SELECT * FROM macro_groups')
        cols = [desc[0] for desc in cur.description]
        faction_records = [dict(zip(cols, row)) for row in cur.fetchall()]
        
        for record in faction_records:
            agent = FactionAgent(f'faction_{record["id"]}', self, record)
            self.grid.place_agent(agent, record['cell_id'])
            self._all_agents.append(agent)
            
        cur.close()
        conn.close()

    def step(self):
        # 1. Load prisons, global state and resource nodes
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('SELECT * FROM global_state WHERE id = 1')
        g_state = dict(cur.fetchone())
        current_day = g_state['current_day']
        warden_pop = g_state['warden_population']
        warden_recruits = g_state['warden_recruits_accumulated']
        
        cur.execute('SELECT * FROM dragon_prisons')
        prisons_rows = cur.fetchall()
        prisons_dict = {r['magistar_id'] if 'magistar_id' in r.keys() else f"prison_{r['id']}": r['seal_integrity'] for r in prisons_rows}
        # Standard prison names mapping fallback
        prisons_keys = ["Tiraton", "Stagus", "Metrion", "Aurgenas", "Vecelo", "Lophex", "Tyrustis", "Opecten", "Carulkem", "Termhill", "Virantor", "Gavusrix"]
        for idx, r in enumerate(prisons_rows):
            name = prisons_keys[idx] if idx < len(prisons_keys) else f"prison_{r['id']}"
            prisons_dict[name] = r['seal_integrity']
        prisons_dict["warden_population"] = warden_pop
        prisons_dict["warden_recruits_accumulated"] = warden_recruits
        
        cur.execute('SELECT * FROM resource_nodes')
        resource_nodes = [dict(r) for r in cur.fetchall()]
        
        cur.close()
        conn.close()
        
        # 2. Master loops sequence
        cal = CalendarManager()
        current_day += 1
        
        # Get cell agents list
        cell_agents = [a for a in self._all_agents if isinstance(a, CellAgent)]
        faction_agents = [a for a in self._all_agents if isinstance(a, FactionAgent)]
        
        # Weather calculations
        for cell in cell_agents:
            # Check if chaos_saturation changed
            old_chaos = cell.chaos_saturation
            new_chaos = max(cell.chaos_saturation, cell.chaos_base_modifier)
            if new_chaos != old_chaos:
                cell.chaos_saturation = new_chaos
                cell._changed = True
                
            is_oceanic = cell.is_underwater or cell.biome == 'Ocean'
            # Look up magistar prison closest
            mg_group = next((f for f in faction_agents if f.cell_id == cell.cell_id), None)
            magistar_id = mg_group.magistar_id if mg_group else "Tiraton"
            
            w_info = calculate_aether_weather(cell.chaos_saturation, 0.5, magistar_id, is_oceanic)
            old_weather = cell.weather
            cell.weather = w_info['type']
            if cell.weather != old_weather:
                cell._changed = True
            
        # Oceanic systems
        groups_list = []
        for f in faction_agents:
            groups_list.append(f)
            
        ocean_res = run_oceanic_tick(8.0, groups_list) # 8 hours delta
        
        # AI Expansion & Trade Routes
        grid_grid_representation = []
        # Construct grid representations for expansion
        expansion_logs, routes, wealth_bonus, ruined_penalty = run_expansion_tick(groups_list, None)
        
        # Save bonuses to agents
        for f in faction_agents:
            f.hub_wealth = wealth_bonus.get(f.macro_group_id, 0.0)
            f.ruined_hub_penalty = ruined_penalty.get(f.macro_group_id, 0.0)
            
        # Global Cellular Ecology
        # Convert CellAgents to the ecology grid dictionary expected
        ecology_grid = {}
        for cell in cell_agents:
            ecology_grid[cell.cell_id] = {
                "id": cell.cell_id,
                "biome": cell.biome,
                "flora": cell.flora.get("name", "flora_stone_root"),
                "flora_pop": cell.flora.get("population", 50.0),
                "fauna": cell.fauna.get("name", "fauna_timber_wolf"),
                "fauna_pop": cell.fauna.get("population", 20.0),
                "neighbors": list(self.G.neighbors(cell.cell_id))
            }
            
        process_global_ecology_tick(ecology_grid, "Clear")
        
        # Save ecology results back to CellAgents (only if changed significantly)
        for cell in cell_agents:
            eco_data = ecology_grid.get(cell.cell_id)
            if eco_data:
                old_flora_name = cell.flora.get("name")
                old_flora_pop = cell.flora.get("population")
                old_fauna_name = cell.fauna.get("name")
                old_fauna_pop = cell.fauna.get("population")
                
                cell.flora = {"name": eco_data["flora"], "population": eco_data["flora_pop"]}
                cell.fauna = {"name": eco_data["fauna"], "population": eco_data["fauna_pop"]}
                
                if (cell.flora["name"] != old_flora_name or
                    cell.fauna["name"] != old_fauna_name or
                    abs(cell.flora["population"] - (old_flora_pop or 0.0)) > 0.01 or
                    abs(cell.fauna["population"] - (old_fauna_pop or 0.0)) > 0.01):
                    cell._changed = True

        # Inject into the scheduler shim for rules_engine import
        import scheduler
        scheduler._GLOBAL_ECOLOGY_GRID = ecology_grid

        # Wellbeing & Living World Tick
        tick_logs = []
        global_state_dict = {"current_day": current_day}
        
        for f in faction_agents:
            # Get seasonal modifier
            season_mod = cal.apply_seasonal_modifier(f.magistar_id if f.magistar_id else "Tiraton", current_day)
            reality_mod = calculate_reality_spike(f.magistar_id, f.is_active)
            
            # Local weather
            local_cell = next((c for c in cell_agents if c.cell_id == f.cell_id), None)
            local_weather_name = local_cell.weather if local_cell else "Stable"
            local_weather_dict = {"type": local_weather_name, "travel_cost": 1.0, "growth_mult": 1.0, "degradation_rate": 0.0}
            
            # Format group dict
            g_dict = {
                "id": f.macro_group_id,
                "name": f.faction_name,
                "population": f.population,
                "chaos_level": f.chaos_level,
                "pressure": f.pressure,
                "magistar_id": f.magistar_id,
                "is_active": f.is_active == 1,
                "physical_well_being": f.physical_well_being,
                "mental_well_being": f.mental_well_being,
                "crime_level": f.crime_level,
                "discontent": f.discontent,
                "camps_count": f.camps_count,
                "mines_count": f.mines_count,
                "docks_count": f.docks_count,
                "farms_count": f.farms_count,
                "watchtowers_count": f.watchtowers_count,
                "walls_count": f.walls_count,
                "barracks_count": f.barracks_count,
                "kelp_farms_count": f.kelp_farms_count,
                "underwater_domes_count": f.underwater_domes_count,
                "coral_mines_count": f.coral_mines_count,
                "reef_walls_count": f.reef_walls_count,
                "cult_infiltration": f.cult_infiltration,
                "cult_population": f.cult_population,
                "cult_devoted": f.cult_devoted,
                "distance_to_chaos_structure": f.distance_to_chaos_structure,
                "distance_to_convergence": f.distance_to_convergence,
                "flora_ghost_flower": f.flora_ghost_flower,
                "flora_stone_root": f.flora_stone_root,
                "fauna_sky_grazer": f.fauna_sky_grazer,
                "fauna_timber_wolf": f.fauna_timber_wolf,
                "domestic_greenhouses": f.domestic_greenhouses,
                "domestic_orchards": f.domestic_orchards,
                "domestic_pens": f.domestic_pens,
                "domestic_kennels": f.domestic_kennels,
                "churches_count": f.churches_count,
                "theatres_count": f.theatres_count,
                "arenas_count": f.arenas_count,
                "gambling_dens_count": f.gambling_dens_count,
                "black_markets_count": f.black_markets_count,
                "workshops_count": f.workshops_count,
                "paragon": f.paragon
            }
            
            # Format buildings dict
            buildings_dict = {
                "farms": f.farms_count,
                "watchtowers": f.watchtowers_count,
                "barracks": f.barracks_count,
                "walls": f.walls_count
            }
            
            # Process wellbeing
            stats = process_well_being_tick(
                g_dict,
                buildings_dict,
                f.chaos_level,
                hub_wealth_bonus=f.hub_wealth,
                ruined_hub_penalty=f.ruined_hub_penalty
            )
            
            # Process living world
            tick_res = process_living_world_tick(
                g_dict,
                f.inventory,
                current_day,
                season_mod,
                reality_mod,
                local_weather_dict,
                prisons=prisons_dict,
                global_state=global_state_dict,
                resource_nodes=resource_nodes
            )
            
            # Update attributes back
            f.population = tick_res["population"]
            f.physical_well_being = tick_res["physical_well_being"]
            f.mental_well_being = tick_res["mental_well_being"]
            f.crime_level = tick_res["crime_level"]
            f.discontent = tick_res["discontent"]
            f.inventory = tick_res["inventory"]
            f.cult_infiltration = tick_res["cult_infiltration"]
            f.cult_population = tick_res["cult_population"]
            f.cult_devoted = tick_res["cult_devoted"]
            
            f.farms_count = g_dict["farms_count"]
            f.watchtowers_count = g_dict["watchtowers_count"]
            f.barracks_count = g_dict["barracks_count"]
            f.mines_count = g_dict["mines_count"]
            f.walls_count = g_dict["walls_count"]
            f.camps_count = g_dict["camps_count"]
            f.docks_count = g_dict["docks_count"]
            f.kelp_farms_count = g_dict["kelp_farms_count"]
            f.underwater_domes_count = g_dict["underwater_domes_count"]
            f.coral_mines_count = g_dict["coral_mines_count"]
            f.reef_walls_count = g_dict["reef_walls_count"]
            f.churches_count = tick_res["churches_count"]
            f.theatres_count = tick_res["theatres_count"]
            f.arenas_count = tick_res["arenas_count"]
            f.gambling_dens_count = tick_res["gambling_dens_count"]
            f.black_markets_count = tick_res["black_markets_count"]
            f.workshops_count = g_dict["workshops_count"]
            f.paragon = tick_res.get("paragon")
            
            # Ecology back
            f.flora_ghost_flower = tick_res["flora_ghost_flower"]
            f.flora_stone_root = tick_res["flora_stone_root"]
            f.fauna_sky_grazer = tick_res["fauna_sky_grazer"]
            f.fauna_timber_wolf = tick_res["fauna_timber_wolf"]
            
            # Domestic back
            f.domestic_greenhouses = tick_res["domestic_greenhouses"]
            f.domestic_orchards = tick_res["domestic_orchards"]
            f.domestic_pens = tick_res["domestic_pens"]
            f.domestic_kennels = tick_res["domestic_kennels"]
            
            prisons_dict = tick_res["prisons"]
            
            # Collect logs
            for log in tick_res.get("logs", []):
                f._event_logs.append({"type": "SAGA", "desc": log, "severity": 1})
                
            # Cultist spread to adjacent factions
            if tick_res.get("spread_target"):
                target_name, amount = tick_res["spread_target"]
                target_f = next((tg for tg in faction_agents if tg.faction_name == target_name), None)
                if target_f:
                    target_f.cult_population = min(target_f.population, target_f.cult_population + amount)
                    target_f.cult_infiltration = target_f.cult_population / max(1.0, target_f.population)
                    target_f._changed = True
                    f._event_logs.append({
                        "type": "CULT_SPREAD",
                        "desc": f"Cult branched from {f.faction_name} into {target_name}, seeding {amount} cultists.",
                        "severity": 3
                     })
            
            # Scale settlement populations
            scale_ratio = f.population / max(1.0, sum(f.settlements))
            f.settlements = [int(p * scale_ratio) for p in f.settlements]
            
            f._changed = True

        # Inter-Faction Diplomacy
        groups_by_name_dict = {f.faction_name: f.__dict__ for f in faction_agents}
        diplomacy_logs = []
        diplomacy_status = deserialize_diplomacy(g_state.get('diplomacy_json', '{}'))
        process_diplomacy_tick(diplomacy_status, groups_by_name_dict, diplomacy_logs)
        for log in diplomacy_logs:
            tick_logs.append((self.current_tick, "DIPLOMACY", log, 3))
            
        # Global Trade and Conflict
        territory_changes = []
        process_global_trade_and_conflict(groups_list, tick_logs, resource_nodes, territory_changes)
        
        # Apply territory expansions
        for src_cid, dest_cid, faction_name in territory_changes:
            cell_dest = next((c for c in cell_agents if c.cell_id == dest_cid), None)
            if cell_dest:
                cell_src = next((c for c in cell_agents if c.cell_id == src_cid), None)
                if cell_src:
                    cell_dest.controlling_burg_id = cell_src.controlling_burg_id
                    cell_dest._changed = True
                    tick_logs.append((self.current_tick, "CONQUEST", f"{faction_name} expanded influence to cell {dest_cid}!", 5))

        # Fringe Group Operations
        fringe_logs = []
        fringe_groups = json.loads(g_state.get('fringe_groups_json', '{}'))
        process_fringe_tick(fringe_groups, groups_by_name_dict, diplomacy_status, fringe_logs)
        for log in fringe_logs:
            tick_logs.append((self.current_tick, "FRINGE_OPS", log, 2))
            
        # Convergence void drain
        avg_seal = sum(prisons_dict.get(name, 1.0) for name in prisons_keys) / 12.0
        if avg_seal < 0.75:
            for f in faction_agents:
                proximity_mult = 1.0 - f.distance_to_chaos_structure
                f.chaos_level = min(1.0, f.chaos_level + 0.04 * proximity_mult)
                f.pressure = min(1.0, f.pressure + 0.04 * proximity_mult)
                f._changed = True
            tick_logs.append((self.current_tick, "CONVERGENCE SURGE", f"Integrity at {avg_seal * 100:.0f}%. Chaos surging globally!", 5))
            
        # Grey Warden recruitment/decay
        warden_pop = prisons_dict.get("warden_population", 1500.0)
        warden_recruits = prisons_dict.get("warden_recruits_accumulated", 0.0)
        warden_decay = warden_pop * 0.08
        warden_pop = max(0.0, warden_pop - warden_decay + warden_recruits)
        
        prisons_dict["warden_population"] = warden_pop
        prisons_dict["warden_recruits_accumulated"] = 0.0
        tick_logs.append((self.current_tick, "WARDENS", f"🛡️ Grey Warden Population: {warden_pop:.0f} Sentinels (-{warden_decay:.0f} decay, +{warden_recruits:.0f} recruits)", 3))
        
        # Clean up depleted resource nodes
        depleted = [n for n in resource_nodes if n.get("yield_remaining", 1) <= 0]
        for d in depleted:
            tick_logs.append((self.current_tick, "RESOURCE", f"The {d['name']} node in cell {d['cell_id']} has been completely mined out!", 3))
        resource_nodes = [n for n in resource_nodes if n.get("yield_remaining", 1) > 0]
        
        # Dragonstone Meteor Strikes
        if avg_seal < 0.85 and random.random() < 0.15:
            target_cell = random.choice(cell_agents)
            matching_f = next((tg for tg in faction_agents if tg.cell_id == target_cell.cell_id), None)
            fid = matching_f.faction_id if matching_f else 0
            new_node = {
                "cell_id": target_cell.cell_id,
                "faction_id": fid,
                "name": "Dragonstone Crater",
                "icon": "🔮",
                "description": "Fresh meteor strike! Yields Dragonstone.",
                "yield_remaining": float(random.randint(30, 80)),
                "is_discovered": 1
            }
            resource_nodes.append(new_node)
            tick_logs.append((self.current_tick, "METEOR STRIKE", f"☄️ A meteor crashed in cell {target_cell.cell_id}, creating a fresh Dragonstone Crater!", 5))

        # 3. DB unified save transaction
        self._commit_to_database(current_day, warden_pop, prisons_dict, diplomacy_status, fringe_groups, resource_nodes, tick_logs)
        self.current_tick += 1

    def _commit_to_database(self, current_day, warden_pop, prisons_dict, diplomacy_status, fringe_groups, resource_nodes, tick_logs):
        cell_agents = [a for a in self._all_agents if isinstance(a, CellAgent)]
        faction_agents = [a for a in self._all_agents if isinstance(a, FactionAgent)]
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Start Transaction
        cur.execute('BEGIN TRANSACTION;')
        
        try:
            # 1. Bulk update dirty cells
            cell_updates = []
            for a in cell_agents:
                if a._changed:
                    cell_updates.append((
                        a.food_supply,
                        a.chaos_saturation,
                        a.weather,
                        a.controlling_burg_id,
                        json.dumps(a.cults_influence),
                        json.dumps(a.fringe_influence),
                        json.dumps(a.flora),
                        json.dumps(a.fauna),
                        a.cell_id
                     ))
                    a._changed = False
                    
            if cell_updates:
                cur.executemany('''
                    UPDATE cells 
                     SET food_supply = ?, chaos_saturation = ?, weather = ?, controlling_burg_id = ?, 
                        cults_json = ?, fringe_json = ?, flora_json = ?, fauna_json = ?
                    WHERE id = ?
                ''', cell_updates)
                
            # 2. Bulk update dirty macro groups
            faction_updates = []
            for f in faction_agents:
                if f._changed:
                    faction_updates.append((
                        f.chaos_level, f.population, f.discontent, f.crime_level, f.food_supply,
                        f.physical_well_being, f.mental_well_being, f.safety_rating,
                        f.camps_count, f.mines_count, f.farms_count, f.barracks_count, f.watchtowers_count,
                        f.pressure, f.is_active, f.docks_count, f.walls_count,
                        f.kelp_farms_count, f.underwater_domes_count, f.coral_mines_count, f.reef_walls_count,
                        f.cult_infiltration, f.cult_population, f.cult_devoted,
                        f.flora_ghost_flower, f.flora_stone_root, f.fauna_sky_grazer, f.fauna_timber_wolf,
                        f.domestic_greenhouses, f.domestic_orchards, f.domestic_pens, f.domestic_kennels,
                        f.churches_count, f.theatres_count, f.arenas_count, f.gambling_dens_count, f.black_markets_count, f.workshops_count,
                        json.dumps(f.settlements), json.dumps(f.paragon), json.dumps(f.inventory),
                        f.hub_wealth, f.ruined_hub_penalty,
                        f.macro_group_id
                    ))
                    f._changed = False
                    
            if faction_updates:
                cur.executemany('''
                    UPDATE macro_groups
                     SET chaos_level = ?, population = ?, discontent = ?, crime_level = ?, food_supply = ?,
                        physical_well_being = ?, mental_well_being = ?, safety_rating = ?,
                        camps_count = ?, mines_count = ?, farms_count = ?, barracks_count = ?, watchtowers_count = ?,
                        pressure = ?, is_active = ?, docks_count = ?, walls_count = ?,
                        kelp_farms_count = ?, underwater_domes_count = ?, coral_mines_count = ?, reef_walls_count = ?,
                        cult_infiltration = ?, cult_population = ?, cult_devoted = ?,
                        flora_ghost_flower = ?, flora_stone_root = ?, fauna_sky_grazer = ?, fauna_timber_wolf = ?,
                        domestic_greenhouses = ?, domestic_orchards = ?, domestic_pens = ?, domestic_kennels = ?,
                        churches_count = ?, theatres_count = ?, arenas_count = ?, gambling_dens_count = ?, black_markets_count = ?, workshops_count = ?,
                        settlements_json = ?, paragon_json = ?, inventory_json = ?,
                        hub_wealth = ?, ruined_hub_penalty = ?
                    WHERE id = ?
                ''', faction_updates)
                
            # 3. Update Prisons
            prison_updates = []
            prisons_keys = ["Tiraton", "Stagus", "Metrion", "Aurgenas", "Vecelo", "Lophex", "Tyrustis", "Opecten", "Carulkem", "Termhill", "Virantor", "Gavusrix"]
            for idx, key in enumerate(prisons_keys):
                seal = prisons_dict.get(key, 1.0)
                prison_updates.append((seal, idx + 1))
                
            cur.executemany('''
                UPDATE dragon_prisons
                SET seal_integrity = ?
                WHERE id = ?
            ''', prison_updates)
            
            # 4. Update Global State
            cur.execute('''
                UPDATE global_state
                SET current_day = ?, warden_population = ?, warden_recruits_accumulated = ?,
                    diplomacy_json = ?, fringe_groups_json = ?
                WHERE id = 1
            ''', (current_day, warden_pop, prisons_dict.get("warden_recruits_accumulated", 0.0),
                  serialize_diplomacy(diplomacy_status), json.dumps(fringe_groups)))
            
            # 5. Sync Resource Nodes table (re-insert all active nodes)
            cur.execute('DELETE FROM resource_nodes')
            for node in resource_nodes:
                cur.execute('''
                    INSERT INTO resource_nodes (cell_id, faction_id, name, icon, description, yield_remaining, is_discovered)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (node['cell_id'], node['faction_id'], node['name'], node['icon'], node['description'], node['yield_remaining'], node['is_discovered']))
                
            # 6. Insert simulation logs
            all_db_logs = []
            for f in faction_agents:
                for log in f._event_logs:
                    all_db_logs.append((self.current_tick, log['type'], f"{f.faction_name}: {log['desc']}", log['severity']))
                f._event_logs.clear()
            for tick, ev_type, desc, severity in tick_logs:
                all_db_logs.append((tick, ev_type, desc, severity))
                
            if all_db_logs:
                cur.executemany('''
                    INSERT INTO simulation_logs (tick_number, event_type, description, severity)
                    VALUES (?, ?, ?, ?)
                ''', all_db_logs)
                
            cur.execute('COMMIT;')
        except Exception as e:
            cur.execute('ROLLBACK;')
            print(f"Error executing bulk simulation step: {e}")
            raise e
        finally:
            cur.close()
            conn.close()
