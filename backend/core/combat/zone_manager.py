import logging
from typing import Dict, Any
from beta_build.core.fov_calculator import calculate_fov

logger = logging.getLogger("ZoneManager")

class ZoneManager:
    def __init__(self, bus):
        self.bus = bus
        self.grid_data = []
        self.entities = {}

        self.bus.subscribe("MAP_PAYLOAD_READY", self._on_map_payload_ready)
        self.bus.subscribe("SPAWN_ENTITY", self._on_spawn_entity)
        self.bus.subscribe("MOVE_ENTITY", self._on_move_entity)
        self.bus.subscribe("REMOVE_ENTITY", self._on_remove_entity)

    def _on_map_payload_ready(self, payload: Dict[str, Any]):
        """Caches the generated Pydantic terrain matrix."""
        self.grid_data = payload.get("grid", [])
        self.entities.clear()

        # We don't spawn the player here; main_window orchestrates that by emitting SPAWN_ENTITY.
        logger.info("ZoneManager cached physical grid data.")

    def _on_spawn_entity(self, payload: Dict[str, Any]):
        uuid = payload.get("uuid")
        if uuid:
            self.entities[uuid] = {
                "x": payload.get("x", 0),
                "y": payload.get("y", 0),
                "tags": payload.get("tags", []),
                "name": payload.get("name", "Unknown"),
                "stats": payload.get("stats", {})
            }

    def _on_move_entity(self, payload: Dict[str, Any]):
        uuid = payload.get("uuid")
        if uuid in self.entities:
            self.entities[uuid]["x"] = payload.get("x", 0)
            self.entities[uuid]["y"] = payload.get("y", 0)

    def _on_remove_entity(self, payload: Dict[str, Any]):
        uuid = payload.get("uuid")
        if uuid in self.entities:
            del self.entities[uuid]

    def get_entity_pos(self, uuid: str) -> tuple[int, int]:
        ent = self.entities.get(uuid)
        if ent:
            return ent["x"], ent["y"]
        return -1, -1

    def is_tile_passable(self, target_x: int, target_y: int) -> tuple[bool, str, Dict[str, Any]]:
        """
        Validates if the coordinate is within bounds and doesn't contain blocking tags/types.
        Returns (is_passable, reason, tile_data)
        """
        if not self.grid_data:
            return False, "no_map", {}

        if target_y < 0 or target_y >= len(self.grid_data) or target_x < 0 or target_x >= len(self.grid_data[0]):
            return False, "edge_of_map", {}

        target_node = self.grid_data[target_y][target_x]

        tile_type = target_node.get("tile_type", "floor")
        tags = target_node.get("tags", [])

        if tile_type in ("wall", "obstacle"):
            return False, "collision", target_node

        if "blocks_movement" in tags or "blocks_los" in tags:
            return False, "collision", target_node

        return True, "clear", target_node

    def get_visible_context(self, x: int, y: int, radius: int = 7) -> str:
        """
        Uses FOV math to generate a string describing exactly what is visible to the player at this coordinate.
        """
        if not self.grid_data:
            return "You see nothing. (Grid not loaded)"

        visible_coords = calculate_fov(self.grid_data, x, y, radius)

        visible_entities = []
        for ent_uuid, ent in self.entities.items():
            if ent_uuid == "player_1": continue
            if (ent["x"], ent["y"]) in visible_coords:
                visible_entities.append(ent.get("name", "Unknown Entity"))

        visible_tags = set()
        for vx, vy in visible_coords:
            if vy >= 0 and vy < len(self.grid_data) and vx >= 0 and vx < len(self.grid_data[0]):
                node = self.grid_data[vy][vx]
                if node.get("tile_type") in ("obstacle", "wall", "water"):
                    visible_tags.add(node.get("tile_type"))

        context_str = ""
        if visible_entities:
            context_str += f"Visible Entities: {', '.join(visible_entities)}. "
        if visible_tags:
            context_str += f"Visible Terrain features: {', '.join(list(visible_tags))}."

        return context_str.strip()

    def get_entity_by_name_heuristic(self, target_name: str) -> str:
        """
        Attempts to find a uuid for an entity that matches the text.
        """
        target_lower = target_name.lower().strip()

        # 1. Exact match
        for uuid, ent in self.entities.items():
            if uuid == "player_1": continue
            if ent.get("name", "").lower() == target_lower:
                return uuid

        # 2. Substring match
        for uuid, ent in self.entities.items():
            if uuid == "player_1": continue
            if target_lower in ent.get("name", "").lower():
                return uuid

        return ""
