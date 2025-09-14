# recovery_agent/config_service/loader.py

import os  # <-- DIESE ZEILE MUSS HIER SEIN
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .exceptions import ConfigFileError

logger = logging.getLogger(__name__)


def load_raw_config(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Lädt eine YAML-Datei sicher und gibt sie als Dictionary zurück.

    Args:
        path: Der Pfad zur YAML-Konfigurationsdatei. Wenn None, wird CONFIG_PATH ENV-Variable oder 'config.yaml' verwendet.

    Returns:
        Der Inhalt der YAML-Datei als Dictionary.

    Raises:
        ConfigFileError: Wenn die Datei nicht gefunden wird oder ungültiges YAML enthält.
    """
    if path is None:
        # Determine the project root (assuming this file is in `recovery_agent/config_service`)
        project_root = Path(__file__).parent.parent.parent
        default_config_path = project_root / "config.yaml"
        path_to_load = os.getenv("CONFIG_PATH", str(default_config_path))
    else:
        path_to_load = path

    config_path = Path(path_to_load)
    logger.info(f"Lade Konfiguration von: {config_path.resolve()}")

    try:
        with config_path.open("r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)
            if not isinstance(raw_config, dict):
                raise ConfigFileError(
                    f"Die Konfigurationsdatei '{path_to_load}' muss ein YAML-Mapping (Dictionary) sein."
                )
            return raw_config
    except yaml.YAMLError as e:
        logger.error(f"Fehler beim Parsen der YAML-Datei: {path_to_load}", exc_info=True)
        raise ConfigFileError(f"Fehler beim Parsen der YAML-Datei: {e}") from e
    except OSError as e:
        if isinstance(e, FileNotFoundError):
            logger.error(f"Konfigurationsdatei nicht gefunden: {path_to_load}")
            raise ConfigFileError(f"Konfigurationsdatei nicht gefunden: {path_to_load}") from e
        # Handle other OS errors
        logger.error(f"Fehler beim Lesen der Konfigurationsdatei '{path_to_load}': {e}")
        raise ConfigFileError(f"Fehler beim Lesen der Konfigurationsdatei '{path_to_load}': {e}") from e
