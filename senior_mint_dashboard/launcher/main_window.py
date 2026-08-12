"""
Main Dashboard Kiosk Window for Senior Mint Dashboard.
Uses a single-layer layout with wallpaper as background-image stylesheet.
Avoids QStackedLayout transparency issues on Qt6/XCB/Linux.
"""

import sys
import os
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QFrame
)
from PyQt6.QtCore import Qt, QFileSystemWatcher, QTimer
from PyQt6.QtGui import QFont, QPixmap, QPalette, QBrush, QColor

from senior_mint_dashboard.config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, PALETTE, TYPOGRAPHY,
    WALLPAPER_DIR, VERSION_FILE, APP_NAME, FALLBACK_BACKGROUND_COLOR
)
from senior_mint_dashboard.launcher.grid_layout import SeniorGridWidget
from senior_mint_dashboard.launcher.wallpaper_manager import WallpaperManager
from senior_mint_dashboard.launcher.widgets.clock_widget import ClockWidget
from senior_mint_dashboard.launcher.widgets.weather_widget import WeatherWidget
from senior_mint_dashboard.launcher.widgets.printer_widget import PrinterWidget
from senior_mint_dashboard.launcher.settings_dialog import SettingsDialog

logger = logging.getLogger("SeniorMintDashboard")


