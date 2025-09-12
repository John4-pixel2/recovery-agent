# tests/test_config_service.py

import os
from unittest.mock import patch

import pytest
import yaml

# Importiere die öffentliche API
from config_service import (
    ConfigFileError,
    ConfigValidationError,
    get_config,
)
# Importiere interne Teile für Test-Setup
from config_service.accessor import _reset_config_cache_for_testing
from config_service.models import AppConfig


@pytest.fixture(autouse=True)
def reset_cache():
    """Stellt sicher, dass der Cache vor jedem Test leer ist."""
    _reset_config_cache_for_testing()
    # Stelle sicher, dass die ENV-Variable sauber ist
    if "CONFIG_PATH" in os.environ:
        del os.environ["CONFIG_PATH"]


def create_test_config_file(tmp_path, content):
    """Hilfsfunktion zum Erstellen einer temporären config.yaml."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump(content))
    return str(config_file)


# --- Test-Szenarien ---

def test_load_valid_config_success(tmp_path):
    """
    Happy Path: Testet das erfolgreiche Laden und Validieren einer korrekten Konfiguration.
    """
    valid_content = {
        "server": {"host": "0.0.0.0", "port": 9000},
        "logging": {"level": "DEBUG"},
        "app_name": "MyTestApp",
        "debug_mode": True,
    }
    config_path = create_test_config_file(tmp_path, valid_content)
    os.environ["CONFIG_PATH"] = config_path

    config = get_config()

    assert isinstance(config, AppConfig)
    assert config.server.host == "0.0.0.0"
    assert config.server.port == 9000
    assert config.logging.level == "DEBUG"
    assert config.app_name == "MyTestApp"
    assert config.debug_mode is True


def test_config_is_cached(tmp_path):
    """
    Testet, ob die Konfiguration nach dem ersten Laden gecacht wird.
    Der Loader darf nur einmal aufgerufen werden.
    """
    valid_content = {
        "server": {"host": "localhost", "port": 8080},
        "logging": {"level": "INFO"},
        "app_name": "CacheTest",
    }
    config_path = create_test_config_file(tmp_path, valid_content)
    os.environ["CONFIG_PATH"] = config_path

    with patch("config_service.loader.load_raw_config", wraps=load_raw_config) as mock_loader:
        # Erster Aufruf: Soll die Datei laden
        config1 = get_config()
        mock_loader.assert_called_once()

        # Zweiter Aufruf: Soll aus dem Cache kommen
        config2 = get_config()
        mock_loader.assert_called_once()  # Immer noch nur ein Aufruf

        assert config1 is config2  # Soll dasselbe Objekt sein


def test_file_not_found_raises_error():
    """
    Edge Case: Testet, ob ein `ConfigFileError` ausgelöst wird, wenn die Datei nicht existiert.
    """
    os.environ["CONFIG_PATH"] = "non_existent_file.yaml"
    with pytest.raises(ConfigFileError, match="Konfigurationsdatei nicht gefunden"):
        get_config()


def test_invalid_yaml_raises_error(tmp_path):
    """
    Edge Case: Testet, ob ein `ConfigFileError` bei syntaktisch falschem YAML ausgelöst wird.
    """
    invalid_yaml_content = "server: { host: 'localhost', port: 8080"  # Fehlende schließende Klammer
    config_file = tmp_path / "invalid.yaml"
    config_file.write_text(invalid_yaml_content)
    os.environ["CONFIG_PATH"] = str(config_file)

    with pytest.raises(ConfigFileError, match="Fehler beim Parsen der YAML-Datei"):
        get_config()


def test_validation_error_missing_field(tmp_path):
    """
    Edge Case (Pydantic): Testet, ob ein `ConfigValidationError` bei einem fehlenden Pflichtfeld ausgelöst wird.
    """
    incomplete_content = {
        "server": {"host": "localhost", "port": 8080},
        # "logging" fehlt
        "app_name": "IncompleteApp",
    }
    config_path = create_test_config_file(tmp_path, incomplete_content)
    os.environ["CONFIG_PATH"] = config_path

    with pytest.raises(ConfigValidationError, match="logging"):
        get_config()


def test_validation_error_wrong_type(tmp_path):
    """
    Edge Case (Pydantic): Testet, ob ein `ConfigValidationError` bei falschem Datentyp ausgelöst wird.
    """
    wrong_type_content = {
        "server": {"host": "localhost", "port": "not-a-number"},
        "logging": {"level": "INFO"},
        "app_name": "WrongTypeApp",
    }
    config_path = create_test_config_file(tmp_path, wrong_type_content)
    os.environ["CONFIG_PATH"] = config_path

    with pytest.raises(ConfigValidationError, match="server.port"):
        get_config()


def test_validation_error_field_constraint(tmp_path):
    """
    Edge Case (Pydantic): Testet, ob ein `ConfigValidationError` bei einer verletzten Feld-Regel ausgelöst wird.
    """
    invalid_port_content = {
        "server": {"host": "localhost", "port": -80},  # Port muss positiv sein
        "logging": {"level": "INFO"},
        "app_name": "InvalidPortApp",
    }
    config_path = create_test_config_file(tmp_path, invalid_port_content)
    os.environ["CONFIG_PATH"] = config_path

    with pytest.raises(ConfigValidationError, match="server.port"):
        get_config()
