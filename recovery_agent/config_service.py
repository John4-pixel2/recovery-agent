
# recovery_agent/config_service.py

import yaml
from pathlib import Path
from typing import Optional, Dict, Any


class ConfigError(Exception):
    pass


_config_cache: Optional[Dict[str, Any]] = None


def get_config(path: Optional[str | Path] = None) -> dict:
    """
    Loads, validates, and returns the application configuration from a YAML file.
    The result is cached to avoid repeated file I/O on subsequent calls.
    """
    global _config_cache
    if path is None and _config_cache is not None:
        return _config_cache

    config_path = Path(path) if path else Path("config.yaml")

    if not config_path.is_file():
        raise ConfigError(f"Configuration file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
            if not isinstance(data, dict):
                raise ConfigError("Configuration file must be a mapping (dict).")

            if path is None:  # Only cache when using the default path
                _config_cache = data
            return data
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML configuration: {e}") from e
