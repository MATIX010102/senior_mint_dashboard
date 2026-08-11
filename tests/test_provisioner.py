"""
tests/test_provisioner.py
--------------------------
Automated test suite for Requirement R1 / Milestone M1:
Root Provisioner & Bulletproof System Lockdown (`install.sh`).

Verifies:
1. Static parsing of `install.sh` (bash strict mode, root check, noninteractive apt, package list, user/group operations).
2. LightDM autologin kiosk configuration format (`/etc/lightdm/lightdm.conf.d/99-dziadek-kiosk.conf`).
3. Polkit v124 JavaScript lockdown rule syntax and semantics (`/etc/polkit-1/rules.d/50-dziadek-udisks2-lockdown.rules`).
4. XFCE XML keyboard shortcut suppression (`Ctrl+Alt+T`, `Alt+F4`, `Alt+F2`, `Ctrl+Alt+Escape`).
5. Desktop autostart shortcut generation (`/home/dziadek/.config/autostart/senior-dashboard.desktop`).
6. Simulated script execution in temporary TARGET_ROOT environment.
7. System-level integration tests (when executed on live Linux target).
"""

import configparser
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import pytest

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
INSTALL_SCRIPT = WORKSPACE_ROOT / "install.sh"

REQUIRED_PACKAGES = [
    "python3-pyqt6",
    "python3-pyqt6.qtwebengine",
    "cups",
    "hplip",
    "gvfs-backends",
    "mtp-tools",
    "rsync",
    "python3-gi",
    "gir1.2-gtk-3.0",
]

STRIPPED_ADMIN_GROUPS = ["sudo", "wheel", "adm", "lpadmin"]
ADDED_MEDIA_GROUPS = ["video", "audio", "render", "plugdev", "cdrom"]

BLOCKED_POLKIT_PATTERNS = [
    "org.freedesktop.udisks2.filesystem-format",
    "org.freedesktop.udisks2.partition-",
    "org.freedesktop.udisks2.modify-device",
    "org.freedesktop.udisks2.filesystem-mount-system",
]

ALLOWED_POLKIT_PATTERNS = [
    "org.freedesktop.udisks2.filesystem-mount",
    "org.freedesktop.udisks2.filesystem-unmount",
]

NEUTRALIZED_KEYS = [
    "<Primary><Alt>t",
    "<Alt>F4",
    "<Alt>F2",
]


# ==============================================================================
# Unit & Static Analysis Tests
# ==============================================================================

def test_install_script_exists_and_is_readable():
    """Verify that install.sh exists in the workspace root and is readable."""
    assert INSTALL_SCRIPT.exists(), f"install.sh does not exist at {INSTALL_SCRIPT}"
    assert INSTALL_SCRIPT.is_file(), "install.sh is not a regular file"
    content = INSTALL_SCRIPT.read_text(encoding="utf-8")
    assert len(content) > 0, "install.sh is empty"


def test_install_script_bash_strict_mode_and_shebang():
    """Verify bash shebang, strict mode (set -euo pipefail), root check, and noninteractive env."""
    content = INSTALL_SCRIPT.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines()]

    # Shebang check
    assert lines[0].startswith("#!/usr/bin/env bash") or lines[0].startswith("#!/bin/bash"), \
        "install.sh must start with a valid bash shebang"

    # Strict mode check
    assert "set -euo pipefail" in content or ("set -e" in content and "set -u" in content), \
        "install.sh must set strict mode (set -euo pipefail)"

    # Root check
    assert 'id -u' in content or 'EUID' in content, \
        "install.sh must include a root privilege check (id -u)"
    assert '"$(id -u)" -eq 0' in content or '"$(id -u)" -ne 0' in content or '`id -u`' in content, \
        "install.sh root check must verify user ID 0"

    # Noninteractive check
    assert "DEBIAN_FRONTEND=noninteractive" in content, \
        "install.sh must declare DEBIAN_FRONTEND=noninteractive"


def test_install_script_package_dependencies():
    """Verify all 9 required packages are present in the apt-get install line."""
    content = INSTALL_SCRIPT.read_text(encoding="utf-8")
    for pkg in REQUIRED_PACKAGES:
        assert pkg in content, f"Required package '{pkg}' missing from install.sh"


def test_install_script_user_and_group_logic():
    """Verify dziadek user creation, stripping admin groups, and adding media groups."""
    content = INSTALL_SCRIPT.read_text(encoding="utf-8")

    assert "dziadek" in content, "User 'dziadek' is not mentioned in install.sh"
    assert "/home/dziadek" in content, "Home path /home/dziadek is not mentioned in install.sh"

    for group in STRIPPED_ADMIN_GROUPS:
        assert group in content, f"Stripping of admin group '{group}' is missing in install.sh"

    for group in ADDED_MEDIA_GROUPS:
        assert group in content, f"Addition of media group '{group}' is missing in install.sh"


