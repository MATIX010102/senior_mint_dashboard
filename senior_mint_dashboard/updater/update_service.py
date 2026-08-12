"""
Entry point for Systemd User Service timer (/home/dziadek/senior-mint-updater.service).
"""

import sys
import logging
from pathlib import Path
from senior_mint_dashboard.updater.git_updater import check_and_apply_updates

# Setup logging for background systemd updater run
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("SeniorMintDashboard.Updater")


def main():
    logger.info("Starting background update check...")
    repo_dir = Path(__file__).resolve().parent.parent.parent
    result = check_and_apply_updates(repo_dir)
    if result['success']:
        if result['updated']:
            logger.info("Senior Mint Dashboard updated successfully!")
        else:
            logger.info("Dashboard is already up to date.")
        sys.exit(0)
    else:
        logger.error(f"Update check failed: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
