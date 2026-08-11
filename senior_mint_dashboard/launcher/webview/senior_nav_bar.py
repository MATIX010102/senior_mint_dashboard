"""
Senior Navigation Bar component for embedded WebViews.
Provides simple, high-contrast controls: Domowa, Odśwież, Powiększ czcionkę, Zamknij.
"""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt


NAV_BAR_STYLE = """
QFrame#SeniorNavBar {
    background-color: #181825;
    border-bottom: 3px solid #89B4FA;
    padding: 6px 12px;
}

QPushButton.nav-btn {
    background-color: #313244;
    color: #FFFFFF;
    border: 2px solid #89B4FA;
    border-radius: 8px;
    font-size: 16pt;
    font-weight: bold;
    padding: 8px 16px;
    min-height: 50px;
}

QPushButton.nav-btn:hover {
    background-color: #45475A;
    border-color: #F9E2AF;
}

QPushButton.nav-btn:pressed {
    background-color: #585B70;
}

QPushButton.nav-btn-close {
    background-color: #D20F39;
    color: #FFFFFF;
    border: 2px solid #F38BA8;
}

QPushButton.nav-btn-close:hover {
    background-color: #E64553;
}
"""


class SeniorNavBar(QFrame):
    """Senior-friendly navigation header bar."""

    home_clicked = pyqtSignal()
    refresh_clicked = pyqtSignal()
    zoom_clicked = pyqtSignal()
    close_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SeniorNavBar")
        self.setStyleSheet(NAV_BAR_STYLE)
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(15)

        # 1. Domowa
        self.btn_home = QPushButton("🏠 Domowa", self)
        self.btn_home.setProperty("class", "nav-btn")
        self.btn_home.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_home.clicked.connect(self.home_clicked.emit)
        layout.addWidget(self.btn_home)

        # 2. Odśwież
        self.btn_refresh = QPushButton("🔄 Odśwież", self)
        self.btn_refresh.setProperty("class", "nav-btn")
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.refresh_clicked.emit)
        layout.addWidget(self.btn_refresh)

        # 3. Powiększ czcionkę
        self.btn_zoom = QPushButton("🔍 Powiększ czcionkę", self)
        self.btn_zoom.setProperty("class", "nav-btn")
        self.btn_zoom.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_zoom.clicked.connect(self.zoom_clicked.emit)
        layout.addWidget(self.btn_zoom)

        layout.addStretch(1)

        # 4. Zamknij
        self.btn_close = QPushButton("❌ Zamknij", self)
        self.btn_close.setProperty("class", "nav-btn nav-btn-close")
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self.close_clicked.emit)
        layout.addWidget(self.btn_close)
