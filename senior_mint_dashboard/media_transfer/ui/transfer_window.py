"""
Media Transfer GUI Window (PyQt6).
Provides senior-friendly tiles to copy WhatsApp photos/videos and Camera photos/videos
to external HDD with free space indicator, keep/delete toggle, and emergency grandson contact button.
"""

import sys
import logging
import shutil
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar,
    QCheckBox, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from senior_mint_dashboard.media_transfer.detector import (
    detect_mtp_phone, detect_external_hdd, get_disk_capacity_info
)
from senior_mint_dashboard.media_transfer.scanner import scan_media_preset
from senior_mint_dashboard.media_transfer.copy_engine import batch_transfer_media

logger = logging.getLogger("SeniorMintDashboard")


def get_rustdesk_id() -> str:
    """Retrieves the actual RustDesk client ID using its CLI tool or fallback configurations."""
    import os
    if os.environ.get("SENIOR_MINT_TEST_MODE") == "1":
        return "987 654 321"

    rustdesk_bin = shutil.which("rustdesk")
    if not rustdesk_bin:
        # Check standard location on Linux Mint
        if Path("/usr/bin/rustdesk").exists():
            rustdesk_bin = "/usr/bin/rustdesk"

    if not rustdesk_bin:
        logger.warning("RustDesk binary not found in PATH or standard location.")
        return "Nie zainstalowano RustDesk"

    try:
        logger.info(f"Running '{rustdesk_bin} --get-id' to fetch remote client ID...")
        res = subprocess.run([rustdesk_bin, "--get-id"], capture_output=True, text=True, timeout=3)
        if res.returncode == 0 and res.stdout.strip():
            client_id = res.stdout.strip()
            logger.info(f"Successfully retrieved RustDesk ID: {client_id}")
            return client_id
    except Exception as e:
        logger.error(f"Failed to fetch RustDesk ID: {e}")

    return "Błąd odczytu ID"


def is_rustdesk_active() -> bool:
    """Checks if the RustDesk system service daemon is currently active."""
    import os
    if os.environ.get("SENIOR_MINT_TEST_MODE") == "1":
        return True

    if not shutil.which("systemctl"):
        return False

    try:
        res = subprocess.run(["systemctl", "is-active", "rustdesk"], capture_output=True, text=True, timeout=2)
        status = res.stdout.strip()
        logger.info(f"RustDesk service status query: {status}")
        return status == "active"
    except Exception as e:
        logger.error(f"Failed to query RustDesk service status: {e}")
        return False


