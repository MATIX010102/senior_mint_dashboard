"""
Dynamic Photo Wallpaper Slideshow & Picker Engine for Senior Mint Dashboard.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Optional
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QFileDialog, QLabel, QWidget

from senior_mint_dashboard.config import (
    WALLPAPER_DIR, SLIDESHOW_INTERVAL_MS, FALLBACK_BACKGROUND_COLOR
)

logger = logging.getLogger("SeniorMintDashboard")


class WallpaperManager(QLabel):
    """
    Manages background photo wallpaper slideshow cycling from ~/Obrazki/Tapety
    and provides GUI photo picker dialog integration.
    """
    wallpaper_changed = pyqtSignal(str)

    VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    DEFAULT_FALLBACK_COLOR = FALLBACK_BACKGROUND_COLOR
    DEFAULT_INTERVAL_MS = SLIDESHOW_INTERVAL_MS

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        wallpaper_dir: Optional[Path] = None,
        interval_ms: int = DEFAULT_INTERVAL_MS
    ):
        super().__init__(parent)
        self.wallpaper_dir = wallpaper_dir or WALLPAPER_DIR
        self.interval_ms = interval_ms
        self.images: List[Path] = []
        self.current_index: int = 0

        self.setScaledContents(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.timer = QTimer(self)
        self.timer.setInterval(self.interval_ms)
        self.timer.timeout.connect(self.next_wallpaper)

        self.scan_wallpapers()
        if self.images:
            self._set_wallpaper_index(0)
        else:
            self._apply_fallback_color()

    def scan_wallpapers(self) -> List[Path]:
        """Scans ~/Obrazki/Tapety for supported image files (.jpg, .jpeg, .png, .webp)."""
        if not self.wallpaper_dir.exists():
            try:
                self.wallpaper_dir.mkdir(parents=True, exist_ok=True)
            except OSError:
                pass
            self.images = []
            return self.images

        self.images = sorted([
            p for p in self.wallpaper_dir.glob("*")
            if p.is_file() and p.suffix.lower() in self.VALID_EXTENSIONS
        ])
        return self.images

    def start_slideshow(self) -> None:
        """Starts periodic slideshow cycling."""
        self.scan_wallpapers()
        if self.images:
            self.timer.start()
            self._emit_current()

    def stop_slideshow(self) -> None:
        """Stops slideshow timer."""
        self.timer.stop()

    def next_wallpaper(self) -> str:
        """Cycles to next wallpaper image in sequence, looping back to 0."""
        self.scan_wallpapers()
        if not self.images:
            self._apply_fallback_color()
            self.wallpaper_changed.emit("")
            return ""

        self.current_index = (self.current_index + 1) % len(self.images)
        return self._set_wallpaper_index(self.current_index)

    def get_current_wallpaper_path(self) -> Optional[str]:
        """Returns path of current wallpaper or None if fallback color active."""
        if not self.images or self.current_index >= len(self.images):
            return None
        return str(self.images[self.current_index])

    def set_active_wallpaper(self, image_path: Path) -> None:
        """Sets active wallpaper immediately to the specified image path."""
        self.scan_wallpapers()
        try:
            resolved_path = Path(image_path).resolve()
            for idx, p in enumerate(self.images):
                if p.resolve() == resolved_path:
                    self.current_index = idx
                    self._set_wallpaper_index(idx)
                    return
            # If image was not in scanned list, add it
            self.images.append(Path(image_path))
            self.current_index = len(self.images) - 1
            self._set_wallpaper_index(self.current_index)
        except Exception:
            self._emit_current()

    def add_and_set_wallpaper(self, file_path: str or Path) -> Optional[str]:
        """Copies file to ~/Obrazki/Tapety, rescans, and sets active wallpaper immediately."""
        src_path = Path(file_path)
        if not src_path.exists() or src_path.suffix.lower() not in self.VALID_EXTENSIONS:
            return None

        if not self.wallpaper_dir.exists():
            self.wallpaper_dir.mkdir(parents=True, exist_ok=True)

        dest_path = self.wallpaper_dir / src_path.name
        try:
            if src_path.resolve() != dest_path.resolve():
                logger.info(f"Copying new family wallpaper: from '{src_path}' to '{dest_path}'")
                shutil.copy(src_path, dest_path)
        except Exception as e:
            logger.error(f"Copying wallpaper failed: {e}", exc_info=True)
            return None

        self.set_active_wallpaper(dest_path)
        return str(dest_path)

    def open_picker(self, parent_widget: Optional[QWidget] = None) -> Optional[str]:
        """
        Opens QFileDialog with 'Zmień tapetę rodzinną' title, copies selected image into ~/Obrazki/Tapety,
        rescans pool, and sets wallpaper immediately.
        """
        dialog_title = "Zmień tapetę rodzinną"
        file_filter = "Obrazy (*.jpg *.jpeg *.png *.webp)"

        parent = parent_widget or self
        file_path, _ = QFileDialog.getOpenFileName(
            parent,
            dialog_title,
            str(Path.home()),
            file_filter
        )

        if not file_path:
            return None

        return self.add_and_set_wallpaper(file_path)

    def _set_wallpaper_index(self, index: int) -> str:
        if 0 <= index < len(self.images):
            img_path = self.images[index]
            str_path = str(img_path)
            pixmap = QPixmap(str_path)
            if not pixmap.isNull():
                self.setStyleSheet("")
                self.setPixmap(pixmap)
            else:
                self._apply_fallback_color()
            self.wallpaper_changed.emit(str_path)
            return str_path
        else:
            self._apply_fallback_color()
            self.wallpaper_changed.emit("")
            return ""

    def _apply_fallback_color(self) -> None:
        self.clear()
        self.setStyleSheet(f"background-color: {self.DEFAULT_FALLBACK_COLOR};")

    def _emit_current(self) -> None:
        path = self.get_current_wallpaper_path()
        self.wallpaper_changed.emit(path or "")
