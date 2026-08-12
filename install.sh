#!/usr/bin/env bash
# ==============================================================================
# Senior Mint Dashboard - One-Line Root Provisioner & Bulletproof Lockdown Script
# Target OS: Linux Mint 22 XFCE 64-bit (Ubuntu 24.04 noble base)
# Target Hardware: HP 15t-r100 (Intel Celeron N2840, 4GB RAM, HDD)
# Usage: curl -sSL https://raw.githubusercontent.com/MATIX010102/senior_mint_dashboard/main/install.sh | sudo bash
# ==============================================================================

set -euo pipefail

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}"
export DEBIAN_FRONTEND=noninteractive

LOGFILE="/var/log/senior_mint_dashboard_install.log"
INSTALL_DIR="/home/dziadek/senior_mint_dashboard"
GITHUB_REPO="https://github.com/MATIX010102/senior_mint_dashboard.git"
TARGET_ROOT="${TARGET_ROOT:-}"
DZIADEK_USER="dziadek"
DZIADEK_PASS="dziadek123"

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg"
    echo "$msg" >> "$LOGFILE" 2>/dev/null || true
}

# ------------------------------------------------------------------------------
# 0. Root Check
# ------------------------------------------------------------------------------
if [ "$(id -u)" -ne 0 ]; then
    if [ "${DRY_RUN:-0}" -ne 1 ]; then
        echo "ERROR: install.sh must be executed with root privileges." >&2
        echo "Usage: curl -sSL <URL>/install.sh | sudo bash" >&2
        exit 1
    fi
fi

log "============================================="
log "Senior Mint Dashboard — Installer v2.0"
log "============================================="

user_exists() {
    local username="$1"
    if [ -n "${TARGET_ROOT:-}" ] && [ -f "${TARGET_ROOT}/etc/passwd" ]; then
        grep -q "^${username}:" "${TARGET_ROOT}/etc/passwd" 2>/dev/null
    else
        id "${username}" &>/dev/null
    fi
}

# ------------------------------------------------------------------------------
# 1. APT Dependencies
# ------------------------------------------------------------------------------
log "===> [1/9] Updating package index and installing dependencies..."
if [ "${DRY_RUN:-0}" -eq 1 ]; then
    log "[DRY-RUN] apt-get update && apt-get install ..."
