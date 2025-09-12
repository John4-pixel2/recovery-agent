# config_service/models.py
from typing import Dict, Optional

from pydantic import BaseModel, Field, PositiveInt


class ServerSettings(BaseModel):
    """Pydantic model for server settings."""

    host: str = "127.0.0.1"
    port: PositiveInt = 8000


class LoggingSettings(BaseModel):
    """Pydantic model for logging settings."""

    level: str = Field("INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    format: str = "%(asctime)s - %(levelname)s - %(message)s"


class RecoverySettings(BaseModel):
    """Pydantic model for the legacy restoration settings."""

    target_dir: str
    backup_formats: Dict[str, str]
    encrypt_key: Optional[str] = None


class AppConfig(BaseModel):
    """The main Pydantic model that validates the entire config.yaml."""

    app_name: str = Field(..., min_length=1)
    debug_mode: bool = False
    server: ServerSettings
    logging: LoggingSettings
    recovery_settings: RecoverySettings  # Nested model for legacy settings
