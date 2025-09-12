# Recovery Agent

[![Python CI](https://github.com/John4-pixel2/recovery-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/John4-pixel2/recovery-agent/actions) [![codecov](https://codecov.io/gh/John4-pixel2/recovery-agent/branch/main/graph/badge.svg)](https://codecov.io/gh/John4-pixel2/recovery-agent)

A flexible agent designed to automate the restoration of application state from various backup formats.

## Features

- **Command-Line Interface**: A powerful CLI to trigger and manage restoration tasks.
- **Intelligent Actions**: Includes analysis, self-repair, and an intelligent restore protocol.
- **Web UI**: A simple Flask-based web interface to monitor the agent's status.
- **Configurable**: Easily configure backup formats and target directories via a `config.yaml` file.
- **Robust Testing**: High test coverage with `pytest` to ensure reliability.
- **Automated Quality Checks**: CI pipeline using GitHub Actions for linting, formatting, type checking, and testing.

## Architecture Highlight: Modular Self-Repair

The agent is designed to be extensible. A key example is the **Self-Repair Script Generator**, which allows new error-handling rules to be added without modifying the core logic.

This design makes the system highly modular. To support a new error type, you simply create a new class that inherits from `RepairRule` and register it with the generator.

### Example: Adding a `PermissionErrorRule`

```python
# 1. Define a specific rule
class PermissionErrorRule(RepairRule):
    def matches(self, log_content: str) -> bool:
        return "Permission denied" in log_content

    def generate_script(self, log_content: str) -> str:
        path = extract_path_from_log(log_content)
        return f"chmod -R 755 {path}"

# 2. Register the rule and use it
generator = RepairScriptGenerator()
generator.register_rule(PermissionErrorRule())
suggested_script = generator.generate("CRITICAL: Permission denied for file /var/data/db.sql")
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

-   **Run the full intelligent restore protocol:**
    This simulates a full autonomous recovery, including diagnosis, intelligence gathering, and planning.
    ```sh
    recovery-agent-cli --action intelligent-restore --error-log /path/to/error.log
    ```

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
