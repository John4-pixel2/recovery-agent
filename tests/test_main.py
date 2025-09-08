import sys
from unittest.mock import patch

import pytest

from recovery_agent import main
from recovery_agent.config_service import ConfigError


def test_main_happy_path_restore(monkeypatch):
    """
    Tests that main() correctly parses arguments, loads configuration,
    and instantiates the RestorationEngine with the correct parameters.
    """
    mock_settings = {
        "target_dir": "/tmp",
        "encrypt_key": "KEY",
        "backup_formats": {"all": "*"},
    }
    test_args = ["recovery_agent", "--action", "restore", "--backup", "/tmp/source"]
    monkeypatch.setattr(sys, "argv", test_args)

    with (
        patch(
            "recovery_agent.main.get_config", return_value=mock_settings
        ) as mock_get_config,
        patch(
            "recovery_agent.main.RestorationEngine", autospec=True
        ) as mock_engine_class,
    ):
        exit_code = main.main()
        assert exit_code == 0
        mock_get_config.assert_called_once()
        mock_engine_class.assert_called_once_with(
            backup_path="/tmp/source", config=mock_settings
        )
        mock_engine_class.return_value.run_restore.assert_called_once()


def test_main_handles_config_error(monkeypatch, caplog):
    """
    Tests that main() exits with code 1 if get_config() raises a ConfigError.
    """
    with patch(
        "recovery_agent.main.get_config", side_effect=ConfigError("File not found")
    ):
        exit_code = main.main()
        assert exit_code == 1

    assert "Configuration error: File not found" in caplog.text


def test_main_exits_if_backup_missing_for_restore(monkeypatch):
    """
    Tests that main() exits via argparse if --backup is missing for the restore action.
    """
    monkeypatch.setattr("recovery_agent.main.get_config", lambda: {})
    test_args = ["recovery_agent", "--action", "restore"]
    monkeypatch.setattr(sys, "argv", test_args)

    with pytest.raises(SystemExit) as e:
        main.main()
    assert e.value.code == 2


def test_main_exits_on_invalid_action(monkeypatch):
    """
    Tests that main() exits via argparse for an invalid action choice.
    """
    monkeypatch.setattr("recovery_agent.main.get_config", lambda: {})
    test_args = ["recovery_agent", "--action", "invalid_action"]
    monkeypatch.setattr(sys, "argv", test_args)

    with pytest.raises(SystemExit) as e:
        main.main()
    assert e.value.code == 2


def test_main_handles_test_action_successfully(monkeypatch, caplog):
    """
    Tests that the 'test' action runs successfully and logs the correct message.
    """
    caplog.set_level("INFO")
    monkeypatch.setattr("recovery_agent.main.get_config", lambda: {})

    test_args = ["recovery_agent", "--action", "test"]
    monkeypatch.setattr(sys, "argv", test_args)

    exit_code = main.main()
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
    config_file.write_text("target_dir: /tmp\nencrypt_key: secret\nbackup_formats: {}")

    # 2. Change the current directory to where the config is
    monkeypatch.chdir(tmp_path)

    # 3. Provide minimal valid command-line arguments
    monkeypatch.setattr(sys, "argv", ["recovery_agent", "--action", "test"])

    # 4. Patch sys.exit to prevent the test runner from stopping
    with patch("sys.exit") as mock_exit:
        # Use runpy to execute the module's __main__ block
        import runpy

        runpy.run_module("recovery_agent.main", run_name="__main__")

        # 6. Assert that the program exited with code 0 (success)
        mock_exit.assert_called_once_with(0)
