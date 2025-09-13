# tests/conftest.py

import pytest

from recovery_agent.config_service.models import (
    AppConfig,
    LoggingSettings,
    RecoverySettings,
    ServerSettings,
)


@pytest.fixture
def mock_config() -> AppConfig:
    """Provides a complete and valid AppConfig object for testing."""
    return AppConfig(
        app_name="TestApp",
        server=ServerSettings(),
        logging=LoggingSettings(),
        recovery_settings=RecoverySettings(
            target_dir="/opt/app",
            backup_formats={"logs": "*.log", "db": "*.sql"},
            encrypt_key="a-valid-test-secret-key",  # This field is now included
        ),
    )