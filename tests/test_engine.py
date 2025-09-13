# tests/test_engine.py
import logging
import shutil

import pytest
from recovery_agent.config_service.models import (
    AppConfig,
    LoggingSettings,
    RecoverySettings,
    ServerSettings,
)
from recovery_agent.restoration.engine import RestorationEngine


def create_mock_config() -> AppConfig:
    """Creates a valid mock AppConfig object for testing."""
    return AppConfig(
        app_name="TestEngineApp",
        server=ServerSettings(),
        logging=LoggingSettings(),
        recovery_settings=RecoverySettings(
            target_dir="/opt/app",
            backup_formats={"logs": "*.log", "db": "*.sql"},
            encrypt_key="test-secret-key",
        ),
    )


def test_engine_initialization_success():
    """Tests that the RestorationEngine initializes correctly with a valid config."""
    mock_config = create_mock_config()
    engine = RestorationEngine(backup_path="/tmp/backups", config=mock_config)

    assert str(engine.backup_path) == "/tmp/backups"
    assert str(engine.target_dir) == mock_config.recovery_settings.target_dir
    assert engine.encrypt_key == mock_config.recovery_settings.encrypt_key


def test_run_restore_happy_path(tmp_path, caplog):
    """
    Tests a successful run_restore operation, including file copying and logging.
    """
    source_dir = tmp_path / "backup"
    target_dir = tmp_path / "target"
    source_dir.mkdir()

    (source_dir / "app.log").touch()
    (source_dir / "database.sql").touch()

    mock_config = create_mock_config()
    # Update the Pydantic model attribute, not a dict key
    mock_config.recovery_settings.target_dir = str(target_dir)

    engine = RestorationEngine(backup_path=str(source_dir), config=mock_config)

    with caplog.at_level(logging.INFO):
        success = engine.run_restore()
        assert success is True
        assert (target_dir / "app.log").exists()
        assert (target_dir / "database.sql").exists()
        assert "Restoration process completed successfully." in caplog.text


def test_run_restore_fails_if_backup_source_missing(tmp_path, caplog):
    """Tests that run_restore fails if the backup source does not exist."""
    non_existent_source = tmp_path / "non_existent_backup"
    mock_config = create_mock_config()
    engine = RestorationEngine(backup_path=str(non_existent_source), config=mock_config)

    with caplog.at_level(logging.ERROR):
        success = engine.run_restore()
        assert success is False
        assert f"Backup source directory '{non_existent_source}' does not exist" in caplog.text
