"""
Global Configuration & Senior Design Tokens for Senior Mint Dashboard.
"""

from pathlib import Path
import os

# Application Metadata
APP_NAME = "Senior Mint Dashboard"
APP_VERSION = "1.0.0"

# Performance SLAs
RAM_MAX_MB = 150
COLD_BOOT_MAX_SEC = 2.0

# Display & Layout SLA
WINDOW_WIDTH = 1366
WINDOW_HEIGHT = 768
GRID_COLUMNS = 3
GRID_ROWS = 2
GRID_SPACING = 20
GRID_MARGINS = (24, 24, 24, 24)

# File Paths & Directories
HOME_DIR = Path(os.path.expanduser("~"))
WALLPAPER_DIR = HOME_DIR / "Obrazki" / "Tapety"
CONFIG_DIR = HOME_DIR / ".config" / "senior_dashboard"
CACHE_DIR = HOME_DIR / ".cache" / "senior_dashboard"
VERSION_FILE = CONFIG_DIR / "version.json"
WEATHER_CACHE_FILE = CACHE_DIR / "weather_cache.json"

# Slideshow Settings
SLIDESHOW_INTERVAL_MS = 300000  # 5 minutes (300 seconds)
FALLBACK_BACKGROUND_COLOR = "#2D2A4A"

# High-Contrast Senior Dark Translucent Palette Tokens
PALETTE = {
    "BACKGROUND_DARK": "#1E1E2E",
    "CARD_TRANSLUCENT": "rgba(30, 30, 46, 0.85)",
    "CARD_BORDER": "rgba(249, 226, 175, 0.3)",
    "TEXT_BRIGHT": "#FFFFFF",
    "TEXT_MUTED": "#CDD6F4",
    "ACCENT_YELLOW": "#F9E2AF",
    "BUTTON_BLUE": "#89B4FA",
    "BUTTON_HOVER": "#B4BEFE",
    "BUTTON_ACTIVE": "#74C7EC",
    "CARD_HOVER_BORDER": "#F9E2AF",
    "BANNER_INFO_BG": "rgba(137, 180, 250, 0.9)",
    "BANNER_INFO_TEXT": "#11111B",
}

# Typography Scales (in pt)
TYPOGRAPHY = {
    "TIME_SIZE_PT": 54,
    "DATE_SIZE_PT": 22,
    "WEATHER_SIZE_PT": 20,
    "TILE_HEADER_PT": 24,
    "TILE_SUBTITLE_PT": 14,
    "NAV_BUTTON_PT": 18,
}

# Hybrid Web Launcher Presets
WEB_LAUNCHERS = {
    "bank": {
        "title": "Bankowość",
        "subtitle": "mBank Online",
        "url": "https://online.mbank.pl",
        "icon": "bank_icon.png",
    },
    "gmail": {
        "title": "Poczta Gmail",
        "subtitle": "Wiadomości Google",
        "url": "https://mail.google.com",
        "icon": "gmail_icon.png",
    },
    "onet": {
        "title": "Onet Poczta",
        "subtitle": "Wiadomości Onet",
        "url": "https://poczta.onet.pl",
        "icon": "onet_icon.png",
    },
    "insurance": {
        "title": "Ubezpieczenia",
        "subtitle": "Portal PZU",
        "url": "https://pzu.pl",
        "icon": "pzu_icon.png",
    },
}

# Standalone Applications & Games
GAMES = {
    "solitaire": {
        "title": "Pasjans (Solitaire)",
        "command": "aisleriot",
        "web_fallback": "https://worldofsolitaire.com",
    },
    "mahjong": {
        "title": "Mahjong",
        "command": "gnome-mahjongg",
        "web_fallback": "https://www.mahjongjp.com",
    },
}

BROWSER_COMMANDS = ["x-www-browser", "firefox", "chromium-browser", "google-chrome"]
DEFAULT_BROWSER_HOMEPAGE = "https://www.google.pl"
