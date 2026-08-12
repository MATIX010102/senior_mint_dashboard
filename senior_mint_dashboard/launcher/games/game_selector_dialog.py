"""
Senior-friendly Game Selector Dialog for Solitaire and Mahjong.
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from senior_mint_dashboard.config import PALETTE, TYPOGRAPHY


class GameSelectorDialog(QDialog):
    """
    Popup dialog providing giant, easy-to-press buttons to choose between
    Solitaire (Pasjans) and Mahjong.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wybierz Grę")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setMinimumSize(500, 320)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {PALETTE['BACKGROUND_DARK']};
                border: 3px solid {PALETTE['CARD_BORDER']};
                border-radius: 16px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        title = QLabel("🎮 Wybierz grę, w którą chcesz zagrać:", self)
        title.setFont(QFont("Sans-Serif", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {PALETTE['TEXT_BRIGHT']}; background: transparent; font-size: 18pt; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        btn_style = f"""
            QPushButton {{
                background-color: rgba(45, 42, 74, 0.9);
                color: {PALETTE['TEXT_BRIGHT']};
                font-size: 18pt;
                font-weight: bold;
                border: 2px solid {PALETTE['CARD_BORDER']};
                border-radius: 12px;
                padding: 20px;
                min-height: 100px;
            }}
            QPushButton:hover {{
                border: 3px solid {PALETTE['CARD_HOVER_BORDER']};
                background-color: rgba(60, 56, 95, 0.95);
            }}
        """

        self.btn_solitaire = QPushButton("🂠 Pasjans\n(Solitaire)", self)
        self.btn_solitaire.setStyleSheet(btn_style)
        self.btn_solitaire.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_solitaire.clicked.connect(self.accept_solitaire)

        self.btn_mahjong = QPushButton("🀄 Mahjong", self)
        self.btn_mahjong.setStyleSheet(btn_style)
        self.btn_mahjong.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mahjong.clicked.connect(self.accept_mahjong)

        btn_layout.addWidget(self.btn_solitaire)
        btn_layout.addWidget(self.btn_mahjong)
        layout.addLayout(btn_layout)

        # Close button at the bottom
        self.btn_close = QPushButton("❌ Zamknij", self)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-size: 16pt;
                font-weight: bold;
                border-radius: 10px;
                padding: 12px;
                border: 2px solid #b02a37;
            }
            QPushButton:hover {
                background-color: #bb2d3b;
            }
        """)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self.reject)
        layout.addWidget(self.btn_close)

        self.selected_game = None

    def accept_solitaire(self):
        self.selected_game = "solitaire"
        self.accept()

    def accept_mahjong(self):
        self.selected_game = "mahjong"
        self.accept()
