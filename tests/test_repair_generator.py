# tests/test_repair_generator.py

import pytest
from recovery_agent.self_repair.repair_generator import (
    MissingDirectoryRule,
    PermissionErrorRule,
    RepairRule,  # Importiere die Basisklasse für Testzwecke
    RuleRegistry,
)
from typing import Optional


# Eine Hilfsklasse für Tests, die immer zutrifft.
# Nützlich, um die Reihenfolge der Regelausführung zu testen.
class CatchAllRule(RepairRule):
    """Eine Testregel, die immer zutrifft und ein generisches Skript erzeugt."""

    def matches(self, error_message: str, tenant: Optional[str] = None) -> bool:
        """Passt immer auf jede Fehlermeldung."""
        return True

    def generate_script(self, error_message: str, tenant: Optional[str] = None) -> str:
        """Generiert ein generisches Catch-all-Skript."""
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
    assert "# Repariere Berechtigungsproblem für Pfad: /var/log/app.log" in script


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
    assert "# Erstelle fehlendes Verzeichnis" in script


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
    assert "# Error: Konnte keinen gültigen Pfad aus der 'Permission denied'-Meldung extrahieren." in script


def test_path_extraction_failure_in_missing_directory_rule_returns_error_comment(registry):
    """
    Testet, dass eine Fehlermeldung zurückgegeben wird, wenn die MissingDirectoryRule keinen Pfad extrahieren kann.
    """
    error_log = "No such file or directory, but no path is given."
    script = registry.generate_script_suggestion(error_log)
    assert script is not None
    assert "# Error: Konnte keinen gültigen Pfad aus der 'No such file or directory'-Meldung extrahieren." in script


def test_register_invalid_rule_raises_type_error():
    """
    Testet, dass RuleRegistry einen TypeError auslöst, wenn ein Objekt registriert wird,
    das nicht von RepairRule erbt.
    """
    registry = RuleRegistry()
    with pytest.raises(TypeError, match="Die Regel muss eine Instanz von RepairRule sein."):
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
