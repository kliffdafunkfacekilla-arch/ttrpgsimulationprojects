from PyQt6.QtGui import QPixmap, QColor, QPainter, QBrush, QPen
from PyQt6.QtCore import Qt
import os
import glob

import json

class SpriteManager:
    """
    Central repository for caching, scaling, and managing 2D sprite graphics.
    """
    def __init__(self, tile_size=40):
        self.tile_size = tile_size
        self.cache = {}
        self.base_assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
        self.mapping_file = os.path.join(self.base_assets_dir, "tile_mapping.json")
        self.custom_mapping = self._load_mapping()
        
        # Ensure directory exists
        if not os.path.exists(self.base_assets_dir):
            os.makedirs(self.base_assets_dir, exist_ok=True)
            
        self._load_fallback_sprites()
        self._build_asset_index()

    def _build_asset_index(self):
        """Recursively scans the assets directory and builds an O(1) lookup index of all pngs."""
        self.asset_index = {}
        for root, dirs, files in os.walk(self.base_assets_dir):
            for file in files:
                if file.lower().endswith('.png'):
                    # Store filename without extension as the key
                    basename = os.path.splitext(file)[0].lower()
                    # Only map if not already mapped, or maybe override? We'll just map first found.
                    if basename not in self.asset_index:
                        self.asset_index[basename] = os.path.join(root, file)

    def _load_mapping(self):
        if os.path.exists(self.mapping_file):
            try:
                with open(self.mapping_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Failed to load tile mapping: {e}")
        return {}

    def set_mapping(self, terrain_name: str, filepath: str):
        self.custom_mapping[terrain_name] = filepath
        try:
            with open(self.mapping_file, "w") as f:
                json.dump(self.custom_mapping, f, indent=4)
        except Exception as e:
            print(f"Failed to save tile mapping: {e}")
            
        # Invalidate cache for this name
        if terrain_name in self.cache:
            del self.cache[terrain_name]
        
    def _load_fallback_sprites(self):
        """Creates procedural pixmaps if files are missing."""
        self.fallback = {}
        
        # Grass Fallback
        pm = QPixmap(self.tile_size, self.tile_size)
        pm.fill(QColor(30, 100, 30))
        self.fallback["grass"] = pm
        
        # Wall Fallback
        pm_wall = QPixmap(self.tile_size, self.tile_size)
        pm_wall.fill(QColor(100, 100, 100))
        self.fallback["wall"] = pm_wall
        
        # Default Entity Fallback
        pm_ent = QPixmap(self.tile_size, self.tile_size)
        pm_ent.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pm_ent)
        painter.setBrush(QBrush(QColor(200, 50, 50)))
        painter.drawEllipse(2, 2, self.tile_size-4, self.tile_size-4)
        painter.end()
        self.fallback["entity_red"] = pm_ent
        
        pm_ent_b = QPixmap(self.tile_size, self.tile_size)
        pm_ent_b.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pm_ent_b)
        painter.setBrush(QBrush(QColor(50, 50, 200)))
        painter.drawEllipse(2, 2, self.tile_size-4, self.tile_size-4)
        painter.end()
        self.fallback["entity_blue"] = pm_ent_b

    def get_sprite(self, name: str) -> QPixmap:
        """Returns the scaled QPixmap for a given name, checking cache first."""
        search_name = name.lower()
        if search_name in self.cache:
            return self.cache[search_name]
            
        matches = []
        
        # 1. Check custom JSON mapping first
        if search_name in self.custom_mapping and os.path.exists(self.custom_mapping[search_name]):
            matches = [self.custom_mapping[search_name]]
            
        # 2. Check the recursive asset index O(1)
        if not matches and search_name in self.asset_index:
            matches = [self.asset_index[search_name]]

        if matches:
            filepath = matches[0]
            pixmap = QPixmap(filepath)
            if not pixmap.isNull():
                scaled = pixmap.scaled(self.tile_size, self.tile_size, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.cache[name] = scaled
                return scaled
                
        # Handle miss: assign a random processed sprite if it's likely an entity
        is_terrain = any(term in search_name for term in ["wall", "grass", "floor", "door", "path"])
        if not is_terrain:
            processed_dir = os.path.join(self.base_assets_dir, "sprites", "processed")
            if os.path.exists(processed_dir):
                import random
                import glob
                processed_sprites = glob.glob(os.path.join(processed_dir, "*.png"))
                if processed_sprites:
                    chosen_sprite = random.choice(processed_sprites)
                    # Use set_mapping to persist the assignment
                    self.set_mapping(search_name, chosen_sprite)
                    pixmap = QPixmap(chosen_sprite)
                    if not pixmap.isNull():
                        scaled = pixmap.scaled(self.tile_size, self.tile_size, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        self.cache[search_name] = scaled
                        return scaled

        # Handle miss: fallback depending on name
        if "wall" in name.lower():
            return self.fallback["wall"]
        elif "grass" in name.lower() or "floor" in name.lower():
            return self.fallback["grass"]
        elif "enemy" in name.lower():
            return self.fallback["entity_red"]
        else:
            return self.fallback["entity_blue"]
