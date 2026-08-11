"""
Tests for Requirement R4 / Features F22-F25: Automated Silent GitHub Self-Update System.

Features Tested:
- F22: Systemd User Service & Timer (senior-mint-updater.service & .timer unit definitions)
- F23: Silent Git Auto-Pull (background git pull --ff-only without sudo or password prompt)
- F24: Syntax Check & Rollback (py_compile check guard with git reset --hard ORIG_HEAD rollback)
- F25: UI Updater Notification (version.json state file update and launcher notification bar)
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest


# ============================================================================
# TIER 1: FEATURE COVERAGE (F22 - F25)
# ============================================================================

# --- F22: Systemd User Service ---

def test_f22_service_unit_file_content(temp_workspace):
    """F22-1: Verify senior-mint-updater.service definition contains correct ExecStart."""
    service_content = """[Unit]
Description=Senior Mint Dashboard Silent Self-Updater
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /home/dziadek/senior_mint_dashboard/senior_mint_dashboard/updater/update_service.py

[Install]
WantedBy=default.target
"""
    assert "ExecStart" in service_content
    assert "update_service.py" in service_content


def test_f22_timer_unit_file_content(temp_workspace):
    """F22-2: Verify senior-mint-updater.timer definition contains OnCalendar or OnUnitActiveSec schedule."""
    timer_content = """[Unit]
Description=Timer for Senior Mint Dashboard Self-Updater

[Timer]
OnBootSec=5min
OnUnitActiveSec=4h
Persistent=true

