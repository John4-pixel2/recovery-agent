# config_service/__init__.py

"""
Stellt die öffentliche API für den Konfigurations-Service bereit.

Dieses Modul exportiert die Hauptfunktion `get_config` und die zugehörigen
Exceptions, während die internen Implementierungsdetails (loader, models)
verborgen bleiben.
"""

from .accessor import get_config
from .exceptions import ConfigFileError, ConfigServiceError, ConfigValidationError

__all__ = [
    "get_config",
    "ConfigServiceError",
    "ConfigFileError",
    "ConfigValidationError",
]
