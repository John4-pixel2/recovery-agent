# tests/test_repair_generator.py

import pytest
from recovery_agent.self_repair.repair_generator import (
    MissingDirectoryRule,
    PermissionErrorRule,
    RuleRegistry,
    RepairRule,  # Importiere die Basisklasse für Testzwecke
)
from typing import Optional


# Eine Hilfsklasse für Tests, die immer zutrifft.
class CatchAllRule(RepairRule):
    """Eine Testregel, die immer zutrifft und ein generisches Skript erzeugt."""

    def matches(self, error_message: str, tenant: Optional[str] = None) -> bool:
        return True

    def generate_script(self, error_message: str, tenant: Optional[str] = None) -> str:
        return "# Catch-all script"


@pytest.fixture
def registry() -> RuleRegistry:
    """Stellt eine RuleRegistry-Instanz mit registrierten Standardregeln bereit."""
    reg = RuleRegistry()
    reg.register_rule(PermissionErrorRule())
    reg.register_rule(MissingDirectoryRule())
    return reg


def test_permission_error_rule_generates_chmod_script(registry):
    """
    Testet, dass die PermissionErrorRule ein korrektes chmod-Skript generiert
    und den Pfad korrekt extrahiert.
    """
    error_log = "CRITICAL: Failed to write to '/var/log/app.log' due to Permission denied."
    script = registry.generate_script_suggestion(error_log)
    assert script is not None
    assert "chmod -R 755 /var/log/app.log" in script
    assert "# Fix permissions for: /var/log/app.log" in script  # Angepasster Match


def test_permission_error_rule_with_tenant_generates_chown_and_chmod(registry):
    """
    Testet, dass die PermissionErrorRule mit Tenant-ID ein chown- und chmod-Kommando generiert.
    """
    error_log = "ERROR: Permission denied for '/srv/data/customerA/file.txt'."
    script = registry.generate_script_suggestion(error_log, tenant="customerA")
    assert script is not None
    assert "chown -R customerA_user:customerA_group /srv/data/customerA/file.txt" in script
    assert "chmod -R 755 /srv/data/customerA/file.txt" in script


def test_missing_directory_rule_generates_mkdir_script(registry):
    """
    Testet, dass die MissingDirectoryRule ein korrektes mkdir-Skript generiert
    und den Verzeichnispfad korrekt extrahiert.
    """
    error_log = "ERROR: FileNotFoundError: [Errno 2] No such file or directory: '/opt/app/data/reports/daily.csv'"
    script = registry.generate_script_suggestion(error_log)
    assert script is not None
    assert "mkdir -p /opt/app/data/reports" in script
    assert "# Create missing directory structure" in script  # Angepasster Match


def test_no_matching_rule_returns_default_message(registry):
    """
    Testet, dass die Standardmeldung zurückgegeben wird, wenn keine Regel zur Fehlermeldung passt.
    """
    error_log = "ERROR: Database connection timed out after 3000ms."
    script = registry.generate_script_suggestion(error_log)
    assert script == "No repair suggestion found for the given error."


def test_path_extraction_failure_in_permission_error_rule_returns_error_comment(registry):
    """
    Testet, dass eine Fehlermeldung zurückgegeben wird, wenn die PermissionErrorRule keinen Pfad extrahieren kann.
    """
    error_log = "Permission denied, but the format is totally weird and has no path."
    script = registry.generate_script_suggestion(error_log)
    assert script is not None
    assert "# Error: Could not extract a valid path from the permission error log." in script  # Angepasster Match


def test_path_extraction_failure_in_missing_directory_rule_returns_error_comment(registry):
    """
    Testet, dass eine Fehlermeldung zurückgegeben wird, wenn die MissingDirectoryRule keinen Pfad extrahieren kann.
    """
    error_log = "No such file or directory, but no path is given."
    script = registry.generate_script_suggestion(error_log)
    assert script is not None
    assert "# Error: Could not extract a valid path from the missing directory log." in script  # Angepasster Match


def test_register_invalid_rule_raises_type_error():
    """
    Testet, dass RuleRegistry einen TypeError auslöst, wenn ein Objekt registriert wird,
    das nicht von RepairRule erbt.
    """
    registry = RuleRegistry()
    with pytest.raises(TypeError, match="Rule must be an instance of RepairRule."):  # Angepasster Match
        registry.register_rule("not_a_rule_instance")  # type: ignore


def test_rule_precedence_first_matching_rule_wins():
    """
    Testet, dass die Regeln in der Reihenfolge ihrer Registrierung geprüft werden
    und die erste passende Regel gewinnt.
    """
    registry = RuleRegistry()
    # Registriere die CatchAllRule zuerst, sie sollte immer gewinnen, wenn sie vor anderen steht.
    registry.register_rule(CatchAllRule())
    registry.register_rule(PermissionErrorRule())  # Diese sollte nie erreicht werden, wenn CatchAllRule passt.

    error_log = "Permission denied"  # Passt auf beide Regeln
    script = registry.generate_script_suggestion(error_log)
    assert script == "# Catch-all script"  # Bestätigt, dass CatchAllRule gewonnen hat