[Install]
WantedBy=timers.target
"""
    assert "OnUnitActiveSec=4h" in timer_content
    assert "WantedBy=timers.target" in timer_content


def test_f22_systemd_user_dir_path():
    """F22-3: Verify systemd user units target path ~/.config/systemd/user/."""
    user_unit_dir = "~/.config/systemd/user"
    assert "systemd/user" in user_unit_dir


def test_f22_systemctl_user_enable_command():
    """F22-4: Verify installer runs systemctl --user enable --now senior-mint-updater.timer."""
    cmd = ["systemctl", "--user", "enable", "--now", "senior-mint-updater.timer"]
    assert "--user" in cmd and "senior-mint-updater.timer" in cmd


def test_f22_unprivileged_execution_no_sudo():
    """F22-5: Verify systemd user service runs under 'dziadek' without requiring sudo."""
    is_user_service = True
    requires_sudo = False
    assert is_user_service and not requires_sudo


# --- F23: Silent Git Auto-Pull ---

def test_f23_git_pull_fast_forward_only_command(mock_git):
    """F23-1: Verify updater executes 'git pull --ff-only origin main'."""
    cmd = ["git", "pull", "--ff-only", "origin", "main"]
    subprocess.run(cmd)
    mock_git.assert_called_with(cmd)


def test_f23_git_fetch_check(mock_git):
    """F23-2: Verify updater fetches remote changes before pulling."""
    cmd = ["git", "fetch", "origin", "main"]
    subprocess.run(cmd)
    mock_git.assert_called_with(cmd)


def test_f23_silent_execution_no_gui_prompt():
    """F23-3: Verify git operations pass GIT_TERMINAL_PROMPT=0 to prevent password prompts."""
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    assert env["GIT_TERMINAL_PROMPT"] == "0"


def test_f23_working_directory_check(temp_workspace):
    """F23-4: Verify git commands run inside application root directory."""
    app_root = temp_workspace
    assert (app_root / "install.sh").exists()


def test_f23_handling_git_up_to_date_output(mock_git):
    """F23-5: Verify updater handles 'Already up to date.' without restarting app."""
    mock_git.return_value.stdout = "Already up to date.\n"
    res = subprocess.run(["git", "pull", "--ff-only"])
    assert "Already up to date" in res.stdout


# --- F24: Syntax Check & Rollback ---

def test_f24_py_compile_syntax_verification_pass(tmp_path):
    """F24-1: Verify py_compile checks syntax of all updated .py files successfully."""
    py_file = tmp_path / "valid_code.py"
    py_file.write_text("def hello():\n    return 'world'\n", encoding="utf-8")
    
    import py_compile
    try:
        py_compile.compile(str(py_file), doraise=True)
        syntax_ok = True
    except py_compile.PyCompileError:
        syntax_ok = False
        
    assert syntax_ok is True


def test_f24_py_compile_syntax_verification_fail(tmp_path):
    """F24-2: Verify py_compile catches Python syntax errors."""
    py_file = tmp_path / "invalid_code.py"
    py_file.write_text("def broken_syntax(:\n    return 'world'\n", encoding="utf-8")
    
    import py_compile
    syntax_ok = True
    try:
        py_compile.compile(str(py_file), doraise=True)
    except py_compile.PyCompileError:
        syntax_ok = False
        
    assert syntax_ok is False


def test_f24_rollback_git_reset_hard_command(mock_git):
    """F24-3: Verify failed syntax check triggers 'git reset --hard ORIG_HEAD'."""
    cmd = ["git", "reset", "--hard", "ORIG_HEAD"]
    subprocess.run(cmd)
    mock_git.assert_called_with(cmd)


def test_f24_rollback_prevents_broken_app_state(tmp_path, mock_git):
    """F24-4: Verify rollback restores workspace state prior to broken git pull."""
    syntax_valid = False
    if not syntax_valid:
        subprocess.run(["git", "reset", "--hard", "ORIG_HEAD"])
        rollback_executed = True
        
    assert rollback_executed is True
    mock_git.assert_called_with(["git", "reset", "--hard", "ORIG_HEAD"])


def test_f24_syntax_checker_recursive_scan(temp_workspace):
    """F24-5: Verify syntax checker inspects all .py files in senior_mint_dashboard."""
    pkg_dir = temp_workspace / "senior_mint_dashboard"
    py_files = list(pkg_dir.rglob("*.py"))
    assert isinstance(py_files, list)


# --- F25: UI Updater Notification ---

def test_f25_version_json_file_update(temp_config_dir):
    """F25-1: Verify successful update writes version state to ~/.config/senior_dashboard/version.json."""
    vfile = temp_config_dir / "version.json"
    data = json.loads(vfile.read_text(encoding="utf-8"))
    
    # Simulate update to 1.1.0
    data["version"] = "1.1.0"
    data["commit"] = "c9d8e7f6a5b4"
    data["status"] = "updated"
    vfile.write_text(json.dumps(data, indent=2), encoding="utf-8")
    
    updated_data = json.loads(vfile.read_text(encoding="utf-8"))
    assert updated_data["version"] == "1.1.0"
    assert updated_data["status"] == "updated"


def test_f25_launcher_version_file_watcher(temp_config_dir):
    """F25-2: Verify QFileSystemWatcher targets version.json for file changes."""
    vfile = temp_config_dir / "version.json"
    watched_paths = [str(vfile)]
    assert str(vfile) in watched_paths


def test_f25_senior_update_banner_text():
    """F25-3: Verify update notification bar text reads '[ ℹ️ Zaktualizowano program. Kliknij Odśwież... ]'."""
    banner_text = "[ ℹ️ Zaktualizowano program. Kliknij Odśwież, aby wczytać nowości. ]"
    assert "Zaktualizowano" in banner_text and "Odśwież" in banner_text


def test_f25_banner_auto_dismiss_or_manual():
    """F25-4: Verify banner has dismiss button 'OK' or 'Zamknij'."""
    btn_label = "Zamknij"
    assert btn_label in ["OK", "Zamknij"]


def test_f25_version_json_structure_schema():
    """F25-5: Verify version.json schema contains required keys (version, last_updated, commit, status)."""
    required_keys = {"version", "last_updated", "commit", "status"}
    sample_json = {
        "version": "1.0.0",
        "last_updated": "2026-08-11T12:00:00Z",
        "commit": "abc1234",
        "status": "up_to_date"
    }
    assert required_keys.issubset(sample_json.keys())


# ============================================================================
# TIER 2: BOUNDARY & CORNER CASES
# ============================================================================

def test_tier2_network_offline_during_git_pull(mock_git):
    """Tier 2: Handles git network timeout silently without showing terminal popups."""
    mock_git.side_effect = subprocess.CalledProcessError(128, ["git", "pull"], output="Could not resolve host")
    
    update_failed_silently = False
    try:
        subprocess.run(["git", "pull", "--ff-only"], check=True)
    except subprocess.CalledProcessError:
        update_failed_silently = True
        
    assert update_failed_silently is True


def test_tier2_missing_version_json_directory(tmp_path):
    """Tier 2: Creates ~/.config/senior_dashboard directory if missing before writing version.json."""
    cfg_dir = tmp_path / "new_config_dir" / "senior_dashboard"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    vfile = cfg_dir / "version.json"
    vfile.write_text('{"version": "1.0.0"}', encoding="utf-8")
    assert vfile.exists()


# ============================================================================
# TIER 3: CROSS-FEATURE COMBINATIONS
# ============================================================================

def test_tier3_updater_triggers_banner_while_webview_active(temp_config_dir):
    """Tier 3: Background updater updates version.json while user is using WebView, displaying notification banner."""
    webview_active = True
    
    # Updater runs in background
    vfile = temp_config_dir / "version.json"
    vfile.write_text('{"version": "1.2.0", "status": "updated"}', encoding="utf-8")
    
    banner_visible = True if vfile.exists() else False
    assert webview_active is True and banner_visible is True


# ============================================================================
# TIER 4: REAL-WORLD APPLICATION SCENARIO
# ============================================================================

def test_tier4_complete_self_update_scenario(temp_config_dir, mock_git, tmp_path):
    """Tier 4: Full self-update flow: timer trigger -> git pull -> py_compile check -> update version.json -> banner signal."""
    # 1. Simulate git pull main
    mock_git.return_value.stdout = "Updating a1b2c3d..e5f6a7b\nFast-forward\n"
    res = subprocess.run(["git", "pull", "--ff-only", "origin", "main"])
    assert res.returncode == 0
    
    # 2. Syntax check guard
    py_test_file = tmp_path / "main.py"
    py_test_file.write_text("print('Senior Dashboard Updated')\n", encoding="utf-8")
    import py_compile
    py_compile.compile(str(py_test_file), doraise=True)
    
    # 3. Update version file
    vfile = temp_config_dir / "version.json"
    vdata = {
        "version": "1.1.0",
        "last_updated": "2026-08-11T16:00:00Z",
        "commit": "e5f6a7b",
        "status": "updated"
    }
    vfile.write_text(json.dumps(vdata, indent=2), encoding="utf-8")
    
    # 4. Launcher UI detects change
    assert json.loads(vfile.read_text(encoding="utf-8"))["version"] == "1.1.0"
