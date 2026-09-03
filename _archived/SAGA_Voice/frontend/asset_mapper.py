import os

class AssetMapper:
    def __init__(self, base_asset_dir="frontend/assets"):
        self.base_dir = base_asset_dir
        
        # Dictionary bridging game tags/identifiers to local asset filenames
        self.background_map = {
            "Underground Vault": "backgrounds/biome_underground.png",
            "Drift Anomaly": "backgrounds/biome_drift_anomaly.png",
            "Default": "backgrounds/biome_underground.png"
        }
        
        self.prop_map = {
            "Fractured Core Regulator": "interactive_props/prop_core_regulator.png",
            "Steel Crate": "interactive_props/prop_crate_heavy.png",
            "Console": "interactive_props/prop_console.png"
        }
        
        self.entity_map = {
            "npc_cultist": "entities/npc_cultist.png",
            "Default": "entities/npc_cultist.png"
        }

    def _verify_path(self, relative_path: str) -> str:
        full_path = os.path.join(self.base_dir, relative_path)
        if os.path.exists(full_path):
            return full_path
        # Return a placeholder or just None if the asset is entirely missing
        return None

    def get_background(self, biome_tag: str) -> str:
        relative_path = self.background_map.get(biome_tag, self.background_map["Default"])
        return self._verify_path(relative_path)

    def get_prop_asset(self, prop_name: str) -> str:
        relative_path = self.prop_map.get(prop_name, "interactive_props/prop_console.png")
        return self._verify_path(relative_path)
        
    def get_entity_asset(self, entity_tag: str) -> str:
        relative_path = self.entity_map.get(entity_tag, self.entity_map["Default"])
        return self._verify_path(relative_path)
