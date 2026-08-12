"""
Media Scanner and Thumbnail Generator for Smartphone MTP.
Optimized for high-performance scanning to prevent MTP timeouts and lags on Linux Mint.
"""

import time
import logging
from pathlib import Path

logger = logging.getLogger("SeniorMintDashboard")


def scan_media_preset(mtp_root, preset_key):
    """
    Scans mtp_root for files matching preset_key:
    - 'wa_photos': WhatsApp Images (.jpg, .png)
    - 'wa_videos': WhatsApp Videos (.mp4, .mkv)
    - 'dcim_photos': Camera photos (.jpg, .png)
    - 'dcim_videos': Camera videos (.mp4, .mov)
    Returns list of Path objects.
    Optimized to locate specific directories (WhatsApp, DCIM) first rather than scanning the whole drive.
    """
    if not mtp_root or not Path(mtp_root).exists():
        logger.warning(f"Scan aborted: MTP root path '{mtp_root}' does not exist.")
        return []

    start_time = time.time()
    root = Path(mtp_root)
    found_files = []

    logger.info(f"Starting media scan for preset '{preset_key}' on root: '{root}'")

    if preset_key in ('wa_photos', 'wa_videos'):
        # WhatsApp media folders are usually inside Android/media/com.whatsapp/WhatsApp/Media or similar
        # Doing a shallow search for directories named "WhatsApp"
        target_dirs = []
        for p in root.glob("**/WhatsApp"):
            if p.is_dir():
                target_dirs.append(p)

        # Fallback to rglob if shallow searches yield nothing
        if not target_dirs:
            target_dirs = list(root.rglob("WhatsApp"))

        exts = ('.jpg', '.jpeg', '.png') if preset_key == 'wa_photos' else ('.mp4', '.mkv', '.avi')
        logger.info(f"Scanning WhatsApp directories: {target_dirs}")
        for tdir in target_dirs:
            for p in tdir.rglob("*"):
                if p.is_file() and p.suffix.lower() in exts:
                    found_files.append(p)

    elif preset_key in ('dcim_photos', 'dcim_videos'):
        # Camera pictures/videos are strictly inside DCIM or Camera directories
        target_dirs = []

        # 1. Check root/DCIM
        if (root / "DCIM").is_dir():
            target_dirs.append(root / "DCIM")
        if (root / "Camera").is_dir():
            target_dirs.append(root / "Camera")

        # 2. Check root/*/DCIM (e.g. root/Internal storage/DCIM)
        for p in root.glob("*/DCIM"):
            if p.is_dir():
                target_dirs.append(p)
        for p in root.glob("*/Camera"):
            if p.is_dir():
                target_dirs.append(p)

        # 3. Check root/*/*/DCIM just in case
        for p in root.glob("*/*/DCIM"):
            if p.is_dir():
                target_dirs.append(p)
        for p in root.glob("*/*/Camera"):
            if p.is_dir():
                target_dirs.append(p)

        # Fallback to recursive search if not found, but limit to directories named DCIM or Camera
        if not target_dirs:
            logger.info("DCIM/Camera directory not found at expected levels. Performing rglob search for DCIM...")
            for p in root.rglob("*"):
                if p.is_dir() and p.name.upper() in ("DCIM", "CAMERA"):
                    target_dirs.append(p)

        # Final fallback: scan from root
        if not target_dirs:
            logger.warning("No DCIM or Camera directory found. Scanning full phone storage (slow)...")
            target_dirs = [root]

        exts = ('.jpg', '.jpeg', '.png') if preset_key == 'dcim_photos' else ('.mp4', '.mov', '.avi')
        logger.info(f"Scanning camera directories: {target_dirs}")
        for tdir in target_dirs:
            for p in tdir.rglob("*"):
                # Exclude WhatsApp subdirectory if scanning full phone fallback
                if "WhatsApp" in p.parts:
                    continue
                if p.is_file() and p.suffix.lower() in exts:
                    found_files.append(p)

    elapsed_time = time.time() - start_time
    logger.info(f"Scan finished. Found {len(found_files)} files matching '{preset_key}' in {elapsed_time:.3f} seconds.")
    return found_files
