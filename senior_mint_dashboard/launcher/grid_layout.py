"""
Senior Action Tile Grid Layout for Senior Mint Dashboard.
"""

import logging
from PyQt6.QtWidgets import QWidget, QGridLayout, QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from senior_mint_dashboard.config import (
    PALETTE, TYPOGRAPHY, WEB_LAUNCHERS, GAMES, BROWSER_COMMANDS, DEFAULT_BROWSER_HOMEPAGE
)

logger = logging.getLogger("SeniorMintDashboard")


class SeniorTileButton(QFrame):
    """High-contrast touch-friendly senior action card widget."""

    clicked = pyqtSignal()

    def __init__(self, title: str, subtitle: str, icon_name: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.subtitle = subtitle
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(6)

        self.title_label = QLabel(title, self)
        self.title_label.setFont(QFont("Sans-Serif", TYPOGRAPHY['TILE_HEADER_PT'], QFont.Weight.Bold))
        self.title_label.setStyleSheet(
            f"color: {PALETTE['TEXT_BRIGHT']}; background: transparent; font-size: {TYPOGRAPHY['TILE_HEADER_PT']}pt; font-weight: bold;"
        )

        self.subtitle_label = QLabel(subtitle, self)
        self.subtitle_label.setFont(QFont("Sans-Serif", TYPOGRAPHY['TILE_SUBTITLE_PT']))
        self.subtitle_label.setStyleSheet(
            f"color: {PALETTE['TEXT_MUTED']}; background: transparent; font-size: {TYPOGRAPHY['TILE_SUBTITLE_PT']}pt;"
        )

        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        layout.addStretch()

        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(45, 42, 74, 0.9);
                border: 2px solid {PALETTE['CARD_BORDER']};
                border-radius: 16px;
            }}
            QFrame:hover {{
                border: 3px solid {PALETTE['CARD_HOVER_BORDER']};
                background-color: rgba(60, 56, 95, 0.95);
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class SeniorGridWidget(QWidget):
    """3x3 Grid Widget organizing senior action tiles symmetrically."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid = QGridLayout(self)
        self.grid.setSpacing(20)
        self.grid.setContentsMargins(10, 10, 10, 10)

        self._create_tiles()

    def _create_tiles(self):
        tiles_data = [
            ("Poczta Gmail", "Wiadomości Google", lambda: self._launch_webview("gmail"), 0, 0),
            ("Onet Poczta", "Wiadomości Onet", lambda: self._launch_webview("onet"), 0, 1),
            ("Bankowość", "mBank Online", lambda: self._launch_webview("bank"), 0, 2),
            ("Ubezpieczenia", "Portal PZU", lambda: self._launch_webview("insurance"), 1, 0),
            ("Przeglądarka Internetowa", "Otwórz strony WWW", self._launch_system_browser, 1, 1),
            ("Gry i Pasjans", "Pasjans, Mahjong", self._launch_game_selector, 1, 2),
            ("Zdjęcia i Filmy", "Kopiuj zdjęcia z telefonu", self._launch_media_transfer, 2, 0),
            ("Zdalna Pomoc", "Poproś wnuka o pomoc", self._launch_help_dialog, 2, 1),
        ]

        logger.info("Initializing dashboard action tiles...")
        for title, subtitle, callback, row, col in tiles_data:
            tile = SeniorTileButton(title, subtitle, parent=self)
            tile.clicked.connect(callback)
            self.grid.addWidget(tile, row, col)
            logger.info(f"Tile added: '{title}' at grid position ({row}, {col})")

        # Dynamically retrieve and embed the PrinterWidget in the 9th slot (row 2, col 2)
        win = self.window()
        if win and hasattr(win, "printer_widget") and win.printer_widget is not None:
            self.grid.addWidget(win.printer_widget, 2, 2)
            logger.info("Embedded PrinterWidget at grid position (2, 2)")
        else:
            logger.warning("PrinterWidget could not be located on main window to embed in grid.")

    def _launch_webview(self, key):
        logger.info(f"Launching webview preset for key: '{key}'")
        from senior_mint_dashboard.launcher.webview.browser_window import SeniorBrowserWindow
        preset = WEB_LAUNCHERS.get(key)
        if preset:
            try:
                win = SeniorBrowserWindow(preset["url"], title=preset["title"], parent=self)
                win.show()
                logger.info(f"SeniorBrowserWindow shown for {preset['title']}")
            except Exception as e:
                logger.error(f"Error instantiating or showing SeniorBrowserWindow: {e}", exc_info=True)
        else:
            logger.error(f"No webview preset found for key: '{key}'")

    def _launch_system_browser(self):
        logger.info(f"Launching external system browser at: {DEFAULT_BROWSER_HOMEPAGE}")
        from senior_mint_dashboard.launcher.webview.browser_window import launch_system_browser
        success = launch_system_browser(DEFAULT_BROWSER_HOMEPAGE)
        if success:
            logger.info("System browser process launched successfully.")
        else:
            logger.error("Failed to launch system browser process.")

    def _launch_game_selector(self):
        logger.info("Launching Game Selector Dialog...")
        from senior_mint_dashboard.launcher.games.game_selector_dialog import GameSelectorDialog
        from senior_mint_dashboard.launcher.games.game_launcher import launch_game
        try:
            dialog = GameSelectorDialog(self)
            if dialog.exec():
                if dialog.selected_game:
                    logger.info(f"User selected game: '{dialog.selected_game}'. Launching...")
                    launch_game(dialog.selected_game, self)
                else:
                    logger.info("Game selector dialog closed without selection.")
            else:
                logger.info("Game selector dialog cancelled.")
        except Exception as e:
            logger.error(f"Failed to load or execute game selector dialog: {e}", exc_info=True)

    def _launch_media_transfer(self):
        logger.info("Launching Media Transfer Utility...")
        try:
            from senior_mint_dashboard.media_transfer.ui.transfer_window import MediaTransferWindow
            dialog = MediaTransferWindow(parent=self)
            dialog.show()
            logger.info("MediaTransferWindow displayed.")
        except Exception as e:
            logger.error(f"Failed to import or show MediaTransferWindow: {e}", exc_info=True)

    def _launch_help_dialog(self):
        logger.info("Emergency help action triggered.")
        try:
            from senior_mint_dashboard.media_transfer.ui.transfer_window import MediaTransferWindow
            dialog = MediaTransferWindow(parent=self)
            dialog._show_emergency_help()
            logger.info("Emergency help QMessageBox shown.")
        except Exception as e:
            logger.error(f"Failed to show help dialog: {e}", exc_info=True)
