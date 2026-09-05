# Multiplatform & Surface Architecture Reference

`agy-powerpack` includes an intelligent environment and surface detector (`scripts/env_detector.py`) designed to ensure 100% portable operation across operating systems and execution surfaces.

---

## 1. Operating System Compatibility Matrix

| Feature | Linux | macOS (Darwin) | Windows 10/11 |
| :--- | :--- | :--- | :--- |
| **Terminal Tab Bell (🔔)** | `\a` to `/dev/tty` + OSC 9/777 | `\a` to `/dev/tty` + OSC 9 | `\a` to `CONOUT$` / `winsound` / stderr |
| **Desktop Notifications** | `notify-send -h int:transient:1` (4s auto-dismiss) | `osascript` (AppleScript) / `terminal-notifier` | PowerShell Native WinRT Toast Notification |
| **Database & Config** | `~/.gemini/antigravity-cli/` | `~/.gemini/antigravity-cli/` | `%USERPROFILE%\.gemini\antigravity-cli\` |
| **Workspace Boundary** | Portable `os.path.commonpath` | Portable `os.path.commonpath` | Drive-aware `os.path.commonpath` (`C:\`, `D:\`) |
| **Installer** | `install.sh` / `install.py` | `install.sh` / `install.py` | `install.ps1` / `install.py` |

---

## 2. Execution Surface Detection

Antigravity operates across three primary surfaces, automatically identified at runtime:

### A. Antigravity CLI (`cli`)
- **Detection**: Default interactive terminal or PTY session.
- **Environment**: Inspects `$TERM`, `$SHELL`, and terminal emulator IDs (`KONSOLE_VERSION`, `ORCA_PANE_KEY`, `ITERM_SESSION_ID`, `KITTY_WINDOW_ID`, `WT_SESSION`).
- **Experience**: Complete 3-line ANSI statusline, terminal bell on tab headers, and fast stdin/stdout hook piping.

### B. Antigravity IDE (`ide`)
- **Detection**: Environment variables `ANTIGRAVITY_IDE=1`, `TERM_PROGRAM=vscode`, `VSCODE_PID`, or `VSCODE_CWD`.
- **Environment**: Integrated development environment based on VS Code.
- **Behavior**: The integrated terminal runs `agy` with full statusline support. Hooks enforce workspace security boundaries respecting the active project directory (`workspace.current_dir`).

### C. Antigravity 2.0 Desktop App (`desktop_app`)
- **Detection**: Environment variables `ANTIGRAVITY_ELECTRON=1`, `ANTIGRAVITY_APP=1`, or `ELECTRON_RUN_AS_NODE`.
- **Environment**: Standalone Electron desktop application with Chat Canvas and HTML Auxiliary Pane.
- **Behavior**: Seamless coexistence. Hooks protect host system resources without interfering with desktop app background processes.

---

## 3. Dynamic Path & Workspace Resolution

To prevent hardcoded directory assumptions (e.g. `/home/user`):
1. **Application Data Directory**:
   ```python
   def get_app_data_dir():
       custom = os.environ.get("ANTIGRAVITY_APP_DATA_DIR") or os.environ.get("GEMINI_CLI_HOME")
       if custom and os.path.isdir(custom):
           return os.path.abspath(custom)
       return os.path.expanduser("~/.gemini/antigravity-cli")
   ```
2. **Safe Workspace Containment**:
   ```python
   # Verifies that target files are located within the active project root
   # or the user home directory, blocking traversal into system directories (/etc, C:\Windows).
   os.path.commonpath([workspace_root, target_file]) == workspace_root
   ```
