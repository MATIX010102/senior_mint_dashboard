"""
MTP Smartphone and External HDD Auto-Detector Module.
Detects mounted smartphones under GVFS (/run/user/<UID>/gvfs/mtp*)
and mounted external USB drives under /media/dziadek/*.
"""

import os
import sys
import shutil
from pathlib import Path


def get_current_user_uid():
    try:
        return os.getuid()
    except AttributeError:
        return 1000


def detect_mtp_phone(custom_gvfs_path=None):
    """
    Locates the primary MTP smartphone mount directory.
    Returns Path object or None if no phone is connected.
    """
    if custom_gvfs_path:
        gvfs_dir = Path(custom_gvfs_path)
    else:
        uid = get_current_user_uid()
        gvfs_dir = Path(f"/run/user/{uid}/gvfs")

    if not gvfs_dir.exists():
        return None

    # Matches mtp:host=* (Linux) or mtp_host=* (Windows/Tests)
    mounts = list(gvfs_dir.glob("mtp*host=*"))
    if mounts:
        return mounts[0]

    return None


def detect_external_hdd(custom_media_path=None):
    """
    Locates the primary mounted external USB hard drive.
    Returns Path object or None if no external HDD is mounted.
    """
    if custom_media_path:
        media_dir = Path(custom_media_path)
    else:
        media_dir = Path("/media/dziadek")

    if not media_dir.exists():
        return None

    drives = [d for d in media_dir.glob("*") if d.is_dir()]
    if drives:
        return drives[0]

    return None


def get_disk_capacity_info(drive_path):
    """
    Calculates total, used, free bytes and free percentage for drive_path.
    Returns dict: {'total_gb': float, 'free_gb': float, 'free_pct': float, 'color_zone': str, 'label': str}
    """
    if not drive_path or not Path(drive_path).exists():
        return {
            "total_gb": 0.0,
            "free_gb": 0.0,
            "free_pct": 0.0,
            "color_zone": "red",
            "label": "Dysk niepodłączony"
        }

    try:
        usage = shutil.disk_usage(drive_path)
        total_gb = usage.total / (1024 ** 3)
        free_gb = usage.free / (1024 ** 3)
        free_pct = (usage.free / usage.total) * 100.0 if usage.total > 0 else 0.0

        if free_pct > 20.0:
            color_zone = "green"
        elif free_pct > 10.0:
            color_zone = "amber"
        else:
            color_zone = "red"

        label = f"Wolne miejsce: {free_gb:.1f} GB z {total_gb:.1f} GB ({int(free_pct)}%)"

        return {
            "total_gb": total_gb,
            "free_gb": free_gb,
            "free_pct": free_pct,
            "color_zone": color_zone,
            "label": label
        }
    except Exception:
        return {
            "total_gb": 0.0,
            "free_gb": 0.0,
            "free_pct": 0.0,
            "color_zone": "red",
            "label": "Błąd odczytu dysku"
        }
