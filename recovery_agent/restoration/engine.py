# recovery_agent/restoration/engine.py

import logging
import shutil
from pathlib import Path

from recovery_agent.config_service.models import AppConfig

logger = logging.getLogger(__name__)


class RestorationEngine:
    def __init__(self, backup_path: str, config: AppConfig):
        """
        Initializes the engine with a validated Pydantic config object.

        Args:
            backup_path: The path to the backup source directory.
            config: A validated AppConfig instance.
        """
        self.backup_path = Path(backup_path)
        self.config = config
        # Access settings through the validated, nested Pydantic model
        self.target_dir = Path(config.recovery_settings.target_dir)
        self.encrypt_key = config.recovery_settings.encrypt_key
        self.patterns = config.recovery_settings.backup_formats

    def run_restore(self) -> bool:
        logger.info(
            "Starting restoration from '%s' to '%s'",
            self.backup_path,
            self.target_dir,
        )

        if not self.backup_path.is_dir():
            logger.error(
                "Backup source directory '%s' does not exist", self.backup_path
            )
            return False

        if self.target_dir.exists() and not self.target_dir.is_dir():
            logger.error(
                "Target directory '%s' is not a valid directory", self.target_dir
            )
            return False

        files_to_restore = []
        for pattern in self.patterns.values():
            files_to_restore.extend(self.backup_path.glob(pattern))

        if not files_to_restore:
            logger.warning("No backup files found matching configured patterns.")
            return True

        logger.info("Found %d files to restore.", len(files_to_restore))
        if self.encrypt_key:
            logger.info("Simulating decryption of backup files...")

        self.target_dir.mkdir(parents=True, exist_ok=True)

        try:
            for file_path in files_to_restore:
                shutil.copy2(file_path, self.target_dir / file_path.name)
        except OSError as e:
            logger.critical("A critical I/O error occurred during file copy: %s", e)
            return False

        logger.info("Restoration process completed successfully.")
        return True