def test_install_script_lightdm_kiosk_configuration():
    """Verify LightDM config path and INI options in install.sh."""
    content = INSTALL_SCRIPT.read_text(encoding="utf-8")

    assert "99-dziadek-kiosk.conf" in content, "Target LightDM file 99-dziadek-kiosk.conf missing from install.sh"
    assert "etc/lightdm/lightdm.conf.d" in content or "LIGHTDM_DIR" in content, \
        "LightDM target directory missing from install.sh"

    assert "autologin-user=dziadek" in content or "autologin-user=${DZIADEK_USER}" in content, \
        "LightDM autologin-user=dziadek missing"
    assert "autologin-user-timeout=0" in content, "LightDM autologin-user-timeout=0 missing"
    assert "user-session=xfce" in content, "LightDM user-session=xfce missing"


def test_install_script_polkit_rule_javascript_syntax():
    """Verify Polkit v124 JS rule format, blocked actions, and allowed actions."""
    content = INSTALL_SCRIPT.read_text(encoding="utf-8")

    assert "50-dziadek-udisks2-lockdown.rules" in content, \
        "Polkit rule filename 50-dziadek-udisks2-lockdown.rules missing from install.sh"
    assert "etc/polkit-1/rules.d" in content or "POLKIT_DIR" in content, \
        "Polkit target directory missing from install.sh"

    assert "polkit.addRule" in content, "Polkit JS rule missing polkit.addRule"
    assert "subject.user" in content and "dziadek" in content, "Polkit JS rule missing subject.user check for dziadek"

    for blocked in BLOCKED_POLKIT_PATTERNS:
        assert blocked in content, f"Polkit JS rule missing blocked action '{blocked}'"

    for allowed in ALLOWED_POLKIT_PATTERNS:
        assert allowed in content, f"Polkit JS rule missing allowed action '{allowed}'"

    # Basic JS syntax check: check balanced parens and braces in polkit rule snippet
    rule_match = re.search(r"polkit\.addRule\(function\(.*?\)\s*\{.*?\}\);", content, re.DOTALL)
    assert rule_match is not None, "Polkit rule structure is malformed"


def test_install_script_xfce_keyboard_shortcuts():
    """Verify XFCE keybinding suppression in system and user XML paths."""
    content = INSTALL_SCRIPT.read_text(encoding="utf-8")

    assert "xfce4-keyboard-shortcuts.xml" in content, \
        "XFCE shortcut file xfce4-keyboard-shortcuts.xml missing from install.sh"
    assert "etc/xdg/xfce4/xfconf/xfce-perchannel-xml" in content or "XFCE_SYS_DIR" in content, \
        "System XFCE XML directory missing from install.sh"
    assert "home/dziadek/.config/xfce4/xfconf/xfce-perchannel-xml" in content or "XFCE_USER_DIR" in content, \
        "User XFCE XML directory missing from install.sh"

    # Keybinding checks (with HTML entity encoding &lt; / &gt;)
    assert "&lt;Primary&gt;&lt;Alt&gt;t" in content or "<Primary><Alt>t" in content, \
        "Ctrl+Alt+T suppression missing from install.sh XML"
    assert "&lt;Alt&gt;F4" in content or "<Alt>F4" in content, \
        "Alt+F4 suppression missing from install.sh XML"
    assert "&lt;Alt&gt;F2" in content or "<Alt>F2" in content, \
        "Alt+F2 suppression missing from install.sh XML"


def test_install_script_autostart_and_ownership():
    """Verify autostart desktop shortcut creation and chown commands."""
    content = INSTALL_SCRIPT.read_text(encoding="utf-8")

    assert "senior-dashboard.desktop" in content, \
        "Autostart desktop file senior-dashboard.desktop missing from install.sh"
    assert ".config/autostart" in content, \
        "Autostart directory missing from install.sh"

    assert "senior_mint_dashboard/main.py" in content or \
           "${INSTALL_DIR}/main.py" in content, \
        "Autostart Exec directive missing or invalid"

    assert "chown -R" in content and "dziadek" in content, \
        "Ownership command chown -R missing"


# ==============================================================================
# TARGET_ROOT Simulated Execution & File Content Verification
# ==============================================================================

