# Recovery Agent

[![Python CI](https://github.com/John4-pixel2/recovery-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/John4-pixel2/recovery-agent/actions) [![codecov](https://codecov.io/gh/John4-pixel2/recovery-agent/branch/main/graph/badge.svg)](https://codecov.io/gh/John4-pixel2/recovery-agent)

A flexible agent designed to automate the restoration of application state from various backup formats.

## Features

- **Command-Line Interface**: A powerful CLI to trigger and manage restoration tasks.
- **Intelligent Actions**: Includes analysis, self-repair, and an intelligent restore protocol.
- **Web UI**: A simple Flask-based web interface to monitor the agent's status.
- **Configurable**: Easily configure backup formats and target directories via a `config.yaml` file, validated by Pydantic models.
- **Robust Testing**: **100% test coverage** with `pytest` to ensure reliability.
- **Automated Quality Checks**: CI pipeline using GitHub Actions for linting, formatting, type checking, and testing.

## Configuration

The `recovery-agent` uses a `config.yaml` file for its settings. The configuration is loaded and validated using Pydantic models, ensuring data integrity and type safety.

By default, the agent looks for `config.yaml` in the current working directory. You can specify a custom path using the `CONFIG_PATH` environment variable.

### Error Handling

The configuration service is designed to be robust. When calling `get_config()`, you can expect the following specific exceptions:

-   `ConfigServiceError`: Raised for any issues related to file access (e.g., file not found, permission denied, invalid YAML format).
-   `ConfigValidationError`: Raised if the content of the configuration file does not match the required structure or data types defined in the Pydantic models.

This clear separation allows for precise error handling in the application's main logic.

### `config.yaml` Structure Example

```yaml
app_name: "MyRecoveryAgent"
debug_mode: false

server:
  host: "127.0.0.1"
  port: 8000

logging:
  level: "INFO"
  format: "%(asctime)s - %(levelname)s - %(message)s"

recovery_settings:
  target_dir: "/opt/recovery_agent/restored_files"
  encrypt_key: "your-super-secret-base64-key" # Placeholder, should be generated securely
  backup_formats:
    logs: "*.log"
    db: "*.sql"
```
## Role in an Agentic Ecosystem
 
 This project is designed not just as a standalone tool, but as a **specialist agent** that can be part of a larger, collaborative swarm of agents.
 
 ### As a Tool for an Orchestrator
 
 A higher-level "Agent" or a Language Model (LLM) can use `recovery-agent-cli` as a reliable tool. The agent has a well-defined command-line interface that acts as its API:
 
 -   **Input**: It accepts structured arguments like `--action` and `--error-log`.
 -   **Output**: It produces predictable output, such as a repair script or a JSON status, which can be parsed and used by the calling agent for further decisions.
 
 This allows an orchestrator to delegate the complex task of "system recovery" without needing to know the internal implementation details.
 
 ### Example Swarm Collaboration
 1.  A **Monitoring Agent** detects a critical error and saves the log.
 2.  It invokes the **Recovery Agent** (`intelligent-restore`) with the path to the error log.
 3.  The **Recovery Agent** analyzes the error, generates a fix, and applies it.
 4.  A **Validation Agent** is then triggered to confirm that the system is healthy again.




## Architecture Highlight: Modular Self-Repair

The agent is designed to be extensible. A key example is the **Self-Repair Script Generator**, which allows new error-handling rules to be added without modifying the core logic.

This design makes the system highly modular. To support a new error type, you simply create a new class that inherits from `RepairRule` and register it with the generator.

### Example: Adding a `PermissionErrorRule`

This self-contained example demonstrates how to define and register a new rule.

```python
# --- Illustrative Example: How to add a new rule ---
# In a real scenario, these classes would be imported from the agent's modules.
# For this example, we define minimal versions to make it self-contained.
import abc
import re
from typing import List, Optional

class RepairRule(abc.ABC):
    """Abstract base class for a repair rule."""
    PATH_REGEX = re.compile(r"'/([^']+)'")
    @abc.abstractmethod
    def matches(self, error_message: str, tenant: Optional[str] = None) -> bool: ...
    @abc.abstractmethod
    def generate_script(self, error_message: str, tenant: Optional[str] = None) -> str: ...

class RuleRegistry:
    """A simple registry to manage and apply repair rules."""
    def __init__(self): self._rules: List[RepairRule] = []
    def register_rule(self, rule: RepairRule): self._rules.append(rule)
    def find_repair(self, error_message: str, tenant: Optional[str] = None) -> str:
        for rule in self._rules:
            if rule.matches(error_message, tenant):
                return rule.generate_script(error_message, tenant)
        return "No repair suggestion found."

# 1. Define your specific rule
class PermissionErrorRule(RepairRule):
    """A rule that detects 'Permission denied' and suggests a fix."""
    def matches(self, error_message: str, tenant: Optional[str] = None) -> bool:
        # This specific rule doesn't use the tenant, but others might.
        return "Permission denied" in error_message

    def generate_script(self, error_message: str, tenant: Optional[str] = None) -> str:
        match = self.PATH_REGEX.search(error_message)
        if not match:
            return "# Error: Could not extract a valid path from the error."
        path = match.group(1)

        # Tenant-specific logic can be added
        if tenant:
            return f"chown -R {tenant}_user:{tenant}_group '{path}'\nchmod -R 755 '{path}'"
        return f"chmod -R 755 '{path}'"

# 2. Register the rule and use it
registry = RuleRegistry()
registry.register_rule(PermissionErrorRule())

# Find a repair for a specific error log
error = "CRITICAL: Permission denied for file '/var/data/db.sql'"
suggested_script = registry.find_repair(error, tenant="acme")

print(suggested_script)
```

## Installation

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/John4-pixel2/recovery-agent.git
    cd recovery-agent
    ```

2.  **Create and activate a virtual environment:**
    ```sh
    python -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the project in editable mode:**
    ```sh
    pip install -e ".[test,dev]"
    ```

## Usage

### Command-Line Interface (CLI)

The agent provides several actions. The `--action` argument is always required.

-   **Run a standard restoration:**
    ```sh
    recovery-agent-cli --action restore --backup /path/to/your/backups
    ```

-   **Analyze a backup for anomalies:**
    ```sh
    recovery-agent-cli --action analyze --backup /path/to/your/backups
    ```

-   **Generate a repair script from an error log:**
    ```sh
    recovery-agent-cli --action repair --error-log /path/to/error.log
    ```
    For tenant-specific repairs:
    ```sh
    recovery-agent-cli --action repair --error-log /path/to/error.log --tenant acme
    ```

-   **Run the full intelligent restore protocol:**
    This simulates a full autonomous recovery, including diagnosis, intelligence gathering, and planning.
    ```sh
    recovery-agent-cli --action intelligent-restore --error-log /path/to/error.log
    ```
    This action also supports the optional `--tenant` flag.

### Web UI

The Flask application provides a simple status dashboard.

1.  **Run the development server:**
    ```sh
    flask --app recovery_agent.ui.app:create_app run
    ```
    The UI will be available at `http://127.0.0.1:5000`.

## Development

This project uses a suite of tools to ensure code quality.

-   **Run all tests:**
    ```sh
    pytest
    ```

-   **Check formatting and linting:**
    ```sh
    ruff check . && black --check .
    ```

-   **Apply formatting:**
    ```sh
    ruff format . && black .
    ```
