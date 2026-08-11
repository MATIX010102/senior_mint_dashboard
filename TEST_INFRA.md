# E2E Test Infrastructure & Methodology — Senior Mint Dashboard

This document describes the test infrastructure, test runner architecture, mock environment, and 4-tier testing methodology for the Senior Mint Dashboard project.

---

## 1. Overview & Framework Stack

The test suite is designed as an opaque-box, requirement-driven E2E test harness using Python's standard `pytest` framework alongside `pytest-qt` and `unittest.mock`.

- **Test Framework**: `pytest` 8.0+
- **Qt GUI Harness**: `pytest-qt` with offscreen QPA platform binding (`QT_QPA_PLATFORM=offscreen`)
- **System Mocks**: `unittest.mock` for hardware detection, GVFS MTP, CUPS/HPLIP, Git, LightDM, and Polkit
- **Target OS**: Linux Mint 22 XFCE 64-bit ("Wilma", Ubuntu 24.04 noble base)

---

## 2. Directory Layout & File Organization

```
tests/
├── __init__.py               # Package initializer
├── conftest.py               # PyQt6 QApplication lifecycle, offscreen setup, hardware & OS mocks
├── test_provisioner.py       # R1 / F01-F06: Root Provisioner & Bulletproof System Lockdown
├── test_launcher.py          # R2 / F07-F14: Senior Dashboard Kiosk Launcher & WebViews
├── test_media_transfer.py    # R3 / F15-F21: Photo & Media Transfer Utility (MTP / HDD)
├── test_updater.py           # R4 / F22-F25: Automated Silent GitHub Self-Update System
└── test_e2e_suite.py         # M5: End-to-End Acceptance Test Suite (Tiers 1-4)
```

---

## 3. Feature Coverage Mapping (F01 - F25)

| Requirement | Module File | Features Covered | Minimum Tier 1 Test Count |
|-------------|-------------|------------------|---------------------------|
| **R1: System Provisioning** | `tests/test_provisioner.py` | F01 (One-Line Provisioner), F02 (Kiosk User Creation), F03 (Security Lockdown), F04 (APT Dependency Install), F05 (Hotkey Suppression), F06 (Polkit UDisks2 Rule) | >= 30 tests |
| **R2: Senior Launcher** | `tests/test_launcher.py` | F07 (PyQt6 Core & Performance), F08 (Wallpaper Slideshow), F09 (Wallpaper Picker GUI), F10 (Date/Time/Weather Widgets), F11 (Hybrid Web Launchers & Senior Nav Bar), F12 (Browser Launcher), F13 (Offline Games), F14 (CUPS Print Shortcut) | >= 40 tests |
| **R3: Media Transfer** | `tests/test_media_transfer.py` | F15 (MTP & HDD Auto-Detect), F16 (Disk Capacity Bar), F17 (Thumbnail Grid Preview), F18 (WhatsApp Presets), F19 (DCIM Presets), F20 (Safe Copy & Delete Toggle), F21 (Emergency Help Button) | >= 35 tests |
| **R4: Self-Updater** | `tests/test_updater.py` | F22 (Systemd User Service), F23 (Silent Git Auto-Pull), F24 (Syntax Check & Rollback), F25 (UI Updater Notification) | >= 20 tests |
| **Acceptance Integration** | `tests/test_e2e_suite.py` | F01 - F25 Integration & Full Senior Session Scenarios | 11 E2E Scenarios |

---

## 4. 4-Tier Test Case Methodology

1. **Tier 1: Feature Coverage**:
   - Comprehensive unit and integration coverage for each individual feature F01 through F25.
   - Enforces >=5 explicit test cases per feature for Requirements R1, R2, R3, R4.

2. **Tier 2: Boundary & Corner Cases**:
   - Empty wallpaper directories, non-image files, corrupted weather JSON caches, disconnected MTP smartphones, 0 byte free space on external HDDs, network offline timeouts during git pull, missing system binaries, and locked source files.

3. **Tier 3: Cross-Feature Combinations**:
   - Concurrent execution scenarios: media transfer while launcher is active, wallpaper picker interaction during active slideshow, printer shortcut execution during WebEngine navigation, background self-updater triggering version banner while user browses web.

4. **Tier 4: Real-World Senior User Scenarios**:
   - Full senior user session simulation: System boot -> launcher init -> wallpaper slideshow -> photo & video transfer from phone to HDD -> Pasjans/Mahjong game launch -> HP printer test page check -> background update check & UI refresh.
   - Benchmarking and verification of hardware constraint targets (< 150 MB RAM, < 2.0s cold boot).

---

## 5. Running the Tests

To execute the complete E2E test suite:

```bash
# Run all tests headlessly
pytest tests/ -v

# Run specific subsystem test modules
pytest tests/test_provisioner.py -v
pytest tests/test_launcher.py -v
pytest tests/test_media_transfer.py -v
pytest tests/test_updater.py -v
pytest tests/test_e2e_suite.py -v
```
