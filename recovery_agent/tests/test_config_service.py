# tests/test_config_service.py

import os
from unittest.mock import patch

import pytest
import yaml

# Import the public API
from recovery_agent.config_service import (
    ConfigFileError,
    ConfigValidationError,
    ConfigServiceError,
    get_config,
)
# Import internal parts for test setup
from recovery_agent.config_service.accessor import _config_cache
from recovery_agent.config_service.loader import load_raw_config
from recovery_agent.config_service.models import AppConfig


@pytest.fixture(autouse=True)
def reset_cache():
    """Ensures the cache is empty and environment is clean before each test."""
    global _config_cache
    _config_cache = None
    if "CONFIG_PATH" in os.environ:
        del os.environ["CONFIG_PATH"]


def create_test_config_file(tmp_path, content):
    """Helper function to create a temporary config.yaml."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump(content))
    return str(config_file)


# --- Test Scenarios ---

def test_load_valid_config_success(tmp_path):
    """
    Happy Path: Tests the successful loading and validation of a correct configuration.
    """
    valid_content = {
        "server": {"host": "0.0.0.0", "port": 9000},
        "logging": {"level": "DEBUG"},
        "app_name": "MyTestApp",
        "debug_mode": True,
        "recovery_settings": {
            "target_dir": "/tmp",
            "backup_formats": {"logs": "*.log"},
            "encrypt_key": "test-key",  # Added missing required field
        },
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
    assert config.recovery_settings.encrypt_key.get_secret_value() == "test-key"


def test_config_is_cached(tmp_path):
    """
    Tests that the configuration is cached after the first load.
    The loader function should only be called once.
    """
    valid_content = {
        "server": {"host": "localhost", "port": 8080},
        "logging": {"level": "INFO"},
        "app_name": "CacheTest",
        "recovery_settings": {
            "target_dir": "/tmp",
            "backup_formats": {"logs": "*.log"},
            "encrypt_key": "another-key",
        },
    }
    config_path = create_test_config_file(tmp_path, valid_content)
    os.environ["CONFIG_PATH"] = config_path

    with patch("recovery_agent.config_service.service.load_raw_config", wraps=load_raw_config) as mock_loader:
        # First call: should load the file
        config1 = get_config()
        mock_loader.assert_called_once()

        # Second call: should come from the cache
        config2 = get_config()
        mock_loader.assert_called_once()  # Still only called once

        assert config1 is config2  # Should be the exact same object


def test_file_not_found_raises_error():
    """
    Edge Case: Tests that a ConfigServiceError is raised if the config file does not exist.
    """
    os.environ["CONFIG_PATH"] = "non_existent_file.yaml"
    with pytest.raises(ConfigServiceError, match="Fehler beim Lesen der Konfigurationsdatei"):
        get_config()


def test_invalid_yaml_raises_error(tmp_path):
    """
    Edge Case: Tests that a ConfigServiceError is raised for syntactically incorrect YAML.
    """
    invalid_yaml_content = "server: { host: 'localhost', port: 8080"  # Missing closing brace
    config_file = tmp_path / "invalid.yaml"
    config_file.write_text(invalid_yaml_content)
    os.environ["CONFIG_PATH"] = str(config_file)

    with pytest.raises(ConfigServiceError, match="Fehler beim Parsen der YAML-Datei") as exc_info:
        get_config()
    assert "while parsing a flow mapping" in str(exc_info.value)


def test_validation_error_missing_field(tmp_path):
    """
    Edge Case (Pydantic): Tests that a ConfigValidationError is raised for a missing required field.
    """
    incomplete_content = {
        "server": {"host": "localhost", "port": 8080},
        "recovery_settings": {
            "target_dir": "/tmp", "backup_formats": {"logs": "*.log"},
            "encrypt_key": "test-key",
        },
        "app_name": "IncompleteApp",
    }
    config_path = create_test_config_file(tmp_path, incomplete_content)
    os.environ["CONFIG_PATH"] = config_path

    with pytest.raises(ConfigValidationError, match="Field required.*logging"):
        get_config()


def test_validation_error_wrong_type(tmp_path):
    """
    Edge Case (Pydantic): Tests that a ConfigValidationError is raised for an incorrect data type.
    """
    wrong_type_content = {
        "server": {"host": "localhost", "port": "not-a-number"},
        "logging": {"level": "INFO"},
        "app_name": "WrongTypeApp",
        "recovery_settings": {
            "target_dir": "/tmp", "backup_formats": {"logs": "*.log"},
            "encrypt_key": "test-key",
        },
    }
    config_path = create_test_config_file(tmp_path, wrong_type_content)
    os.environ["CONFIG_PATH"] = config_path

    with pytest.raises(ConfigValidationError, match="server.port"):
        get_config()


def test_validation_error_field_constraint(tmp_path):
    """
    Edge Case (Pydantic): Tests that a ConfigValidationError is raised for a violated field constraint.
    """
    invalid_port_content = {
        "server": {"host": "localhost", "port": -80},  # Port must be positive
        "logging": {"level": "INFO"},
        "app_name": "InvalidPortApp",
        "recovery_settings": {
            "target_dir": "/tmp", "backup_formats": {"logs": "*.log"},
            "encrypt_key": "test-key",
        },
    }
    config_path = create_test_config_file(tmp_path, invalid_port_content)
    os.environ["CONFIG_PATH"] = config_path

    with pytest.raises(ConfigValidationError, match="server.port"):
        get_config()
