import logging
from pydantic import ValidationError
from .models import AppConfig
from .loader import load_raw_config
from .exceptions import ConfigFileError, ConfigServiceError, ConfigValidationError

logger = logging.getLogger(__name__)
_config_cache = None

def get_config() -> AppConfig:
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

    except ValidationError as e:
        logger.critical(f"Validierungsfehler: {e}")
        # Pydantic-Validierungsfehler kapseln
        raise ConfigValidationError(str(e)) from e

    except ConfigFileError as e:
        # Cleanly wrap the specific file error into the public service error
        raise ConfigServiceError(str(e)) from e
