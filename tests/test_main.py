# tests/test_main.py
import sys
import logging
from unittest.mock import MagicMock, patch

import pytest

# Import the correct base exception from the config service
from recovery_agent.config_service import ConfigServiceError
from recovery_agent.main import main


def test_main_happy_path_restore(monkeypatch):
    """Tests the happy path for the restore action."""
    # Mock get_config to return a dummy Pydantic-like object
    mock_config = MagicMock()
    monkeypatch.setattr("recovery_agent.main.get_config", lambda: mock_config)

    # Mock the RestorationEngine class
    mock_engine_class = MagicMock()
    monkeypatch.setattr("recovery_agent.main.RestorationEngine", mock_engine_class)

    with patch("sys.argv", ["prog", "--action", "restore", "--backup", "/tmp/backup"]):
        assert main() == 0

    # Verify that the engine was instantiated with the correct config object
    mock_engine_class.assert_called_once_with(
        backup_path="/tmp/backup", config=mock_config
    )
    mock_engine_class.return_value.run_restore.assert_called_once()


def test_main_handles_config_error(monkeypatch, caplog):
    """Tests that the application exits gracefully on a ConfigServiceError."""
    # Patch get_config to raise the specific error
    monkeypatch.setattr(
        "recovery_agent.main.get_config",
        lambda: (_ for _ in ()).throw(ConfigServiceError("File not found")),
    )
    with patch("sys.argv", ["prog", "--action", "test"]):
        assert main() == 1
    # Verify that the error message was logged correctly
    assert "Configuration error: File not found" in caplog.text


def test_main_exits_if_backup_missing_for_restore(monkeypatch):
    """
    Tests that main() exits via argparse if --backup is missing for the restore action.
    """
    # Mock get_config to avoid a real file read
    monkeypatch.setattr("recovery_agent.main.get_config", lambda: {})

    # Set args without --backup
    monkeypatch.setattr(sys, "argv", ["prog", "--action", "restore"])

    # Assert that argparse causes a SystemExit
    with pytest.raises(SystemExit) as e:
        main()
    assert e.value.code == 2


def test_main_exits_on_invalid_action(monkeypatch):
    """
    Tests that main() exits via argparse for an invalid action choice.
    """
    monkeypatch.setattr("recovery_agent.main.get_config", lambda: {})
    monkeypatch.setattr(sys, "argv", ["prog", "--action", "invalid_action"])

    with pytest.raises(SystemExit) as e:
        main()
    assert e.value.code == 2


def test_main_handles_test_action_successfully(monkeypatch, caplog):
    """
    Tests that the 'test' action runs successfully and logs the correct message.
    """
    # Set the capture level to INFO, so the test can see the application's logs
    caplog.set_level(logging.INFO)

    monkeypatch.setattr("recovery_agent.main.get_config", lambda: {})
    monkeypatch.setattr(sys, "argv", ["prog", "--action", "test"])

    exit_code = main()
    assert exit_code == 0

    assert "Starting tests..." in caplog.text
    assert "Tests passed!" in caplog.text


@pytest.mark.filterwarnings("ignore:.*'recovery_agent.main' found in sys.modules.*")
def test_main_entry_point_dunder(monkeypatch, tmp_path):
    """
    Tests that the if __name__ == '__main__' block correctly calls main().
    """
    # 1. Create a dummy config file so the real get_config() doesn't fail
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "app_name: Test\n"
        "server: {host: localhost, port: 8000}\n"
        "logging: {level: INFO}\n"
        "recovery_settings: {target_dir: /tmp, backup_formats: {}}"
    )

    # 2. Change the current directory to where the config is
    monkeypatch.chdir(tmp_path)

    # 3. Provide minimal valid command-line arguments
    monkeypatch.setattr(sys, "argv", ["recovery_agent", "--action", "test"])

    # 4. Patch sys.exit to prevent the test runner from stopping
    with patch("sys.exit") as mock_exit:
        # Use runpy to execute the module's __main__ block
        import runpy

        runpy.run_module("recovery_agent.main", run_name="__main__")

        # 5. Assert that the program exited with code 0 (success)
        mock_exit.assert_called_once_with(0)
