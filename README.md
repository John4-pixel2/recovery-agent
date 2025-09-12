# Recovery Agent

[![Python CI](https://github.com/John4-pixel2/recovery-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/John4-pixel2/recovery-agent/actions) [![codecov](https://codecov.io/gh/John4-pixel2/recovery-agent/branch/main/graph/badge.svg)](https://codecov.io/gh/John4-pixel2/recovery-agent)

A flexible agent designed to automate the restoration of application state from various backup formats.

## Features

- **Command-Line Interface**: A powerful CLI to trigger and manage restoration tasks.
- **Web UI**: A simple Flask-based web interface to monitor the agent's status.
- **Configurable**: Easily configure backup formats and target directories via a `config.yaml` file.
- **Robust Testing**: High test coverage with `pytest` to ensure reliability.
- **Automated Quality Checks**: CI pipeline using GitHub Actions for linting, formatting, type checking, and testing.

## Architecture Highlight: Modular Self-Repair

The agent is designed to be extensible. A key example is the **Self-Repair Script Generator**, which allows new error-handling rules to be added without modifying the core logic.

The architecture is based on two main components:

1.  **`RepairRule` (The Contract)**: An abstract base class that defines a common interface for all rules. Each rule must know how to `matches` a specific error in a log and how to `generate_script` for it.

2.  **`RepairScriptGenerator` (The Orchestrator)**: This class manages a list of rule instances. It iterates through them and uses the first one that matches the error log to generate a suggested repair script.

This design makes the system highly modular. To support a new error type, you simply create a new class that inherits from `RepairRule` and register it with the generator.

### Example: Adding a `PermissionErrorRule`

```python
# 1. Define a specific rule
class PermissionErrorRule(RepairRule):
    def matches(self, log_content: str) -> bool:
        return "Permission denied" in log_content

    def generate_script(self, log_content: str) -> str:
        # Logic to extract path and generate a `chmod` command
        path = extract_path_from_log(log_content)
        return f"chmod -R 755 {path}"

# 2. Register the rule with the generator
generator = RepairScriptGenerator()
generator.register_rule(PermissionErrorRule())

# 3. Use the generator to get a script for a given error
error_log = "CRITICAL: Permission denied for file /var/data/db.sql"
suggested_script = generator.generate(error_log)
# Output: "chmod -R 755 /var/data/db.sql"
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
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    ```

3.  **Install the project in editable mode with all dependencies:**
    ```sh
    pip install -e ".[test,dev]"
    ```

## Usage

### Command-Line Interface (CLI)

The primary way to use the agent is through the `recovery-agent-cli` command.

-   **Run a restoration:**
    ```sh
    recovery-agent-cli --action restore --backup /path/to/your/backups
    ```

-   **Run a test action:**
    ```sh
    recovery-agent-cli --action test
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

-   **Run tests with coverage report:**
    ```sh
    pytest --cov=recovery_agent
    ```

-   **Check formatting and linting:**
    ```sh
    ruff check .
    black --check .
    ```

-   **Apply formatting:**
    ```sh
    ruff format .
    black .
    ```
