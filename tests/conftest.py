"""
pytest conftest.py for Senior Mint Dashboard E2E Test Suite.
Provides global fixtures, PyQt6 QApplication lifecycle management,
and hardware/system mocks (GVFS/MTP, External HDD, CUPS/HPLIP, Git, Polkit, LightDM).
"""

import os
import sys
import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Force offscreen QPA platform for headless PyQt6 testing
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["SENIOR_MINT_TEST_MODE"] = "1"

# Ensure root directory is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def qapp():
    """Provides a single QApplication instance for Qt GUI tests."""
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        yield app
    except ImportError:
        # Fallback dummy QApplication mock if PyQt6 is not installed in current environment
        mock_app = MagicMock()
        yield mock_app


@pytest.fixture
def temp_workspace(tmp_path):
    """Provides a clean isolated workspace directory structure."""
    ws = tmp_path / "senior_mint_dashboard"
    ws.mkdir(parents=True, exist_ok=True)
    
    # Create standard directories
    (ws / "senior_mint_dashboard").mkdir(parents=True, exist_ok=True)
    (ws / "senior_mint_dashboard" / "launcher").mkdir(parents=True, exist_ok=True)
    (ws / "senior_mint_dashboard" / "media_transfer").mkdir(parents=True, exist_ok=True)
    (ws / "senior_mint_dashboard" / "updater").mkdir(parents=True, exist_ok=True)
    
    # Create sample install.sh
    install_sh = ws / "install.sh"
    install_sh.write_text("""#!/usr/bin/env bash
set -euo pipefail

# Senior Mint Dashboard Provisioner
USER_NAME="dziadek"

if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: Must be run as root" >&2
    exit 1
fi

# Create user
useradd -m -s /bin/bash "$USER_NAME" || true
gpasswd -d "$USER_NAME" sudo || true
gpasswd -d "$USER_NAME" wheel || true
gpasswd -d "$USER_NAME" adm || true
gpasswd -d "$USER_NAME" lpadmin || true

# LightDM Autologin
mkdir -p /etc/lightdm/lightdm.conf.d
cat << 'EOF' > /etc/lightdm/lightdm.conf.d/99-dziadek-kiosk.conf
[Seat:*]
autologin-user=dziadek
autologin-user-timeout=0
user-session=xfce
EOF

# APT Packages
apt-get update -qq
apt-get install -y python3-pyqt6 python3-pyqt6.qtwebengine cups hplip gvfs-backends mtp-tools rsync python3-gi

# Polkit rules
mkdir -p /etc/polkit-1/rules.d
cat << 'EOF' > /etc/polkit-1/rules.d/50-dziadek-udisks2-lockdown.rules
polkit.addRule(function(action, subject) {
    if (subject.user === "dziadek") {
        if (action.id.indexOf("org.freedesktop.udisks2.filesystem-mount-system") === 0 ||
            action.id.indexOf("org.freedesktop.udisks2.modify-device") === 0 ||
            action.id.indexOf("org.freedesktop.udisks2.format") === 0) {
            return polkit.Result.NO;
        }
    }
});
EOF

echo "Installation complete."
""", encoding="utf-8")

    return ws


@pytest.fixture
def wallpaper_dir(tmp_path):
    """Provides a sample ~/Obrazki/Tapety directory with test image files."""
    wp_dir = tmp_path / "Obrazki" / "Tapety"
    wp_dir.mkdir(parents=True, exist_ok=True)
    
    # Create dummy image files
    (wp_dir / "rodzina1.jpg").write_text("DUMMY_JPEG_DATA_1", encoding="utf-8")
    (wp_dir / "rodzina2.jpg").write_text("DUMMY_JPEG_DATA_2", encoding="utf-8")
    (wp_dir / "wnuki3.png").write_text("DUMMY_PNG_DATA_3", encoding="utf-8")
    
    return wp_dir


@pytest.fixture
def mock_gvfs_mtp(tmp_path):
    """Mocks GVFS MTP smartphone mount directory with camera & WhatsApp media."""
    mtp_folder = "mtp_host=Samsung_Galaxy_S20_12345" if sys.platform == "win32" else "mtp:host=Samsung_Galaxy_S20_12345"
    mtp_root = tmp_path / "gvfs" / mtp_folder
    mtp_root.mkdir(parents=True, exist_ok=True)
    
    dcim_dir = mtp_root / "Internal storage" / "DCIM" / "Camera"
    dcim_dir.mkdir(parents=True, exist_ok=True)
    (dcim_dir / "20260801_120000.jpg").write_bytes(b"MOCK_PHOTO_DATA_100KB" * 5000)
    (dcim_dir / "20260802_153000.jpg").write_bytes(b"MOCK_PHOTO_DATA_200KB" * 10000)
    (dcim_dir / "20260803_180000.mp4").write_bytes(b"MOCK_VIDEO_DATA_5MB" * 100000)
    
    wa_img_dir = mtp_root / "Internal storage" / "Android" / "media" / "com.whatsapp" / "WhatsApp" / "Media" / "WhatsApp Images"
    wa_img_dir.mkdir(parents=True, exist_ok=True)
    (wa_img_dir / "IMG-20260805-WA0001.jpg").write_bytes(b"MOCK_WA_IMG_50KB" * 2500)
    (wa_img_dir / "IMG-20260806-WA0002.jpg").write_bytes(b"MOCK_WA_IMG_75KB" * 3750)
    
    wa_vid_dir = mtp_root / "Internal storage" / "Android" / "media" / "com.whatsapp" / "WhatsApp" / "Media" / "WhatsApp Video"
    wa_vid_dir.mkdir(parents=True, exist_ok=True)
    (wa_vid_dir / "VID-20260807-WA0003.mp4").write_bytes(b"MOCK_WA_VID_2MB" * 50000)
    
    return mtp_root


@pytest.fixture
def mock_external_hdd(tmp_path):
    """Mocks mounted external HDD directory /media/dziadek/EXT_HDD."""
    hdd_root = tmp_path / "media" / "dziadek" / "EXT_HDD"
    hdd_root.mkdir(parents=True, exist_ok=True)
    (hdd_root / "Zdjecia_Dziadka").mkdir(exist_ok=True)
    return hdd_root


@pytest.fixture
def mock_cups_hplip():
    """Mocks CUPS and HPLIP command line outputs and printing status."""
    with patch("subprocess.run") as mock_run, patch("subprocess.Popen") as mock_popen:
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = "printer HP_DeskJet_2130 is idle. enabled since Tue 11 Aug 2026 12:00:00 AM CEST\n"
        mock_res.stderr = ""
        mock_run.returncode = 0
        mock_run.return_value = mock_res
        
        yield {
            "run": mock_run,
            "popen": mock_popen,
            "printer_name": "HP_DeskJet_2130",
            "status": "idle"
        }


@pytest.fixture
def mock_git():
    """Mocks git CLI wrapper for updater module."""
    with patch("subprocess.run") as mock_run:
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = "Already up to date.\n"
        mock_res.stderr = ""
        mock_run.return_value = mock_res
        yield mock_run


@pytest.fixture
def temp_config_dir(tmp_path):
    """Mocks senior dashboard configuration directory ~/.config/senior_dashboard."""
    cfg_dir = tmp_path / ".config" / "senior_dashboard"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    
    version_file = cfg_dir / "version.json"
    version_data = {
        "version": "1.0.0",
        "last_updated": "2026-08-11T12:00:00Z",
        "commit": "a1b2c3d4e5f6",
        "status": "up_to_date"
    }
    version_file.write_text(json.dumps(version_data, indent=2), encoding="utf-8")
    
    return cfg_dir
