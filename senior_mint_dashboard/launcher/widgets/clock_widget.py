"""
Senior Large Typography Clock Widget (54pt Time / 22pt Date) for Senior Mint Dashboard.
"""

import datetime
from typing import Optional
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

from senior_mint_dashboard.config import TYPOGRAPHY


class ClockWidget(QWidget):
    """
    High-contrast senior-friendly widget displaying time in 54pt and date in 22pt with Polish locale.
    """
    DAY_NAMES = [
        "Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"
    ]
    MONTH_NAMES = [
        "stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
        "lipca", "sierpnia", "września", "października", "listopada", "grudnia"
    ]

    TIME_FONT_PT = TYPOGRAPHY.get("TIME_SIZE_PT", 54)
    DATE_FONT_PT = TYPOGRAPHY.get("DATE_SIZE_PT", 22)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.time_label = QLabel(self)
        self.date_label = QLabel(self)

        self._init_ui()

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start()

        self.update_clock()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        time_font = QFont("Sans-Serif", self.TIME_FONT_PT, QFont.Weight.Bold)
        self.time_label.setFont(time_font)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("color: #FFFFFF; font-size: 54pt; font-weight: bold;")

        date_font = QFont("Sans-Serif", self.DATE_FONT_PT, QFont.Weight.Bold)
        self.date_label.setFont(date_font)
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_label.setStyleSheet("color: #BAC2DE; font-size: 22pt; font-weight: bold;")

        layout.addWidget(self.time_label)
        layout.addWidget(self.date_label)

    def get_time_string(self, dt: Optional[datetime.datetime] = None) -> str:
        """Returns HH:MM formatted time string."""
        now = dt or datetime.datetime.now()
        return now.strftime("%H:%M")

    def get_date_string(self, dt: Optional[datetime.datetime] = None) -> str:
        """Returns Polish locale date string e.g. 'Wtorek, 11 sierpnia 2026'."""
        now = dt or datetime.datetime.now()
        day_name = self.DAY_NAMES[now.weekday()]
        month_name = self.MONTH_NAMES[now.month - 1]
        return f"{day_name}, {now.day} {month_name} {now.year}"

    def update_clock(self) -> None:
        """Updates label texts with current time and date."""
        now = datetime.datetime.now()
        self.time_label.setText(self.get_time_string(now))
        self.date_label.setText(self.get_date_string(now))
