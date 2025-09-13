# tests/test_repair_generator.py

from typing import Optional

import pytest

from recovery_agent.self_repair.repair_generator import (
    MissingDirectoryRule,
    PermissionErrorRule,
    RepairRule,  # Importiere die Basisklasse
    RuleRegistry,
)


# Definiere die Hilfsklasse auf Modulebene für sauberen Scope
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


def test_permission_error_rule_generates_chmod(registry):
    """Testet, dass die PermissionErrorRule ein korrektes chmod-Skript generiert."""
    error_log = "CRITICAL: Failed to write to '/var/log/app.log' due to Permission denied."
    script = registry.generate_script_suggestion(error_log)
    assert script is not None
    assert "chmod -R 755 /var/log/app.log" in script


def test_missing_directory_rule_generates_mkdir(registry):
    """Testet, dass die MissingDirectoryRule ein korrektes mkdir-Skript generiert."""
    error_log = "ERROR: No such file or directory: '/opt/app/data/reports/daily.csv'"
    script = registry.generate_script_suggestion(error_log)
    assert script is not None
    assert "mkdir -p /opt/app/data/reports" in script


def test_no_matching_rule_returns_default_message(registry):
    """Testet, dass die Standardmeldung zurückgegeben wird, wenn keine Regel passt."""
    error_log = "ERROR: Database connection timed out."
    script = registry.generate_script_suggestion(error_log)
    assert script == "No repair suggestion found for the given error."


def test_rule_precedence():
    """
    Testet, dass die Regeln in der Reihenfolge ihrer Registrierung geprüft werden
    und die erste passende Regel gewinnt.
    """
    registry = RuleRegistry()
    registry.register_rule(CatchAllRule())  # Diese Regel wird zuerst registriert
    registry.register_rule(PermissionErrorRule())  # Diese sollte nie erreicht werden

    error_log = "Permission denied"
    script = registry.generate_script_suggestion(error_log)
    assert script == "# Catch-all script"
