import random
import collections
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from rules_engine import calculate_tech_level, get_unlocked_transport

class ExpansionSystem:
    def __init__(self):
        self.next_faction_id = 100
        self.biome_resources = {
            "mountain": "Stone",
            "forest": "Lumber",
            "plains": "Grain",
            "reef": "Kelp",
            "thermal": "Deep-Sea Vents",
            "desert": "Dragonstone"
        }
        self.active_trade_routes = []
        self.traffic_map = {} # (x,y) -> traffic_count
        # trade_hubs: (x,y) -> {"owner": faction_id, "decay": int, "ruined": bool}
        self.trade_hubs = {}

    def _find_trade_route(self, grid, start_tiles, target_id, max_depth=50, transports=None):
        if not start_tiles:
            return None
        if transports is None:
            transports = []
            
        has_naval = "Naval Travel" in transports
        has_airships = "Airships" in transports
            
        grid_height = len(grid)
        grid_width = len(grid[0])
        
        queue = collections.deque()
        visited = set()
        parent_map = {}
        
        for sx, sy in start_tiles:
            queue.append((sx, sy, 0))
            visited.add((sx, sy))
            parent_map[(sx, sy)] = None
            
        while queue:
            cx, cy, depth = queue.popleft()
            
            if depth > max_depth and not has_airships:
                continue
                
            for nx, ny in [(cx-1, cy), (cx+1, cy), (cx, cy-1), (cx, cy+1)]:
                if 0 <= nx < grid_width and 0 <= ny < grid_height:
                    if (nx, ny) not in visited:
                        cell = grid[ny][nx]
                        fid = cell.get("factionId")
                        biome = cell.get("biome")
                        
                        if not has_airships:
                            if biome in ["ocean", "abyssal"] and not has_naval:
                                continue
                            if fid is not None and fid != target_id:
                                continue
                        
                        visited.add((nx, ny))
                        parent_map[(nx, ny)] = (cx, cy)
                        
                        if fid == target_id:
                            path = []
                            curr = (nx, ny)
                            while curr is not None:
                                path.append(curr)
                                curr = parent_map[curr]
                            path.reverse()
                            return path
                            
                        queue.append((nx, ny, depth + 1))
                            
        return None

    def _score_tile_azgaar_style(self, grid, x, y, needed_resources):
        score = 1.0
        grid_height = len(grid)
        grid_width = len(grid[0])
        
        tdata = grid[y][x]
        biome = tdata.get("biome")
        
        if biome in ["desert", "abyssal"]:
            score *= 0.5
        elif biome in ["plains", "forest", "coastal"]:
            score *= 1.5
            
        b_res = self.biome_resources.get(biome)
        if b_res and b_res in needed_resources:
            score += 5.0
            
        is_coastal = False
        for nx, ny in [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]:
            if 0 <= nx < grid_width and 0 <= ny < grid_height:
                if grid[ny][nx].get("biome") in ["ocean", "coastal", "reef"]:
                    is_coastal = True
                    break
        if is_coastal:
            score += 3.0
            
        traffic = self.traffic_map.get((x, y), 0)
        if traffic > 0:
            score += (traffic * 2.0)
            
        return score

    def process_expansion(self, groups, grid):
        if not grid:
            return ["No map grid data found for expansion."], {}, {}
            
        logs = []
        
        # Decay active trade routes
        surviving_routes = []
        for route in self.active_trade_routes:
            # If it's a legacy route (just a list), convert it or drop it
            if isinstance(route, list):
                continue
            route["ttl"] -= 1
            if route["ttl"] > 0:
                surviving_routes.append(route)
        self.active_trade_routes = surviving_routes
        for key in list(self.traffic_map.keys()):
            self.traffic_map[key] = max(0, self.traffic_map[key] - 1)
            if self.traffic_map[key] == 0:
                del self.traffic_map[key]
                
        grid_height = len(grid)
        grid_width = len(grid[0])
        
        faction_tiles = {g.id: [] for g in groups}
        for y in range(grid_height):
            for x in range(grid_width):
                fid = grid[y][x].get("factionId")
                if fid in faction_tiles:
                    faction_tiles[fid].append((x, y))

        hub_wealth_bonuses = {} # fid -> wealth
        ruined_hub_penalties = {} # fid -> ruined_count

        for group in groups:
            owned = faction_tiles.get(group.id, [])
            if not owned:
                continue

            tech_lvl = calculate_tech_level(group.settlements)
            transports = get_unlocked_transport(tech_lvl)

            capacity = len(owned) * 1000
            housing_need = 0
            if group.population > capacity:
                housing_need = (group.population - capacity) / capacity

            resource_needs = {}
            if group.inventory.get("Stone", 0) < 50:
                resource_needs["Stone"] = 1.0
            if group.inventory.get("Lumber", 0) < 50:
                resource_needs["Lumber"] = 1.0

            # Process Trade Hub Wealth Generation & Decay
            for (hx, hy), hub_data in list(self.trade_hubs.items()):
                if hub_data["owner"] == group.id:
                    if self.traffic_map.get((hx, hy), 0) > 0:
                        # Active Hub
                        hub_data["decay"] = 10
                        if hub_data["ruined"]:
                            hub_data["ruined"] = False
                            logs.append(f"[{group.name}] A ruined Trade Hub was repopulated by new trade routes!")
                    else:
                        # Decaying Hub
                        hub_data["decay"] -= 1
                        if hub_data["decay"] <= 0 and not hub_data["ruined"]:
                            hub_data["ruined"] = True
                            logs.append(f"[{group.name}] A Trade Hub lost all traffic and withered into an Abandoned Ruin. Crime is rising.")
                            
                    # Tally penalties
                    if hub_data["ruined"]:
                        ruined_hub_penalties[group.id] = ruined_hub_penalties.get(group.id, 0) + 1
                        
                        # AI logic: Spend weapons to clear out bandits from ruined hub
                        if group.inventory.get("Basic Weapons", 0) >= 20:
                            group.inventory["Basic Weapons"] -= 20
                            del self.trade_hubs[(hx, hy)]
                            
                            bld = random.choice(["barracks", "watchtowers"])
                            if not hasattr(group, "buildings"):
                                group.buildings = {"farms": 1, "watchtowers": 1, "barracks": 0, "walls": 0}
                            group.buildings[bld] = group.buildings.get(bld, 0) + 1
                            
                            logs.append(f"[{group.name}] Deployed troops to clear out bandits at an Abandoned Trade Hub, converting the ruins into a {bld[:-1]}.")
                            ruined_hub_penalties[group.id] -= 1

            border_tiles = []
            for cx, cy in owned:
                for nx, ny in [(cx-1, cy), (cx+1, cy), (cx, cy-1), (cx, cy+1)]:
                    if 0 <= nx < grid_width and 0 <= ny < grid_height:
                        target = grid[ny][nx]
                        if target.get("factionId") != group.id:
                            border_tiles.append((nx, ny, target))

            action_taken = False

            # Action 1: Settle
            if housing_need > 0.5 or resource_needs:
                if random.random() < 0.2:
                    best_tile = None
                    best_score = -1
                    for nx, ny, tdata in border_tiles:
                        if tdata.get("factionId") is None and tdata.get("biome") != "ocean":
                            score = self._score_tile_azgaar_style(grid, nx, ny, resource_needs)
                            
                            if score > best_score:
                                best_score = score
                                best_tile = (nx, ny, tdata)
                    
                    if best_tile:
                        nx, ny, tdata = best_tile
                        tdata["factionId"] = group.id
                        b_res = self.biome_resources.get(tdata.get("biome"), "Land")
                        logs.append(f"[{group.name}] Founded a new settlement on {tdata.get('biome')} (Score: {best_score:.1f}).")
                        action_taken = True

            # Action 2: Trade Route
            if not action_taken and resource_needs:
                if random.random() < 0.3:
                    other_groups = [g for g in groups if g.id != group.id]
                    random.shuffle(other_groups)
                    
                    for target_group in other_groups:
                        path = self._find_trade_route(grid, owned, target_group.id, max_depth=50, transports=transports)
                        if path:
                            hub_used = False
                            hub_owner = None
                            
                            # Tally Traffic
                            for px, py in path:
                                self.traffic_map[(px, py)] = self.traffic_map.get((px, py), 0) + 2
                                
                                # Trade Hub Spawning
                                if self.traffic_map[(px, py)] > 5 and (px, py) not in self.trade_hubs:
                                    tile_owner = grid[py][px].get("factionId")
                                    if tile_owner:
                                        self.trade_hubs[(px, py)] = {"owner": tile_owner, "decay": 10, "ruined": False}
                                        owner_name = next((g.name for g in groups if g.id == tile_owner), "Unknown")
                                        logs.append(f"TRADE HUB: [{owner_name}] established a bustling Trade Hub on a major route crossing!")
                                        
                                if (px, py) in self.trade_hubs and not self.trade_hubs[(px, py)]["ruined"]:
                                    hub_used = True
                                    hub_owner = self.trade_hubs[(px, py)]["owner"]

                            if group.inventory.get("Grain", 0) > 100:
                                for needed_res in resource_needs.keys():
                                    if target_group.inventory.get(needed_res, 0) > 50:
                                        
                                        # Base yield: 50 -> 25
                                        yield_amt = 25
                                        cost_amt = 50
                                        
                                        # Hub Efficiency & Tolls
                                        if hub_used and hub_owner:
                                            yield_amt = 40 # High efficiency!
                                            group.inventory["Wealth"] = max(0, group.inventory.get("Wealth", 0) - 10)
                                            hub_wealth_bonuses[hub_owner] = hub_wealth_bonuses.get(hub_owner, 0) + 10
                                            
                                        group.inventory["Grain"] -= cost_amt
                                        target_group.inventory["Grain"] = target_group.inventory.get("Grain", 0) + cost_amt
                                        
                                        target_group.inventory[needed_res] -= yield_amt
                                        group.inventory[needed_res] = group.inventory.get(needed_res, 0) + yield_amt
                                        
                                        log_msg = f"TRADE ROUTE: [{group.name}] physically routed {cost_amt} Grain to [{target_group.name}] for {yield_amt} {needed_res}."
                                        if hub_used:
                                            log_msg += f" (Hub Efficiency Applied - Toll Paid to Owner {hub_owner})"
                                        if "Airships" in transports:
                                            log_msg = f"AIRSHIP TRADE: [{group.name}] flew {cost_amt} Grain to [{target_group.name}] for {yield_amt} {needed_res}."
                                            
                                        logs.append(log_msg)
                                        self.active_trade_routes.append({"path": path, "ttl": 5})
                                        action_taken = True
                                        break
                        if action_taken:
                            break

            # Action 3: War
            if not action_taken and (housing_need > 0.8 or resource_needs):
                if group.chaos_level > 0.5 and random.random() < 0.1:
                    for nx, ny, tdata in border_tiles:
                        tid = tdata.get("factionId")
                        if tid:
                            target_group = next((g for g in groups if g.id == tid), None)
                            if target_group:
                                attacker_weapons = min(group.inventory.get("Basic Weapons", 0), group.population)
                                attacker_armor = min(group.inventory.get("Leather Armor", 0), group.population)
                                
                                defender_weapons = min(target_group.inventory.get("Basic Weapons", 0), target_group.population)
                                defender_armor = min(target_group.inventory.get("Leather Armor", 0), target_group.population)
                                
                                group.inventory["Basic Weapons"] -= attacker_weapons * 0.1
                                group.inventory["Leather Armor"] -= attacker_armor * 0.1
                                target_group.inventory["Basic Weapons"] -= defender_weapons * 0.1
                                target_group.inventory["Leather Armor"] -= defender_armor * 0.1
                                
                                my_str = (group.population + (attacker_weapons * 5) + (attacker_armor * 2)) * random.uniform(0.8, 1.2)
                                enemy_str = (target_group.population + (defender_weapons * 5) + (defender_armor * 2)) * random.uniform(0.8, 1.2)
                                
                                casualties = int((enemy_str / (my_str + 1)) * 100) + random.randint(10, 50)
                                group.population = max(10, group.population - casualties)
                                target_group.population = max(10, target_group.population - casualties)
                                
                                if my_str > enemy_str:
                                    # Conquer tile
                                    tdata["factionId"] = group.id
                                    # Survivors become refugees: reduce target population and increase discontent
                                    refugee_count = int(target_group.population * 0.05)
                                    target_group.population = max(10, target_group.population - refugee_count)
                                    # Increase discontent for both factions due to displacement
                                    target_group.discontent = min(1.0, target_group.discontent + 0.15)
                                    group.discontent = min(1.0, group.discontent + 0.05)
                                    logs.append(f"WAR: [{group.name}] conquered a tile from [{target_group.name}]! Casualties: {casualties}. Refugees: {refugee_count} added to discontent.")
                                else:
                                    logs.append(f"WAR: [{group.name}] attacked [{target_group.name}] but failed. Casualties: {casualties}.")
                                action_taken = True
                                break

        return logs, hub_wealth_bonuses, ruined_hub_penalties

expansion_ai = ExpansionSystem()

def run_expansion_tick(groups, grid):
    logs, wealth_bonus, ruined_penalty = expansion_ai.process_expansion(groups, grid)
    routes = expansion_ai.active_trade_routes
    return logs, routes, wealth_bonus, ruined_penalty
