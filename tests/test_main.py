# tests/test_main.py
from unittest.mock import MagicMock, patch

import pytest

# Importiere die neue, korrekte Basis-Exception
from recovery_agent.config_service import ConfigServiceError
from recovery_agent.main import main


@patch("recovery_agent.main.get_config")
@patch("recovery_agent.main.RestorationEngine")
def test_main_restore_action_success(mock_engine, mock_get_config):
    """Tests the happy path for the restore action."""
    # Mock get_config, um ein Dummy-Pydantic-Objekt zurückzugeben
    mock_config = MagicMock()
    mock_get_config.return_value = mock_config

    with patch("sys.argv", ["prog", "--action", "restore", "--backup", "/tmp/backup"]):
        # Wir erwarten, dass main() erfolgreich durchläuft (Exit-Code 0)
        assert main() == 0

    # Überprüfe, ob die Engine mit dem korrekten Konfigurationsobjekt aufgerufen wurde
    mock_engine.assert_called_once_with(backup_path="/tmp/backup", config=mock_config)
    mock_engine.return_value.run_restore.assert_called_once()


@patch("recovery_agent.main.get_config", side_effect=ConfigServiceError("File not found"))
def test_main_config_error_exit(mock_get_config, caplog):
    """Tests that the application exits gracefully on a ConfigServiceError."""
    with patch("sys.argv", ["prog", "--action", "test"]):
        # Wir erwarten, dass main() mit einem Fehlercode (1) beendet wird
        assert main() == 1
    # Überprüfe, ob die Fehlermeldung korrekt geloggt wurde
    assert "Configuration error: File not found" in caplog.text
