# Original User Request

## Initial Request — 2026-08-11T16:07:19Z

Ultra-lightweight, locked-down senior-friendly custom desktop launcher & system environment for Linux Mint 22 XFCE 64-bit on low-end hardware (Intel Celeron N2840, 4GB RAM, HDD). Features automatic system provisioner script (`curl ... | sudo bash`), bulletproof non-admin user lockdown, family photo wallpaper slideshow, enlarged widgets (bank, Gmail, Onet mail, weather, games), phone-to-external-HDD media transfer tool, and legacy HP printer integration.

Working directory: ~/teamwork_projects/senior_mint_dashboard
Integrity mode: development
Target Hardware: HP 15t-r100 (Intel Celeron N2840 @ 2.16 GHz, 4GB RAM, HDD) - Requires lightweight stack (Python 3 + PyQt6 / GTK / QtWebEngine).

## Requirements

### R1. One-Line Root Provisioner & Bulletproof System Lockdown
Single command installation: `curl -sSL https://raw.githubusercontent.com/USER/senior_mint_dashboard/main/install.sh | sudo bash`:
- Creates dedicated restricted user `dziadek` with autologin via LightDM / systemd kiosk.
- Strips `sudo`, wheel, and administrative privileges from `dziadek`.
- Installs dependencies (`python3-pyqt6`, `python3-pyqt6.qtwebengine`, `cups`, `hplip`, `gvfs-backends`, `mtp-tools`, `rsync`, `pygobject`).
- Disables terminal hotkeys (Ctrl+Alt+T), Alt+F4, Alt+F2, and restricts polkit udisks2 permissions so the senior user cannot format disks or modify system partitions.

### R2. Lightweight Senior Dashboard Launcher (Python + PyQt6)
Modern, high-contrast, minimalist launcher optimized for 1366x768 / HD screens on Intel Celeron CPU:
- Dynamic family photo wallpaper background with slideshow support from `~/Obrazki/Tapety` and simple "Zmień tapetę rodzinną" GUI picker.
- Large, clear Date, Time, and Weather widgets.
- Hybrid Web Launchers: Embedded dedicated WebViews with simplified navigation header (Domowa, Odśwież, Powiększ czcionkę) for Bank, Gmail, Onet Poczta, and Insurance; plus standard Browser launcher button.
- Classic pre-installed offline games: Solitaire (Pasjans) and Mahjong.
- One-click print shortcut utilizing CUPS/HPLIP for legacy HP printers.

### R3. Advanced Senior Photo & Media Transfer Utility
Dedicated photo & video transfer module for smartphones (Android/iOS via MTP/gvfs) and mounted external hard drive:
- Auto-detect phone and external HDD mount points.
- Visual disk capacity bar showing remaining free space on the external hard drive.
- Thumbnail grid preview of photos/videos detected on the connected phone.
- Action presets:
  - "Skopiuj zdjęcia z WhatsApp na dysk" (with toggle: "Usuń z telefonu po skopiowaniu" vs "Zostaw w telefonie").
  - "Skopiuj filmy z WhatsApp na dysk".
  - "Skopiuj zdjęcia z aparatu (DCIM) na dysk".
  - "Skopiuj filmy z aparatu (DCIM) na dysk".
- Emergency "Poproś wnuka o pomoc" helper button.

### R4. Automated Silent GitHub Self-Update System
Background service that checks GitHub repo releases/updates, auto-pulls changes without requiring password entry or terminal interaction from `dziadek`, and updates the launcher cleanly.

## Acceptance Criteria

### Security & Provisioning
- [ ] Executing `sudo bash install.sh` creates user `dziadek`, sets up LightDM kiosk autostart, and locks down sudo/terminal access.
- [ ] Polkit policy prevents formatting, partitioning, or unmounting critical drives.

### Launcher UI & Performance
- [ ] UI footprint < 150 MB RAM with fast startup (< 2s) on Intel Celeron N2840 + HDD.
- [ ] Wallpaper slideshow cycles images from `~/Obrazki/Tapety` smoothly.
- [ ] Embedded WebViews display Gmail, Onet, Bank, and Insurance with simplified navigation.
- [ ] Solitaire and Mahjong launch cleanly from dashboard icons.

### Media Transfer & Utilities
- [ ] Media transfer detects phone via MTP, previews thumbnails, and copies WhatsApp/DCIM photos to external HDD.
- [ ] Free disk space on external HDD is accurately calculated and displayed.
- [ ] CUPS / HPLIP legacy HP printer integration works via print shortcut.

### Self-Updater
- [ ] System checks GitHub on boot/timer and updates application files automatically.
