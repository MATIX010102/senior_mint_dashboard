"""
Main Dashboard Kiosk Window for Senior Mint Dashboard.
Uses a single-layer layout with wallpaper as background-image stylesheet.
Avoids QStackedLayout transparency issues on Qt6/XCB/Linux.
"""

import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog
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

        self._current_wallpaper_pixmap = None
        self._init_ui()
        self._init_wallpaper()
        self._init_version_watcher()
        logger.info("SeniorDashboardWindow initialized successfully.")

    def keyPressEvent(self, event):
        """Allow admin exit with Ctrl+Q (hidden shortcut for maintenance)."""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Q:
            self.close()
        super().keyPressEvent(event)

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

        self.version_banner = QLabel("", self)
        self.version_banner.setVisible(False)
        self.version_banner.setStyleSheet(f"""
            background-color: {PALETTE['BANNER_INFO_BG']};
            color: {PALETTE['BANNER_INFO_TEXT']};
            font-size: 16pt;
            font-weight: bold;
            padding: 8px 16px;
            border-radius: 8px;
        """)

        header_layout.addWidget(self.clock_widget)
        header_layout.addStretch()
        header_layout.addWidget(self.version_banner)
        header_layout.addStretch()
        header_layout.addWidget(self.weather_widget)

        main_layout.addLayout(header_layout)

        # --- Main Tile Grid ---
        self.grid_widget = SeniorGridWidget(self)
        main_layout.addWidget(self.grid_widget, stretch=1)

        # --- Bottom Toolbar ---
        bottom_layout = QHBoxLayout()

        self.btn_picker = QPushButton("🖼️ Zmień tapetę rodzinną", self)
        self.btn_picker.setStyleSheet(self._button_style())
        self.btn_picker.clicked.connect(self._open_wallpaper_picker)

        self.printer_widget = PrinterWidget(parent=self)

        bottom_layout.addWidget(self.btn_picker)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.printer_widget)

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

    def _init_version_watcher(self):
        self.watcher = QFileSystemWatcher(self)
        if VERSION_FILE.exists():
            self.watcher.addPath(str(VERSION_FILE))
            self.watcher.fileChanged.connect(self._on_version_changed)

    def _on_version_changed(self, path):
        self.version_banner.setText("ℹ️ Zaktualizowano program. Kliknij Odśwież, aby wczytać nowości.")
        self.version_banner.setVisible(True)
