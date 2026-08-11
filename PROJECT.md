# Project Specification: Senior Mint Dashboard

Target Platform: Linux Mint 22 XFCE 64-bit ("Wilma", Ubuntu 24.04 noble base)  
Target Hardware: HP 15t-r100 (Intel Celeron N2840 @ 2.16 GHz, 4GB RAM, 500GB HDD)  
Workspace Root: `c:\Users\matig\Documents\Porgram dashbord dla dziadka`

---

## Architecture

The Senior Mint Dashboard is an integrated, low-footprint desktop environment and application suite designed for senior users (`dziadek`). It consists of four primary subsystems:

1. **System Provisioning & Bulletproof Lockdown (`install.sh`)**:
   - Single-command root provisioner (`curl -sSL ... | sudo bash`).
   - Dedicated restricted user `dziadek` (no sudo, no wheel, no lpadmin).
   - LightDM autologin kiosk session configuration (`/etc/lightdm/lightdm.conf.d/99-dziadek-kiosk.conf`).
   - Polkit v124+ JavaScript security lockdown (`/etc/polkit-1/rules.d/50-dziadek-udisks2-lockdown.rules`).
   - Neutralization of terminal hotkeys (`Ctrl+Alt+T`, `Alt+F4`, `Alt+F2`) via XFCE shortcut XML configuration.
   - Non-interactive APT dependency installer (`python3-pyqt6`, `python3-pyqt6.qtwebengine`, `cups`, `hplip`, `gvfs-backends`, `mtp-tools`, `rsync`, `python3-gi`).

2. **Lightweight Senior Dashboard Launcher (`senior_mint_dashboard/launcher/`)**:
   - Modular Python 3 + PyQt6 application optimized for Celeron CPU (<150MB RAM, <2s cold boot).
   - High-contrast 1366x768 desktop grid with wallpaper background.
   - Dynamic photo wallpaper slideshow cycling images from `~/Obrazki/Tapety` with simple GUI wallpaper picker (`QFileDialog`).
   - Senior widgets: Large Date (22pt), Time (54pt), and Weather (20pt) with offline JSON cache fallback.
   - Hybrid Web Launchers: Dedicated embedded WebViews with senior navigation header (Domowa, Odśwież, Powiększ czcionkę, Zamknij) for Bank, Gmail, Onet Poczta, and Insurance; standard Browser launcher.
   - Offline Classic Games: Launchers for Solitaire (`aisleriot`) and Mahjong (`gnome-mahjongg`) with fallback web implementations.
   - One-click Printer Shortcut: CUPS / HPLIP integration for legacy HP printers.

3. **Advanced Photo & Media Transfer Utility (`senior_mint_dashboard/media_transfer/`)**:
   - MTP Smartphone auto-detection (`/run/user/<UID>/gvfs/mtp:host=*`) & External HDD mount auto-detection (`/media/dziadek/*`).
   - Disk space capacity bar widget (`shutil.disk_usage`) with high-contrast color zones (green/amber/red).
   - Non-blocking async media scanner (`QThread`) and thumbnail generator (`QThreadPool` + `QImageReader` pre-scaled decoding) with thumbnail caching (`~/.cache/senior_dashboard/thumbnails/`).
   - Action presets: WhatsApp Photos, WhatsApp Videos, DCIM Photos, DCIM Videos.
   - Atomic safe copy protocol with mandatory file size verification before optional post-copy deletion (toggle: "Usuń z telefonu po skopiowaniu", defaulting to FALSE/Keep).
   - Emergency "Poproś wnuka o pomoc" helper dialog with RustDesk / AnyDesk remote ID status and contact details.

4. **Automated Silent GitHub Self-Update System (`senior_mint_dashboard/updater/`)**:
   - Unprivileged systemd user service & timer (`~/.config/systemd/user/senior-mint-updater.service` & `.timer`).
   - Periodic silent git pull (`git pull --ff-only origin main`).
   - Automatic Python syntax verification check (`py_compile`) with automatic rollback (`git reset --hard ORIG_HEAD`) on failure.
   - Dynamic UI hot-reload notification tag (`~/.config/senior_dashboard/version.json`).

---

## Feature Inventory

Every feature requested in `ORIGINAL_REQUEST.md` is enumerated and assigned to a milestone:

| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| F01 | One-Line Provisioner | Single command `curl ... | sudo bash` execution with `set -euo pipefail` | M1 | R1 |
| F02 | Kiosk User Creation | Create user `dziadek`, set up LightDM autologin kiosk | M1 | R1 |
| F03 | Security Lockdown | Strip `sudo`, `wheel`, `adm`, `lpadmin` from `dziadek` | M1 | R1 |
| F04 | APT Dependency Install | Install `python3-pyqt6`, `python3-pyqt6.qtwebengine`, `cups`, `hplip`, `gvfs-backends`, `mtp-tools`, `rsync`, `python3-gi` | M1 | R1 |
| F05 | Hotkey Suppression | Disable `Ctrl+Alt+T`, `Alt+F4`, `Alt+F2` in XFCE keybindings XML | M1 | R1 |
| F06 | Polkit UDisks2 Rule | Block format, partition modify/delete; allow removable media mounts | M1 | R1 |
| F07 | PyQt6 Launcher Core | Low-memory Python 3 + PyQt6 1366x768 launcher grid (<150MB RAM, <2s boot) | M2 | R2 |
| F08 | Wallpaper Slideshow | Dynamic wallpaper background cycling from `~/Obrazki/Tapety` | M2 | R2 |
| F09 | Wallpaper Picker GUI | Simple "Zmień tapetę rodzinną" GUI file picker dialog | M2 | R2 |
| F10 | Date/Time/Weather | Large typography Date (22pt), Time (54pt), Weather (20pt) widgets | M2 | R2 |
| F11 | Hybrid Web Launchers | Embedded WebViews with senior nav bar (Domowa, Odśwież, Powiększ czcionkę) for Bank, Gmail, Onet, Insurance | M2 | R2 |
| F12 | Browser Launcher | Process launcher button for standard system browser | M2 | R2 |
| F13 | Offline Games | Launchers for Solitaire (Pasjans) and Mahjong | M2 | R2 |
| F14 | CUPS Print Shortcut | One-click HP printer status & test print shortcut | M2 | R2 |
| F15 | MTP & HDD Auto-Detect | Auto-detect smartphone MTP/gvfs mounts and external HDD mounts | M3 | R3 |
| F16 | Disk Capacity Bar | High-contrast visual free space progress bar for external HDD | M3 | R3 |
| F17 | Thumbnail Grid Preview | Non-blocking async media scanner and thumbnail preview grid | M3 | R3 |
| F18 | WhatsApp Presets | "Skopiuj zdjęcia z WhatsApp" and "Skopiuj filmy z WhatsApp" preset tiles | M3 | R3 |
| F19 | DCIM Presets | "Skopiuj zdjęcia z aparatu" and "Skopiuj filmy z aparatu" preset tiles | M3 | R3 |
| F20 | Safe Copy & Delete Toggle | Safe copy engine with size verification and optional deletion toggle | M3 | R3 |
| F21 | Emergency Help Button | "Poproś wnuka o pomoc" helper modal with grandson contact & remote ID | M3 | R3 |
| F22 | Systemd User Service | `senior-mint-updater.service` and `.timer` user unit definitions | M4 | R4 |
| F23 | Silent Git Auto-Pull | Background `git pull --ff-only` check without sudo or password prompts | M4 | R4 |
| F24 | Syntax Check & Rollback | `py_compile` syntax verification guard with `git reset --hard` rollback | M4 | R4 |
| F25 | UI Updater Notification | Version tag update notifying launcher UI of new release | M4 | R4 |
| F26 | E2E Acceptance Testing | Tiers 1-4 full test suite execution + Tier 5 adversarial coverage hardening | M5 | Acceptance |

---

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Root Provisioner & Bulletproof Lockdown | `install.sh`, LightDM autologin, Polkit JS rules, XFCE hotkey XML, APT dependencies | None | DONE |
| M2 | Lightweight Senior Dashboard Launcher | PyQt6 launcher core, slideshow, wallpaper picker, widgets, WebViews, games, CUPS shortcut | M1 | DONE |
| M3 | Advanced Photo & Media Transfer Utility | MTP/gvfs & HDD detection, capacity bar, thumbnail grid, presets, safe copy engine, emergency dialog | M1, M2 | DONE |
| M4 | Automated Silent GitHub Self-Update System | Systemd user service/timer, git pull updater script, syntax check, rollback engine | M1, M2 | DONE |
| M5 | Final Integration & E2E Acceptance Testing | E2E test suite pass (Tiers 1-4) + Tier 5 Adversarial Coverage Hardening | M1, M2, M3, M4 | DONE |

---

## Interface Contracts

### 1. Provisioner ↔ Launcher Contract
- `install.sh` provisions code to `/opt/senior_mint_dashboard` (or clones repository to `/home/dziadek/senior_mint_dashboard`).
- `install.sh` creates autostart file `/home/dziadek/.config/autostart/senior-dashboard.desktop` invoking `/usr/bin/python3 /home/dziadek/senior_mint_dashboard/main.py`.
- `install.sh` creates default wallpaper directory `/home/dziadek/Obrazki/Tapety`.

### 2. Launcher ↔ Media Transfer Contract
- `launcher/main.py` imports `media_transfer.ui.transfer_window.MediaTransferWindow`.
- "Zdjęcia i Filmy" tile in launcher invokes `MediaTransferWindow.show()`.
- Emergency help button in launcher header invokes `help_dialog.EmergencyHelpDialog.show()`.

### 3. Launcher ↔ Self-Updater Contract
- Self-updater writes version state to `~/.config/senior_dashboard/version.json`.
- Launcher watches `~/.config/senior_dashboard/version.json` via `QFileSystemWatcher`.
- Upon file modification, launcher displays a senior-friendly top-bar notification banner (`[ ℹ️ Zaktualizowano program. Kliknij Odśwież, aby wczytać nowości. ]`).

---

## Code Layout

