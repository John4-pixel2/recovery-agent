# recovery_agent/analysis/anomaly_detector.py

from pathlib import Path
from typing import Any, Dict

from recovery_agent.config_service.models import AppConfig


def analyze_backup(backup_path_str: str, config: AppConfig) -> Dict[str, Any]:
    """
    Analyzes a backup directory based on simple heuristics, using a validated config.

    Args:
        backup_path_str: The path to the backup source directory.
        config: A validated AppConfig instance.

    Returns:
        A dictionary with analysis results.
    """
    backup_path = Path(backup_path_str)
    if not backup_path.is_dir():
        return {
            "status": "error",
            "details": {"error": f"Backup directory not found: {backup_path}"},
        }

    # Access settings through the validated, nested Pydantic model
    recovery_conf = config.recovery_settings
    sql_pattern = recovery_conf.backup_formats.get("db", "*.sql")
    log_pattern = recovery_conf.backup_formats.get("logs", "*.log")

    sql_files = list(backup_path.glob(sql_pattern))
    log_files = list(backup_path.glob(log_pattern))

    if not sql_files:
        return {
            "status": "error",
            "details": {"error": f"No SQL files matching '{sql_pattern}' found."},
        }

    if sql_files[0].stat().st_size == 0:
        return {
            "status": "error",
            "details": {"error": f"SQL file '{sql_files[0]}' is empty."},
        }

    if not log_files:
        return {
            "status": "warn",
            "details": {"warning": f"No log files matching '{log_pattern}' found."},
        }

    return {
        "status": "ok",
        "details": {
            "sql_file_count": len(sql_files),
            "log_file_count": len(log_files),
            "first_sql_file_size": sql_files[0].stat().st_size,
        },
    }
