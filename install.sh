#!/usr/bin/env bash
# ==============================================================================
# Senior Mint Dashboard - One-Line Root Provisioner & Bulletproof Lockdown Script
# Milestone M1 Implementation
# Target OS: Linux Mint 22 XFCE 64-bit (Ubuntu 24.04 noble base)
# Target Hardware: HP 15t-r100 (Intel Celeron N2840, 4GB RAM, HDD)
# Usage: curl -sSL https://raw.githubusercontent.com/USER/senior_mint_dashboard/main/install.sh | sudo bash
# ==============================================================================

set -euo pipefail

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}"

# ------------------------------------------------------------------------------
# 1. Root Execution & Environment Check
# ------------------------------------------------------------------------------
if [ "$(id -u)" -ne 0 ]; then
    if [ "${DRY_RUN:-0}" -ne 1 ]; then
        echo "ERROR: install.sh must be executed with root privileges." >&2
        echo "Usage: curl -sSL <URL>/install.sh | sudo bash" >&2
        exit 1
    fi
fi

export DEBIAN_FRONTEND=noninteractive
TARGET_ROOT="${TARGET_ROOT:-}"

user_exists() {
    local username="$1"
    if [ -n "${TARGET_ROOT:-}" ] && [ -f "${TARGET_ROOT}/etc/passwd" ]; then
        grep -q "^${username}:" "${TARGET_ROOT}/etc/passwd" 2>/dev/null
    else
        id "${username}" &>/dev/null
    fi
}

echo "==> [1/7] Updating package index and installing dependencies..."
if [ "${DRY_RUN:-0}" -eq 1 ]; then
    echo "[DRY-RUN] apt-get update -qq"
    echo "[DRY-RUN] apt-get install -y --no-install-recommends python3-pyqt6 python3-pyqt6.qtwebengine cups hplip gvfs-backends mtp-tools rsync python3-gi gir1.2-gtk-3.0"
else
    apt-get update -qq || true
    apt-get install -y --no-install-recommends \
        python3-pyqt6 \
        python3-pyqt6.qtwebengine \
        cups \
        hplip \
        gvfs-backends \
        mtp-tools \
        rsync \
        python3-gi \
        gir1.2-gtk-3.0

    systemctl enable cups --now || true
fi

# ------------------------------------------------------------------------------
# 2. Restricted User Lifecycle Management
# ------------------------------------------------------------------------------
echo "==> [2/7] Provisioning restricted user 'dziadek'..."
if [ "${DRY_RUN:-0}" -eq 1 ]; then
    echo "[DRY-RUN] useradd -m -d /home/dziadek -s /bin/bash -c 'Dziadek' dziadek"
else
    if ! user_exists "dziadek"; then
        useradd -m -d "/home/dziadek" -s /bin/bash -c "Dziadek" dziadek
    fi

    # Strip administrative privileges
    for grp in sudo wheel adm lpadmin; do
        if getent group "$grp" >/dev/null 2>&1; then
            gpasswd -d dziadek "$grp" 2>/dev/null || true
        fi
    done

    # Ensure basic hardware access privileges
    for grp in video audio render plugdev cdrom; do
        if getent group "$grp" >/dev/null 2>&1; then
            usermod -aG "$grp" dziadek 2>/dev/null || true
        fi
    done
fi

# ------------------------------------------------------------------------------
# 3. LightDM Kiosk Configuration
# ------------------------------------------------------------------------------
echo "==> [3/7] Setting up LightDM autologin kiosk session..."
LIGHTDM_DIR="${TARGET_ROOT}/etc/lightdm/lightdm.conf.d"
mkdir -p "$LIGHTDM_DIR"
cat << 'EOF' > "${LIGHTDM_DIR}/99-dziadek-kiosk.conf"
[Seat:*]
autologin-user=dziadek
autologin-user-timeout=0
user-session=xfce
EOF
chmod 644 "${LIGHTDM_DIR}/99-dziadek-kiosk.conf"

