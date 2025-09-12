# tests/test_anomaly_detector.py

from recovery_agent.analysis.anomaly_detector import analyze_backup
from recovery_agent.config_service.models import (
    AppConfig,
    LoggingSettings,
    RecoverySettings,
    ServerSettings,
)


def create_mock_config() -> AppConfig:
    """Creates a valid mock AppConfig object for testing."""
    return AppConfig(
        app_name="TestAnomalyDetectorApp",
        server=ServerSettings(),
        logging=LoggingSettings(),
        recovery_settings=RecoverySettings(
            target_dir="/tmp",
            backup_formats={"logs": "*.log", "db": "*.sql"},
        ),
    )


def test_analyze_backup_success_with_valid_backup(tmp_path):
    """Tests a successful analysis with a valid backup."""
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    (backup_dir / "db.sql").write_text("SELECT * FROM users;")
    (backup_dir / "app.log").touch()

    result = analyze_backup(str(backup_dir), create_mock_config())

    assert result["status"] == "ok"
    assert result["details"]["sql_file_count"] == 1


def test_analyze_backup_fails_with_empty_sql_file(tmp_path):
    """Tests that analysis fails if the SQL file is empty."""
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    (backup_dir / "db.sql").touch()  # Empty file
    (backup_dir / "app.log").touch()

    result = analyze_backup(str(backup_dir), create_mock_config())

    assert result["status"] == "error"
    assert "is empty" in result["details"]["error"]


def test_analyze_backup_warns_if_no_log_files_found(tmp_path):
    """Tests that analysis returns a warning if no log files are found."""
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    (backup_dir / "db.sql").write_text("SELECT * FROM users;")

    result = analyze_backup(str(backup_dir), create_mock_config())

    assert result["status"] == "warn"
    assert "No log files" in result["details"]["warning"]