class DashboardCentralWidget(QWidget):
    """Central widget that paints a wallpaper background via QPalette."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)
        self._apply_fallback()

    def set_wallpaper_pixmap(self, pixmap: QPixmap):
        """Set a pixmap as the background using QPalette brush."""
        if pixmap.isNull():
            self._apply_fallback()
            return
        palette = self.palette()
        scaled = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        palette.setBrush(QPalette.ColorRole.Window, QBrush(scaled))
        self.setPalette(palette)

    def _apply_fallback(self):
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(FALLBACK_BACKGROUND_COLOR))
        self.setPalette(palette)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Re-apply wallpaper on resize so it scales properly
        parent = self.parent()
        if parent and hasattr(parent, '_refresh_wallpaper_background'):
            parent._refresh_wallpaper_background()


class SeniorDashboardWindow(QMainWindow):
    """Primary Fullscreen Frameless Kiosk Dashboard Window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        self._allow_exit = False
        self._current_wallpaper_pixmap = None
        self._init_ui()
        self._init_wallpaper()
        self._init_version_watcher()
        self._disable_system_panel()
        logger.info("SeniorDashboardWindow initialized successfully.")

    def _disable_system_panel(self):
        """Temporarily stops xfce4-panel to lock down the kiosk session."""
        import os
        import subprocess
        if os.environ.get("SENIOR_MINT_TEST_MODE") == "1":
            return
        try:
            logger.info("Stopping xfce4-panel to secure kiosk mode...")
            subprocess.Popen(["killall", "xfce4-panel"])
        except Exception as e:
            logger.warning(f"Could not kill xfce4-panel: {e}")

    def keyPressEvent(self, event):
        """Allow admin exit with Ctrl+Q (hidden shortcut for maintenance)."""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Q:
            logger.info("Admin exit shortcut Ctrl+Q pressed.")
            self._allow_exit = True
            self.close()
        super().keyPressEvent(event)

    def closeEvent(self, event):
        """Guard to prevent accidental or unauthorized closing of the kiosk launcher."""
        import os
        import subprocess
        if self._allow_exit or os.environ.get("SENIOR_MINT_TEST_MODE") == "1":
            event.accept()
            if os.environ.get("SENIOR_MINT_TEST_MODE") != "1":
                try:
                    logger.info("Restoring xfce4-panel...")
                    subprocess.Popen(["xfce4-panel"])
                except Exception as e:
                    logger.warning(f"Could not restore xfce4-panel: {e}")
            logger.info("Dashboard closed cleanly.")
        else:
            event.ignore()
            logger.warning("Attempted to close kiosk launcher without admin privileges. Close event ignored.")

    def _init_ui(self):
        self.central = DashboardCentralWidget(self)
        self.setCentralWidget(self.central)

        main_layout = QVBoxLayout(self.central)
        main_layout.setContentsMargins(24, 16, 24, 16)
        main_layout.setSpacing(12)

        # --- Header: Clock + Version Banner + Weather ---
        header_layout = QHBoxLayout()

        self.clock_widget = ClockWidget(self)
        self.weather_widget = WeatherWidget(parent=self)

        self.version_banner = QFrame(self)
        self.version_banner.setVisible(False)
        self.version_banner.setStyleSheet(f"""
            QFrame {{
                background-color: {PALETTE['BANNER_INFO_BG']};
                border-radius: 8px;
                border: 2px solid {PALETTE['BUTTON_BLUE']};
            }}
        """)
        
        banner_layout = QHBoxLayout(self.version_banner)
        banner_layout.setContentsMargins(12, 6, 12, 6)
        banner_layout.setSpacing(12)
        
        self.banner_text = QLabel("ℹ️ Zaktualizowano program.", self.version_banner)
        self.banner_text.setStyleSheet(f"color: {PALETTE['BANNER_INFO_TEXT']}; font-size: 14pt; font-weight: bold; border: none; background: transparent;")
        
        self.btn_restart = QPushButton("Uruchom ponownie", self.version_banner)
        self.btn_restart.setStyleSheet(f"""
            QPushButton {{
                background-color: {PALETTE['BACKGROUND_DARK']};
                color: {PALETTE['TEXT_BRIGHT']};
                font-size: 12pt;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 6px;
                border: 1px solid {PALETTE['CARD_BORDER']};
            }}
            QPushButton:hover {{
                background-color: #313244;
            }}
        """)
        self.btn_restart.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_restart.clicked.connect(self._restart_application)
        
        banner_layout.addWidget(self.banner_text)
        banner_layout.addWidget(self.btn_restart)

        header_layout.addWidget(self.clock_widget)
        header_layout.addStretch()
        header_layout.addWidget(self.version_banner)
        header_layout.addStretch()
        header_layout.addWidget(self.weather_widget)

        main_layout.addLayout(header_layout)

        # --- Printer Widget (instantiated early to embed in the grid) ---
        self.printer_widget = PrinterWidget(parent=self)

        # --- Main Tile Grid ---
        self.grid_widget = SeniorGridWidget(self)
        main_layout.addWidget(self.grid_widget, stretch=1)

        # --- Bottom Toolbar ---
        bottom_layout = QHBoxLayout()

        self.btn_picker = QPushButton("🖼️ Zmień tapetę rodzinną", self)
        self.btn_picker.setStyleSheet(self._button_style())
        self.btn_picker.clicked.connect(self._open_wallpaper_picker)

        self.btn_settings = QPushButton("⚙️ Ustawienia i Aktualizacje", self)
        self.btn_settings.setStyleSheet(self._button_style())
        self.btn_settings.clicked.connect(self._open_settings_dialog)

        bottom_layout.addWidget(self.btn_picker)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_settings)

        main_layout.addLayout(bottom_layout)

    def _init_wallpaper(self):
        """Initialize wallpaper manager (hidden, just for image scanning)."""
        self.wallpaper_manager = WallpaperManager(parent=None)
        self.wallpaper_manager.setVisible(False)
        self.wallpaper_manager.wallpaper_changed.connect(self._on_wallpaper_changed)

        # Load initial wallpaper
        wp_path = self.wallpaper_manager.get_current_wallpaper_path()
        if wp_path:
            self._load_wallpaper(wp_path)
        else:
            logger.info("No wallpapers found, using fallback color.")

        # Start slideshow timer
        self.wallpaper_manager.start_slideshow()

    def _on_wallpaper_changed(self, path: str):
        if path:
            self._load_wallpaper(path)

    def _load_wallpaper(self, path: str):
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self._current_wallpaper_pixmap = pixmap
            self.central.set_wallpaper_pixmap(pixmap)
            logger.info(f"Wallpaper set: {path}")
        else:
            self._current_wallpaper_pixmap = None
            self.central._apply_fallback()

    def _refresh_wallpaper_background(self):
        """Re-apply current wallpaper after resize."""
        if self._current_wallpaper_pixmap and not self._current_wallpaper_pixmap.isNull():
            self.central.set_wallpaper_pixmap(self._current_wallpaper_pixmap)

    def _button_style(self):
        return f"""
            QPushButton {{
                background-color: {PALETTE['BUTTON_BLUE']};
                color: #11111B;
                font-size: {TYPOGRAPHY['NAV_BUTTON_PT']}pt;
                font-weight: bold;
                border-radius: 10px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: {PALETTE['BUTTON_HOVER']};
            }}
        """

    def _open_wallpaper_picker(self):
        result = self.wallpaper_manager.open_picker(self)
        if result:
            self._load_wallpaper(result)

    def _open_settings_dialog(self):
        logger.info("Opening Settings Dialog...")
        dialog = SettingsDialog(weather_widget=self.weather_widget, parent=self)
        dialog.exec()

    def _init_version_watcher(self):
        self.watcher = QFileSystemWatcher(self)
        if VERSION_FILE.exists():
            self.watcher.addPath(str(VERSION_FILE))
            self.watcher.fileChanged.connect(self._on_version_changed)

    def _on_version_changed(self, path):
        logger.info("Local version.json file changed. Checking status...")
        import json
        if VERSION_FILE.exists():
            try:
                data = json.loads(VERSION_FILE.read_text(encoding="utf-8"))
                if data.get("status") == "updated":
                    logger.info("Update status is 'updated'. Showing banner.")
                    self.banner_text.setText("ℹ️ Zaktualizowano program. Kliknij obok, aby wczytać nowości:")
                    self.version_banner.setVisible(True)
                    return
            except Exception as e:
                logger.error(f"Failed to read version.json in watcher: {e}")
        self.version_banner.setVisible(False)

    def _restart_application(self):
        """Restarts the launcher application cleanly."""
        logger.info("Application reload requested from update banner. Restarting process...")
        self._allow_exit = True
        self.close()
        # execv replaces the current python process immediately
        os.execv(sys.executable, [sys.executable] + sys.argv)
