# TEST READY — Senior Mint Dashboard E2E Test Suite

**Status**: READY  
**Date**: 2026-08-11  
**Project**: Senior Mint Dashboard (Linux Mint 22 XFCE 64-bit Kiosk Environment)  
**Target Hardware**: HP 15t-r100 (Intel Celeron N2840, 4GB RAM, HDD)  

---

## E2E Test Suite Summary

The complete, requirement-driven opaque-box E2E test suite for the Senior Mint Dashboard project has been fully authored and published in the `tests/` directory.

### Created Test Components

1. **`tests/conftest.py`**:
   - PyQt6 `QApplication` lifecycle fixture configured for offscreen rendering (`QT_QPA_PLATFORM=offscreen`).
   - Isolated workspace & configuration directory fixtures (`tmp_path`).
   - Mock fixtures for GVFS MTP smartphone mounts (`/run/user/<UID>/gvfs/mtp:host=*`), External HDD mounts (`/media/dziadek/EXT_HDD`), CUPS / HPLIP printing services, Git CLI, systemd user services, LightDM kiosk config, and Polkit JS rules.

2. **`tests/test_provisioner.py` (R1 / F01-F06)**:
   - 30+ test cases covering script execution (`install.sh`), bash error flags (`set -euo pipefail`), `dziadek` user creation, LightDM autologin kiosk config, group stripping (`sudo`, `wheel`, `adm`, `lpadmin`), APT dependency installation, XFCE hotkey suppression (`Ctrl+Alt+T`, `Alt+F4`, `Alt+F2`), and Polkit UDisks2 lockdown rule.

3. **`tests/test_launcher.py` (R2 / F07-F14)**:
   - 40+ test cases covering 1366x768 kiosk resolution, cold boot time benchmark (<2s), RAM memory footprint target (<150MB), dynamic wallpaper slideshow (`~/Obrazki/Tapety`), wallpaper picker GUI ("Zmień tapetę rodzinną"), Date/Time/Weather widgets (Date 22pt, Time 54pt, Weather 20pt with JSON cache fallback), embedded WebViews with Senior Nav Bar (Domowa, Odśwież, Powiększ czcionkę, Zamknij), standard browser launcher, offline Solitaire & Mahjong games, and CUPS HP printer shortcut.

4. **`tests/test_media_transfer.py` (R3 / F15-F21)**:
   - 35+ test cases covering smartphone MTP auto-detection, external HDD mount detection, visual disk capacity progress bar (green/amber/red zones), async thumbnail grid preview, WhatsApp photo/video presets, DCIM photo/video presets, safe byte-by-byte copy protocol, post-copy deletion toggle default (FALSE/Keep), and Emergency "Poproś wnuka o pomoc" helper modal with RustDesk/AnyDesk ID display.

5. **`tests/test_updater.py` (R4 / F22-F25)**:
   - 20+ test cases covering systemd user service & timer (`senior-mint-updater.service` & `.timer`), silent background `git pull --ff-only`, `py_compile` syntax verification guard, `git reset --hard ORIG_HEAD` rollback, `version.json` file state update, and launcher top-bar notification banner.

6. **`tests/test_e2e_suite.py` (M5 Acceptance Suite)**:
   - 11 comprehensive End-to-End acceptance scenarios verifying full integration across all features F01 through F25 and complete real-world senior user session workflows.

---

## 4-Tier Test Case Distribution

| Tier Level | Focus Area | Coverage Status |
|------------|------------|-----------------|
| **Tier 1** | Feature Coverage (F01 - F25) | >= 5 tests per feature for R1, R2, R3, R4 (125+ tests total) |
| **Tier 2** | Boundary & Corner Cases | Empty folders, missing mounts, disconnected MTP, 0 byte free space, network offline, corrupted JSON, locked files |
| **Tier 3** | Cross-Feature Combinations | Concurrent slideshow & picker, webview browsing during update check, media transfer while launcher active, printing during slideshow |
| **Tier 4** | Real-World Application Scenarios | Complete senior user session workflow & hardware constraint benchmarks (<150MB RAM, <2s cold boot) |

---

## Execution Command

```bash
pytest tests/ -v
```

All test files are self-contained, isolated, and fully executable using standard `pytest` and `pytest-qt`.
