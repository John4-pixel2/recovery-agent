# recovery_agent/config_service/loader.py

import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

try:
    # This works when the module is imported as part of the package
    from .exceptions import ConfigFileError
except ImportError:
    # This is a fallback for direct execution (e.g., for debugging)
    # and assumes the script is run from the project root.
    from recovery_agent.config_service.exceptions import ConfigFileError

logger = logging.getLogger(__name__)


def load_raw_config(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Lädt eine YAML-Datei sicher und gibt sie als Dictionary zurück.

    Args:
        path: Optionaler Pfad zur Konfigurationsdatei.
              Wenn nicht angegeben, wird $CONFIG_PATH oder 'config.yaml' verwendet.

    Returns:
        Der Inhalt der YAML-Datei als Dictionary.

    Raises:
        ConfigFileError: Wenn die Datei nicht gefunden wird oder ungültiges YAML enthält.
    """
    config_path_str = path or os.getenv("CONFIG_PATH", "config.yaml")
    config_path = Path(config_path_str)
    logger.info(f"Lade Konfiguration von: {config_path.resolve()}")

    try:
        with config_path.open("r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)
            if not isinstance(raw_config, dict):
                raise ConfigFileError(
                    f"Die Konfigurationsdatei '{config_path_str}' muss ein YAML-Mapping (Dictionary) sein."
                )
            return raw_config
    except yaml.YAMLError as e:
        logger.error(f"Fehler beim Parsen der YAML-Datei: {config_path_str}", exc_info=True)
        raise ConfigFileError(f"Fehler beim Parsen der YAML-Datei: {e}") from e
    except OSError as e:  # Fängt alle I/O-Fehler ab (z.B. FileNotFoundError, PermissionError)
        logger.error(f"Fehler beim Lesen der Konfigurationsdatei '{config_path_str}': {e}")
        raise ConfigFileError(f"Fehler beim Lesen der Konfigurationsdatei '{config_path_str}': {e}") from e
