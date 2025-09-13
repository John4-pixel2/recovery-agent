# recovery_agent/config_service/exceptions.py

class ConfigServiceError(Exception):
    """Base exception for any configuration service related issue."""
    pass

class ConfigFileError(Exception):
    """Custom exception for errors related to the configuration file."""
    pass

class ConfigValidationError(Exception):
    """Custom exception for errors during Pydantic model validation."""
    pass