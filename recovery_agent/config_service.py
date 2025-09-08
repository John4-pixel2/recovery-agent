# recovery_agent/config_service.py

import copy
from pathlib import Path
from typing import Any

import yaml


class ConfigError(Exception):
    """Custom exception for configuration errors."""


_config_cache: dict[str, Any] | None = None

# Default configuration values
DEFAULTS: dict[str, Any] = {
    "target_dir": "/opt/recovery_agent/restored_files",
    "backup_formats": {"db": "*.sql", "logs": "*.log"},
}


def get_config(path: str | Path | None = None) -> dict[str, Any]:
    """
    Loads, validates, and returns the application configuration from a YAML file.

    - If a path is provided, it must exist.
    - If no path is provided, it falls back to `config.yaml` but does not fail
      if it's missing.
    - Loaded settings are merged with default values.
    - The result is cached to avoid repeated file I/O on subsequent calls.
    """
    global _config_cache
    if path is None and _config_cache is not None:
        return _config_cache

    config = copy.deepcopy(DEFAULTS)

    has_explicit_path = path is not None
    config_path = Path(path) if has_explicit_path else Path("config.yaml")

    if config_path.is_file():
        with config_path.open("r", encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f)
                if data:
                    if not isinstance(data, dict):
                        raise ConfigError("Config must be a mapping (dict).")
                    config.update(data)
            except yaml.YAMLError as e:
                raise ConfigError(f"Invalid YAML configuration: {e}") from e
    elif has_explicit_path:
        # If a specific path was given and not found, raise an error.
        raise ConfigError(f"Configuration file not found: {config_path}")

    if not has_explicit_path:  # Only cache when using the default path
        _config_cache = config

    return config