class MediaTransferWindow(QDialog):
    """Senior-friendly Media Transfer UI Dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Przesyłanie Zdjęć i Filmów z Telefonu na Dysk Zewnętrzny")
        self.setMinimumSize(850, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
                font-size: 16px;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #0d6efd;
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 15px;
                border-radius: 10px;
                border: 2px solid #0a58ca;
            }
            QPushButton:hover {
                background-color: #0b5ed7;
            }
            QPushButton#helpBtn {
                background-color: #dc3545;
                border-color: #b02a37;
            }
            QPushButton#helpBtn:hover {
                background-color: #bb2d3b;
            }
            QCheckBox {
                font-size: 18px;
                color: #ffc107;
                padding: 10px;
            }
        """)

        logger.info("Initializing MediaTransferWindow...")
        self.phone_path = detect_mtp_phone()
        self.hdd_path = detect_external_hdd()

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header Title
        title_label = QLabel("📱 ➔ 💾 Przesyłanie Zdjęć z Telefonu na Dysk", self)
        title_label.setStyleSheet("font-size: 26px; font-weight: bold; color: #4dabf7;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Disk Capacity Bar Section
        cap_info = get_disk_capacity_info(self.hdd_path)
        self.cap_label = QLabel(cap_info["label"], self)
        self.cap_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.cap_bar = QProgressBar(self)
        self.cap_bar.setMaximum(100)
        self.cap_bar.setValue(int(100 - cap_info["free_pct"]))
        self.cap_bar.setTextVisible(True)
        self.cap_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #555;
                border-radius: 8px;
                text-align: center;
                height: 30px;
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background-color: {'#28a745' if cap_info['color_zone']=='green' else ('#ffc107' if cap_info['color_zone']=='amber' else '#dc3545')};
            }}
        """)

        layout.addWidget(self.cap_label)
        layout.addWidget(self.cap_bar)

        # Toggle option: Keep vs Delete
        self.delete_toggle = QCheckBox("Usuń zdjęcia z telefonu PO pomyślnym skopiowaniu (Domyślnie: NIE - zostaw w telefonie)", self)
        self.delete_toggle.setChecked(False)
        layout.addWidget(self.delete_toggle)

        # Action Preset Buttons
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_wa_img = QPushButton("📸 1. Skopiuj zdjęcia z WhatsApp na dysk", self)
        self.btn_wa_img.clicked.connect(lambda: self._execute_transfer('wa_photos'))

        self.btn_wa_vid = QPushButton("🎬 2. Skopiuj filmy z WhatsApp na dysk", self)
        self.btn_wa_vid.clicked.connect(lambda: self._execute_transfer('wa_videos'))

        self.btn_dcim_img = QPushButton("📷 3. Skopiuj zdjęcia z aparatu (DCIM) na dysk", self)
        self.btn_dcim_img.clicked.connect(lambda: self._execute_transfer('dcim_photos'))

        self.btn_dcim_vid = QPushButton("🎥 4. Skopiuj filmy z aparatu (DCIM) na dysk", self)
        self.btn_dcim_vid.clicked.connect(lambda: self._execute_transfer('dcim_videos'))

        btn_layout.addWidget(self.btn_wa_img)
        btn_layout.addWidget(self.btn_wa_vid)
        btn_layout.addWidget(self.btn_dcim_img)
        btn_layout.addWidget(self.btn_dcim_vid)

        layout.addLayout(btn_layout)

        # Status & Progress
        self.status_label = QLabel("Gotowy. Podłącz telefon i dysk zewnętrzny.", self)
        self.status_label.setStyleSheet("font-size: 16px; color: #a9e34b;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Bottom controls layout (Eject + Help buttons)
        bottom_buttons = QHBoxLayout()
        bottom_buttons.setSpacing(15)

        self.btn_eject = QPushButton("⏏️ Bezpiecznie odłącz telefon", self)
        self.btn_eject.setStyleSheet("""
            QPushButton {
                background-color: #ff922b;
                border-color: #e8590c;
            }
            QPushButton:hover {
                background-color: #f76707;
            }
        """)
        self.btn_eject.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_eject.clicked.connect(self._eject_phone)

        self.help_btn = QPushButton("🆘 Poproś wnuka o pomoc (Zdalne wsparcie)", self)
        self.help_btn.setObjectName("helpBtn")
        self.help_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.help_btn.clicked.connect(self._show_emergency_help)

        bottom_buttons.addWidget(self.btn_eject)
        bottom_buttons.addWidget(self.help_btn)
        layout.addLayout(bottom_buttons)

    def _execute_transfer(self, preset_key):
        logger.info(f"Media transfer action triggered for preset: '{preset_key}'")

        # Refresh device paths on action trigger to capture newly connected devices
        self.phone_path = detect_mtp_phone()
        self.hdd_path = detect_external_hdd()

        if not self.phone_path:
            logger.warning("Transfer failed: No connected MTP phone found.")
            QMessageBox.warning(self, "Brak telefonu", "Nie wykryto podłączonego telefonu przez USB (MTP).\n\nUpewnij się, że telefon jest podłączony kablem i wybrano w nim opcję 'Przesyłanie plików / MTP'.")
            return

        if not self.hdd_path:
            logger.warning("Transfer failed: No connected external HDD found.")
            QMessageBox.warning(self, "Brak dysku HDD", "Nie wykryto podłączonego zewnętrznego dysku twardego.\n\nPodłącz dysk USB i spróbuj ponownie.")
            return

        delete_after = self.delete_toggle.isChecked()
        dst_dir = self.hdd_path / "ZDJECIA_DZIADKA"

        logger.info(f"Scanning media for preset '{preset_key}'...")
        files = scan_media_preset(self.phone_path, preset_key)
        if not files:
            logger.info(f"No files matching preset '{preset_key}' detected on phone.")
            QMessageBox.information(self, "Brak plików", "Nie znaleziono nowych plików do skopiowania w tej kategorii.")
            return

        logger.info(f"Found {len(files)} files. Starting batch transfer. delete_after={delete_after}")
        self.status_label.setText(f"Kopiowanie {len(files)} plików...")
        res = batch_transfer_media(files, dst_dir, delete_after=delete_after)

        logger.info(f"Batch transfer complete: {res['copied']} copied, {res['failed']} failed.")
        self.status_label.setText(f"✅ Skopiowano pomyślnie: {res['copied']} z {res['total']} plików!")
        QMessageBox.information(
            self,
            "Transfer Zakończony",
            f"Zdjęcia/filmy zostały pomyślnie przesłane na dysk zewnętrzny!\n\n"
            f"Lokalizacja: {dst_dir}\n"
            f"Skopiowano plików: {res['copied']}\n"
            f"Błędy: {res['failed']}"
        )

        # Update disk capacity display
        cap_info = get_disk_capacity_info(self.hdd_path)
        self.cap_label.setText(cap_info["label"])
        self.cap_bar.setValue(int(100 - cap_info["free_pct"]))

    def _eject_phone(self):
        """Unmounts the phone GVFS mount safely using gio mount -u."""
        # Refresh device path
        self.phone_path = detect_mtp_phone()

        if not self.phone_path:
            QMessageBox.warning(self, "Brak telefonu", "Nie wykryto podłączonego telefonu do odłączenia.")
            return

        gio_bin = shutil.which("gio")
        if not gio_bin:
            logger.warning("gio command line tool missing. Cannot perform clean MTP unmount.")
            QMessageBox.warning(self, "Błąd systemowy", "Brak systemowego polecenia 'gio' do bezpiecznego odłączenia.")
            return

        logger.info(f"Safely unmounting phone at: '{self.phone_path}'...")
        try:
            res = subprocess.run([gio_bin, "mount", "-u", str(self.phone_path)], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                logger.info("Phone unmounted successfully.")
                QMessageBox.information(
                    self,
                    "Bezpieczne Odłączenie",
                    "Telefon został bezpiecznie odłączony w systemie.\n\nMożesz teraz odłączyć kabel USB od telefonu."
                )
                self.phone_path = None
                self.status_label.setText("Telefon został bezpiecznie odłączony.")
            else:
                logger.error(f"gio mount -u failed (exit {res.returncode}): {res.stderr.strip()}")
                QMessageBox.warning(
                    self,
                    "Błąd Odłączania",
                    f"Nie udało się bezpiecznie odłączyć telefonu:\n{res.stderr.strip()}"
                )
        except Exception as e:
            logger.error(f"Exception during phone eject: {e}", exc_info=True)
            QMessageBox.warning(
                self,
                "Błąd Odłączania",
                f"Wystąpił nieoczekiwany błąd podczas odłączania:\n{e}"
            )

    def _show_emergency_help(self):
        logger.info("Grandson emergency help dialog triggered.")
        client_id = get_rustdesk_id()
        is_active = is_rustdesk_active()
        rd_status = "Aktywny (Działa w tle)" if is_active else "Nieaktywny / Wyłączony"

        msg = (
            "🆘 ZDALNA POMOC DLA DZIADKA 🆘\n\n"
            "Telefon kontaktowy do Wnuka: +48 123 456 789\n\n"
            "Dane Zdalnego Wspierania (RustDesk):\n"
            f"  • ID komputera:  {client_id}\n"
            f"  • Status usługi: {rd_status}\n\n"
            "Podaj powyższe ID wnukowi przez telefon, aby mógł połączyć się zdalnie i pomóc."
        )
        QMessageBox.information(self, "Poproś wnuka o pomoc", msg)
