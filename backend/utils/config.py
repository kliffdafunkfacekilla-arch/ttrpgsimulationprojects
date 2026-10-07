"""
Configuration management for SAGA Unified.
Handles loading, saving, and validating configuration files.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from utils.logging.logger import get_logger

logger = get_logger("SAGA.Config")

class ConfigManager:
    """Manages application configuration with support for multiple profiles."""

    def __init__(self, config_dir: str = "config/profiles"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.current_config: Dict[str, Any] = {}
        self.config_file: Optional[Path] = None

    def load_config(self, profile_name: str = "default_config") -> Dict[str, Any]:
        """
        Load configuration from a profile file.

        Args:
            profile_name: Name of the configuration profile (without .json extension)

        Returns:
            Configuration dictionary
        """
        config_path = self.config_dir / f"{profile_name}.json"

        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return self.get_default_config()

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.current_config = json.load(f)
                self.config_file = config_path
                logger.info(f"Loaded configuration from {config_path}")
                return self.current_config
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return self.get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self.get_default_config()

    def save_config(self, profile_name: str = "default_config") -> bool:
        """
        Save current configuration to a profile file.

        Args:
            profile_name: Name of the configuration profile (without .json extension)

        Returns:
            True if successful, False otherwise
        """
        config_path = self.config_dir / f"{profile_name}.json"

        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.current_config, f, indent=2)
                self.config_file = config_path
                logger.info(f"Saved configuration to {config_path}")
                return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key (supports nested keys with dot notation).

        Args:
            key: Configuration key (e.g., "audio.tts.voice")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.current_config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value by key (supports nested keys with dot notation).

        Args:
            key: Configuration key (e.g., "audio.tts.voice")
            value: Value to set
        """
        keys = key.split('.')
        config = self.current_config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def get_default_config(self) -> Dict[str, Any]:
        """Get the default configuration."""
        return {
            "app": {
                "name": "SAGA Unified",
                "version": "1.0.0",
                "debug": True
            },
            "audio": {
                "tts": {
                    "engine": "edge-tts",
                    "voice": "en-GB-RyanNeural",
                    "enabled": True
                },
                "stt": {
                    "engine": "speech_recognition",
                    "backend": "google",
                    "enabled": False
                }
            },
            "ai": {
                "model_path": "",
                "system_prompt": "You are a gritty black-powder fantasy game master. Describe scenes with atmospheric detail, but never calculate game mechanics.",
                "temperature": 0.7
            },
            "data": {
                "chromadb_path": "data/chromadb",
                "sqlite_path": "data/sqlite",
                "save_directory": "data/saves"
            },
            "world": {
                "external_db_enabled": False,
                "omnis_db_path": "",
                "procedural_generation": True
            },
            "game": {
                "difficulty": "Normal",
                "combat_frequency": "Medium",
                "content_filters": {
                    "alcohol": False,
                    "gore": False,
                    "spiders": False
                }
            }
        }

# Global config manager instance
config_manager = ConfigManager()