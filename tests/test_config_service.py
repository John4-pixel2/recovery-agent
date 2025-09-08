#pip install -e .

#pytest tests/test_config_service.py -v
#pytest --cov=recovery_agent --cov-report=term-missing


from unittest.mock import patch, mock_open

import pytest
import yaml

from recovery_agent import config_service
from recovery_agent.config_service import get_config, ConfigError, DEFAULTS


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

    # Expected result is a merge of defaults and the file content
    expected_config = DEFAULTS.copy()
    expected_config.update(config_content)

    conf = get_config(config_path)
    assert conf == expected_config


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
    m = mock_open(read_data=config_data)

    with patch("pathlib.Path.is_file", return_value=True), patch(
        "pathlib.Path.open", m
    ):
        # First call, should read from "file" and merge with defaults
        first_call_result = get_config()
        assert first_call_result["key"] == "value"
        assert "backup_formats" in first_call_result  # from DEFAULTS
        m.assert_called_once()

        # Second call, should read from cache
        second_call_result = get_config()
        assert second_call_result == first_call_result
        m.assert_called_once()  # Should not be called again
