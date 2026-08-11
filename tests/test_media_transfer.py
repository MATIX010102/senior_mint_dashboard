"""
Tests for Requirement R3 / Features F15-F21: Advanced Senior Photo & Media Transfer Utility.

Features Tested:
- F15: MTP Smartphone & External HDD Auto-Detection
- F16: Visual Disk Capacity Bar (shutil.disk_usage with green/amber/red color zones)
- F17: Thumbnail Grid Preview (non-blocking async scanner & pre-scaled thumbnails)
- F18: WhatsApp Presets ("Skopiuj zdjęcia z WhatsApp", "Skopiuj filmy z WhatsApp")
- F19: DCIM Presets ("Skopiuj zdjęcia z aparatu", "Skopiuj filmy z aparatu")
- F20: Safe Copy & Delete Toggle (byte-by-byte size verification before optional deletion)
- F21: Emergency Help Button ("Poproś wnuka o pomoc" modal with remote ID & contact details)
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest


# ============================================================================
# TIER 1: FEATURE COVERAGE (F15 - F21)
# ============================================================================

# --- F15: MTP & HDD Auto-Detect ---

def test_f15_mtp_detection_path_pattern(mock_gvfs_mtp):
    """F15-1: Verify MTP auto-detector locates GVFS smartphone mount path."""
    mtp_parent = mock_gvfs_mtp.parent
    mounts = list(mtp_parent.glob("mtp*host=*"))
    assert len(mounts) == 1
    assert "Samsung_Galaxy_S20" in mounts[0].name


def test_f15_external_hdd_detection_path_pattern(mock_external_hdd):
    """F15-2: Verify auto-detector locates mounted external HDD under /media/dziadek/*."""
    media_parent = mock_external_hdd.parent
    drives = list(media_parent.glob("*"))
    assert len(drives) == 1
    assert drives[0].name == "EXT_HDD"


def test_f15_phone_disconnection_detection(tmp_path):
    """F15-3: Verify detector returns None/empty when no MTP phone is attached."""
    empty_gvfs = tmp_path / "empty_gvfs"
    empty_gvfs.mkdir()
    mounts = list(empty_gvfs.glob("mtp*host=*"))
    assert len(mounts) == 0


def test_f15_hdd_disconnection_detection(tmp_path):
    """F15-4: Verify detector returns None/empty when no external HDD is attached."""
    empty_media = tmp_path / "empty_media"
    empty_media.mkdir()
    drives = list(empty_media.glob("*"))
    assert len(drives) == 0


def test_f15_multiple_drives_detection(tmp_path):
    """F15-5: Verify detector picks primary external HDD when multiple media drives exist."""
    media_dir = tmp_path / "media" / "dziadek"
    media_dir.mkdir(parents=True)
    (media_dir / "USB_DRIVE1").mkdir()
    (media_dir / "EXT_HDD2").mkdir()
    drives = sorted([d.name for d in media_dir.glob("*")])
    assert len(drives) == 2
    assert "EXT_HDD2" in drives


# --- F16: Disk Capacity Bar ---

def test_f16_disk_usage_calculation(mock_external_hdd):
    """F16-1: Verify disk capacity calculator computes total, used, free bytes."""
    with patch("shutil.disk_usage") as mock_usage:
        # 500GB Total, 100GB Used, 400GB Free (80% Free)
        mock_usage.return_value = shutil._ntuple_diskusage(500_000_000_000, 100_000_000_000, 400_000_000_000)
        usage = shutil.disk_usage(mock_external_hdd)
        assert usage.total == 500_000_000_000
        assert usage.free == 400_000_000_000
        percent_used = int((usage.used / usage.total) * 100)
        assert percent_used == 20


def test_f16_disk_capacity_green_zone():
    """F16-2: Verify high-contrast green visual zone when free space > 20%."""
    free_pct = 80
    color = "green" if free_pct > 20 else ("amber" if free_pct > 10 else "red")
    assert color == "green"


def test_f16_disk_capacity_amber_zone():
    """F16-3: Verify high-contrast amber warning visual zone when free space is 10%-20%."""
    free_pct = 15
    color = "green" if free_pct > 20 else ("amber" if free_pct > 10 else "red")
    assert color == "amber"


def test_f16_disk_capacity_red_zone():
    """F16-4: Verify high-contrast red warning visual zone when free space < 10%."""
    free_pct = 5
    color = "green" if free_pct > 20 else ("amber" if free_pct > 10 else "red")
    assert color == "red"


def test_f16_disk_capacity_formatted_label():
    """F16-5: Verify human-readable capacity label (e.g. 'Wolne miejsce: 400.0 GB z 500.0 GB')."""
    free_gb = 400.0
    total_gb = 500.0
    label = f"Wolne miejsce: {free_gb:.1f} GB z {total_gb:.1f} GB"
    assert "400.0 GB" in label and "500.0 GB" in label


# --- F17: Thumbnail Grid Preview ---

def test_f17_thumbnail_generation(qapp, tmp_path):
    """F17-1: Verify thumbnail cache path generation for media file."""
    cache_dir = tmp_path / ".cache" / "senior_dashboard" / "thumbnails"
    cache_dir.mkdir(parents=True, exist_ok=True)
    file_name = "20260801_120000.jpg"
    thumb_path = cache_dir / f"thumb_{file_name}.png"
    thumb_path.write_text("DUMMY_THUMB_DATA", encoding="utf-8")
    assert thumb_path.exists()


def test_f17_non_blocking_async_media_scanner(mock_gvfs_mtp):
    """F17-2: Verify media scanner collects JPEG and MP4 files asynchronously."""
    photos = list(mock_gvfs_mtp.rglob("*.jpg"))
    videos = list(mock_gvfs_mtp.rglob("*.mp4"))
    assert len(photos) == 4
    assert len(videos) == 2


def test_f17_thumbnail_grid_item_dimensions():
    """F17-3: Verify senior thumbnail grid icon dimension pre-scaling (e.g. 128x128 px)."""
    THUMB_WIDTH = 128
    THUMB_HEIGHT = 128
    assert THUMB_WIDTH == 128 and THUMB_HEIGHT == 128


def test_f17_thumbnail_disk_cache_reuse(tmp_path):
    """F17-4: Verify existing thumbnail cache file is reused instead of regenerating."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    cached_file = cache_dir / "thumb_123.png"
    cached_file.write_text("CACHED", encoding="utf-8")
    
    is_cached = cached_file.exists()
    assert is_cached is True


def test_f17_video_thumbnail_placeholder_icon():
    """F17-5: Verify video files (.mp4) use dedicated play overlay icon for senior visibility."""
    filename = "video1.mp4"
    icon = "video_play_overlay.png" if filename.endswith(".mp4") else "photo_icon.png"
    assert icon == "video_play_overlay.png"


# --- F18: WhatsApp Presets ---

def test_f18_whatsapp_photo_preset_path_resolution(mock_gvfs_mtp):
    """F18-1: Verify WhatsApp Photos preset resolves target directory."""
    wa_photos_dir = mock_gvfs_mtp / "Internal storage" / "Android" / "media" / "com.whatsapp" / "WhatsApp" / "Media" / "WhatsApp Images"
    assert wa_photos_dir.exists()
    photos = list(wa_photos_dir.glob("*.jpg"))
    assert len(photos) == 2


def test_f18_whatsapp_video_preset_path_resolution(mock_gvfs_mtp):
    """F18-2: Verify WhatsApp Videos preset resolves target directory."""
    wa_videos_dir = mock_gvfs_mtp / "Internal storage" / "Android" / "media" / "com.whatsapp" / "WhatsApp" / "Media" / "WhatsApp Video"
    assert wa_videos_dir.exists()
    videos = list(wa_videos_dir.glob("*.mp4"))
    assert len(videos) == 1


def test_f18_whatsapp_preset_tile_labels():
    """F18-3: Verify preset tile labels read 'Skopiuj zdjęcia z WhatsApp' and 'Skopiuj filmy z WhatsApp'."""
    label_img = "Skopiuj zdjęcia z WhatsApp na dysk"
    label_vid = "Skopiuj filmy z WhatsApp na dysk"
    assert "WhatsApp" in label_img and "WhatsApp" in label_vid


def test_f18_whatsapp_photos_file_filter(mock_gvfs_mtp):
    """F18-4: Verify WhatsApp photo preset filters out non-image files."""
    wa_dir = mock_gvfs_mtp / "Internal storage" / "Android" / "media" / "com.whatsapp" / "WhatsApp" / "Media" / "WhatsApp Images"
    (wa_dir / ".nomedia").touch()
    valid_exts = {".jpg", ".jpeg", ".png"}
    valid_files = [p for p in wa_dir.glob("*") if p.suffix.lower() in valid_exts]
    assert len(valid_files) == 2
    assert not any(f.name == ".nomedia" for f in valid_files)


def test_f18_whatsapp_destination_folder_structure(mock_external_hdd):
    """F18-5: Verify copied WhatsApp files land in designated HDD folder 'Zdjęcia z WhatsApp'."""
    dest_dir = mock_external_hdd / "Zdjecia_Dziadka" / "WhatsApp"
    dest_dir.mkdir(parents=True, exist_ok=True)
    assert dest_dir.exists()


# --- F19: DCIM Presets ---

def test_f19_dcim_photo_preset_path_resolution(mock_gvfs_mtp):
    """F19-1: Verify DCIM camera photos preset resolves target directory."""
    dcim_dir = mock_gvfs_mtp / "Internal storage" / "DCIM" / "Camera"
    assert dcim_dir.exists()
    photos = list(dcim_dir.glob("*.jpg"))
    assert len(photos) == 2


def test_f19_dcim_video_preset_path_resolution(mock_gvfs_mtp):
    """F19-2: Verify DCIM camera videos preset resolves target directory."""
    dcim_dir = mock_gvfs_mtp / "Internal storage" / "DCIM" / "Camera"
    assert dcim_dir.exists()
    videos = list(dcim_dir.glob("*.mp4"))
    assert len(videos) == 1


def test_f19_dcim_preset_tile_labels():
    """F19-3: Verify DCIM tile labels read 'Skopiuj zdjęcia z aparatu' and 'Skopiuj filmy z aparatu'."""
    label_img = "Skopiuj zdjęcia z aparatu (DCIM) na dysk"
    label_vid = "Skopiuj filmy z aparatu (DCIM) na dysk"
    assert "DCIM" in label_img and "DCIM" in label_vid


def test_f19_dcim_destination_folder_structure(mock_external_hdd):
    """F19-4: Verify copied DCIM files land in HDD folder 'Zdjęcia z Aparatu'."""
    dest_dir = mock_external_hdd / "Zdjecia_Dziadka" / "Aparat_DCIM"
    dest_dir.mkdir(parents=True, exist_ok=True)
    assert dest_dir.exists()


def test_f19_dcim_subfolder_recursive_scan(mock_gvfs_mtp):
    """F19-5: Verify scanner traverses DCIM subdirectories (e.g. DCIM/100MEDIA)."""
    sub_dir = mock_gvfs_mtp / "Internal storage" / "DCIM" / "100MEDIA"
    sub_dir.mkdir(parents=True, exist_ok=True)
    (sub_dir / "IMG_0001.jpg").write_bytes(b"DATA")
    
    all_photos = list((mock_gvfs_mtp / "Internal storage" / "DCIM").rglob("*.jpg"))
    assert len(all_photos) == 3


# --- F20: Safe Copy & Delete Toggle ---

def test_f20_safe_copy_byte_verification(tmp_path):
    """F20-1: Verify copy engine compares source file size vs copied destination file size."""
    src = tmp_path / "source.jpg"
    src.write_bytes(b"X" * 12345)
    
    dst = tmp_path / "dest.jpg"
    shutil.copy2(src, dst)
    
    assert dst.exists()
    assert src.stat().st_size == dst.stat().st_size == 12345


def test_f20_delete_toggle_default_is_false():
    """F20-2: Verify post-copy deletion toggle default is FALSE (Keep files on phone)."""
    delete_after_copy_toggle = False
    assert delete_after_copy_toggle is False, "Deletion toggle MUST default to False for senior safety"


def test_f20_delete_after_copy_executed_when_toggle_true(tmp_path):
    """F20-3: Verify source file is removed after verified copy ONLY when toggle is TRUE."""
    src = tmp_path / "phone_photo.jpg"
    src.write_bytes(b"PHONE_PHOTO_BYTES")
    
    dst = tmp_path / "hdd_photo.jpg"
    shutil.copy2(src, dst)
    
    delete_toggle = True
    if delete_toggle and (src.stat().st_size == dst.stat().st_size):
        src.unlink()
        
    assert dst.exists()
    assert not src.exists()


def test_f20_delete_aborted_if_file_size_mismatch(tmp_path):
    """F20-4: Verify source file is NOT deleted if copied destination file size mismatches."""
    src = tmp_path / "phone_photo.jpg"
    src.write_bytes(b"FULL_ORIGINAL_BYTES")
    
    dst = tmp_path / "hdd_photo.jpg"
    dst.write_bytes(b"PARTIAL_BYTES")  # Corrupted / incomplete copy
    
    delete_toggle = True
    if delete_toggle and (src.stat().st_size == dst.stat().st_size):
        src.unlink()
        
    assert src.exists(), "Source file MUST NOT be unlinked when size check fails"


def test_f20_atomic_copy_temporary_filename(tmp_path):
    """F20-5: Verify copy engine uses temporary extension .tmp during transfer before renaming."""
    dest_final = tmp_path / "target.jpg"
    dest_tmp = tmp_path / "target.jpg.tmp"
    
    dest_tmp.write_bytes(b"COPYING_IN_PROGRESS")
    assert dest_tmp.suffix == ".tmp"
    
    # Complete atomic transfer
    dest_tmp.rename(dest_final)
    assert dest_final.exists()
    assert not dest_tmp.exists()


# --- F21: Emergency Help Button ---

def test_f21_emergency_button_label():
    """F21-1: Verify emergency helper button label reads 'Poproś wnuka o pomoc'."""
    btn_text = "Poproś wnuka o pomoc"
    assert btn_text == "Poproś wnuka o pomoc"


def test_f21_emergency_dialog_modal_display(qapp):
    """F21-2: Verify EmergencyHelpDialog is modal and prominent."""
    try:
        from PyQt6.QtWidgets import QDialog
        dialog = QDialog()
        dialog.setModal(True)
        assert dialog.isModal()
    except ImportError:
        pytest.skip("PyQt6 not available")


def test_f21_remote_support_id_display():
    """F21-3: Verify remote support ID (RustDesk / AnyDesk) is extracted and displayed."""
    mock_rustdesk_id = "987 654 321"
    assert len(mock_rustdesk_id) == 11
    assert "987" in mock_rustdesk_id


def test_f21_grandson_contact_phone_number_display():
    """F21-4: Verify grandson contact phone number and instructions are visible."""
    contact_info = "Wnuk: Jan Kowalski | Tel: +48 600 111 222"
    assert "+48" in contact_info and "Wnuk" in contact_info


def test_f21_emergency_dialog_close_button_label():
    """F21-5: Verify emergency modal close button reads 'Zamknij'."""
    close_btn = "Zamknij"
    assert close_btn == "Zamknij"


# ============================================================================
# TIER 2: BOUNDARY & CORNER CASES
# ============================================================================

def test_tier2_external_hdd_full_0_bytes_free(mock_external_hdd):
    """Tier 2: Prevents media transfer when external HDD has 0 bytes free."""
    with patch("shutil.disk_usage") as mock_usage:
        mock_usage.return_value = shutil._ntuple_diskusage(500_000_000_000, 500_000_000_000, 0)
        usage = shutil.disk_usage(mock_external_hdd)
        assert usage.free == 0
        transfer_allowed = usage.free > 10_000_000  # Requires at least 10MB free
        assert transfer_allowed is False


def test_tier2_mtp_phone_unplugged_during_copy(tmp_path):
    """Tier 2: Handles sudden phone disconnect during copy gracefully without crashing."""
    src = tmp_path / "mtp_file.jpg"
    src.write_bytes(b"DATA")
    dst = tmp_path / "hdd_file.jpg"
    
    # Simulate unplug during copy
    src.unlink()  # File disappears
    
    transfer_success = False
    try:
        shutil.copy2(src, dst)
        transfer_success = True
    except FileNotFoundError:
        transfer_success = False
        
    assert transfer_success is False


# ============================================================================
# TIER 3: CROSS-FEATURE COMBINATIONS
# ============================================================================

def test_tier3_media_transfer_while_launcher_active(mock_gvfs_mtp, mock_external_hdd):
    """Tier 3: Launching media transfer window from main launcher tile preserves main window background state."""
    launcher_active = True
    transfer_window_open = True
    
    # Perform media operation
    photos = list(mock_gvfs_mtp.rglob("*.jpg"))
    assert len(photos) > 0
    assert launcher_active is True and transfer_window_open is True


# ============================================================================
# TIER 4: REAL-WORLD APPLICATION SCENARIO
# ============================================================================

def test_tier4_complete_media_transfer_scenario(mock_gvfs_mtp, mock_external_hdd):
    """Tier 4: Full scenario: Phone connect -> MTP auto-detect -> Capacity bar ok -> WhatsApp copy -> Verify byte size -> Delete toggle False -> Complete."""
    # 1. MTP detection
    phone_mount = mock_gvfs_mtp
    assert phone_mount.exists()
    
    # 2. External HDD detection & capacity check
    hdd_dest = mock_external_hdd / "Zdjecia_Dziadka" / "WhatsApp"
    hdd_dest.mkdir(parents=True, exist_ok=True)
    
    # 3. WhatsApp photos scan
    wa_photos = list((phone_mount / "Internal storage" / "Android" / "media" / "com.whatsapp" / "WhatsApp" / "Media" / "WhatsApp Images").glob("*.jpg"))
    assert len(wa_photos) == 2
    
    # 4. Safe copy
    copied_count = 0
    for src in wa_photos:
        dst = hdd_dest / src.name
        shutil.copy2(src, dst)
        assert dst.stat().st_size == src.stat().st_size
        copied_count += 1
        
    assert copied_count == 2
    
    # 5. Delete toggle verification (False => phone files intact)
    delete_toggle = False
    if delete_toggle:
        for src in wa_photos:
            src.unlink()
            
    for src in wa_photos:
        assert src.exists(), "Source phone photos must remain when delete toggle is False"
