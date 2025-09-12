# recovery_agent/self_repair/repair_generator.py

import abc
import re
from pathlib import Path
from typing import List, Optional


class RepairRule(abc.ABC):
    """
    Abstrakte Basisklasse für eine einzelne Self-Repair-Regel.

    Jede konkrete Regel muss diese Klasse implementieren und die Methoden
    `matches` und `generate_script` überschreiben. Dies stellt sicher, dass
    alle Regeln eine einheitliche Schnittstelle haben und der
    `RuleRegistry` bekannt sind.
    """

    # Eine robuste Regex, um Dateipfade (Linux/Windows) zu erfassen,
    # optional in einfachen oder doppelten Anführungszeichen.
    # Gruppe 1 fängt den eigentlichen Pfad ein.
    PATH_REGEX = re.compile(r"""['"]?([a-zA-Z]:[\\/][^'"\s]+|/[^\s'"]+)['"]?""")

    @abc.abstractmethod
    def matches(self, error_message: str, tenant: Optional[str] = None) -> bool:
        """
        Prüft, ob die gegebene Fehlermeldung auf diese Regel zutrifft.

        Args:
            error_message: Der vollständige Text der Fehlermeldung.
            tenant: Die optionale ID des Mandanten, falls die Regel
                    mandantenspezifische Kriterien hat.

        Returns:
            True, wenn die Regel zutrifft, andernfalls False.
        """
        pass

    @abc.abstractmethod
    def generate_script(self, error_message: str, tenant: Optional[str] = None) -> str:
        """
        Generiert ein Bash-Reparaturskript basierend auf der Fehlermeldung.

        Diese Methode wird nur aufgerufen, wenn `matches()` zuvor True
        zurückgegeben hat.

        Args:
            error_message: Der vollständige Text der Fehlermeldung.
            tenant: Die optionale ID des Mandanten, um mandantenspezifische
                    Skripte zu erzeugen (z.B. Pfade, Benutzernamen).

        Returns:
            Ein String, der ein ausführbares Bash-Kommando enthält.
        """
        pass


class PermissionErrorRule(RepairRule):
    """
    Konkrete Regel zur Erkennung und Behebung von "Permission denied"-Fehlern.

    Diese Regel sucht nach dem String "Permission denied" in der Fehlermeldung
    und versucht, einen Pfad zu extrahieren, um ein `chmod`- oder `chown`-Kommando
    vorzuschlagen.
    """

    def matches(self, error_message: str, tenant: Optional[str] = None) -> bool:
        """
        Erkennt Fehlermeldungen, die auf "Permission denied" hinweisen.
        """
        return "Permission denied" in error_message

    def generate_script(self, error_message: str, tenant: Optional[str] = None) -> str:
        """
        Generiert ein `chmod`-Kommando für den im Log gefundenen Pfad.
        Optional wird ein `chown`-Kommando für mandantenspezifische Benutzer
        hinzugefügt.
        """
        match = self.PATH_REGEX.search(error_message)
        if not match:
            return "# Error: Could not extract a valid path from the 'Permission denied' message."

        path = match.group(1)
        script = f"# Repariere Berechtigungsproblem für Pfad: {path}\n"

        if tenant:
            # Beispiel für mandantenspezifische Anpassung:
            # Setze den Eigentümer auf einen Tenant-spezifischen Benutzer.
            script += f"chown -R {tenant}_user:{tenant}_group {path}\n"

        script += f"chmod -R 755 {path}"
        return script


class MissingDirectoryRule(RepairRule):
    """
    Konkrete Regel zur Erkennung und Behebung von "No such file or directory"-Fehlern.

    Diese Regel sucht nach dem String "No such file or directory" und versucht,
    einen Pfad zu extrahieren, um ein `mkdir -p`-Kommando vorzuschlagen.
    """

    def matches(self, error_message: str, tenant: Optional[str] = None) -> bool:
        """
        Erkennt Fehlermeldungen, die auf ein fehlendes Verzeichnis hinweisen.
        """
        return "No such file or directory" in error_message

    def generate_script(self, error_message: str, tenant: Optional[str] = None) -> str:
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
        return f"# Erstelle fehlendes Verzeichnis\nmkdir -p {path}"


class RuleRegistry:
    """
    Verwaltet und orchestriert die Self-Repair-Regeln.

    Diese Klasse hält eine Liste von `RepairRule`-Instanzen. Sie kann eine
    Fehlermeldung analysieren und die erste passende Regel verwenden, um
    einen Reparaturskript-Vorschlag zu generieren.
    """

    def __init__(self):
        """Initialisiert die Registry mit einer leeren Regelliste."""
        self._rules: List[RepairRule] = []

    def register_rule(self, rule: RepairRule):
        """
        Registriert eine neue Regel in der Registry.

        Regeln werden in der Reihenfolge ihrer Registrierung geprüft.
        Die erste passende Regel wird verwendet.

        Args:
            rule: Eine Instanz einer Klasse, die von `RepairRule` erbt.

        Raises:
            TypeError: Wenn das übergebene Objekt keine Instanz von `RepairRule` ist.
        """
        if not isinstance(rule, RepairRule):
            raise TypeError("Die Regel muss eine Instanz von RepairRule sein.")
        self._rules.append(rule)

    def generate_script_suggestion(
        self, error_message: str, tenant: Optional[str] = None
    ) -> str:
        """
        Analysiert eine Fehlermeldung und generiert einen Reparaturskript-Vorschlag.

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
