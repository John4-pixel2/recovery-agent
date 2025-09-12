# tests/test_repair_generator.py

import pytest
from typing import Optional

from recovery_agent.self_repair.repair_generator import (
    MissingDirectoryRule,
    PermissionErrorRule,
    RuleRegistry,
    RepairRule,  # Import the base class
)


@pytest.fixture
def registry() -> RuleRegistry:
    """Stellt eine RuleRegistry-Instanz mit registrierten Standardregeln bereit."""
    reg = RuleRegistry()
    reg.register_rule(PermissionErrorRule())
    reg.register_rule(MissingDirectoryRule())
    return reg


def test_permission_error_rule_generates_chmod(registry):
    """
    Testet, dass die PermissionErrorRule ein korrektes chmod-Skript generiert.
    """
    error_log = "CRITICAL: Failed to write to '/var/log/app.log' due to Permission denied."
    script = registry.find_repair(error_log)
    assert script is not None
    assert "chmod -R 755 /var/log/app.log" in script
    assert "# Repairing permission issue for path: /var/log/app.log" in script


def test_permission_error_rule_with_tenant_generates_chown(registry):
    """
    Testet, dass die PermissionErrorRule mit Tenant-ID ein chown-Kommando generiert.
    """
    error_log = "ERROR: Permission denied for '/srv/data/customerA/file.txt'."
    script = registry.find_repair(error_log, tenant="customerA")
    assert script is not None
    assert "chown -R customerA_user:customerA_group /srv/data/customerA/file.txt" in script
    assert "chmod -R 755 /srv/data/customerA/file.txt" in script


def test_missing_directory_rule_generates_mkdir(registry):
    """
    Testet, dass die MissingDirectoryRule ein korrektes mkdir-Skript generiert.
    """
    error_log = "ERROR: FileNotFoundError: [Errno 2] No such file or directory: '/opt/app/data/reports/daily.csv'"
    script = registry.find_repair(error_log)
    assert script is not None
    assert "mkdir -p /opt/app/data/reports" in script
    assert "# Creating missing directory structure" in script


def test_no_matching_rule_returns_default_message(registry):
    """
    Testet, dass die Standardmeldung zurückgegeben wird, wenn keine Regel passt.
    """
    error_log = "ERROR: Database connection timed out after 3000ms."
    script = registry.find_repair(error_log)
    assert script == "No repair suggestion found for the given error."


def test_path_extraction_failure_in_permission_error_rule(registry):
    """
    Testet, dass eine Fehlermeldung zurückgegeben wird, wenn der Pfad nicht extrahiert werden kann.
    """
    error_log = "Permission denied, but the format is totally weird and has no path."
    script = registry.find_repair(error_log)
    assert script is not None
    assert "# Error: Could not extract a valid path from the 'Permission denied' message." in script


def test_path_extraction_failure_in_missing_directory_rule(registry):
    """
    Testet, dass eine Fehlermeldung zurückgegeben wird, wenn der Pfad nicht extrahiert werden kann.
    """
    error_log = "No such file or directory, but no path is given."
    script = registry.find_repair(error_log)
    assert script is not None
    assert "# Error: Could not extract a valid path from the 'No such file or directory' message." in script


def test_register_invalid_rule_raises_type_error():
    """
    Testet, dass RuleRegistry einen TypeError auslöst, wenn eine ungültige Regel registriert wird.
    """
    registry = RuleRegistry()
    with pytest.raises(TypeError, match="Rule must be an instance of RepairRule."):
        registry.register_rule("not_a_rule_instance")  # type: ignore


def test_rule_precedence(tmp_path):
    """
    Testet, dass die Regeln in der Reihenfolge ihrer Registrierung geprüft werden
    und die erste passende Regel gewinnt.
    """

    class CatchAllRule(RepairRule):
        def matches(self, error_message: str, tenant: Optional[str] = None) -> bool:
            return True  # Passt immer

        def generate_script(self, error_message: str, tenant: Optional[str] = None) -> str:
            return "# Catch-all script"

    registry = RuleRegistry()
    registry.register_rule(CatchAllRule())  # Diese Regel wird zuerst registriert
    registry.register_rule(PermissionErrorRule())  # Diese sollte nie erreicht werden

    error_log = "Permission denied"
    script = registry.find_repair(error_log)
    assert script == "# Catch-all script"  # Bestätigt, dass CatchAllRule gewonnen hat