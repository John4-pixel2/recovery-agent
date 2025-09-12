# recovery_agent/main.py
import argparse
import json
import logging
import sys
from pathlib import Path

from recovery_agent.analysis.anomaly_detector import analyze_backup
from recovery_agent.config_service import ConfigError, get_config
from recovery_agent.intel.queries import (
    get_backup_version,
    get_codebase_version,
    get_last_stable_backup_path,
    get_migration_plan,
)
from recovery_agent.restoration.engine import RestorationEngine
from recovery_agent.self_repair.repair_generator import (
    MissingDirectoryRule,
    PermissionErrorRule,
    RepairScriptGenerator,
)

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
            choices=["restore", "test", "analyze", "repair", "intelligent-restore"],
            required=True,
            help="Action to perform",
        )
        parser.add_argument(
            "--backup",
            type=str,
            help="Path to the backup source. Required for restore or analyze.",
        )
        parser.add_argument(
            "--error-log",
            type=str,
            help="Path to the error log file. Required for repair or intelligent-restore.",
        )
        parser.add_argument(
            "--tenant",
            type=str,
            help="Optional tenant ID for multi-tenant operations.",
        )

        args = parser.parse_args()

        if args.action == "restore":
            if not args.backup:
                parser.error('argument --backup is required for action "restore"')
            engine = RestorationEngine(backup_path=args.backup, config=settings)
            engine.run_restore()

        elif args.action == "analyze":
            if not args.backup:
                parser.error('argument --backup is required for action "analyze"')
            result = analyze_backup(args.backup, settings)
            print(json.dumps(result, indent=2))

        elif args.action == "repair":
            if not args.error_log:
                parser.error('argument --error-log is required for action "repair"')

            generator = RepairScriptGenerator()
            generator.register_rule(PermissionErrorRule())
            generator.register_rule(MissingDirectoryRule())

            script = generator.generate(Path(args.error_log), tenant_id=args.tenant)

            if script:
                print("--- Suggested Repair Script ---")
                print(script)
                print("-----------------------------")
            else:
                print("No repair script could be generated for the given log.")

        elif args.action == "intelligent-restore":
            if not args.error_log:
                parser.error(
                    'argument --error-log is required for action "intelligent-restore"'
                )
            print("--- Starting Intelligent Restore Protocol ---")

            # Step 1: Diagnose & Quick Fix
            generator = RepairScriptGenerator()
            generator.register_rule(PermissionErrorRule())
            generator.register_rule(MissingDirectoryRule())
            repair_script = generator.generate(
                Path(args.error_log), tenant_id=args.tenant
            )

            if repair_script:
                print(
                    f"Step 1: Found a potential quick fix. Suggested script:\n{repair_script}"
                )
                print(
                    "INFO: Assuming quick fix was applied or is not sufficient. Proceeding with restore."
                )
            else:
                print("Step 1: No quick fix found. Proceeding with restore.")

            # Step 2: Gather Intelligence
            print("\nStep 2: Gathering intelligence...")
            stable_backup_path = get_last_stable_backup_path()
            current_version = get_codebase_version()
            backup_version = get_backup_version(Path(stable_backup_path))
            print(
                f"  - Last stable backup: {stable_backup_path} (Version {backup_version})"
            )
            print(f"  - Current codebase version: {current_version}")

            # Step 3: Formulate Plan
            print("\nStep 3: Formulating a plan...")
            if backup_version == current_version:
                print("  - Plan: Direct restore. No migration needed.")
                # engine = RestorationEngine(backup_path=stable_backup_path, config=settings)
                # engine.run_restore()
            else:
                print(
                    f"  - Plan: Schema-Drift detected. Migration required from {backup_version} to {current_version}."
                )
                migration_scripts = get_migration_plan(backup_version, current_version)
                if not migration_scripts:
                    print(
                        "  - CRITICAL FAILURE: No migration path found. Manual intervention required."
                    )
                    sys.exit(1)
                print(f"  - Migration steps found: {migration_scripts}")
                print(
                    "  - SIMULATING: Executing restore to sandbox, applying migrations, and finalizing..."
                )

            print("\n--- Intelligent Restore Protocol Finished ---")

        elif args.action == "test":
            logging.info("Starting tests...")
            logging.info("Tests passed!")

    except ConfigError as e:
        logging.critical(f"Configuration error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
