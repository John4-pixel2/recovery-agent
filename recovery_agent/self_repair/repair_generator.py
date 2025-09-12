# recovery_agent/self_repair/repair_generator.py

import abc
import re
from pathlib import Path
from typing import List


class RepairRule(abc.ABC):
    """
    Abstrakte Basisklasse für eine einzelne Self-Repair-Regel.

    Jede konkrete Regel muss diese Klasse implementieren und die Methoden
    `matches` und `generate_script` überschreiben. Dies stellt sicher, dass
    alle Regeln eine einheitliche Schnittstelle haben.
    """

    # Eine robuste Regex, um Dateipfade (Linux/Windows) zu erfassen,
    # optional in einfachen oder doppelten Anführungszeichen.
    PATH_REGEX = re.compile(r"""['"]?([a-zA-Z]:[\\/][^'"\s]+|/[^\s'"]+)['"]?""")

    @abc.abstractmethod
    def matches(self, error_message: str, tenant: str | None = None) -> bool:
        """
        Prüft, ob die gegebene Fehlermeldung auf diese Regel zutrifft.

        Args:
            error_message: Der vollständige Text der Fehlermeldung.
            tenant: Die optionale ID des Mandanten für mandantenspezifische Logik.

        Returns:
            True, wenn die Regel zutrifft, andernfalls False.
        """
        pass

    @abc.abstractmethod
    def generate_script(self, error_message: str, tenant: str | None = None) -> str:
        """
        Generiert ein Bash-Reparaturskript basierend auf der Fehlermeldung.

        Args:
            error_message: Der vollständige Text der Fehlermeldung.
            tenant: Die optionale ID des Mandanten für mandantenspezifische Skripte.

        Returns:
            Ein String, der ein ausführbares Bash-Kommando enthält.
        """
        pass


class PermissionErrorRule(RepairRule):
    """
    Regel zur Erkennung und Behebung von "Permission denied"-Fehlern.
    """

    def matches(self, error_message: str, tenant: str | None = None) -> bool:
        """
        Erkennt Fehlermeldungen, die auf "Permission denied" oder "PermissionError" hinweisen.
        """
        return "Permission denied" in error_message or "PermissionError" in error_message

    def generate_script(self, error_message: str, tenant: str | None = None) -> str:
        """
        Generiert ein `chmod`-Kommando für den im Log gefundenen Pfad.
        Wenn ein Mandant (`tenant`) angegeben ist, wird zusätzlich ein `chown`
        für einen mandantenspezifischen Benutzer hinzugefügt.
        """
        match = self.PATH_REGEX.search(error_message)
        if not match:
            return "# Error: Could not extract a valid path from the 'Permission denied' message."

        path = match.group(1)
        script_lines = [f"# Repairing permission issue for path: {path}"]

        if tenant:
            # Beispiel für mandantenspezifische Anpassung
            script_lines.append(f"chown -R {tenant}_user:{tenant}_group {path}")

        script_lines.append(f"chmod -R 755 {path}")
        return "\n".join(script_lines)


class MissingDirectoryRule(RepairRule):
    """
    Regel zur Erkennung und Behebung von "No such file or directory"-Fehlern.
    """

    def matches(self, error_message: str, tenant: str | None = None) -> bool:
        """
        Erkennt Fehlermeldungen, die auf ein fehlendes Verzeichnis hinweisen.
        """
        return "No such file or directory" in error_message

    def generate_script(self, error_message: str, tenant: str | None = None) -> str:
        """
        Generiert ein `mkdir -p`-Kommando, um die fehlende Verzeichnisstruktur
        zu erstellen.
        """
        match = self.PATH_REGEX.search(error_message)
        if not match:
            return "# Error: Could not extract a valid path from the 'No such file or directory' message."

        # Extrahiere den Verzeichnis-Teil des Pfades, da die Fehlermeldung
        # oft den Dateinamen enthält, aber wir das Verzeichnis erstellen wollen.
        path = str(Path(match.group(1)).parent)
        return f"# Creating missing directory structure\nmkdir -p {path}"


class RuleRegistry:
    """
    Verwaltet und orchestriert die Self-Repair-Regeln.

    Diese Klasse hält eine Liste von `RepairRule`-Instanzen. Sie kann eine
    Fehlermeldung analysieren und die erste passende Regel verwenden, um
    ein Reparaturskript zu generieren.
    """

    def __init__(self):
        """Initialisiert die Registry mit einer leeren Regelliste."""
        self._rules: List[RepairRule] = []

    def register_rule(self, rule: RepairRule):
        """
        Registriert eine neue Regel in der Registry.

        Regeln werden in der Reihenfolge ihrer Registrierung geprüft.

        Args:
            rule: Eine Instanz einer Klasse, die von `RepairRule` erbt.

        Raises:
            TypeError: Wenn das übergebene Objekt keine Instanz von `RepairRule` ist.
        """
        if not isinstance(rule, RepairRule):
            raise TypeError("Rule must be an instance of RepairRule.")
        self._rules.append(rule)

    def find_repair(self, error_message: str, tenant: str | None = None) -> str:
        """
        Analysiert eine Fehlermeldung und generiert ein Reparaturskript.

        Durchläuft die registrierten Regeln und gibt das Skript der ersten
        passenden Regel zurück.

        Args:
            error_message: Der vollständige Text der Fehlermeldung.
            tenant: Die optionale ID des Mandanten für mandantenspezifische Regeln.

        Returns:
            Ein String mit dem Bash-Reparaturskript, wenn eine passende Regel
            gefunden wurde. Andernfalls wird eine Standardmeldung zurückgegeben.
        """
        for rule in self._rules:
            if rule.matches(error_message, tenant):
                return rule.generate_script(error_message, tenant)

        return "No repair suggestion found for the given error."