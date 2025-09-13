# recovery_agent/self_repair/repair_generator.py

import abc
import re
from pathlib import Path
from typing import List, Optional


class RepairRule(abc.ABC):
    """
    Abstract base class for a single self-repair rule.
    """

    PATH_REGEX = re.compile(r"""['"]?([a-zA-Z]:[\\/][^'"\s]+|/[^\s'"]+)['"]?""")

    @abc.abstractmethod
    def matches(self, error_message: str, tenant: Optional[str] = None) -> bool:
        pass

    @abc.abstractmethod
    def generate_script(self, error_message: str, tenant: Optional[str] = None) -> str:
        pass


class PermissionErrorRule(RepairRule):
    """Rule for "Permission denied" errors."""

    def matches(self, error_message: str, tenant: Optional[str] = None) -> bool:
        return "Permission denied" in error_message

    def generate_script(self, error_message: str, tenant: Optional[str] = None) -> str:
        match = self.PATH_REGEX.search(error_message)
        if not match:
            return "# Error: Could not extract a valid path from the permission error log."
        path = match.group(1)
        script = f"# Fix permissions for: {path}\n"
        if tenant:
            script += f"chown -R {tenant}_user:{tenant}_group {path}\n"
        script += f"chmod -R 755 {path}"
        return script


class MissingDirectoryRule(RepairRule):
    """Rule for "No such file or directory" errors."""

    def matches(self, error_message: str, tenant: Optional[str] = None) -> bool:
        return "No such file or directory" in error_message

    def generate_script(self, error_message: str, tenant: Optional[str] = None) -> str:
        match = self.PATH_REGEX.search(error_message)
        if not match:
            return "# Error: Could not extract a valid path from the missing directory log."
        path = str(Path(match.group(1)).parent)
        return f"# Create missing directory structure\nmkdir -p {path}"


class RuleRegistry:
    """Orchestrates the generation of repair scripts."""

    def __init__(self):
        self._rules: List[RepairRule] = []

    def register_rule(self, rule: RepairRule):
        if not isinstance(rule, RepairRule):
            raise TypeError("Rule must be an instance of RepairRule.")
        self._rules.append(rule)

    def generate_script_suggestion(self, error_message: str, tenant: Optional[str] = None) -> str:
        """Analyzes an error log and generates a repair script suggestion."""
        for rule in self._rules:
            if rule.matches(error_message, tenant):
                return rule.generate_script(error_message, tenant)
        return "No repair suggestion found for the given error."
