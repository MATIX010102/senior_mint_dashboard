# Instructions for Antigravity Coding Agents

This project is a kiosk-based Python application called **Senior Mint Dashboard**.
All coding agents working on this workspace MUST adhere to the following rules:

## 1. Always Push Changes to the GitHub Repository
- Whenever you implement a new feature, fix a bug, or make any source code modifications, you **must** stage, commit, and push those changes to the remote Git repository immediately after verifying they work.
- Run the following commands as part of your verification and delivery workflow:
  ```bash
  git add .
  git commit -m "Your descriptive commit message"
  git push origin main
  ```
- Before concluding your turn or declaring a task complete, confirm that the changes are pushed and online.

## 2. Security and Kiosk Mode Preservation
- Do not modify key suppression files or main window close event handlers in a way that allows escaping the kiosk mode (unless specifically requested or when bypassing for testing under `SENIOR_MINT_TEST_MODE=1`).

## 3. High-Contrast Senior Aesthetics
- Preserve the high-contrast color scheme and large typography designed for senior users (e.g., 20pt+ font sizes for weather, 22pt+ for dates, and 54pt for the clock).
