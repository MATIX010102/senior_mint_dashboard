"""
Silent GitHub Git Auto-Updater Module.
Performs git pull --ff-only origin main, validates python syntax using py_compile,
and automatically rolls back via git reset --hard ORIG_HEAD if compilation fails.
Checks remote commit using git ls-remote before running pulls.
"""

import sys
import json
import py_compile
import subprocess
import logging
import datetime
from pathlib import Path
from senior_mint_dashboard.config import APP_VERSION, VERSION_FILE

logger = logging.getLogger("SeniorMintDashboard.Updater")


def write_version_file(version, commit_hash, status):
    """Writes status metadata details to version.json file."""
    vdata = {
        "version": version,
        "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
        "commit": commit_hash,
        "status": status
    }
    try:
        VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        VERSION_FILE.write_text(json.dumps(vdata, indent=2), encoding="utf-8")
        logger.info(f"Successfully wrote version.json: commit={commit_hash[:7]}, status={status}")
    except Exception as e:
        logger.error(f"Failed to write version.json: {e}")


def check_and_apply_updates(repo_dir=None):
    """
    Executes update process:
    1. Compares local commit hash with remote commit hash via git ls-remote.
    2. Runs git pull --ff-only origin main if different.
    3. Validates python files syntax.
    4. Rolls back if syntax errors found.
    Returns dict: {'updated': bool, 'success': bool, 'error': str}
    """
    if not repo_dir:
        repo_dir = Path(__file__).resolve().parent.parent.parent

    repo_path = Path(repo_dir)
    logger.info(f"Target repository directory: '{repo_path}'")
    if not (repo_path / ".git").exists():
        msg = "Not a git repository (missing .git folder)"
        logger.error(msg)
        return {'updated': False, 'success': False, 'error': msg}

    try:
        # Get local commit hash
        local_commit = ""
        res_loc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_path, capture_output=True, text=True)
        if res_loc.returncode == 0:
            local_commit = res_loc.stdout.strip()
            logger.info(f"Local commit hash: '{local_commit}'")

        # Get remote commit hash without pulling (using ls-remote)
        remote_commit = ""
        res_rem = subprocess.run(
            ["git", "ls-remote", "origin", "refs/heads/main"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=15
        )
        if res_rem.returncode == 0 and res_rem.stdout.strip():
            remote_commit = res_rem.stdout.split()[0].strip()
            logger.info(f"Remote commit hash: '{remote_commit}'")
        else:
            logger.warning(f"Could not check remote commit hash: {res_rem.stderr.strip()}")

        if remote_commit and local_commit == remote_commit:
            logger.info("Local commit matches remote commit. No updates available.")
            write_version_file(APP_VERSION, local_commit, "up_to_date")
            return {'updated': False, 'success': True, 'error': None}

        # Commits differ or remote check failed, proceed with Git pull
        logger.info(f"Updates available (local={local_commit[:7]}, remote={remote_commit[:7]}). Executing pull...")
        res = subprocess.run(
            ["git", "pull", "--ff-only", "origin", "main"],
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )

        if res.returncode != 0:
            logger.error(f"Git pull failed with exit code {res.returncode}. Stderr: {res.stderr.strip()}")
            return {'updated': False, 'success': False, 'error': res.stderr}

        output_str = res.stdout.strip()
        logger.info(f"Git pull output: {output_str}")

        # Validate syntax of updated python files
        syntax_ok = True
        for py_file in repo_path.rglob("*.py"):
            try:
                # Skip virtual environments or cache folders if they are in the directory structure
                if ".venv" in py_file.parts or "venv" in py_file.parts or ".pytest_cache" in py_file.parts:
                    continue
                py_compile.compile(str(py_file), doraise=True)
            except py_compile.PyCompileError as pe:
                logger.error(f"Syntax compilation failed for file '{py_file}': {pe}")
                syntax_ok = False
                break

        # Step 3: Rollback if syntax fails
        if not syntax_ok:
            logger.warning("Syntax verification failed! Triggering automatic rollback via 'git reset --hard ORIG_HEAD'...")
            reset_res = subprocess.run(
                ["git", "reset", "--hard", "ORIG_HEAD"],
                cwd=repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            write_version_file(APP_VERSION, local_commit, "up_to_date")
            return {'updated': True, 'success': False, 'error': 'Syntax check failed, rolled back'}

        # Get the new local commit hash after successful pull
        new_commit = local_commit
        res_new = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_path, capture_output=True, text=True)
        if res_new.returncode == 0:
            new_commit = res_new.stdout.strip()

        # Update version.json status to 'updated'
        write_version_file(APP_VERSION, new_commit, "updated")

        logger.info("Syntax check passed successfully. Kiosk update applied.")
        return {'updated': True, 'success': True, 'error': None}

    except Exception as e:
        logger.error(f"Unexpected error during update process: {e}", exc_info=True)
        return {'updated': False, 'success': False, 'error': str(e)}
