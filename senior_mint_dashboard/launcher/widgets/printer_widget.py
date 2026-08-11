"""
One-Click CUPS / HPLIP HP Printer Status & Test Print Shortcut Widget for Senior Mint Dashboard.
"""

import subprocess
import shutil
from typing import Optional, Tuple
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox, QFrame
)


class PrinterWidget(QFrame):
    """
    Senior printer widget featuring status indicator and one-click 'Drukuj Stronę Próbną' shortcut button.
    Integrates with CUPS / HPLIP via lpstat and lp CLI commands.
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
        self.setStyleSheet("""
            QFrame {
                background-color: #313244;
                border: 2px solid #45475A;
                border-radius: 12px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        status_font = QFont("Sans-Serif", 14, QFont.Weight.Medium)
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #CDD6F4; font-size: 14pt;")

        btn_font = QFont("Sans-Serif", 16, QFont.Weight.Bold)
        self.print_button.setFont(btn_font)
        self.print_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.print_button.setStyleSheet("""
            QPushButton {
                background-color: #89B4FA;
                color: #11111B;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 16pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #B4BEFE;
            }
            QPushButton:pressed {
                background-color: #74C7EC;
            }
        """)
        self.print_button.clicked.connect(self.print_test_page)

        layout.addWidget(self.status_label)
        layout.addWidget(self.print_button)

    def check_printer_status(self) -> Tuple[bool, str]:
        """
        Executes 'lpstat -p' to query CUPS printer status.
        Returns tuple: (is_online: bool, status_message: str).
        """
        if not shutil.which("lpstat"):
            msg = "Brak usługi druku (CUPS)"
            self.status_label.setText(f"Drukarka HP: {msg}")
            return False, msg

        try:
            res = subprocess.run(["lpstat", "-p"], capture_output=True, text=True, timeout=3)
            if res.returncode == 0 and res.stdout:
                output = res.stdout
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
                self.status_label.setText(f"Drukarka HP: {msg}")
                return False, msg
        except (subprocess.SubprocessError, FileNotFoundError):
            msg = "Błąd połączenia z drukarką"
            self.status_label.setText(f"Drukarka HP: {msg}")
            return False, msg

    def print_test_page(self) -> bool:
        """
        Submits test print job via 'lp -d <printer_name> /usr/share/cups/data/testprint'.
        Displays QMessageBox.warning on failure.
        """
        is_online, status_msg = self.check_printer_status()
        if not is_online:
            QMessageBox.warning(
                self,
                "Błąd Drukarki HP",
                f"Nie można wydrukować strony próbnej.\nPowód: {status_msg}.\n\nSprawdź czy kabel USB / zasilanie drukarki jest podłączone."
            )
            return False

        if not shutil.which("lp"):
            QMessageBox.warning(self, "Błąd Drukarki HP", "Polecenie 'lp' nie jest zainstalowane.")
            return False

        try:
            cmd = ["lp", "-d", self.default_printer, self.TEST_PAGE_PATH]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                QMessageBox.information(
                    self,
                    "Sukces Drukowania",
                    "Strona próbna została wysłana do drukarki HP!"
                )
                return True
            else:
                QMessageBox.warning(
                    self,
                    "Błąd Drukowania",
                    f"Wysyłanie zadania drukowania nie powiodło się:\n{res.stderr}"
                )
                return False
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            QMessageBox.warning(
                self,
                "Błąd Drukowania",
                f"Wystąpił błąd podczas próby drukowania: {e}"
            )
            return False
