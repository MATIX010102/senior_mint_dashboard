"""
One-Click CUPS / HPLIP HP Printer Status & Test Print Shortcut Widget for Senior Mint Dashboard.
Matches the style of SeniorTileButton to act as a proper grid cell.
"""

import subprocess
import shutil
import logging
from typing import Optional, Tuple
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox, QFrame
)
from senior_mint_dashboard.config import PALETTE

logger = logging.getLogger("SeniorMintDashboard")


class PrinterWidget(QFrame):
    """
    Senior printer widget featuring status indicator and one-click 'Drukuj Stronę Próbną' shortcut button.
    Integrates with CUPS / HPLIP via lpstat and lp CLI commands.
    Styled as a Senior Action Card to fit directly into the 3x3 grid.
    """
    BUTTON_LABEL = "Drukuj Stronę Próbną"
    DEFAULT_PRINTER = "HP_DeskJet_2130"
    TEST_PAGE_PATH = "/usr/share/cups/data/testprint"

    def __init__(self, parent: Optional[QWidget] = None, default_printer: str = DEFAULT_PRINTER):
        if isinstance(parent, str) and not isinstance(parent, QWidget):
            default_printer = parent
            parent = None
        super().__init__(parent)
        self.default_printer = default_printer

        self.status_label = QLabel("Status drukarki: Sprawdzanie...", self)
        self.print_button = QPushButton(self.BUTTON_LABEL, self)

        self._init_ui()
        self.check_printer_status()

    def _init_ui(self) -> None:
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(45, 42, 74, 0.9);
                border: 2px solid {PALETTE['CARD_BORDER']};
                border-radius: 16px;
                padding: 16px;
            }}
            QFrame:hover {{
                border: 3px solid {PALETTE['CARD_HOVER_BORDER']};
                background-color: rgba(60, 56, 95, 0.95);
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Title/Header (matches tile header)
        self.title_label = QLabel("Drukarka HP", self)
        self.title_label.setFont(QFont("Sans-Serif", 24, QFont.Weight.Bold))
        self.title_label.setStyleSheet(
            f"color: {PALETTE['TEXT_BRIGHT']}; background: transparent; font-size: 24pt; font-weight: bold;"
        )
        layout.addWidget(self.title_label)

        # Status Label (matches card subtitle)
        status_font = QFont("Sans-Serif", 14, QFont.Weight.Medium)
        self.status_label.setFont(status_font)
        self.status_label.setStyleSheet("color: #CDD6F4; background: transparent; font-size: 14pt;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Print Button
        btn_font = QFont("Sans-Serif", 16, QFont.Weight.Bold)
        self.print_button.setFont(btn_font)
        self.print_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.print_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {PALETTE['BUTTON_BLUE']};
                color: #11111B;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 16pt;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {PALETTE['BUTTON_HOVER']};
            }}
            QPushButton:pressed {{
                background-color: {PALETTE['BUTTON_ACTIVE']};
            }}
        """)
        self.print_button.clicked.connect(self.print_test_page)
        layout.addWidget(self.print_button)

    def check_printer_status(self) -> Tuple[bool, str]:
        """
        Executes 'lpstat -p' to query CUPS printer status.
        Returns tuple: (is_online: bool, status_message: str).
        """
        logger.info(f"Checking HP printer status for '{self.default_printer}'...")
        if not shutil.which("lpstat"):
            msg = "Brak usługi druku (CUPS)"
            logger.warning("lpstat binary missing. CUPS is not installed or not in PATH.")
            self.status_label.setText(f"Drukarka HP: {msg}")
            return False, msg

        try:
            res = subprocess.run(["lpstat", "-p"], capture_output=True, text=True, timeout=3)
            if res.returncode == 0 and res.stdout:
                output = res.stdout
                logger.info(f"lpstat output: {output.strip()}")
                if "idle" in output or "ready" in output or "is printing" in output or self.default_printer in output:
                    msg = "Gotowa (idle)"
                    self.status_label.setText(f"Drukarka HP: {msg}")
                    return True, "idle"
                else:
                    msg = "Wykryta, bezczynna"
                    self.status_label.setText(f"Drukarka HP: {msg}")
                    return True, "idle"
            else:
                msg = "Odłączona lub niedostępna"
                logger.warning(f"Printer status check failed (lpstat exit {res.returncode}): {res.stderr}")
                self.status_label.setText(f"Drukarka HP: {msg}")
                return False, msg
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            msg = "Błąd połączenia z drukarką"
            logger.error(f"Failed to execute lpstat status query: {e}")
            self.status_label.setText(f"Drukarka HP: {msg}")
            return False, msg

    def print_test_page(self) -> bool:
        """
        Submits test print job via 'lp -d <printer_name> /usr/share/cups/data/testprint'.
        Displays QMessageBox.warning on failure.
        """
        logger.info("Attempting to print test page...")
        is_online, status_msg = self.check_printer_status()
        if not is_online:
            logger.warning(f"Cannot print test page: printer is offline ({status_msg}).")
            QMessageBox.warning(
                self,
                "Błąd Drukarki HP",
                f"Nie można wydrukować strony próbnej.\nPowód: {status_msg}.\n\nSprawdź czy kabel USB / zasilanie drukarki jest podłączone."
            )
            return False

        if not shutil.which("lp"):
            logger.error("lp command line tool is missing.")
            QMessageBox.warning(self, "Błąd Drukarki HP", "Polecenie 'lp' nie jest zainstalowane.")
            return False

        try:
            cmd = ["lp", "-d", self.default_printer, self.TEST_PAGE_PATH]
            logger.info(f"Executing: {' '.join(cmd)}")
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                logger.info("Test page print job submitted successfully.")
                QMessageBox.information(
                    self,
                    "Sukces Drukowania",
                    "Strona próbna została wysłana do drukarki HP!"
                )
                return True
            else:
                logger.error(f"lp command failed with exit code {res.returncode}. Stderr: {res.stderr}")
                QMessageBox.warning(
                    self,
                    "Błąd Drukowania",
                    f"Wysyłanie zadania drukowania nie powiodło się:\n{res.stderr}"
                )
                return False
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logger.error(f"Subprocess error when running lp: {e}")
            QMessageBox.warning(
                self,
                "Błąd Drukowania",
                f"Wystąpił błąd podczas próby drukowania: {e}"
            )
            return False
