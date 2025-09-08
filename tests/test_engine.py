# tests/test_engine.py
import logging
import shutil

from recovery_agent.restoration.engine import RestorationEngine


def create_mock_config() -> dict:
    """Creates a valid mock config dictionary for testing."""
    return {
        "backup_formats": {"logs": "*.log", "db": "*.sql"},
        "target_dir": "/opt/app",
        "encrypt_key": "test-secret-key",
    }


def test_engine_initialization_success():
    """Tests that the RestorationEngine initializes correctly with a valid config."""
    mock_config = create_mock_config()
    engine = RestorationEngine(backup_path="/tmp/backups", config=mock_config)

    assert str(engine.backup_path) == "/tmp/backups"
    assert str(engine.target_dir) == mock_config["target_dir"]
    assert engine.encrypt_key == mock_config["encrypt_key"]


def test_run_restore_happy_path(tmp_path, caplog):
    """
    Tests a successful run_restore operation, including file copying and logging.
    """
    # 1. Setup environment
    source_dir = tmp_path / "backup"
    target_dir = tmp_path / "target"
    source_dir.mkdir()
    target_dir.mkdir()

    # Create dummy backup files
    (source_dir / "app.log").touch()
    (source_dir / "database.sql").touch()
    (source_dir / "ignored.txt").touch()

    # 2. Instantiate engine
    mock_config = create_mock_config()
    mock_config["target_dir"] = str(target_dir)
    engine = RestorationEngine(backup_path=str(source_dir), config=mock_config)

    # 3. Run and Assert
    with caplog.at_level(logging.INFO):
        success = engine.run_restore()

        assert success is True
        # Check if files were copied
        assert (target_dir / "app.log").exists()
        assert (target_dir / "database.sql").exists()
        assert not (target_dir / "ignored.txt").exists()

        # Check logs
        assert "Starting restoration" in caplog.text
        assert "Found 2 files to restore." in caplog.text
        assert "Simulating decryption of backup files..." in caplog.text
        assert "Restoration process completed successfully." in caplog.text


def test_run_restore_fails_if_backup_source_missing(tmp_path, caplog):
    """
    Tests that run_restore fails gracefully if the backup source directory does not exist.
    """
    non_existent_source = tmp_path / "non_existent_backup"
    target_dir = tmp_path / "target"
    target_dir.mkdir()

    mock_config = create_mock_config()
    mock_config["target_dir"] = str(target_dir)
    engine = RestorationEngine(backup_path=str(non_existent_source), config=mock_config)

    with caplog.at_level(logging.ERROR):
        success = engine.run_restore()

        assert success is False
        assert (
            f"Backup source directory '{non_existent_source}' does not exist"
            in caplog.text
        )


def test_run_restore_handles_io_error(tmp_path, monkeypatch, caplog):
    """
    Tests that run_restore handles an IOError during file copy and returns False.
    """
    source_dir = tmp_path / "backup"
    target_dir = tmp_path / "target"
    source_dir.mkdir()
    target_dir.mkdir()
    (source_dir / "app.log").touch()

    # Mock shutil.copy2 to raise an IOError
    def mock_copy2(*args, **kwargs):
        raise OSError("Disk full!")

    monkeypatch.setattr(shutil, "copy2", mock_copy2)

    mock_config = create_mock_config()
    mock_config["target_dir"] = str(target_dir)
    engine = RestorationEngine(backup_path=str(source_dir), config=mock_config)

    with caplog.at_level(logging.CRITICAL):
        success = engine.run_restore()

        assert success is False
        assert "A critical I/O error occurred during file copy" in caplog.text
        assert "Disk full!" in caplog.text


def test_run_restore_success_with_no_matching_files(tmp_path, caplog):
    """
    Tests that run_restore completes successfully and logs a warning
    if no backup files match the configured patterns.
    """
    source_dir = tmp_path / "backup"
    target_dir = tmp_path / "target"
    source_dir.mkdir()
    target_dir.mkdir()

    # Create a file that does NOT match the patterns
    (source_dir / "ignored.txt").touch()

    mock_config = create_mock_config()
    mock_config["target_dir"] = str(target_dir)
    engine = RestorationEngine(backup_path=str(source_dir), config=mock_config)

    with caplog.at_level(logging.WARNING):
        success = engine.run_restore()

        assert success is True
        assert not list(target_dir.iterdir())  # Check that no files were copied
        assert "No backup files found" in caplog.text


def test_run_restore_fails_if_target_dir_is_a_file(tmp_path, caplog):
    """
    Tests that run_restore fails if the target directory is actually a file.
    """
    source_dir = tmp_path / "backup"
    source_dir.mkdir()

    # Create a file where the target directory should be
    target_file = tmp_path / "target"
    target_file.touch()

    mock_config = create_mock_config()
    mock_config["target_dir"] = str(target_file)
    engine = RestorationEngine(backup_path=str(source_dir), config=mock_config)

    with caplog.at_level(logging.ERROR):
        success = engine.run_restore()

        assert success is False
        assert (
            f"Target directory '{target_file}' does not exist or is not a directory"
            in caplog.text
        )