```
.
├── ORIGINAL_REQUEST.md
├── PROJECT.md
├── install.sh                          # Root Provisioner & Lockdown Script (M1)
├── main.py                             # Main Application Entry Point
├── senior_mint_dashboard/              # Python Package Root
│   ├── __init__.py
│   ├── config.py                       # Global Constants & Senior UI Design Tokens
│   ├── launcher/                       # Milestone M2 Subsystem
│   │   ├── __init__.py
│   │   ├── main_window.py              # Main 1366x768 Kiosk Dashboard Window
│   │   ├── grid_layout.py              # High-contrast Senior Tile Grid
│   │   ├── wallpaper_manager.py        # Slideshow Engine & QFileDialog Wallpaper Picker
│   │   ├── widgets/
│   │   │   ├── __init__.py
│   │   │   ├── clock_widget.py         # 54pt Time / 22pt Date Widget
│   │   │   ├── weather_widget.py       # 20pt Weather Widget with offline JSON cache
│   │   │   └── printer_widget.py       # One-click CUPS/HPLIP Printer Shortcut
│   │   ├── webview/
│   │   │   ├── __init__.py
│   │   │   ├── browser_window.py       # Embedded QtWebEngine Window with Senior Nav Header
│   │   │   └── senior_nav_bar.py       # (Domowa, Odśwież, Powiększ czcionkę, Zamknij)
│   │   └── games/
│   │       ├── __init__.py
│   │       └── game_launcher.py        # Solitaire & Mahjong process launcher / web fallback
│   ├── media_transfer/                 # Milestone M3 Subsystem
│   │   ├── __init__.py
│   │   ├── detector.py                 # MTP Smartphone & External HDD Auto-Detector
│   │   ├── storage.py                  # shutil.disk_usage Capacity Calculator
│   │   ├── scanner.py                  # Async QThread Media Scanner
│   │   ├── thumbnail.py                # Async Thumbnail Generator & Disk Cache
│   │   ├── presets.py                  # WhatsApp & DCIM Path Resolvers
│   │   ├── copier.py                   # Safe Copy Engine with Byte Size Verification
│   │   ├── remover.py                  # Safe Post-Copy Source File Deletion
│   │   └── ui/
│   │       ├── __init__.py
│   │       ├── transfer_window.py       # Main Media Transfer Dialog
│   │       ├── capacity_bar.py          # High-contrast QProgressBar Disk Widget
│   │       ├── thumbnail_grid.py        # QListWidget Preview Grid
│   │       ├── preset_tiles.py          # Action Preset Selector Tiles
│   │       └── help_dialog.py           # Emergency "Poproś wnuka o pomoc" Modal
│   └── updater/                        # Milestone M4 Subsystem
│       ├── __init__.py
│       ├── git_client.py               # Subprocess Git CLI Wrapper
│       ├── update_service.py           # Update Checker, Pull, Syntax Guard & Rollback
│       ├── installer.py                # Systemd User Unit Auto-Installer
│       └── assets/
│           ├── senior-mint-updater.service
│           └── senior-mint-updater.timer
└── tests/                              # Dual Track E2E & Unit Test Suite
    ├── __init__.py
    ├── conftest.py                     # pytest-qt and mock fixtures
    ├── test_provisioner.py             # M1 Install & Lockdown Tests
    ├── test_launcher.py                # M2 Launcher UI & WebEngine Tests
    ├── test_media_transfer.py          # M3 Media Transfer & MTP Tests
    ├── test_updater.py                 # M4 Self-Updater Tests
    └── test_e2e_suite.py               # M5 E2E Acceptance Test Runner (Tiers 1-4)
```

---

## Verification & Acceptance Criteria

1. **Security & Provisioning (M1)**:
   - `id dziadek` confirms absence of `sudo`, `wheel`, `adm`, `lpadmin` groups.
   - `/etc/lightdm/lightdm.conf.d/99-dziadek-kiosk.conf` confirms autologin-user=dziadek.
   - Polkit rule `/etc/polkit-1/rules.d/50-dziadek-udisks2-lockdown.rules` syntax is valid.
   - XFCE shortcut query confirms suppression of `Ctrl+Alt+T`, `Alt+F4`, `Alt+F2`.

2. **Launcher UI & Performance (M2)**:
   - Memory footprint < 150 MB RAM at idle.
   - Cold startup time < 2.0 seconds on Celeron N2840 CPU.
   - Wallpaper slideshow cycles images from `~/Obrazki/Tapety`.
   - WebViews (Bank, Gmail, Onet, Insurance) render cleanly with Senior Nav Bar.
   - Solitaire and Mahjong launch correctly.

3. **Media Transfer (M3)**:
   - Phone MTP mount and external HDD auto-detected.
   - Visual disk capacity bar displays free space accurately.
   - Thumbnail grid previews media files asynchronously without GUI lag.
   - Action presets copy files to HDD with byte-size verification before optional deletion.
   - Emergency helper dialog displays grandson contact and remote support status.

4. **Self-Updater (M4)**:
   - Systemd user service/timer active under `dziadek`.
   - `git pull --ff-only` pulls updates cleanly.
   - Failed syntax check triggers `git reset --hard ORIG_HEAD` rollback.
