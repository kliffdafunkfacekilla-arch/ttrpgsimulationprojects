import heapq
import random
import math

class NPCAI:
    """
    Manages autonomous movement and state logic for all entities on the map.
    """
    def __init__(self):
        pass

    def tick(self, entities: list, grid: list, player_x: int, player_y: int):
        """
        Executes one turn of logical behavior for all entities.
        """
        for ent in entities:
            if "behavior" not in ent:
                continue
                
            behavior = ent["behavior"]
            
            # 1. State: Hunt (Aggressive pathing towards player)
            if behavior == "hunt":
                # Check aggro radius (e.g. 15 tiles)
                dist = math.hypot(player_x - ent["x"], player_y - ent["y"])
                if dist < 15:
                    path = self._a_star(grid, (ent["x"], ent["y"]), (player_x, player_y))
                    if path and len(path) > 1:
                        # Move one step towards player
                        next_step = path[1]
                        if not self._is_occupied(next_step[0], next_step[1], entities, player_x, player_y):
                            ent["x"] = next_step[0]
                            ent["y"] = next_step[1]
                            
            # 2. State: Patrol (Wander on roads)
            elif behavior == "patrol":
                if random.random() < 0.5: # 50% chance to move
                    possible_moves = []
                    for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                        nx, ny = ent["x"] + dx, ent["y"] + dy
                        # Prefer roads (tile 4) or empty (0)
                        if 0 <= nx < 100 and 0 <= ny < 100:
                            if grid[ny][nx] in [0, 4] and not self._is_occupied(nx, ny, entities, player_x, player_y):
                                possible_moves.append((nx, ny))
                    if possible_moves:
                        move = random.choice(possible_moves)
                        ent["x"], ent["y"] = move[0], move[1]
                        
            # 3. State: Static/Task (Stay in place or very small wander)
            elif behavior == "task":
                if random.random() < 0.2: # Occasional fidgeting
                    dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0)])
                    nx, ny = ent["x"] + dx, ent["y"] + dy
                    if 0 <= nx < 100 and 0 <= ny < 100 and grid[ny][nx] == 0:
                        if not self._is_occupied(nx, ny, entities, player_x, player_y):
                            # Ensure they don't wander far from origin
                            if "origin_x" not in ent:
                                ent["origin_x"] = ent["x"]
                                ent["origin_y"] = ent["y"]
                            if math.hypot(nx - ent["origin_x"], ny - ent["origin_y"]) < 3:
                                ent["x"], ent["y"] = nx, ny

    def _is_occupied(self, x, y, entities, px, py):
        if x == px and y == py: return True
        for e in entities:
            if e["x"] == x and e["y"] == y:
                return True
        return False

    def _a_star(self, grid, start, goal):
        """A* Pathfinding ignoring other entities, respecting terrain."""
        height = len(grid)
        width = len(grid[0])
        
        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])
            
        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}
        
        while frontier:
            current = heapq.heappop(frontier)[1]
            
            if current == goal:
                break
                
            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)]:
                nx, ny = current[0] + dx, current[1] + dy
                if 0 <= nx < width and 0 <= ny < height:
                    # Impassable tiles: 1 (Obstacles), 2 (Water), 3 (Buildings)
                    if grid[ny][nx] in [1, 2, 3] and (nx, ny) != goal:
                        continue
                        
                    new_cost = cost_so_far[current] + (1.4 if dx != 0 and dy != 0 else 1)
                    if (nx, ny) not in cost_so_far or new_cost < cost_so_far[(nx, ny)]:
                        cost_so_far[(nx, ny)] = new_cost
                        priority = new_cost + heuristic((nx, ny), goal)
                        heapq.heappush(frontier, (priority, (nx, ny)))
                        came_from[(nx, ny)] = current
                        
        # Reconstruct path
        if goal not in came_from:
            # Try to get as close as possible if blocked
            closest = min(cost_so_far.keys(), key=lambda k: heuristic(k, goal))
            if closest == start: return None
            goal = closest
            
        path = []
        curr = goal
        while curr != start:
            path.append(curr)
            curr = came_from[curr]
        path.append(start)
        path.reverse()
        return path
