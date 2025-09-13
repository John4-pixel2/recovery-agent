# recovery_agent/config_service/exceptions.py

class ConfigServiceError(Exception):
    """Base exception for all configuration service-related errors."""
    pass


class ConfigFileError(ConfigServiceError):
    """Exception for errors related to accessing the configuration file."""
    pass


class ConfigValidationError(ConfigServiceError):
    """Exception for errors during Pydantic model validation."""
    pass