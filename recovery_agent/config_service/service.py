import logging
from pydantic import ValidationError
from .loader import load_raw_config
from .models import AppConfig
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
    except ConfigFileError as e:
        logger.error(f"ConfigFileError: {e}")
        raise ConfigServiceError(str(e)) from e
    except ValidationError as e:
        logger.critical(f"Validierungsfehler: {e}")
        raise ConfigValidationError(str(e)) from e
