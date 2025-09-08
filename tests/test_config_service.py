#pip install -e .

#pytest tests/test_config_service.py -v
#pytest --cov=recovery_agent --cov-report=term-missing


import pytest
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open

from recovery_agent import config_service
from recovery_agent.config_service import get_config, ConfigError


@pytest.fixture(autouse=True)
def reset_config_cache():
    """
    Fixture to automatically reset the config cache before each test.
    This ensures test isolation.
    """
    config_service._config_cache = None


def test_get_config_valid(tmp_path):
    """
    Tests that a valid YAML file is correctly read and returned as a dictionary.
    """
    config_path = tmp_path / "config.yaml"
    config_content = {"target_dir": "/tmp/test", "encrypt_key": "abc123"}
    config_path.write_text(yaml.dump(config_content))

    conf = get_config(config_path)
    assert conf == config_content


def test_get_config_file_not_found(tmp_path):
    """
    Tests that ConfigError is raised if the config file does not exist.
    """
    config_path = tmp_path / "missing.yaml"
    with pytest.raises(ConfigError, match="Configuration file not found"):
        get_config(config_path)


def test_get_config_invalid_yaml(tmp_path):
    """
    Tests that ConfigError is raised for a malformed YAML file.
    """
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text("{this: is: invalid}")
    with pytest.raises(ConfigError, match="Invalid YAML configuration"):
        get_config(config_path)


def test_get_config_not_dict(tmp_path):
    """
    Tests that ConfigError is raised if the YAML content is not a dictionary.
    """
    config_path = tmp_path / "list.yaml"
    config_path.write_text("- one\n- two\n")
    with pytest.raises(ConfigError, match="must be a mapping"):
        get_config(config_path)


def test_get_config_uses_cache():
    """
    Tests that the configuration is read from cache on subsequent calls
    when no path is provided.
    """
    # Mock the file-based loading to return a specific dict the first time
    config_data = yaml.dump({"key": "value"})
    with patch(
        "recovery_agent.config_service.Path.is_file", return_value=True
    ), patch("builtins.open", mock_open(read_data=config_data)) as mock_open_call:

        # First call, should read from "file"
        first_call_result = get_config()
        assert first_call_result == {"key": "value"}
        mock_open_call.assert_called_once()

        # Second call, should read from cache (mock_open should not be called again)
        second_call_result = get_config()
        assert second_call_result == {"key": "value"}
        mock_open_call.assert_called_once()  # Still only called once
