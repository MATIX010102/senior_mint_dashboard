"""
Main Dashboard Kiosk Window for Senior Mint Dashboard.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedLayout, QFileDialog
)
from PyQt6.QtCore import Qt, QFileSystemWatcher
from PyQt6.QtGui import QFont

from senior_mint_dashboard.config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, PALETTE, TYPOGRAPHY,
    WALLPAPER_DIR, VERSION_FILE, APP_NAME
)
from senior_mint_dashboard.launcher.grid_layout import SeniorGridWidget
from senior_mint_dashboard.launcher.wallpaper_manager import WallpaperManager
from senior_mint_dashboard.launcher.widgets.clock_widget import ClockWidget
from senior_mint_dashboard.launcher.widgets.weather_widget import WeatherWidget
from senior_mint_dashboard.launcher.widgets.printer_widget import PrinterWidget


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

        self._init_ui()
        self._init_version_watcher()

    def keyPressEvent(self, event):
        """Allow admin exit with Ctrl+Q (hidden shortcut for maintenance)."""
        from PyQt6.QtCore import Qt as QtKeys
        if event.modifiers() == QtKeys.KeyboardModifier.ControlModifier and event.key() == QtKeys.Key.Key_Q:
            self.close()
        super().keyPressEvent(event)


    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self.root_layout = QStackedLayout(central_widget)
        self.root_layout.setStackingMode(QStackedLayout.StackingMode.StackAll)

        # Layer 0: Wallpaper background manager
        self.wallpaper_manager = WallpaperManager(self)
        self.root_layout.addWidget(self.wallpaper_manager)

        # Layer 1: Translucent UI panel overlay
        self.ui_overlay = QWidget(self)
        self.ui_overlay.setObjectName("ui_overlay")
        self.ui_overlay.setStyleSheet(f"""
            QWidget#ui_overlay {{
                background-color: {PALETTE['CARD_TRANSLUCENT']};
            }}
        """)

        overlay_layout = QVBoxLayout(self.ui_overlay)
        overlay_layout.setContentsMargins(24, 16, 24, 16)
        overlay_layout.setSpacing(12)

        # Header Section (Clock, Version Banner, Weather)
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

        overlay_layout.addLayout(header_layout)

        # Main Central Action Tile Grid
        self.grid_widget = SeniorGridWidget(self)
        overlay_layout.addWidget(self.grid_widget, stretch=1)

        # Bottom Toolbar Section
        bottom_layout = QHBoxLayout()

        # Wallpaper Picker Button
        self.btn_picker = QPushButton("Zmień tapetę rodzinną", self)
        self.btn_picker.setStyleSheet(self._button_style())
        self.btn_picker.clicked.connect(self._open_wallpaper_picker)

        # Printer Shortcut Widget
        self.printer_widget = PrinterWidget(parent=self)

        bottom_layout.addWidget(self.btn_picker)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.printer_widget)

        overlay_layout.addLayout(bottom_layout)
        self.root_layout.addWidget(self.ui_overlay)

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
        self.wallpaper_manager.open_picker(self)

    def _init_version_watcher(self):
        self.watcher = QFileSystemWatcher(self)
        if VERSION_FILE.exists():
            self.watcher.addPath(str(VERSION_FILE))
            self.watcher.fileChanged.connect(self._on_version_changed)

    def _on_version_changed(self, path):
        self.version_banner.setText("ℹ️ Zaktualizowano program. Kliknij Odśwież, aby wczytać nowości.")
        self.version_banner.setVisible(True)
