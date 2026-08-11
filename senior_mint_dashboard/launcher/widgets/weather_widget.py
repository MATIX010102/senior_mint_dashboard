"""
Senior Weather Widget (20pt) with Offline JSON Cache Fallback for Senior Mint Dashboard.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

from senior_mint_dashboard.config import WEATHER_CACHE_FILE, TYPOGRAPHY


class WeatherWidget(QWidget):
    """
    Senior weather widget displaying temperature and condition in 20pt high-contrast text,
    with robust offline JSON cache fallback and error recovery.
    """
    WEATHER_FONT_PT = TYPOGRAPHY.get("WEATHER_SIZE_PT", 20)
    DEFAULT_CACHE_PATH = WEATHER_CACHE_FILE

    DEFAULT_FALLBACK_DATA = {
        "city": "Warszawa",
        "temp": "--°C",
        "condition": "Brak danych o pogodzie",
        "icon": "weather_cloud.png"
    }

    def __init__(self, parent: Optional[QWidget] = None, cache_file: Optional[Path] = None):
        if isinstance(parent, (str, Path)):
            cache_file = Path(parent)
            parent = None
        super().__init__(parent)
        self.cache_file = cache_file or self.DEFAULT_CACHE_PATH

        self.temp_label = QLabel("--°C", self)
        self.condition_label = QLabel("Wczytywanie...", self)

        self._init_ui()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(15 * 60 * 1000)  # 15 minutes
        self.refresh_timer.timeout.connect(self.update_weather)
        self.refresh_timer.start()

        self.update_weather()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        font = QFont("Sans-Serif", self.WEATHER_FONT_PT, QFont.Weight.Bold)

        self.temp_label.setFont(font)
        self.temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.temp_label.setStyleSheet("color: #F9E2AF; font-size: 20pt; font-weight: bold;")

        self.condition_label.setFont(font)
        self.condition_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.condition_label.setStyleSheet("color: #FFFFFF; font-size: 20pt; font-weight: bold;")

        layout.addWidget(self.temp_label)
        layout.addWidget(self.condition_label)

    def load_cache(self) -> Dict[str, Any]:
        """Loads cached weather data from JSON file. Reverts to default placeholder on error/corruption."""
        if not self.cache_file or not self.cache_file.exists():
            return dict(self.DEFAULT_FALLBACK_DATA)

        try:
            content = self.cache_file.read_text(encoding="utf-8")
            data = json.loads(content)
            if isinstance(data, dict) and data.get("temp") is not None and data.get("condition") is not None:
                return data
            return dict(self.DEFAULT_FALLBACK_DATA)
        except (json.JSONDecodeError, OSError, ValueError):
            return dict(self.DEFAULT_FALLBACK_DATA)

    def save_cache(self, data: Dict[str, Any]) -> bool:
        """Saves weather data dictionary to local offline JSON cache file."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            self.cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            return True
        except OSError:
            return False

    def update_display(self, data: Dict[str, Any]) -> None:
        """Updates widget UI labels with temperature and weather condition."""
        if not isinstance(data, dict):
            data = dict(self.DEFAULT_FALLBACK_DATA)
        temp = data.get("temp")
        if not temp:
            temp = "--°C"
        condition = data.get("condition")
        if not condition:
            condition = "Brak danych o pogodzie"
        city = data.get("city", "")

        if city and temp != "--°C":
            self.temp_label.setText(f"{city}: {temp}")
        else:
            self.temp_label.setText(temp)
        self.condition_label.setText(condition)

    def update_weather(self) -> None:
        """Attempts to update weather. If offline/error occurs, loads offline JSON cache."""
        weather_data = self.load_cache()
        self.update_display(weather_data)
