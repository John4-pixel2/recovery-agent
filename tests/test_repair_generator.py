# tests/test_repair_generator.py

import pytest

from recovery_agent.self_repair.repair_generator import (
    MissingDirectoryRule,
    PermissionErrorRule,
    RepairScriptGenerator,
)


@pytest.fixture
def generator() -> RepairScriptGenerator:
    """Provides a RepairScriptGenerator instance with standard rules registered."""
    gen = RepairScriptGenerator()
    gen.register_rule(PermissionErrorRule())
    gen.register_rule(MissingDirectoryRule())
    return gen


def test_permission_error_rule(generator):
    """Tests that the PermissionErrorRule generates the correct chmod script."""
    log = "CRITICAL: Failed to write to '/var/log/app.log' due to Permission denied."
    script = generator.generate(log)
    assert script is not None
    assert "chmod -R 755 /var/log/app.log" in script


def test_missing_directory_rule(generator):
    """Tests that the MissingDirectoryRule generates the correct mkdir script."""
    log = "ERROR: FileNotFoundError: [Errno 2] No such file or directory: '/opt/data/reports/daily.csv'"
    script = generator.generate(log)
    assert script is not None
    assert "mkdir -p /opt/data/reports" in script


def test_tenant_specific_permission_error(generator):
    """Tests that a tenant_id correctly modifies the generated script."""
    log = "CRITICAL: Permission denied for '/srv/customers/acme/uploads/file.zip'"
    script = generator.generate(log, tenant_id="acme")
    assert script is not None
    assert "chown -R acme_user:acme_group /srv/customers/acme/uploads/file.zip" in script
    assert "chmod -R 755 /srv/customers/acme/uploads/file.zip" in script


def test_no_matching_rule_returns_none(generator):
    """Tests that None is returned when no rule matches the log content."""
    log = "ERROR: Database connection timed out."
    script = generator.generate(log)
    assert script is None


def test_path_extraction_failure(generator):
    """Tests that an error comment is returned if a path cannot be extracted."""
    log = "Permission denied, but the format is totally weird."
    script = generator.generate(log)
    assert script is not None
    assert "# Error: Could not extract a valid path" in script
