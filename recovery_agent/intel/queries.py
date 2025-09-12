# recovery_agent/intel/queries.py

from pathlib import Path


def get_last_stable_backup_path() -> str:
    """
    Asks a (hypothetical) Backup-Manager-Agent for the path of the last
    successfully validated backup.

    In a real scenario, this would involve an API call (e.g., REST, gRPC).
    For now, it returns a hardcoded, realistic path.
    """
    print("INFO: Querying Backup-Manager-Agent for the last stable backup...")
    # In a real implementation, this path would be dynamically retrieved.
    return "/tmp/backups/2025-09-10_04-00-00_stable/"


def get_codebase_version() -> str:
    """
    Asks a (hypothetical) AI-Code-Assistant for the current version of the codebase.
    """
    print("INFO: Querying AI-Code-Assistant for the current codebase version...")
    # This would be dynamic in a real system.
    return "v1.3.5"


def get_backup_version(backup_path: Path) -> str:
    """
    Reads the version from a metadata file within a backup directory.
    """
    print(f"INFO: Reading metadata from backup path: {backup_path}")
    # Dummy version for demonstration. A real implementation would parse a manifest file.
    return "v1.2.4"


def get_migration_plan(from_version: str, to_version: str) -> list[str]:
    """
    Asks a (hypothetical) Migration-Specialist-Agent for the necessary
    migration scripts to bridge the version gap.
    """
    print(f"INFO: Querying Migration-Specialist for a plan from {from_version} to {to_version}...")
    # Dummy response for a known migration path.
    if from_version == "v1.2.4" and to_version == "v1.3.5":
        return [
            "migrate_v1.2.4_to_v1.3.0.py",
            "migrate_v1.3.0_to_v1.3.5.py",
        ]
    return []
