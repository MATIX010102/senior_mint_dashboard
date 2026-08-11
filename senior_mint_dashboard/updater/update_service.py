"""
Entry point for Systemd User Service timer (/home/dziadek/senior-mint-updater.service).
"""

import sys
from pathlib import Path
from senior_mint_dashboard.updater.git_updater import check_and_apply_updates

def main():
    repo_dir = Path(__file__).resolve().parent.parent.parent
    result = check_and_apply_updates(repo_dir)
    if result['success']:
        if result['updated']:
            print("[INFO] Senior Mint Dashboard updated successfully!")
        else:
            print("[INFO] Dashboard is already up to date.")
        sys.exit(0)
    else:
        print(f"[ERROR] Update failed: {result.get('error')}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
