# recovery_agent/config_service/__init__.py

"""
Makes the config_service a Python package and exposes the public API.

This allows other parts of the application to get the configuration
with a simple import:
`from recovery_agent.config_service import get_config`
"""

from .service import get_config
from .exceptions import ConfigFileError, ConfigServiceError, ConfigValidationError
from .models import AppConfig