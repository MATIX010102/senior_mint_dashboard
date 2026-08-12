"""
Embedded QtWebEngine window with Senior Navigation Header and Standalone Browser Launcher.
Lazy-loads QtWebEngine to keep startup RAM footprint <150MB.
"""

import sys
import shutil
import subprocess
import logging
from typing import Optional
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import QUrl, Qt
from senior_mint_dashboard.launcher.webview.senior_nav_bar import SeniorNavBar

logger = logging.getLogger("SeniorMintDashboard")


def launch_system_browser(url: str = "https://www.google.pl") -> bool:
    """
    Spawns external system web browser process in a detached session.
    First tries x-www-browser, then firefox, then chromium.
    """
    browser_bin = (
        shutil.which("x-www-browser") or
        shutil.which("firefox") or
        shutil.which("chromium-browser") or
        shutil.which("google-chrome")
    )

    if not browser_bin:
        browser_bin = "x-www-browser"

    try:
        logger.info(f"Launching external browser for URL: '{url}'")
        subprocess.Popen([browser_bin, url])
        return True
    except Exception as e:
        logger.error(f"Failed to launch system browser '{browser_bin}': {e}", exc_info=True)
        return False


class SeniorBrowserWindow(QMainWindow):
    """
    Kiosk-friendly web browser window featuring SeniorNavBar and lazy-loaded QtWebEngine.
    """

    DEFAULT_TARGETS = {
        "Bank": "https://online.mbank.pl",
        "Gmail": "https://mail.google.com",
        "Onet Poczta": "https://poczta.onet.pl",
        "Ubezpieczenia": "https://pzu.pl"
    }

    def __init__(self, initial_url: str, title: str = "Przeglądarka", parent=None):
        super().__init__(parent)
        self.initial_url = initial_url
        self.current_zoom = 1.0
        self.MAX_ZOOM = 2.5
        self.ZOOM_STEP = 0.25

        self.setWindowTitle(title)
        self.resize(1366, 768)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)

        self._init_ui()

    def _init_ui(self):
        container = QWidget(self)
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Add Senior Navigation Bar
        self.nav_bar = SeniorNavBar(self)
        self.nav_bar.home_clicked.connect(self.reset_to_home)
        self.nav_bar.refresh_clicked.connect(self.refresh_page)
        self.nav_bar.zoom_clicked.connect(self.increase_zoom)
        self.nav_bar.close_clicked.connect(self.close)
        layout.addWidget(self.nav_bar)

        # 2. Lazy load QWebEngineView
        try:
            logger.info("Importing PyQt6.QtWebEngineWidgets...")
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            logger.info("Import successful. Instantiating QWebEngineView...")
            self.webview = QWebEngineView(self)
            self.webview.setUrl(QUrl(self.initial_url))
            layout.addWidget(self.webview)
            logger.info(f"QWebEngineView embedded successfully for: '{self.initial_url}'")
        except Exception as e:
            logger.warning(
                f"QtWebEngine load failed ({e}). Falling back to external system browser. "
                "Ensure python3-pyqt6.qtwebengine is installed.",
                exc_info=True
            )
            launch_system_browser(self.initial_url)
            self.close()

    def reset_to_home(self):
        """Resets page to initial target URL."""
        if hasattr(self, 'webview') and self.webview is not None:
            self.webview.setUrl(QUrl(self.initial_url))

    def refresh_page(self):
        """Reloads current web page."""
        if hasattr(self, 'webview') and self.webview is not None:
            self.webview.reload()

    def increase_zoom(self):
        """Increases webview zoom factor up to MAX_ZOOM (2.5x)."""
        if hasattr(self, 'webview') and self.webview is not None:
            self.current_zoom = min(self.MAX_ZOOM, self.current_zoom + self.ZOOM_STEP)
            self.webview.setZoomFactor(self.current_zoom)
