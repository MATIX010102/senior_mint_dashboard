"""
Main Entry Point for Senior Mint Dashboard.
"""

import sys
import time
import signal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


def main():
    start_time = time.time()

    # Enable High DPI scaling attributes
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Senior Mint Dashboard")

    # Clean signal handling for SIGINT / SIGTERM
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)

    # Lazy load main window to record exact instantiation overhead
    from senior_mint_dashboard.launcher.main_window import SeniorDashboardWindow

    window = SeniorDashboardWindow()
    window.show()

    elapsed = time.time() - start_time
    print(f"[DEBUG] Senior Mint Dashboard boot time: {elapsed:.3f} seconds")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
