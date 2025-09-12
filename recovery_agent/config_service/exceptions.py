# config_service/exceptions.py

class ConfigServiceError(Exception):
    """Basis-Exception für alle Fehler im Config-Service."""
    pass


class ConfigFileError(ConfigServiceError):
    """Wird ausgelöst, wenn die Konfigurationsdatei nicht geladen werden kann."""
    pass


class ConfigValidationError(ConfigServiceError):
    """Wird ausgelöst, wenn die Konfiguration nicht dem Pydantic-Modell entspricht."""
    pass
