"""
Silent GitHub Git Auto-Updater Module.
Performs git pull --ff-only origin main, validates python syntax using py_compile,
and automatically rolls back via git reset --hard ORIG_HEAD if compilation fails.
"""

import sys
import py_compile
import subprocess
from pathlib import Path


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
    if not (repo_path / ".git").exists():
        return {'updated': False, 'success': False, 'error': 'Not a git repository'}

    try:
        # Step 1: Git pull
        res = subprocess.run(
            ["git", "pull", "--ff-only", "origin", "main"],
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )

        if res.returncode != 0:
            return {'updated': False, 'success': False, 'error': res.stderr}

        output_str = res.stdout.strip()
        if "Already up to date" in output_str or "Already up-to-date" in output_str:
            return {'updated': False, 'success': True, 'error': None}

        # Step 2: Validate syntax of updated python files
        syntax_ok = True
        for py_file in repo_path.rglob("*.py"):
            try:
                py_compile.compile(str(py_file), doraise=True)
            except py_compile.PyCompileError as pe:
                syntax_ok = False
                break

        # Step 3: Rollback if syntax fails
        if not syntax_ok:
            subprocess.run(
                ["git", "reset", "--hard", "ORIG_HEAD"],
                cwd=repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return {'updated': True, 'success': False, 'error': 'Syntax check failed, rolled back'}

        return {'updated': True, 'success': True, 'error': None}

    except Exception as e:
        return {'updated': False, 'success': False, 'error': str(e)}
