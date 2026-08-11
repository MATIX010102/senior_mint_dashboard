"""
Offline Classic Games Launcher module for Solitaire (aisleriot) and Mahjong (gnome-mahjongg).
Includes automatic web fallback when native binaries are missing.
"""

import shutil
import subprocess
from typing import Dict, Any, Optional


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
        print(f"[ERROR] Unknown game key: '{game_key}'")
        return False

    binary = config["binary"]
    fallback_url = config["fallback_url"]

    # Check if native binary is available on PATH
    binary_path = shutil.which(binary)
    if binary_path:
        try:
            subprocess.Popen([binary_path])
            return True
        except Exception as e:
            print(f"[WARN] Error executing '{binary_path}': {e}. Trying web fallback.")

    # Native binary missing or failed -> Web Fallback
    print(f"[INFO] Native game binary '{binary}' missing. Launching fallback URL: {fallback_url}")
    try:
        from senior_mint_dashboard.launcher.webview.browser_window import SeniorBrowserWindow
        win = SeniorBrowserWindow(fallback_url, title=config["title"], parent=parent_widget)
        win.show()
        return True
    except Exception as e:
        from senior_mint_dashboard.launcher.webview.browser_window import launch_system_browser
        return launch_system_browser(fallback_url)


def launch_solitaire(parent_widget: Optional[Any] = None) -> bool:
    """Convenience launcher for Solitaire."""
    return launch_game("solitaire", parent_widget)


def launch_mahjong(parent_widget: Optional[Any] = None) -> bool:
    """Convenience launcher for Mahjong."""
    return launch_game("mahjong", parent_widget)
