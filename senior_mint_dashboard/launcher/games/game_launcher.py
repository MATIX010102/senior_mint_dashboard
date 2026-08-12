"""
Offline Classic Games Launcher module for Solitaire (aisleriot) and Mahjong (gnome-mahjongg).
Includes automatic web fallback when native binaries are missing.
"""

import shutil
import subprocess
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("SeniorMintDashboard")

GAMES_CONFIG: Dict[str, Dict[str, str]] = {
    "solitaire": {
        "title": "Pasjans (Solitaire)",
        "binary": "aisleriot",
        "fallback_url": "https://worldofsolitaire.com",
        "icon": "solitaire_icon.png"
    },
    "mahjong": {
        "title": "Mahjong",
        "binary": "gnome-mahjongg",
        "fallback_url": "https://www.mahjongjp.com",
        "icon": "mahjong_icon.png"
    }
}


def launch_game(game_key: str, parent_widget: Optional[Any] = None) -> bool:
    """
     Launches game by key ('solitaire' or 'mahjong').
    Tries native linux binary first. If missing, launches web fallback.
    """
    config = GAMES_CONFIG.get(game_key.lower())
    if not config:
        logger.error(f"Unknown game key requested: '{game_key}'")
        return False

    binary = config["binary"]
    fallback_url = config["fallback_url"]

    logger.info(f"Attempting to launch native game: '{binary}' ({config['title']})")
    # Check if native binary is available on PATH
    binary_path = shutil.which(binary)
    if binary_path:
        try:
            logger.info(f"Found native game binary at: '{binary_path}'. Spawning process...")
            subprocess.Popen([binary_path])
            logger.info(f"Native game process spawned for '{binary_path}' successfully.")
            return True
        except Exception as e:
            logger.warning(f"Error executing native binary '{binary_path}': {e}. Trying web fallback...", exc_info=True)

    # Native binary missing or failed -> Web Fallback
    logger.info(f"Native game binary '{binary}' is not available or failed to start. Launching web fallback URL: {fallback_url}")
    from senior_mint_dashboard.launcher.webview.browser_window import is_webengine_available, launch_system_browser
    if is_webengine_available():
        try:
            from senior_mint_dashboard.launcher.webview.browser_window import SeniorBrowserWindow
            win = SeniorBrowserWindow(fallback_url, title=config["title"], parent=parent_widget)
            win.show()
            logger.info(f"Embedded web browser launched with fallback URL for '{config['title']}'")
            return True
        except Exception as e:
            logger.error(f"Failed to launch embedded web fallback browser: {e}. Falling back to default system browser...", exc_info=True)
            return launch_system_browser(fallback_url)
    else:
        logger.info("QtWebEngine is not available. Launching system browser directly.")
        return launch_system_browser(fallback_url)


def launch_solitaire(parent_widget: Optional[Any] = None) -> bool:
    """Convenience launcher for Solitaire."""
    return launch_game("solitaire", parent_widget)


def launch_mahjong(parent_widget: Optional[Any] = None) -> bool:
    """Convenience launcher for Mahjong."""
    return launch_game("mahjong", parent_widget)
