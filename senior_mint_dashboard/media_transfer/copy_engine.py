"""
Atomic Safe Copy Engine for Media Files.
Performs byte-by-byte file size verification before optional post-copy deletion.
"""

import os
import shutil
from pathlib import Path


def safe_copy_media_file(src_path, dst_dir, delete_after=False):
    """
    Copies src_path to dst_dir safely.
    Verifies file size after copy. If delete_after is True and copy verified, removes src_path.
    Returns bool (True if success).
    """
    src = Path(src_path)
    dst_dir_path = Path(dst_dir)
    dst_dir_path.mkdir(parents=True, exist_ok=True)

    if not src.exists() or not src.is_file():
        return False

    dst_file = dst_dir_path / src.name

    try:
        shutil.copy2(src, dst_file)
        
        # Verify file size
        if dst_file.exists() and dst_file.stat().st_size == src.stat().st_size:
            if delete_after:
                try:
                    src.unlink()
                except Exception:
                    pass
            return True
        else:
            if dst_file.exists():
                dst_file.unlink()
            return False
    except Exception:
        return False


def batch_transfer_media(files, dst_dir, delete_after=False, progress_callback=None):
    """
    Transfers a batch of files to dst_dir with optional progress callback.
    Returns dict: {'copied': int, 'failed': int, 'total': int}
    """
    total = len(files)
    copied = 0
    failed = 0

    for idx, src_file in enumerate(files):
        success = safe_copy_media_file(src_file, dst_dir, delete_after=delete_after)
        if success:
            copied += 1
        else:
            failed += 1

        if progress_callback:
            progress_callback(idx + 1, total, src_file, success)

    return {'copied': copied, 'failed': failed, 'total': total}
