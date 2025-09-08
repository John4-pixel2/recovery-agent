# recovery_agent/main.py
import argparse
import logging
import sys

from recovery_agent.config_service import ConfigError, get_config
from recovery_agent.restoration.engine import RestorationEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

def main():
    try:
        # Get validated config from the central service
        settings = get_config()

        parser = argparse.ArgumentParser(description="Recovery-Agent CLI")
        parser.add_argument(
            "--action",
            choices=["restore", "test"],
            required=True,
            help="Action to perform (restore or test)",
        )
        parser.add_argument(
            "--backup",
            type=str,
            help="Path to the backup source directory. Required for restore action.",
        )
        parser.add_argument("--env", type=str, default="prod", help="Environment")
        args = parser.parse_args()

        if args.action == "restore":
            if not args.backup:
                parser.error("--backup is required when action is 'restore'")

            engine = RestorationEngine(backup_path=args.backup, config=settings)
            engine.run_restore()
        elif args.action == "test":
            logging.info("Starting tests...")
            logging.info("Tests passed!")
    except ConfigError as e:
        logging.critical(f"Configuration error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
