# config_service/accessor.py

import logging
import os
from typing import Optional

from pydantic import ValidationError

from .exceptions import ConfigValidationError
from .loader import load_raw_config
from .models import AppConfig

logger = logging.getLogger(__name__)

# Modul-interne Variable, die als Singleton-Cache dient.
_config_cache: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    Zentrale API-Funktion zum Laden, Validieren und Abrufen der App-Konfiguration.

    Diese Funktion implementiert ein Singleton-Muster mit Caching. Beim ersten Aufruf
    wird die Konfiguration geladen, validiert und im Cache gespeichert. Bei allen
    folgenden Aufrufen wird die Konfiguration direkt aus dem Cache zurückgegeben.

    Der Pfad zur Konfigurationsdatei wird aus der Umgebungsvariable `CONFIG_PATH`
    gelesen, mit einem Fallback auf `config.yaml` im aktuellen Verzeichnis.

    Returns:
        Eine validierte Pydantic-Instanz von `AppConfig`.

    Raises:
        ConfigFileError: Wenn die Datei nicht geladen werden kann.
        ConfigValidationError: Wenn der Inhalt der Datei nicht der erwarteten Struktur entspricht.
    """
    global _config_cache
    if _config_cache is not None:
        logger.debug("Konfiguration aus dem Cache geladen.")
        return _config_cache

    logger.info("Keine Konfiguration im Cache. Lade und validiere neu.")
    config_path = os.getenv("CONFIG_PATH", "config.yaml")

    # 1. Laden (Delegation an den Loader)
    raw_config = load_raw_config(config_path)

    # 2. Validieren (Delegation an das Pydantic-Modell)
    try:
        validated_config = AppConfig.model_validate(raw_config)
        logger.info("Konfiguration erfolgreich validiert.")
    except ValidationError as e:
        logger.error("Validierungsfehler in der Konfiguration.", exc_info=True)
        # Wir verpacken den pydantic-Fehler in unsere eigene Exception.
        raise ConfigValidationError(f"Konfigurationsfehler: {e}") from e

    # 3. Caching und Rückgabe
    _config_cache = validated_config
    return _config_cache


def _reset_config_cache_for_testing():
    """Nur für Testzwecke, um den Cache zurückzusetzen."""
    global _config_cache
    _config_cache = None