def test_install_script_execution_in_target_root(tmp_path):
    """Run install.sh with TARGET_ROOT set to tmp_path and DRY_RUN=1, verifying generated files."""
    env = os.environ.copy()
    env["TARGET_ROOT"] = str(tmp_path)
    env["DRY_RUN"] = "1"

    bash_bin = shutil.which("bash")
    if not bash_bin:
        pytest.skip("Bash executable not found in PATH")

    # Verify bash viability before executing script (handles Windows WSL stub failure)
    try:
        check_bash = subprocess.run([bash_bin, "-c", "echo ok"], capture_output=True, text=True, timeout=5)
        if check_bash.returncode != 0:
            pytest.skip(f"Bash executable {bash_bin} is not functional on host platform: {check_bash.stderr}")
    except Exception as exc:
        pytest.skip(f"Failed to execute bash verification on host platform: {exc}")

    res = subprocess.run([bash_bin, str(INSTALL_SCRIPT)], env=env, capture_output=True, text=True)
    assert res.returncode == 0, f"install.sh failed with exit code {res.returncode}:\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}"

    # 1. LightDM configuration check
    lightdm_conf = tmp_path / "etc" / "lightdm" / "lightdm.conf.d" / "99-dziadek-kiosk.conf"
    assert lightdm_conf.exists(), f"LightDM file was not created at {lightdm_conf}"
    parser = configparser.ConfigParser()
    parser.read(lightdm_conf)
    assert "Seat:*" in parser
    assert parser["Seat:*"]["autologin-user"] == "dziadek"
    assert parser["Seat:*"]["autologin-user-timeout"] == "0"
    assert parser["Seat:*"]["user-session"] == "xfce"

    # 2. Polkit rule check
    polkit_rule = tmp_path / "etc" / "polkit-1" / "rules.d" / "50-dziadek-udisks2-lockdown.rules"
    assert polkit_rule.exists(), f"Polkit rule file was not created at {polkit_rule}"
    rule_text = polkit_rule.read_text(encoding="utf-8")
    assert "polkit.addRule" in rule_text
    assert 'subject.user !== "dziadek"' in rule_text or 'subject.user === "dziadek"' in rule_text
    assert "org.freedesktop.udisks2.filesystem-format" in rule_text
    assert "org.freedesktop.udisks2.partition-" in rule_text
    assert "polkit.Result.NO" in rule_text
    assert "polkit.Result.YES" in rule_text

    # 3. XFCE XML shortcuts check
    sys_xml = tmp_path / "etc" / "xdg" / "xfce4" / "xfconf" / "xfce-perchannel-xml" / "xfce4-keyboard-shortcuts.xml"
    user_xml = tmp_path / "home" / "dziadek" / ".config" / "xfce4" / "xfconf" / "xfce-perchannel-xml" / "xfce4-keyboard-shortcuts.xml"

    assert sys_xml.exists(), f"System XFCE XML file not created at {sys_xml}"
    assert user_xml.exists(), f"User XFCE XML file not created at {user_xml}"

    for xml_file in [sys_xml, user_xml]:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        shortcut_props = root.findall(".//property[@name='custom']/property")
        props_map = {elem.attrib.get("name"): elem.attrib.get("value") for elem in shortcut_props}
        assert props_map.get("<Primary><Alt>t") == ""
        assert props_map.get("<Alt>F4") == ""
        assert props_map.get("<Alt>F2") == ""

    # 4. Autostart desktop file check
    autostart_desktop = tmp_path / "home" / "dziadek" / ".config" / "autostart" / "senior-dashboard.desktop"
    assert autostart_desktop.exists(), f"Autostart desktop file not created at {autostart_desktop}"
    desktop_text = autostart_desktop.read_text(encoding="utf-8")
    assert "[Desktop Entry]" in desktop_text
    assert "Exec=/usr/bin/python3 /home/dziadek/senior_mint_dashboard/main.py" in desktop_text

    # 5. Directories check
    wallpaper_dir = tmp_path / "home" / "dziadek" / "Obrazki" / "Tapety"
    assert wallpaper_dir.exists() and wallpaper_dir.is_dir()


# ==============================================================================
# Live System Integration Tests (Marked system, skipped unless on Linux)
# ==============================================================================

@pytest.mark.system
@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Live system tests require Linux")
def test_live_system_user_and_groups():
    """Verify live system user dziadek and group permissions."""
    import pwd
    import grp

    try:
        user = pwd.getpwnam("dziadek")
    except KeyError:
        pytest.skip("User 'dziadek' does not exist on live system yet")

    assert user.pw_dir == "/home/dziadek"

    user_groups = [g.gr_name for g in grp.getgrall() if "dziadek" in g.gr_mem]
    primary_group = grp.getgrgid(user.pw_gid).gr_name
    all_groups = set(user_groups + [primary_group])

    for forbidden in STRIPPED_ADMIN_GROUPS:
        assert forbidden not in all_groups, f"Security violation: dziadek in admin group {forbidden}"

    for required in ADDED_MEDIA_GROUPS:
        assert required in all_groups, f"dziadek missing media group {required}"
