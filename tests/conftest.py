# tests/conftest.py

import os
import pytest

# Import the service module to directly manipulate its cache for testing
from recovery_agent.config_service import service
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


@pytest.fixture(autouse=True)
def reset_config_cache_and_env():
    """
    This fixture automatically runs before and after each test.
    It ensures that:
    - The config cache is empty.
    - CONFIG_PATH is not accidentally left over from previous tests.
    """
    # Setup: Clean the cache and environment
    service._config_cache = None
    if "CONFIG_PATH" in os.environ:
        del os.environ["CONFIG_PATH"]

    yield

    # Teardown: Ensure tests end cleanly
    service._config_cache = None
    if "CONFIG_PATH" in os.environ:
        del os.environ["CONFIG_PATH"]