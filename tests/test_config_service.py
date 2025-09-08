from unittest.mock import patch, mock_open

import pytest
import yaml

from recovery_agent import config_service
from recovery_agent.config_service import DEFAULTS, ConfigError, get_config


@pytest.fixture(autouse=True)
def reset_config_cache():
    """
    Fixture to automatically reset the config cache before each test.
    This ensures test isolation.
    """
    config_service._config_cache = None


def test_get_config_valid(tmp_path):
    """
    Tests that a valid YAML file is correctly read and merged with defaults.
    """
    config_path = tmp_path / "config.yaml"
    config_content = {"target_dir": "/tmp/test", "encrypt_key": "abc123"}
    config_path.write_text(yaml.dump(config_content))

    expected_config = DEFAULTS.copy()
    expected_config.update(config_content)

    conf = get_config(config_path)
    assert conf == expected_config


def test_get_config_file_not_found_raises_error(tmp_path):
    """
    Tests that ConfigError is raised if an explicit config file does not exist.
    """
    config_path = tmp_path / "missing.yaml"
    with pytest.raises(ConfigError, match="Configuration file not found"):
        get_config(config_path)


def test_get_config_no_file_returns_defaults():
    """
    Tests that default settings are returned if no config file is specified
    and config.yaml is not found.
    """
    with patch("pathlib.Path.is_file", return_value=False):
        conf = get_config()
        assert conf == DEFAULTS


def test_get_config_invalid_yaml(tmp_path):
    """
    Tests that ConfigError is raised for a malformed YAML file.
    """
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text("{this: is: invalid}")
    with pytest.raises(ConfigError, match="Invalid YAML configuration"):
        get_config(config_path)


def test_get_config_uses_cache():
    """
    Tests that the configuration is read from cache on subsequent calls.
    """
    config_data = yaml.dump({"key": "value"})
    m = mock_open(read_data=config_data)

    with patch("pathlib.Path.is_file", return_value=True), patch("pathlib.Path.open", m):
        # First call should read from file and cache the result
        first_call_result = get_config()
        assert first_call_result["key"] == "value"
        assert "target_dir" in first_call_result  # From defaults

        # Second call should hit the cache and not open the file again
        second_call_result = get_config()
        assert second_call_result == first_call_result
        m.assert_called_once()
