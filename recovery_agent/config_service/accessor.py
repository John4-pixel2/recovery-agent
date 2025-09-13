# config_service/accessor.py

import logging
import os
from pathlib import Path

from pydantic import ValidationError

from .exceptions import ConfigValidationError
from .loader import load_raw_config
from .models import AppConfig

logger = logging.getLogger(__name__)

_config_cache: AppConfig | None = None


def get_config() -> AppConfig:
    """
    Central API function to load, validate, and access the application config.

    Implements a singleton pattern with caching. On the first call, it loads,
    validates, and caches the configuration. Subsequent calls return the cached instance.

    The path to the config file is determined by the `CONFIG_PATH` environment
    variable, falling back to `config.yaml` in the project root.
    """
    global _config_cache
    if _config_cache is not None:
        logger.debug("Configuration loaded from cache.")
        return _config_cache

    logger.info("No configuration in cache. Loading and validating.")

    # Determine the project root (assuming this file is in `recovery_agent/config_service`)
    project_root = Path(__file__).parent.parent.parent
    default_config_path = project_root / "config.yaml"

    config_path_str = os.getenv("CONFIG_PATH", str(default_config_path))

    # 1. Load (delegated to the loader)
    raw_config = load_raw_config(config_path_str)

    # 2. Validate (delegated to the Pydantic model)
    try:
        validated_config = AppConfig.model_validate(raw_config)
        logger.info("Configuration successfully validated.")
    except ValidationError as e:
        logger.error("Configuration validation error.", exc_info=True)
        raise ConfigValidationError(f"Configuration error: {e}") from e

    # 3. Cache and return
    _config_cache = validated_config
    return _config_cache


def _reset_config_cache_for_testing():
    """For testing purposes only, to reset the cache."""
    global _config_cache
    _config_cache = None
