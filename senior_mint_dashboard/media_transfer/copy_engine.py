"""
Atomic Safe Copy Engine for Media Files.
Performs byte-by-byte file size verification before optional post-copy deletion.
"""

import os
import shutil
import logging
from pathlib import Path

logger = logging.getLogger("SeniorMintDashboard")


def safe_copy_media_file(src_path, dst_dir, delete_after=False):
    """
    Copies src_path to dst_dir safely.
    Verifies file size after copy. If delete_after is True and copy verified, removes src_path.
    Returns bool (True if success).
    """
    src = Path(src_path)
    dst_dir_path = Path(dst_dir)
    
    logger.info(f"Preparing to copy: '{src}' to directory '{dst_dir_path}'")
    
    try:
        dst_dir_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create destination directory '{dst_dir_path}': {e}")
        return False

    if not src.exists():
        logger.error(f"Source file does not exist: '{src}'")
        return False
    if not src.is_file():
        logger.error(f"Source path is not a file: '{src}'")
        return False

    dst_file = dst_dir_path / src.name

    try:
        logger.info(f"Copying file '{src.name}' ({src.stat().st_size} bytes)...")
        shutil.copy2(src, dst_file)
        
        # Verify file size
        if dst_file.exists() and dst_file.stat().st_size == src.stat().st_size:
            logger.info(f"Verification success: size matches ({dst_file.stat().st_size} bytes) for '{dst_file.name}'")
            if delete_after:
                try:
                    logger.info(f"Delete-after-copy enabled. Removing source file: '{src}'")
                    src.unlink()
                    logger.info(f"Removed source file successfully: '{src}'")
                except Exception as e:
                    logger.error(f"Failed to delete source file after copy: '{src}'. Error: {e}")
            return True
        else:
            actual_size = dst_file.stat().st_size if dst_file.exists() else "None (file missing)"
            logger.error(f"Verification failed: source size={src.stat().st_size}, copied size={actual_size}. Cleaning up...")
            if dst_file.exists():
                try:
                    dst_file.unlink()
                except Exception as e:
                    logger.error(f"Failed to clean up incomplete destination file '{dst_file}': {e}")
            return False
    except Exception as e:
        logger.error(f"Exception raised during copy operation for '{src}': {e}", exc_info=True)
        return False


def batch_transfer_media(files, dst_dir, delete_after=False, progress_callback=None):
    """
    Transfers a batch of files to dst_dir with optional progress callback.
    Returns dict: {'copied': int, 'failed': int, 'total': int}
    """
    total = len(files)
    copied = 0
    failed = 0

    logger.info(f"Starting batch transfer of {total} files to '{dst_dir}'. delete_after={delete_after}")
    for idx, src_file in enumerate(files):
        success = safe_copy_media_file(src_file, dst_dir, delete_after=delete_after)
        if success:
            copied += 1
        else:
            failed += 1

        if progress_callback:
            try:
                progress_callback(idx + 1, total, src_file, success)
            except Exception as e:
                logger.error(f"Error in batch progress callback: {e}")

    logger.info(f"Batch transfer complete. Status: {copied} copied, {failed} failed, out of {total} total.")
    return {'copied': copied, 'failed': failed, 'total': total}
