# recovery_agent/self_repair/repair_generator.py

import abc
import re
from pathlib import Path
from typing import List, Optional


class RepairRule(abc.ABC):
    """
    Abstract base class for a single self-repair rule.

    Each concrete rule must implement this class, providing a consistent
    interface for matching log content and generating repair scripts.
    """

    # A robust regex to capture file paths (Linux/Windows), with optional quotes.
    PATH_REGEX = re.compile(r"""['"]?([a-zA-Z]:[\\/][^'"\s]+|/[^\s'"]+)['"]?""")

    @abc.abstractmethod
    def matches(self, log_content: str, tenant_id: Optional[str] = None) -> bool:
        """
        Checks if the log content matches the error this rule can handle.

        Args:
            log_content: The full content of the error log as a string.
            tenant_id: An optional tenant ID for tenant-specific analysis.

        Returns:
            True if the rule matches, False otherwise.
        """
        pass

    @abc.abstractmethod
    def generate_script(
        self, log_content: str, tenant_id: Optional[str] = None
    ) -> str:
        """
        Generates a bash repair script based on the provided log content.

        This method is only called if `matches()` has returned True.

        Args:
            log_content: The full content of the error log.
            tenant_id: An optional tenant ID to generate tenant-specific scripts
                       (e.g., using tenant-specific paths or user accounts).

        Returns:
            A string containing an executable bash command or script.
        """
        pass


class PermissionErrorRule(RepairRule):
    """
    Rule to detect and suggest fixes for "Permission denied" errors.
    """

    def matches(self, log_content: str, tenant_id: Optional[str] = None) -> bool:
        """Detects errors pointing to "Permission denied"."""
        return "Permission denied" in log_content

    def generate_script(
        self, log_content: str, tenant_id: Optional[str] = None
    ) -> str:
        """
        Generates a `chmod` or `chown` command for the path found in the log.
        """
        match = self.PATH_REGEX.search(log_content)
        if not match:
            return (
                "# Error: Could not extract a valid path from the permission error log.\n"
                "# Log format might be unexpected."
            )

        path = match.group(1)
        script = f"# Fix permissions for: {path}\n"

        if tenant_id:
            # For multi-tenant environments, set ownership to a tenant-specific user.
            script += f"chown -R {tenant_id}_user:{tenant_id}_group {path}\n"

        script += f"chmod -R 755 {path}"
        return script


class MissingDirectoryRule(RepairRule):
    """
    Rule to detect and suggest fixes for "No such file or directory" errors.
    """

    def matches(self, log_content: str, tenant_id: Optional[str] = None) -> bool:
        """Detects errors indicating a missing file or directory."""
        return "No such file or directory" in log_content

    def generate_script(
        self, log_content: str, tenant_id: Optional[str] = None
    ) -> str:
        """
        Generates a `mkdir -p` command to create the missing directory structure.
        """
        match = self.PATH_REGEX.search(log_content)
        if not match:
            return (
                "# Error: Could not extract a valid path from the missing directory log.\n"
                "# Log format might be unexpected."
            )

        # Extract the directory part of the path using pathlib for robustness
        path = str(Path(match.group(1)).parent)
        return f"# Create missing directory structure\nmkdir -p {path}"


class RepairScriptGenerator:
    """
    Orchestrates the generation of repair scripts based on error logs.

    This class maintains a list of `RepairRule` instances. It processes
    an error log by checking it against each rule. The first rule that
    matches is used to generate a repair script.
    """

    def __init__(self):
        """Initializes the generator with an empty list of rules."""
        self._rules: List[RepairRule] = []

    def register_rule(self, rule: RepairRule):
        """
        Registers a new rule with the generator.

        This method makes the generator extensible. New rules can be added
        dynamically without modifying the generator's core logic.

        Args:
            rule: An instance of a class that inherits from `RepairRule`.
        """
        if not isinstance(rule, RepairRule):
            raise TypeError("Rule must be an instance of RepairRule.")
        self._rules.append(rule)

    def generate(
        self, log_input: str | Path, tenant_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Analyzes an error log and generates a corresponding repair script.

        The log can be provided as a direct string or as a path to a log file.

        Args:
            log_input: The error log string or a `pathlib.Path` to the log file.
            tenant_id: An optional tenant ID for tenant-specific rule processing.

        Returns:
            A string with the bash repair script if a matching rule is found,
            otherwise None.
        """
        log_content = ""
        if isinstance(log_input, Path):
            if not log_input.is_file():
                return f"# Error: Log file not found at {log_input}"
            log_content = log_input.read_text(encoding="utf-8")
        else:
            log_content = log_input

        for rule in self._rules:
            if rule.matches(log_content, tenant_id):
                return rule.generate_script(log_content, tenant_id)

        return None
