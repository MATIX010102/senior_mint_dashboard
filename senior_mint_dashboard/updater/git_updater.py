"""
Silent GitHub Git Auto-Updater Module.
Performs git pull --ff-only origin main, validates python syntax using py_compile,
and automatically rolls back via git reset --hard ORIG_HEAD if compilation fails.
"""

import sys
import py_compile
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger("SeniorMintDashboard.Updater")


def check_and_apply_updates(repo_dir=None):
    """
    Executes silent update process:
    1. Runs git pull --ff-only
    2. Validates python files syntax
    3. Rolls back if syntax errors found
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
        # Step 1: Git pull
        logger.info("Executing 'git pull --ff-only origin main'...")
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
        if "Already up to date" in output_str or "Already up-to-date" in output_str:
            logger.info("No updates found. Repository is already up to date.")
            return {'updated': False, 'success': True, 'error': None}

        logger.info("New updates pulled. Starting python syntax validation check...")
        # Step 2: Validate syntax of updated python files
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
            if reset_res.returncode == 0:
                logger.warning("Rollback completed successfully.")
            else:
                logger.error(f"Rollback failed (git reset returned {reset_res.returncode}): {reset_res.stderr.strip()}")
            return {'updated': True, 'success': False, 'error': 'Syntax check failed, rolled back'}

        logger.info("Syntax check passed successfully. Kiosk update applied.")
        return {'updated': True, 'success': True, 'error': None}

    except Exception as e:
        logger.error(f"Unexpected error during update process: {e}", exc_info=True)
        return {'updated': False, 'success': False, 'error': str(e)}
