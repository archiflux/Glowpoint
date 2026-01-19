"""Configuration manager for SpotCursor application."""
import json
import os
from typing import Dict, Any


class ConfigManager:
    """Manages application configuration and user-defined shortcuts."""

    DEFAULT_CONFIG = {
        "shortcuts": {
            "toggle_spotlight": "<ctrl>+<shift>+s",
            "draw_blue": "<ctrl>+<shift>+b",
            "draw_red": "<ctrl>+<shift>+r",
            "draw_yellow": "<ctrl>+<shift>+y",
            "draw_green": "<ctrl>+<shift>+g",
            "clear_screen": "<ctrl>+<shift>+c",
            "quit": "<ctrl>+<shift>+q"
        },
        "spotlight": {
            "enabled": True,
            "radius": 80,
            "ring_radius": 40,
            "opacity": 0.7,
            "color": "#FFFF64"
        },
        "drawing": {
            "line_width": 4,
            "colors": {
                "blue": "#2196F3",
                "red": "#F44336",
                "yellow": "#FFEB3B",
                "green": "#4CAF50"
            }
        }
    }

    def __init__(self, config_file: str = "config.json"):
        """Initialize configuration manager.

        Args:
            config_file: Path to the configuration file
        """
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default.

        Returns:
            Configuration dictionary
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                # Merge with defaults to ensure all keys exist
                return self._merge_configs(self.DEFAULT_CONFIG, loaded_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config: {e}. Using defaults.")
                return self.DEFAULT_CONFIG.copy()
        else:
            return self.DEFAULT_CONFIG.copy()

    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """Recursively merge loaded config with defaults.

        Args:
            default: Default configuration
            loaded: Loaded configuration

        Returns:
            Merged configuration
        """
        result = default.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result

    def save_config(self) -> bool:
        """Save current configuration to file.

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except IOError as e:
            print(f"Error saving config: {e}")
            return False

    def get_shortcut(self, action: str) -> str:
        """Get shortcut for a specific action.

        Args:
            action: Action name

        Returns:
            Shortcut string
        """
        return self.config["shortcuts"].get(action, "")

    def set_shortcut(self, action: str, shortcut: str) -> None:
        """Set shortcut for a specific action.

        Args:
            action: Action name
            shortcut: Shortcut string
        """
        self.config["shortcuts"][action] = shortcut
        self.save_config()

    def get(self, *keys) -> Any:
        """Get configuration value using dot notation.

        Args:
            *keys: Configuration path keys

        Returns:
            Configuration value
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value

    def set(self, value: Any, *keys) -> None:
        """Set configuration value using dot notation.

        Args:
            value: Value to set
            *keys: Configuration path keys
        """
        config = self.config
        for key in keys[:-1]:
            config = config.setdefault(key, {})
        config[keys[-1]] = value
        self.save_config()
