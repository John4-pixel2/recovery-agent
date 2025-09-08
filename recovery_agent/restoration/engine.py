# recovery_agent/restoration/engine.py
# export FLASK_APP=recovery_agent.ui.app:create_app
# flask run

import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class RestorationEngine:
    def __init__(self, backup_path, config):
        self.backup_path = Path(backup_path)
        self.config = config
        self.target_dir = Path(config.get("target_dir", "./restored"))
        self.encrypt_key = config.get("encrypt_key")  # für Tests benötigt

    def run_restore(self):
        logger.info(
            "Starting restoration from '%s' to '%s'",
            self.backup_path,
            self.target_dir,
        )

        # Quelle prüfen
        if not self.backup_path.exists():
            logger.error(
                "Backup source directory '%s' does not exist", self.backup_path
            )
            return False

        # Falls target existiert, aber keine Directory ist
        if self.target_dir.exists() and not self.target_dir.is_dir():
            logger.error(
                "Target directory '%s' does not exist or is not a directory",
                self.target_dir,
            )
            return False

        # Dateien anhand von Patterns suchen
        patterns = self.config.get("backup_formats", {"logs": "*.log", "db": "*.sql"})
        files = []
        for _, pattern in patterns.items():
            files.extend(self.backup_path.glob(pattern))

        if not files:
            logger.warning("No backup files found matching configured patterns.")
            return True

        logger.info("Found %s files to restore.", len(files))
        logger.info("Simulating decryption of backup files...")

        self.target_dir.mkdir(parents=True, exist_ok=True)

        for f in files:
            try:
                shutil.copy2(f, self.target_dir / f.name)
            except OSError as e:
                logger.critical("A critical I/O error occurred during file copy: %s", e)
                return False

        logger.info("Restoration process completed successfully.")
        return True
