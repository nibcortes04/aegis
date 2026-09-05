# 📋 Compatibility Checklist & Certified Platforms

This document tracks all certified operating systems, terminal emulators, and Antigravity surfaces tested with **AGY PowerPack**.

---

## 🎖️ Primary Development & Reference Environment
The core system was developed, benchmarked, and certified on:
- **Operating System:** Fedora Linux 40/44 (x86_64)
- **Linux Kernel:** 7.1.12
- **Desktop Environment:** KDE Plasma 6.3 (Wayland)
- **Notification Daemon:** KDE Plasma Notification Manager (freedesktop spec with `-h int:transient:1` and `-r 9942`)
- **Terminals Tested:** KDE Konsole (v24.08), Orca Terminal, Alacritty
- **Python Runtime:** Python 3.14.7 & Python 3.11
- **Status:** 🟢 **100% Certified & Production Verified**

---

## 🌐 Platform Verification Matrix

| OS / Distribution | Surface Tested | Notification Backend | Bell Mechanism | CI Status | Real Hardware Certified |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Fedora Linux** | CLI, Orca, VS Code | `notify-send` (transient) | `/dev/tty` BEL + OSC 9 | ✅ PASS | ✅ Certified |
| **Ubuntu 24.04 LTS** | CLI | `notify-send` | `/dev/tty` BEL | ✅ PASS (CI) | ✅ Verified |
| **Ubuntu 22.04 LTS** | CLI | `notify-send` | `/dev/tty` BEL | ✅ PASS (CI) | ✅ Verified |
| **Debian 12 Bookworm**| CLI | `notify-send` | `/dev/tty` BEL | ✅ PASS (CI) | ✅ Verified |
| **Arch Linux** | CLI, Konsole, Kitty | `notify-send` | `/dev/tty` BEL | ✅ PASS | 🟡 Community Testing |
| **macOS 14+ (Sonoma)**| CLI, iTerm2, VS Code | `osascript` / `terminal-notifier` | `/dev/tty` BEL | ✅ PASS | 🟡 Community Testing |
| **Windows 11** | Windows Terminal, CLI| PowerShell WinRT Toast | `CONOUT$` / `winsound` | ✅ PASS | 🟡 Community Testing |

---

## 🧪 Community Compatibility Checklist

To submit a verification test for your distribution or terminal:
1. Clone the repository and run the test suite:
   ```bash
   python3 -m unittest discover -s tests -p "test_*.py" -v
   ./tests/test_hooks.sh
   ```
2. Check the terminal tab: verify that a bell icon 🔔 appears on turn completion.
3. Check desktop notifications: verify that alert popups close automatically within 4 seconds and do not accumulate vertically.
4. Submit a Pull Request updating this checklist with your environment details!
