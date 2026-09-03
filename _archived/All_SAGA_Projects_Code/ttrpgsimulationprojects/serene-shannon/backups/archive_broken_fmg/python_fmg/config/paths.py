import os
from pathlib import Path

# Base directory of the project (one level up from this config file)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory containing all asset subfolders
ASSETS_DIR = PROJECT_ROOT / "assets"

# Ostraka picture assets (copied into the project)
OSTRAKA_PICS = ASSETS_DIR / "ostraka pics"

# Public texture assets (copied into the project)
PUBLIC_TEXTURES = ASSETS_DIR / "public" / "textures"

def asset_path(*parts: str) -> Path:
    """Return a Path object for an asset located under ASSETS_DIR.

    Example:
        asset_path("textures", "water", "deep_water.png")
    """
    return ASSETS_DIR.joinpath(*parts)

__all__ = [
    "PROJECT_ROOT",
    "ASSETS_DIR",
    "OSTRAKA_PICS",
    "PUBLIC_TEXTURES",
    "asset_path",
]
