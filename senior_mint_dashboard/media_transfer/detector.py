"""
MTP Smartphone and External HDD Auto-Detector Module.
Detects mounted smartphones under GVFS (/run/user/<UID>/gvfs/mtp*)
and mounted external USB drives under /media/dziadek/*.
"""

import os
import sys
import shutil
import logging
from pathlib import Path

logger = logging.getLogger("SeniorMintDashboard")


def get_current_user_uid():
    try:
        uid = os.getuid()
        return uid
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

    logger.info(f"Scanning for MTP phone in: '{gvfs_dir}'")
    if not gvfs_dir.exists():
        logger.info(f"GVFS directory '{gvfs_dir}' does not exist. No phone detected.")
        return None

    # Matches mtp:host=* (Linux) or mtp_host=* (Windows/Tests)
    mounts = list(gvfs_dir.glob("mtp*host=*"))
    if mounts:
        logger.info(f"Detected mounted MTP phone at: '{mounts[0]}'")
        return mounts[0]

    logger.info("No active MTP mounts matching 'mtp*host=*' found.")
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

    logger.info(f"Scanning for external HDD in: '{media_dir}'")
    if not media_dir.exists():
        logger.info(f"Media mount directory '{media_dir}' does not exist. No HDD detected.")
        return None

    drives = [d for d in media_dir.glob("*") if d.is_dir()]
    if drives:
        logger.info(f"Detected mounted HDD drive at: '{drives[0]}'")
        return drives[0]

    logger.info("No mounted external hard drive found under media directory.")
    return None


def get_disk_capacity_info(drive_path):
    """
    Calculates total, used, free bytes and free percentage for drive_path.
    Returns dict: {'total_gb': float, 'free_gb': float, 'free_pct': float, 'color_zone': str, 'label': str}
    """
    if not drive_path or not Path(drive_path).exists():
        logger.info("Disk capacity check skipped (drive not connected).")
        return {
            "total_gb": 0.0,
            "free_gb": 0.0,
            "free_pct": 0.0,
            "color_zone": "red",
            "label": "Dysk niepodłączony"
        }

    try:
        logger.info(f"Retrieving disk capacity for path: '{drive_path}'")
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
        logger.info(f"Disk space details: total={total_gb:.1f}GB, free={free_gb:.1f}GB ({int(free_pct)}% free). Zone={color_zone}")

        return {
            "total_gb": total_gb,
            "free_gb": free_gb,
            "free_pct": free_pct,
            "color_zone": color_zone,
            "label": label
        }
    except Exception as e:
        logger.error(f"Failed to calculate disk capacity for '{drive_path}': {e}", exc_info=True)
        return {
            "total_gb": 0.0,
            "free_gb": 0.0,
            "free_pct": 0.0,
            "color_zone": "red",
            "label": "Błąd odczytu dysku"
        }
