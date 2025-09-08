#pip install -e .
#pytest tests/test_config_service.py -v
#pytest tests/test_app.py -v
#pytest --cov=recovery_agent --cov-report=term-missing

# recovery_agent/config_service.py

import yaml
from pathlib import Path

class ConfigError(Exception):
    pass


def get_config(path: str | Path = "config.yaml") -> dict:
    config_path = Path(path)

    if not config_path.exists():
        raise ConfigError(f"Configuration file not found: {config_path}")

    try:
        with config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML configuration: {e}")

    if not isinstance(data, dict):
        raise ConfigError("Configuration file must be a mapping (dict).")

    # <-- das hier fehlt aktuell!
    return data
