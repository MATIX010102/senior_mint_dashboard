"""
Senior Weather Widget (20pt) with Live Open-Meteo API Fetching & Offline JSON Cache Fallback.
Supports configurable coordinates based on settings.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from PyQt6.QtCore import QTimer, Qt, QUrl, QJsonDocument
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest

from senior_mint_dashboard.config import WEATHER_CACHE_FILE, TYPOGRAPHY, SETTINGS_FILE, POLISH_CITIES

logger = logging.getLogger("SeniorMintDashboard")


class WeatherWidget(QWidget):
    """
    Senior weather widget displaying temperature and condition in 20pt high-contrast text.
    Queries the Open-Meteo API asynchronously every 15 minutes and saves to local cache.
    Falls back cleanly to offline JSON cache and fallback placeholders if offline.
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
        self.current_city = "Warszawa"

        self.temp_label = QLabel("--°C", self)
        self.condition_label = QLabel("Wczytywanie...", self)

        self._init_ui()

        # Network Access Manager for async HTTP requests
        self.nam = QNetworkAccessManager(self)
        self.nam.finished.connect(self.on_weather_reply)

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
                # Ensure the cache shows the current configured city name if possible
                if "city" in data:
                    data["city"] = self.current_city
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
        except OSError as e:
            logger.error(f"Failed to write weather JSON cache: {e}")
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

    def load_and_display_cache(self):
        weather_data = self.load_cache()
        self.update_display(weather_data)

    def refresh_location(self) -> None:
        """Reloads settings from file and triggers an immediate weather update."""
        logger.info("Weather widget location refresh requested.")
        self.update_weather()

    def update_weather(self) -> None:
        """Attempts to update weather. If offline/error occurs, loads offline JSON cache."""
        # Load city configuration from user settings
        city_name = "Warszawa"
        lat = 52.2297
        lon = 21.0122

        if SETTINGS_FILE.exists():
            try:
                content = SETTINGS_FILE.read_text(encoding="utf-8")
                settings_data = json.loads(content)
                city = settings_data.get("weather_city", "Warszawa")
                if city in POLISH_CITIES:
                    city_name = city
                    lat = POLISH_CITIES[city]["latitude"]
                    lon = POLISH_CITIES[city]["longitude"]
            except Exception as e:
                logger.error(f"Failed to parse user settings file: {e}")

        self.current_city = city_name

        if os.environ.get("SENIOR_MINT_TEST_MODE") == "1":
            logger.info("Test mode active. Skipping live weather API fetch.")
            self.load_and_display_cache()
            return

        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        logger.info(f"Sending asynchronous weather query for '{city_name}' (lat={lat}, lon={lon}) to Open-Meteo: {url}")
        
        request = QNetworkRequest(QUrl(url))
        request.setTransferTimeout(5000)  # 5 seconds timeout
        self.nam.get(request)

    def on_weather_reply(self, reply):
        """Asynchronous callback handling weather HTTP response."""
        reply.deleteLater()
        
        error = reply.error()
        if error != reply.NetworkError.NoError:
            logger.warning(f"Weather query failed with network error: {error}. Loading offline cache fallback...")
            self.load_and_display_cache()
            return

        try:
            data_bytes = reply.readAll().data()
            json_doc = QJsonDocument.fromJson(data_bytes)
            if json_doc.isNull():
                raise ValueError("Received invalid/malformed JSON data from Weather API")

            json_data = json_doc.toVariant()
            if not isinstance(json_data, dict) or "current_weather" not in json_data:
                raise ValueError("JSON response missing 'current_weather' dictionary details")

            current = json_data["current_weather"]
            temp_val = current.get("temperature")
            code_val = current.get("weathercode")

            if temp_val is None or code_val is None:
                raise ValueError("Weather temperature or code data missing in response")

            # Map WMO weathercode to Polish condition labels
            conditions_map = {
                0: "Słonecznie / Czyste niebo",
                1: "Głównie bezchmurnie",
                2: "Częściowe zachmurzenie",
                3: "Zachmurzenie",
                45: "Mgła",
                48: "Mgła szronowa",
                51: "Lekka mżawka",
                53: "Mżawka",
                55: "Gęsta mżawka",
                61: "Słaby deszcz",
                63: "Deszcz",
                65: "Ulewa",
                71: "Słabe opady śniegu",
                73: "Opady śniegu",
                75: "Śnieżyca",
                77: "Śnieg ziarnisty",
                80: "Lekki deszcz przelotny",
                81: "Deszcz przelotny",
                82: "Ulewny deszcz przelotny",
                85: "Lekki śnieg przelotny",
                86: "Śnieg przelotny",
                95: "Burza",
                96: "Burza z gradem",
                99: "Burza z silnym gradem"
            }

            condition_text = conditions_map.get(code_val, "Umiarkowana pogoda")
            temp_str = f"+{temp_val}°C" if temp_val > 0 else f"{temp_val}°C"

            weather_info = {
                "city": self.current_city,
                "temp": temp_str,
                "condition": condition_text,
                "icon": "weather_cloud.png"
            }

            logger.info(f"Successfully fetched live weather: {temp_str}, {condition_text}. Updating cache.")
            self.update_display(weather_info)
            self.save_cache(weather_info)

        except Exception as e:
            logger.error(f"Error parsing weather API response: {e}. Falling back to cache...", exc_info=True)
            self.load_and_display_cache()
