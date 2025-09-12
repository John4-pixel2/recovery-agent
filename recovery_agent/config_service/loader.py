# config_service/loader.py

import logging
from pathlib import Path
from typing import Any, Dict

import yaml

from .exceptions import ConfigFileError

logger = logging.getLogger(__name__)


def load_raw_config(path: str) -> Dict[str, Any]:
    """
    Lädt eine YAML-Datei sicher und gibt sie als Dictionary zurück.

    Args:
        path: Der Pfad zur YAML-Konfigurationsdatei.

    Returns:
        Der Inhalt der YAML-Datei als Dictionary.

    Raises:
        ConfigFileError: Wenn die Datei nicht gefunden wird oder ungültiges YAML enthält.
    """
    config_path = Path(path)
    logger.info(f"Lade Konfiguration von: {config_path.resolve()}")

    try:
        with config_path.open("r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)
            if not isinstance(raw_config, dict):
                raise ConfigFileError(f"Die Konfigurationsdatei '{path}' muss ein YAML-Mapping (Dictionary) sein.")
            return raw_config
    except FileNotFoundError:
        logger.error(f"Konfigurationsdatei nicht gefunden: {path}")
        raise ConfigFileError(f"Konfigurationsdatei nicht gefunden: {path}") from None
    except yaml.YAMLError as e:
        logger.error(f"Fehler beim Parsen der YAML-Datei: {path}", exc_info=True)
        raise ConfigFileError(f"Fehler beim Parsen der YAML-Datei: {e}") from e
