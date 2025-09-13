# recovery_agent/config_service/service.py

import sys
import logging
from typing import Optional

from pydantic import ValidationError

from .loader import load_raw_config, ConfigLoaderError
from .models import AppConfig
logger = logging.getLogger(__name__)

_config_cache: Optional[AppConfig] = None


class ConfigServiceError(Exception):
    """Base exception for any configuration service related issue."""
    pass


def get_config() -> AppConfig:
    """
    Provides a singleton instance of the validated application configuration.

    On the first call, it loads the raw config from a file, validates it
    against the Pydantic model, and caches the result. Subsequent calls
    return the cached instance.

    If validation fails, it logs a critical error and exits the application.

    Returns:
        A validated AppConfig object.

    Raises:
        ConfigServiceError: If the configuration file cannot be loaded.
    """
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    logger.info("Keine Konfiguration im Cache. Lade und validiere neu.")
    try:
        raw_config = load_raw_config()
        validated_config = AppConfig.model_validate(raw_config)
        logger.info("Konfiguration erfolgreich validiert.")
        _config_cache = validated_config
        return _config_cache
    except ConfigLoaderError as e:
        raise ConfigServiceError(e) from e
    except ValidationError as e:
        logger.critical("Fehler bei der Validierung der Konfiguration:\n%s", e)
        sys.exit(1)

