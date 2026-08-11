"""
Main Entry Point for Senior Mint Dashboard.
Designed for Linux Mint 22 XFCE on Intel Celeron N2840, 4GB RAM, HDD.
"""

import sys
import os
import time
import signal
import logging
import fcntl
from pathlib import Path

# Setup logging BEFORE any Qt imports
LOG_DIR = Path(os.path.expanduser("~")) / ".cache" / "senior_dashboard"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "dashboard.log"
PID_FILE = LOG_DIR / "dashboard.pid"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("SeniorMintDashboard")

# Global lock file handle — must stay open for the entire process lifetime
_lock_fh = None


def acquire_single_instance_lock():
    """Prevent multiple dashboard instances via flock. Returns True if lock acquired."""
    global _lock_fh
    try:
        _lock_fh = open(str(PID_FILE), "w")
        fcntl.flock(_lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        _lock_fh.write(str(os.getpid()))
        _lock_fh.flush()
        return True
    except (IOError, OSError):
        logger.warning("Another instance is already running. Exiting.")
        return False


def main():
    # Single instance guard — prevents double-launch from XFCE autostart
    if not acquire_single_instance_lock():
        sys.exit(0)

    logger.info("=" * 60)
    logger.info("Senior Mint Dashboard starting...")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Platform: {sys.platform}")
    logger.info(f"PID: {os.getpid()}")
    logger.info(f"Working dir: {os.getcwd()}")
    logger.info(f"User: {os.environ.get('USER', os.environ.get('USERNAME', 'unknown'))}")
    logger.info(f"DISPLAY: {os.environ.get('DISPLAY', 'not set')}")
    logger.info("=" * 60)

    start_time = time.time()

    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        logger.info("PyQt6 imported successfully.")
    except ImportError as e:
        logger.critical(f"FATAL: Cannot import PyQt6: {e}")
        logger.critical("Install with: sudo apt install python3-pyqt6 python3-pyqt6.qtwebengine")
        sys.exit(1)

    # Enable High DPI scaling attributes
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Senior Mint Dashboard")
    logger.info("QApplication created.")

    # Clean signal handling for SIGINT / SIGTERM
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)

    try:
        from senior_mint_dashboard.launcher.main_window import SeniorDashboardWindow
        logger.info("SeniorDashboardWindow module loaded.")
    except ImportError as e:
        logger.critical(f"FATAL: Cannot import SeniorDashboardWindow: {e}")
        sys.exit(1)

    window = SeniorDashboardWindow()
    window.showFullScreen()
    logger.info("Dashboard window shown in fullscreen mode.")

    elapsed = time.time() - start_time
    logger.info(f"Boot time: {elapsed:.3f} seconds")

    if elapsed > 2.0:
        logger.warning(f"Boot time ({elapsed:.3f}s) exceeds 2.0s SLA target!")

    exit_code = app.exec()
    logger.info(f"Application exited with code {exit_code}.")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

