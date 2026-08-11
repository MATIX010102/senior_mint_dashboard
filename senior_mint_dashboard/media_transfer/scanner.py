"""
Media Scanner and Thumbnail Generator for Smartphone MTP.
"""

from pathlib import Path


def scan_media_preset(mtp_root, preset_key):
    """
    Scans mtp_root for files matching preset_key:
    - 'wa_photos': WhatsApp Images (.jpg, .png)
    - 'wa_videos': WhatsApp Videos (.mp4, .mkv)
    - 'dcim_photos': Camera photos (.jpg, .png)
    - 'dcim_videos': Camera videos (.mp4, .mov)
    Returns list of Path objects.
    """
    if not mtp_root or not Path(mtp_root).exists():
        return []

    root = Path(mtp_root)
    found_files = []

    if preset_key in ('wa_photos', 'wa_videos'):
        target_dirs = list(root.rglob("WhatsApp"))
        exts = ('.jpg', '.jpeg', '.png') if preset_key == 'wa_photos' else ('.mp4', '.mkv', '.avi')
        for tdir in target_dirs:
            for p in tdir.rglob("*"):
                if p.is_file() and p.suffix.lower() in exts:
                    found_files.append(p)
    elif preset_key in ('dcim_photos', 'dcim_videos'):
        exts = ('.jpg', '.jpeg', '.png') if preset_key == 'dcim_photos' else ('.mp4', '.mov', '.avi')
        for p in root.rglob("*"):
            if p.is_file() and p.suffix.lower() in exts:
                found_files.append(p)

    return found_files
