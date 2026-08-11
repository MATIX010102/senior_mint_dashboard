"""
Senior Action Tile Grid Layout for Senior Mint Dashboard.
"""

from PyQt6.QtWidgets import QWidget, QGridLayout, QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from senior_mint_dashboard.config import (
    PALETTE, TYPOGRAPHY, WEB_LAUNCHERS, GAMES, BROWSER_COMMANDS, DEFAULT_BROWSER_HOMEPAGE
)


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
    """3-Column Grid Widget organizing senior action tiles."""

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
        ]

        for title, subtitle, callback, row, col in tiles_data:
            tile = SeniorTileButton(title, subtitle, parent=self)
            tile.clicked.connect(callback)
            self.grid.addWidget(tile, row, col)

    def _launch_webview(self, key):
        from senior_mint_dashboard.launcher.webview.browser_window import SeniorBrowserWindow
        preset = WEB_LAUNCHERS.get(key)
        if preset:
            win = SeniorBrowserWindow(preset["url"], title=preset["title"], parent=self)
            win.show()

    def _launch_system_browser(self):
        from senior_mint_dashboard.launcher.webview.browser_window import launch_system_browser
        launch_system_browser(DEFAULT_BROWSER_HOMEPAGE)

    def _launch_game_selector(self):
        from senior_mint_dashboard.launcher.games.game_launcher import launch_solitaire
        launch_solitaire(self)

    def _launch_media_transfer(self):
        try:
            from senior_mint_dashboard.media_transfer.ui.transfer_window import MediaTransferWindow
            dialog = MediaTransferWindow(parent=self)
            dialog.show()
        except ImportError:
            pass
