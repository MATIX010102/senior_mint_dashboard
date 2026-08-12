"""
Settings Dialog for Senior Mint Dashboard.
Allows Dziadek to configure basic options (like weather location), check version details,
and run asynchronous GitHub update checks with a dynamic reload option.
"""

import os
import sys
import json
import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from senior_mint_dashboard.config import (
    PALETTE, TYPOGRAPHY, SETTINGS_FILE, VERSION_FILE, APP_VERSION, POLISH_CITIES
)

logger = logging.getLogger("SeniorMintDashboard")


class UpdateWorker(QThread):
    """Background worker thread to run git pull and syntax checks without locking the main thread."""
    finished = pyqtSignal(dict)

    def __init__(self, repo_dir):
        super().__init__()
        self.repo_dir = repo_dir

    def run(self):
        try:
            logger.info("Background UpdateWorker started.")
            from senior_mint_dashboard.updater.git_updater import check_and_apply_updates
            result = check_and_apply_updates(self.repo_dir)
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"Error in UpdateWorker background thread: {e}", exc_info=True)
            self.finished.emit({'success': False, 'updated': False, 'error': str(e)})


class SettingsDialog(QDialog):
    """Senior-friendly Settings Panel with large touch controls."""

    def __init__(self, weather_widget=None, parent=None):
        super().__init__(parent)
        self.weather_widget = weather_widget
        self.setWindowTitle("Ustawienia i Informacje")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setMinimumSize(600, 480)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {PALETTE['BACKGROUND_DARK']};
                border: 3px solid {PALETTE['CARD_BORDER']};
                border-radius: 16px;
            }}
            QLabel {{
                color: {PALETTE['TEXT_BRIGHT']};
                background: transparent;
            }}
            QComboBox {{
                background-color: #313244;
                color: white;
                font-size: 16pt;
                font-weight: bold;
                border: 2px solid {PALETTE['CARD_BORDER']};
                border-radius: 8px;
                padding: 10px;
                min-width: 250px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #313244;
                color: white;
                selection-background-color: {PALETTE['BUTTON_BLUE']};
                selection-color: #11111B;
                font-size: 16pt;
            }}
        """)

        self.update_worker = None
        self._init_ui()
        self._load_current_settings()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header Title
        title = QLabel("⚙️ Ustawienia Pulpitu", self)
        title.setFont(QFont("Sans-Serif", 22, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {PALETTE['ACCENT_YELLOW']}; font-size: 22pt; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # ----------------- Weather Location Section -----------------
        loc_frame = QFrame(self)
        loc_frame.setStyleSheet(f"QFrame {{ border: 2px solid {PALETTE['CARD_BORDER']}; border-radius: 10px; padding: 10px; }}")
        loc_layout = QVBoxLayout(loc_frame)
        loc_layout.setSpacing(8)

        loc_label = QLabel("🌤️ Lokalizacja pogody:", loc_frame)
        loc_label.setFont(QFont("Sans-Serif", 16, QFont.Weight.Bold))
        loc_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        loc_layout.addWidget(loc_label)

        self.city_combo = QComboBox(loc_frame)
        self.city_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        # Populate cities list sorted alphabetically
        for city in sorted(POLISH_CITIES.keys()):
            self.city_combo.addItem(city)
        self.city_combo.currentTextChanged.connect(self._on_city_changed)
        loc_layout.addWidget(self.city_combo)

        layout.addWidget(loc_frame)

        # ----------------- Updates and Version Section -----------------
        up_frame = QFrame(self)
        up_frame.setStyleSheet(f"QFrame {{ border: 2px solid {PALETTE['CARD_BORDER']}; border-radius: 10px; padding: 10px; }}")
        up_layout = QVBoxLayout(up_frame)
        up_layout.setSpacing(8)

        # Version information label
        version_text = f"Wersja programu: {APP_VERSION}"
        if VERSION_FILE.exists():
            try:
                ver_data = json.loads(VERSION_FILE.read_text(encoding="utf-8"))
                version_text += f" ({ver_data.get('date', 'Zaktualizowano')})"
            except Exception:
                pass

        self.version_label = QLabel(version_text, up_frame)
        self.version_label.setFont(QFont("Sans-Serif", 14))
        self.version_label.setStyleSheet("font-size: 14pt; color: #CDD6F4;")
        up_layout.addWidget(self.version_label)

        # Action layout
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)

        self.btn_check_updates = QPushButton("🔄 Sprawdź aktualizacje", up_frame)
        self.btn_check_updates.setStyleSheet(f"""
            QPushButton {{
                background-color: {PALETTE['BUTTON_BLUE']};
                color: #11111B;
                font-size: 14pt;
                font-weight: bold;
                padding: 12px 24px;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {PALETTE['BUTTON_HOVER']};
            }}
        """)
        self.btn_check_updates.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_check_updates.clicked.connect(self._check_for_updates)
        action_layout.addWidget(self.btn_check_updates)

        self.btn_restart = QPushButton("🔄 Uruchom ponownie", up_frame)
        self.btn_restart.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                padding: 12px 24px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.btn_restart.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_restart.setVisible(False)
        self.btn_restart.clicked.connect(self._restart_app)
        action_layout.addWidget(self.btn_restart)

        up_layout.addLayout(action_layout)

        # Status output
        self.update_status = QLabel("Kliknij przycisk powyżej, aby sprawdzić nowości.", up_frame)
        self.update_status.setFont(QFont("Sans-Serif", 12))
        self.update_status.setStyleSheet("font-size: 12pt; color: #a9e34b;")
        self.update_status.setWordWrap(True)
        up_layout.addWidget(self.update_status)

        layout.addWidget(up_frame)

        # Close button
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

    def _load_current_settings(self):
        """Loads and selects current configured city in dropdown combobox."""
        current_city = "Warszawa"
        if SETTINGS_FILE.exists():
            try:
                data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                current_city = data.get("weather_city", "Warszawa")
            except Exception as e:
                logger.error(f"Failed to load settings from file: {e}")

        # Find in dropdown and select it
        index = self.city_combo.findText(current_city)
        if index >= 0:
            self.city_combo.setCurrentIndex(index)

    def _on_city_changed(self, city_name):
        """Saves selected city to user settings and notifies weather widget."""
        logger.info(f"User changed weather location setting to: '{city_name}'")
        settings_data = {"weather_city": city_name}
        try:
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_FILE.write_text(json.dumps(settings_data, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.info("Saved new weather location configuration successfully.")
            
            # Notify the weather widget to refresh instantly
            if self.weather_widget:
                self.weather_widget.refresh_location()
        except Exception as e:
            logger.error(f"Failed to save settings: {e}", exc_info=True)

    def _check_for_updates(self):
        """Disables controls and spawns QThread worker to check updates in the background."""
        logger.info("User requested manual check for updates.")
        self.btn_check_updates.setEnabled(False)
        self.update_status.setText("Checking for updates... Please wait (Sprawdzanie aktualizacji...)")
        self.update_status.setStyleSheet("font-size: 12pt; color: #ffc107;")

        repo_dir = Path(__file__).resolve().parent.parent.parent
        self.update_worker = UpdateWorker(repo_dir)
        self.update_worker.finished.connect(self._on_update_check_finished)
        self.update_worker.start()

    def _on_update_check_finished(self, result):
        """Handles worker return results and guides user on action."""
        logger.info(f"Update check finished. Result: {result}")
        self.btn_check_updates.setEnabled(True)

        if result.get("success"):
            if result.get("updated"):
                self.update_status.setText("✅ Pobrano i zainstalowano nowe aktualizacje! Kliknij przycisk obok, aby uruchomić ponownie program.")
                self.update_status.setStyleSheet("font-size: 12pt; color: #28a745; font-weight: bold;")
                self.btn_restart.setVisible(True)
            else:
                self.update_status.setText("✅ Program jest aktualny. Posiadasz najnowszą wersję!")
                self.update_status.setStyleSheet("font-size: 12pt; color: #a9e34b;")
        else:
            err_msg = result.get("error", "Błąd sieci")
            self.update_status.setText(f"❌ Nie udało się pobrać aktualizacji:\n{err_msg}")
            self.update_status.setStyleSheet("font-size: 12pt; color: #dc3545;")

    def _restart_app(self):
        """Reloads current python process immediately."""
        logger.info("Application reload triggered from settings dialog restart button.")
        # Walk up to main window to set clean exit
        win = self.window()
        if win and hasattr(win, "_allow_exit"):
            win._allow_exit = True
            win.close()
        else:
            self.accept()
        os.execv(sys.executable, [sys.executable] + sys.argv)