# ------------------------------------------------------------------------------
# 4. Polkit v124 JavaScript Lockdown Rule
# ------------------------------------------------------------------------------
echo "==> [4/7] Applying Polkit v124 UDisks2 security lockdown rule..."
POLKIT_DIR="${TARGET_ROOT}/etc/polkit-1/rules.d"
mkdir -p "$POLKIT_DIR"
cat << 'EOF' > "${POLKIT_DIR}/50-dziadek-udisks2-lockdown.rules"
// /etc/polkit-1/rules.d/50-dziadek-udisks2-lockdown.rules
// Restricts user 'dziadek' from disk formatting, partition modification, and system drive tampering.
polkit.addRule(function(action, subject) {
    if (subject.user !== "dziadek") {
        return undefined;
    }

    var actionId = action.id;

    // Block formatting, partition modify/delete, system mount modification for dziadek
    if (actionId.indexOf("org.freedesktop.udisks2.filesystem-format") === 0 ||
        actionId.indexOf("org.freedesktop.udisks2.partition-") === 0 ||
        actionId.indexOf("org.freedesktop.udisks2.modify-device") === 0 ||
        actionId.indexOf("org.freedesktop.udisks2.modify-drive-settings") === 0 ||
        actionId.indexOf("org.freedesktop.udisks2.filesystem-mount-system") === 0 ||
        actionId.indexOf("org.freedesktop.udisks2.filesystem-unmount-others") === 0) {
        return polkit.Result.NO;
    }

    // Allow removable USB/HDD mounting and unmounting
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

# ------------------------------------------------------------------------------
# 5. XFCE Hotkey Suppression (Ctrl+Alt+T, Alt+F4, Alt+F2)
# ------------------------------------------------------------------------------
echo "==> [5/7] Seeding XFCE keyboard shortcuts configuration..."
XFCE_SYS_DIR="${TARGET_ROOT}/etc/xdg/xfce4/xfconf/xfce-perchannel-xml"
XFCE_USER_DIR="${TARGET_ROOT}/home/dziadek/.config/xfce4/xfconf/xfce-perchannel-xml"

mkdir -p "$XFCE_SYS_DIR"
mkdir -p "$XFCE_USER_DIR"

cat << 'EOF' > "${XFCE_SYS_DIR}/xfce4-keyboard-shortcuts.xml"
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfce4-keyboard-shortcuts" version="1.0">
  <property name="commands" type="empty">
    <property name="custom" type="empty">
      <property name="&lt;Primary&gt;&lt;Alt&gt;t" type="string" value=""/>
      <property name="&lt;Alt&gt;F4" type="string" value=""/>
      <property name="&lt;Alt&gt;F2" type="string" value=""/>
      <property name="&lt;Primary&gt;&lt;Alt&gt;Escape" type="string" value=""/>
    </property>
  </property>
  <property name="xfwm4" type="empty">
    <property name="custom" type="empty">
      <property name="&lt;Alt&gt;F4" type="string" value=""/>
    </property>
  </property>
</channel>
EOF
chmod 644 "${XFCE_SYS_DIR}/xfce4-keyboard-shortcuts.xml"

cp "${XFCE_SYS_DIR}/xfce4-keyboard-shortcuts.xml" "${XFCE_USER_DIR}/xfce4-keyboard-shortcuts.xml"
chmod 644 "${XFCE_USER_DIR}/xfce4-keyboard-shortcuts.xml"

# ------------------------------------------------------------------------------
# 6. Directories & Kiosk Autostart Setup
# ------------------------------------------------------------------------------
echo "==> [6/7] Creating application directories and autostart desktop entry..."
HOME_DZIADEK="${TARGET_ROOT}/home/dziadek"
mkdir -p "${HOME_DZIADEK}/Obrazki/Tapety"
mkdir -p "${HOME_DZIADEK}/.config/autostart"
mkdir -p "${HOME_DZIADEK}/.config/senior_dashboard"
mkdir -p "${HOME_DZIADEK}/.cache/senior_dashboard/thumbnails"

cat << 'EOF' > "${HOME_DZIADEK}/.config/autostart/senior-dashboard.desktop"
[Desktop Entry]
Type=Application
Name=Senior Mint Dashboard
Comment=Senior Launcher Kiosk Dashboard
Exec=/usr/bin/python3 /home/dziadek/senior_mint_dashboard/main.py
Icon=preferences-desktop-wallpaper
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
X-XFCE-Autostart-override=true
EOF
chmod 644 "${HOME_DZIADEK}/.config/autostart/senior-dashboard.desktop"

# ------------------------------------------------------------------------------
# 7. Final Ownership & Permissions Fix
# ------------------------------------------------------------------------------
echo "==> [7/7] Setting permissions and ownership for user 'dziadek'..."
if [ "${DRY_RUN:-0}" -eq 1 ]; then
    echo "[DRY-RUN] chown -R dziadek:dziadek ${HOME_DZIADEK}"
else
    if user_exists "dziadek"; then
        chown -R dziadek:dziadek "${HOME_DZIADEK}"
    fi
fi

echo "==> Installation and bulletproof security lockdown completed successfully."
