# tests/test_config_service.py

import os
from unittest.mock import patch

import pytest
import yaml

# Importiere die neue öffentliche API
from recovery_agent.config_service import (
    ConfigFileError,
    ConfigValidationError,
    get_config,
)
# Importiere interne Teile für das Test-Setup
from recovery_agent.config_service.accessor import _reset_config_cache_for_testing
from recovery_agent.config_service.models import AppConfig


@pytest.fixture(autouse=True)
def setup_teardown():
    """Stellt sicher, dass der Cache vor jedem Test leer ist und die ENV-Variable sauber ist."""
    _reset_config_cache_for_testing()
    if "CONFIG_PATH" in os.environ:
        del os.environ["CONFIG_PATH"]
    yield
    _reset_config_cache_for_testing()
    if "CONFIG_PATH" in os.environ:
        del os.environ["CONFIG_PATH"]


def create_test_config_file(tmp_path, content):
    """Hilfsfunktion zum Erstellen einer temporären config.yaml."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump(content))
    return str(config_file)


# --- Test-Szenarien ---

def test_load_valid_config_success(tmp_path):
    """Happy Path: Testet das erfolgreiche Laden und Validieren einer korrekten Konfiguration."""
    valid_content = {
        "app_name": "MyTestApp",
        "server": {"host": "0.0.0.0", "port": 9000},
        "logging": {"level": "DEBUG"},
        "recovery_settings": {
            "target_dir": "/tmp/restored",
            "backup_formats": {"db": "*.bak"},
        },
    }
    config_path = create_test_config_file(tmp_path, valid_content)
    os.environ["CONFIG_PATH"] = config_path

    config = get_config()

    assert isinstance(config, AppConfig)
    assert config.server.host == "0.0.0.0"
    assert config.recovery_settings.target_dir == "/tmp/restored"


def test_config_is_cached(tmp_path):
    """Testet, ob die Konfiguration nach dem ersten Laden gecacht wird."""
    valid_content = {
        "app_name": "CacheTest",
        "server": {"host": "localhost", "port": 8080},
        "logging": {"level": "INFO"},
        "recovery_settings": {
            "target_dir": "/tmp", "backup_formats": {"logs": "*.log"}
        },
    }
    config_path = create_test_config_file(tmp_path, valid_content)
    os.environ["CONFIG_PATH"] = config_path

    # Patche die Funktion dort, wo sie aufgerufen wird (im accessor-Modul)
    with patch("recovery_agent.config_service.accessor.load_raw_config") as mock_loader:
        mock_loader.return_value = valid_content

        # Erster Aufruf: Soll die (gemockte) Ladefunktion aufrufen
        config1 = get_config()
        mock_loader.assert_called_once()

        # Zweiter Aufruf: Soll aus dem Cache kommen und den Loader nicht erneut aufrufen
        config2 = get_config()
        mock_loader.assert_called_once()

        assert config1 is config2


def test_file_not_found_raises_error():
    """Edge Case: Testet, ob ein ConfigFileError ausgelöst wird, wenn die Datei nicht existiert."""
    os.environ["CONFIG_PATH"] = "non_existent_file.yaml"
    with pytest.raises(ConfigFileError, match="Konfigurationsdatei nicht gefunden"):
        get_config()


def test_validation_error_missing_field(tmp_path):
    """Edge Case (Pydantic): Testet, ob ein ConfigValidationError bei einem fehlenden Pflichtfeld ausgelöst wird."""
    incomplete_content = {
        "app_name": "IncompleteApp",
        "server": {"host": "localhost"},
        # logging und recovery_settings fehlen
    }
    config_path = create_test_config_file(tmp_path, incomplete_content)
    os.environ["CONFIG_PATH"] = config_path

    with pytest.raises(ConfigValidationError):
        get_config()


def test_validation_error_wrong_type(tmp_path):
    """Edge Case (Pydantic): Testet, ob ein ConfigValidationError bei falschem Datentyp ausgelöst wird."""
    wrong_type_content = {
        "app_name": "WrongTypeApp",
        "server": {"host": "localhost", "port": "not-a-number"},
        "logging": {"level": "INFO"},
        "recovery_settings": {
            "target_dir": "/tmp", "backup_formats": {"logs": "*.log"}
        },
    }
    config_path = create_test_config_file(tmp_path, wrong_type_content)
    os.environ["CONFIG_PATH"] = config_path

    with pytest.raises(ConfigValidationError, match="server.port"):
        get_config()