else
    # Enable universe repository
    if ! grep -q "^deb.*universe" /etc/apt/sources.list /etc/apt/sources.list.d/* 2>/dev/null; then
        log "Enabling universe repository..."
        if command -v add-apt-repository >/dev/null 2>&1; then
            add-apt-repository -y universe 2>&1 | tee -a "$LOGFILE" || true
        else
            apt-get update -qq || true
            apt-get install -y software-properties-common 2>&1 | tee -a "$LOGFILE" || true
            add-apt-repository -y universe 2>&1 | tee -a "$LOGFILE" || true
        fi
    fi

    apt-get update -qq || true
    apt-get install -y --no-install-recommends \
        python3-pyqt6 \
        python3-pyqt6.qtwebengine \
        cups \
        hplip \
        gvfs-backends \
        gvfs-fuse \
        mtp-tools \
        rsync \
        python3-gi \
        gir1.2-gtk-3.0 \
        git \
        aisleriot \
        gnome-mahjongg \
        2>&1 | tee -a "$LOGFILE"

    systemctl enable cups --now 2>/dev/null || true
    log "[1/9] Dependencies installed OK."
fi

# ------------------------------------------------------------------------------
# 2. User Account Creation with Password
# ------------------------------------------------------------------------------
log "===> [2/9] Provisioning restricted user '${DZIADEK_USER}'..."
if [ "${DRY_RUN:-0}" -eq 1 ]; then
    log "[DRY-RUN] useradd -m -d /home/${DZIADEK_USER} -s /bin/bash -c 'Dziadek' ${DZIADEK_USER}"
else
    if ! user_exists "${DZIADEK_USER}"; then
        useradd -m -d "/home/${DZIADEK_USER}" -s /bin/bash -c "Dziadek" "${DZIADEK_USER}"
        log "User '${DZIADEK_USER}' created."
    else
        log "User '${DZIADEK_USER}' already exists, skipping creation."
    fi

    # Set password for dziadek
    echo "${DZIADEK_USER}:${DZIADEK_PASS}" | chpasswd
    log "Password set for '${DZIADEK_USER}' => '${DZIADEK_PASS}'"

    # Strip administrative privileges
    for grp in sudo wheel adm lpadmin; do
        if getent group "$grp" >/dev/null 2>&1; then
            gpasswd -d "${DZIADEK_USER}" "$grp" 2>/dev/null || true
        fi
    done
    log "Stripped sudo/wheel/adm/lpadmin from '${DZIADEK_USER}'."

    # Ensure basic hardware access privileges
    for grp in video audio render plugdev cdrom lp; do
        if getent group "$grp" >/dev/null 2>&1; then
            usermod -aG "$grp" "${DZIADEK_USER}" 2>/dev/null || true
        fi
    done
    log "Added '${DZIADEK_USER}' to video/audio/render/plugdev/cdrom/lp groups."
fi

# ------------------------------------------------------------------------------
# 3. Clone Repository to /home/dziadek/senior_mint_dashboard
# ------------------------------------------------------------------------------
log "===> [3/9] Cloning repository to ${INSTALL_DIR}..."
if [ "${DRY_RUN:-0}" -eq 1 ]; then
    log "[DRY-RUN] git clone ${GITHUB_REPO} ${INSTALL_DIR}"
else
    if [ -d "${INSTALL_DIR}/.git" ]; then
        log "Repository already exists at ${INSTALL_DIR}, pulling latest..."
        cd "${INSTALL_DIR}"
        git pull --ff-only origin main 2>&1 | tee -a "$LOGFILE" || true
    else
        rm -rf "${INSTALL_DIR}" 2>/dev/null || true
        git clone "${GITHUB_REPO}" "${INSTALL_DIR}" 2>&1 | tee -a "$LOGFILE"
    fi
    log "[3/9] Repository ready at ${INSTALL_DIR}."
fi

# ------------------------------------------------------------------------------
# 4. LightDM Autologin Configuration
# ------------------------------------------------------------------------------
log "===> [4/9] Setting up LightDM autologin for '${DZIADEK_USER}'..."
LIGHTDM_DIR="${TARGET_ROOT}/etc/lightdm/lightdm.conf.d"
mkdir -p "$LIGHTDM_DIR"
cat << EOF > "${LIGHTDM_DIR}/99-dziadek-kiosk.conf"
[Seat:*]
autologin-user=${DZIADEK_USER}
autologin-user-timeout=0
user-session=xfce
greeter-hide-users=false
EOF
chmod 644 "${LIGHTDM_DIR}/99-dziadek-kiosk.conf"

# Also patch main lightdm.conf if it exists
LIGHTDM_MAIN="${TARGET_ROOT}/etc/lightdm/lightdm.conf"
if [ -f "$LIGHTDM_MAIN" ]; then
    # Remove any existing autologin-user lines
    sed -i '/^autologin-user=/d' "$LIGHTDM_MAIN" 2>/dev/null || true
    sed -i '/^autologin-user-timeout=/d' "$LIGHTDM_MAIN" 2>/dev/null || true
    # Append under [Seat:*] if that section exists
    if grep -q '^\[Seat:\*\]' "$LIGHTDM_MAIN"; then
        sed -i "/^\[Seat:\*\]/a autologin-user=${DZIADEK_USER}\nautologin-user-timeout=0" "$LIGHTDM_MAIN"
    fi
fi
log "[4/9] LightDM autologin configured."

# ------------------------------------------------------------------------------
# 5. Polkit v124 JavaScript Lockdown Rule
# ------------------------------------------------------------------------------
log "===> [5/9] Applying Polkit v124 UDisks2 security lockdown rule..."
POLKIT_DIR="${TARGET_ROOT}/etc/polkit-1/rules.d"
mkdir -p "$POLKIT_DIR"
cat << 'EOF' > "${POLKIT_DIR}/50-dziadek-udisks2-lockdown.rules"
// Restricts user 'dziadek' from disk formatting, partition modification, and system drive tampering.
polkit.addRule(function(action, subject) {
    if (subject.user !== "dziadek") {
        return undefined;
    }
    var actionId = action.id;
    if (actionId.indexOf("org.freedesktop.udisks2.filesystem-format") === 0 ||
        actionId.indexOf("org.freedesktop.udisks2.partition-") === 0 ||
        actionId.indexOf("org.freedesktop.udisks2.modify-device") === 0 ||
        actionId.indexOf("org.freedesktop.udisks2.modify-drive-settings") === 0 ||
        actionId.indexOf("org.freedesktop.udisks2.filesystem-mount-system") === 0 ||
        actionId.indexOf("org.freedesktop.udisks2.filesystem-unmount-others") === 0) {
        return polkit.Result.NO;
    }
    if (actionId.indexOf("org.freedesktop.udisks2.filesystem-mount") === 0 ||
        actionId.indexOf("org.freedesktop.udisks2.filesystem-unmount") === 0 ||
        actionId.indexOf("org.freedesktop.udisks2.eject") === 0 ||
        actionId.indexOf("org.freedesktop.udisks2.power-off-drive") === 0) {
        return polkit.Result.YES;
    }
    return undefined;
});
EOF
chmod 644 "${POLKIT_DIR}/50-dziadek-udisks2-lockdown.rules"
log "[5/9] Polkit lockdown rule installed."

# ------------------------------------------------------------------------------
# 6. XFCE Hotkey Suppression (Ctrl+Alt+T, Alt+F4, Alt+F2)
# ------------------------------------------------------------------------------
log "===> [6/9] Seeding XFCE keyboard shortcut suppression..."
XFCE_SYS_DIR="${TARGET_ROOT}/etc/xdg/xfce4/xfconf/xfce-perchannel-xml"
XFCE_USER_DIR="${TARGET_ROOT}/home/${DZIADEK_USER}/.config/xfce4/xfconf/xfce-perchannel-xml"

mkdir -p "$XFCE_SYS_DIR"
mkdir -p "$XFCE_USER_DIR"

cat << 'EOF' > "${XFCE_SYS_DIR}/xfce4-keyboard-shortcuts.xml"
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfce4-keyboard-shortcuts" version="1.0">
  <property name="commands" type="empty">
    <property name="custom" type="empty">
      <property name="&lt;Primary&gt;&lt;Alt&gt;t" type="string" value=""/>
      <property name="&lt;Alt&gt;F1" type="string" value=""/>
      <property name="&lt;Alt&gt;F2" type="string" value=""/>
      <property name="&lt;Alt&gt;F3" type="string" value=""/>
      <property name="&lt;Primary&gt;&lt;Alt&gt;Escape" type="string" value=""/>
      <property name="&lt;Primary&gt;&lt;Alt&gt;Delete" type="string" value=""/>
      <property name="&lt;Super&gt;" type="string" value=""/>
      <property name="&lt;Super&gt;e" type="string" value=""/>
    </property>
  </property>
  <property name="xfwm4" type="empty">
    <property name="custom" type="empty">
      <property name="&lt;Alt&gt;F4" type="string" value=""/>
      <property name="&lt;Alt&gt;Space" type="string" value=""/>
      <property name="&lt;Alt&gt;Tab" type="string" value=""/>
      <property name="&lt;Alt&gt;Escape" type="string" value=""/>
      <property name="&lt;Alt&gt;F10" type="string" value=""/>
      <property name="&lt;Alt&gt;F9" type="string" value=""/>
      <property name="&lt;Alt&gt;F11" type="string" value=""/>
      <property name="&lt;Super&gt;Tab" type="string" value=""/>
    </property>
  </property>
</channel>
EOF
chmod 644 "${XFCE_SYS_DIR}/xfce4-keyboard-shortcuts.xml"

cp "${XFCE_SYS_DIR}/xfce4-keyboard-shortcuts.xml" "${XFCE_USER_DIR}/xfce4-keyboard-shortcuts.xml"
chmod 644 "${XFCE_USER_DIR}/xfce4-keyboard-shortcuts.xml"

# Disable desktop right-click menu, window list menu, and desktop icons
cat << 'EOF' > "${XFCE_SYS_DIR}/xfce4-desktop.xml"
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfce4-desktop" version="1.0">
  <property name="desktop-menu" type="empty">
    <property name="show" type="bool" value="false"/>
  </property>
  <property name="windowlist-menu" type="empty">
    <property name="show" type="bool" value="false"/>
  </property>
  <property name="desktop-icons" type="empty">
    <property name="style" type="int" value="0"/>
  </property>
</channel>
EOF
chmod 644 "${XFCE_SYS_DIR}/xfce4-desktop.xml"

cp "${XFCE_SYS_DIR}/xfce4-desktop.xml" "${XFCE_USER_DIR}/xfce4-desktop.xml"
chmod 644 "${XFCE_USER_DIR}/xfce4-desktop.xml"

log "[6/9] XFCE hotkeys and desktop access neutralized."

# ------------------------------------------------------------------------------
# 7. Autostart Desktop Entry + Session Script
# ------------------------------------------------------------------------------
log "===> [7/9] Creating autostart entry and session launcher..."
HOME_DZIADEK="${TARGET_ROOT}/home/${DZIADEK_USER}"
mkdir -p "${HOME_DZIADEK}/Obrazki/Tapety"
mkdir -p "${HOME_DZIADEK}/.config/autostart"
mkdir -p "${HOME_DZIADEK}/.config/senior_dashboard"
mkdir -p "${HOME_DZIADEK}/.cache/senior_dashboard/thumbnails"
mkdir -p "${HOME_DZIADEK}/.local/share/applications"

# --- Autostart .desktop file ---
cat << EOF > "${HOME_DZIADEK}/.config/autostart/senior-dashboard.desktop"
[Desktop Entry]
Type=Application
Name=Senior Mint Dashboard
Comment=Senior Launcher Kiosk Dashboard
Exec=/usr/bin/python3 ${INSTALL_DIR}/main.py
Icon=preferences-desktop-wallpaper
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
X-XFCE-Autostart-override=true
StartupNotify=false
Hidden=false
EOF
chmod 644 "${HOME_DZIADEK}/.config/autostart/senior-dashboard.desktop"

# --- Also create a .desktop entry in applications menu ---
cat << EOF > "${HOME_DZIADEK}/.local/share/applications/senior-dashboard.desktop"
[Desktop Entry]
Type=Application
Name=Pulpit Dziadka
Comment=Senior Mint Dashboard - Uruchom pulpit
Exec=/usr/bin/python3 ${INSTALL_DIR}/main.py
Icon=preferences-desktop-wallpaper
Terminal=false
Categories=Utility;System;
StartupNotify=true
EOF
chmod 644 "${HOME_DZIADEK}/.local/share/applications/senior-dashboard.desktop"

# --- Create a launcher script for convenience ---
cat << EOF > "${INSTALL_DIR}/launch.sh"
#!/usr/bin/env bash
# Senior Mint Dashboard Launch Script
# Usage: bash /home/dziadek/senior_mint_dashboard/launch.sh
export DISPLAY=\${DISPLAY:-:0}
export PYTHONPATH="${INSTALL_DIR}:\${PYTHONPATH:-}"
cd "${INSTALL_DIR}"
exec /usr/bin/python3 "${INSTALL_DIR}/main.py" >> "/home/${DZIADEK_USER}/.cache/senior_dashboard/dashboard.log" 2>&1
EOF
chmod +x "${INSTALL_DIR}/launch.sh"

log "[7/9] Autostart .desktop + launch.sh created."

# ------------------------------------------------------------------------------
# 8. Systemd User Self-Updater Timer
# ------------------------------------------------------------------------------
log "===> [8/9] Setting up systemd user self-updater service..."
SYSTEMD_USER_DIR="${HOME_DZIADEK}/.config/systemd/user"
mkdir -p "${SYSTEMD_USER_DIR}"

cat << EOF > "${SYSTEMD_USER_DIR}/senior-mint-updater.service"
[Unit]
Description=Senior Mint Dashboard Silent Self-Updater
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=${INSTALL_DIR}
ExecStart=/usr/bin/python3 ${INSTALL_DIR}/senior_mint_dashboard/updater/update_service.py
StandardOutput=append:${HOME_DZIADEK}/.cache/senior_dashboard/updater.log
StandardError=append:${HOME_DZIADEK}/.cache/senior_dashboard/updater.log

[Install]
WantedBy=default.target
EOF

cat << EOF > "${SYSTEMD_USER_DIR}/senior-mint-updater.timer"
[Unit]
Description=Timer for Senior Mint Dashboard Self-Updater

[Timer]
OnBootSec=5min
OnUnitActiveSec=4h
Persistent=true

[Install]
WantedBy=timers.target
EOF

chmod 644 "${SYSTEMD_USER_DIR}/senior-mint-updater.service"
chmod 644 "${SYSTEMD_USER_DIR}/senior-mint-updater.timer"

# Enable the systemd timer for dziadek user (requires loginctl enable-linger)
if [ "${DRY_RUN:-0}" -ne 1 ]; then
    loginctl enable-linger "${DZIADEK_USER}" 2>/dev/null || true
    # Enable the timer as dziadek
    su - "${DZIADEK_USER}" -c "systemctl --user daemon-reload" 2>/dev/null || true
    su - "${DZIADEK_USER}" -c "systemctl --user enable senior-mint-updater.timer" 2>/dev/null || true
    su - "${DZIADEK_USER}" -c "systemctl --user start senior-mint-updater.timer" 2>/dev/null || true
fi
log "[8/9] Systemd auto-updater timer created and enabled."

# ------------------------------------------------------------------------------
# 9. Final Ownership & Permissions
# ------------------------------------------------------------------------------
log "===> [9/9] Setting final permissions and ownership..."
if [ "${DRY_RUN:-0}" -eq 1 ]; then
    log "[DRY-RUN] chown -R ${DZIADEK_USER}:${DZIADEK_USER} ${HOME_DZIADEK}"
else
    if user_exists "${DZIADEK_USER}"; then
        chown -R "${DZIADEK_USER}:${DZIADEK_USER}" "${HOME_DZIADEK}"
        # Make sure INSTALL_DIR is owned by dziadek (for git pull updates)
        chown -R "${DZIADEK_USER}:${DZIADEK_USER}" "${INSTALL_DIR}"
    fi
fi
log "[9/9] Ownership and permissions fixed."

# ==============================================================================
log "============================================="
log "  INSTALLATION COMPLETE!"
log "============================================="
log ""
log "  User:       ${DZIADEK_USER}"
log "  Password:   ${DZIADEK_PASS}"
log "  Dashboard:  ${INSTALL_DIR}/main.py"
log "  Autostart:  ${HOME_DZIADEK}/.config/autostart/senior-dashboard.desktop"
log "  Autologin:  ${LIGHTDM_DIR}/99-dziadek-kiosk.conf"
log "  Updater:    systemd user timer (every 4h)"
log "  Log file:   ${LOGFILE}"
log ""
log "  Reboot now to test autologin + dashboard autostart:"
log "    sudo reboot"
log "============================================="
