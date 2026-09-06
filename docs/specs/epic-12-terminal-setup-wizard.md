# Technical Specification: EPIC-12 — Interactive Terminal Setup & Visual/Audio Bell Wizard

**Epic ID:** EPIC-12  
**GitHub Issue:** [#4](https://github.com/nibcortes04/aegis/issues/4)  
**Status:** In Progress (Sprint 2)  
**Architect:** Nicolas Cortes (@nibcortes04)  
**AI Pair Engine:** Gemini 3.8 Flash (High) via Antigravity (AGY)  

---

## 1. Executive Summary & Objective

In autonomous agentic coding workflows, human engineers frequently switch between browser tabs, code editors, and documentation while an AI agent (such as Antigravity CLI) executes multi-step plans. A critical UX challenge is knowing precisely when an agent:
1. Completes a long-running turn (`Stop` lifecycle event).
2. Requires interactive human confirmation (`PreToolUse` Two-Factor Safety Gate).

Standard OS desktop notifications can be intrusive, noisy, or silenced by "Do Not Disturb" (DND) modes. Terminal tab badges (ASCII `\a` bell) offer a subtle, persistent notification, but terminal emulators differ widely in how they handle bells (some screech with PC speaker audio, some discard bells entirely, and some require specific configuration files).

**EPIC-12** delivers:
- An intelligent terminal profile inspector covering 12+ emulators (Konsole, iTerm2, Alacritty, Kitty, Windows Terminal, Ghostty, WezTerm, Orca, GNOME Terminal/Ptyxis, Mintty, VSCode, Tmux).
- An interactive setup wizard and diagnostic doctor (`aegis doctor --terminal`).
- Non-intrusive, subtle audio chime options using native sound servers (PipeWire, PulseAudio, macOS CoreAudio, Windows SystemSounds) with graceful silence fallbacks.
- An MCP tool `aegis_doctor_terminal` allowing agents to diagnose human interaction channels directly.

---

## 2. Architecture & Components

```
                      +-----------------------------+
                      |   CLI Dispatcher: aegis     |
                      |  (doctor --terminal, test)  |
                      +--------------+--------------+
                                     |
                +--------------------+--------------------+
                |                                         |
+---------------+---------------+         +---------------+---------------+
|  scripts/terminal_wizard.py   |         |     mcp/mcp_server.py         |
|  (Core Inspection & Wizard)   |         | (aegis_doctor_terminal Tool)  |
+---------------+---------------+         +---------------+---------------+
                |                                         |
     +----------+----------+                              |
     |                     |                              |
+----+----+           +----+----+                         |
| Profile |           |  Audio  |                         |
| Matrix  |           | Chimes  |                         |
+----+----+           +----+----+                         |
     |                     |                              |
     v                     v                              v
[12+ Emulators]    [pw-cat/paplay/afplay]     [JSON-RPC Tool Response]
```

---

## 3. Terminal Emulator Matrix & Capabilities

| Emulator | Detection Signals | Visual Bell / Tab Badge | Audio Chimes | Recommended Config Snippet |
| :--- | :--- | :---: | :---: | :--- |
| **KDE Konsole** | `KONSOLE_VERSION`, `KONSOLE_DBUS_SERVICE` | Native 🔔 badge on tab | Mute PC speaker, enable system notification | `BellMode=SystemNotification` |
| **Orca Terminal** | `ORCA_PANE_KEY`, `ORCA_AGENT_LAUNCH_TOKEN` | Native tab badge + IPC | Managed by Orca desktop daemon | Built-in |
| **Kitty** | `KITTY_WINDOW_ID`, `KITTY_PID` | Tab highlight & visual flash | Custom bell command | `enable_audio_bell no`<br>`window_alert_on_bell yes` |
| **Alacritty** | `ALACRITTY_LOG`, `ALACRITTY_WINDOW_ID`, `TERM=alacritty` | Visual color flash | Optional desktop trigger | `[bell]`<br>`animation = "EaseOut"` |
| **iTerm2** | `ITERM_SESSION_ID`, `TERM_PROGRAM=iTerm.app` | 🔔 in tab header | Silence bell, dock bounce | Preferences > Profiles > Terminal > Show bell icon |
| **Windows Terminal** | `WT_SESSION`, `WT_PROFILE_ID` | Taskbar flash & window flash | Windows SystemSounds | `"bellStyle": ["taskbar", "window"]` |
| **Ghostty** | `GHOSTTY_RESOURCES_DIR`, `TERM=xterm-ghostty` | Visual bell flash | Native audio or mute | `bell-action = "cursor"` or `visual` |
| **WezTerm** | `WEZTERM_PANE`, `WEZTERM_EXECUTABLE` | Tab bell indicator | Window flash | `config.visual_bell = { fade_in_duration_ms = 75 }` |
| **GNOME Terminal / Ptyxis** | `GNOME_TERMINAL_SCREEN`, `VTE_VERSION`, `PTYXIS_VERSION` | VTE visual bell | Desktop notifications | Enable "Terminal bell" in preferences |
| **Mintty / Git Bash** | `TERM_PROGRAM=mintty`, `MSYSTEM` | Taskbar badge | Mute sound, flash window | `BellType=2` (Taskbar flash) |
| **VSCode Terminal** | `TERM_PROGRAM=vscode` | Terminal tab indicator | Audio cue configurable | `"terminal.integrated.enableBell": true` |
| **Tmux** | `TMUX`, `TMUX_PANE` | Window activity flag `*` | Passthrough to outer terminal | `set -g visual-bell off`<br>`set -g bell-action any` |

---

## 4. Non-Intrusive Audio Chime System

Traditional terminal bells emit harsh PC speaker beeps (`beep` frequency 750Hz). Aegis implements subtle sound cues:
1. **Linux (PulseAudio / PipeWire):**
   - Probes `paplay`, `pw-cat`, `canberra-gtk-play`.
   - Plays freedesktop sound theme assets: `/usr/share/sounds/freedesktop/stereo/complete.oga`, `/usr/share/sounds/freedesktop/stereo/bell.oga`, or `/usr/share/sounds/ocean/stereo/bell.oga`.
2. **macOS (CoreAudio):**
   - Probes `afplay`.
   - Plays `/System/Library/Sounds/Tink.aiff` or `/System/Library/Sounds/Ping.aiff`.
3. **Windows:**
   - Probes PowerShell: `[System.Media.SystemSounds]::Asterisk.Play()`.
4. **Fallback:**
   - In-memory synthetic sine chime generator (440Hz -> 880Hz harmonious chime) or pure ASCII BEL.
5. **Configurable Policy:**
   - `AGY_AUDIO_CHIME=0` or `"none"`: Audio disabled (visual bell only, default).
   - `AGY_AUDIO_CHIME=1` or `"subtle"`: Soft chime on turn completion or human action prompt.

---

## 5. Unified CLI Interface (`bin/aegis` and `scripts/terminal_wizard.py`)

```bash
# Full terminal inspection and diagnostic report
aegis doctor --terminal

# Test ASCII bell to verify tab icon
aegis doctor --terminal --test-bell

# Test subtle audio chime
aegis doctor --terminal --test-chime

# Output JSON report for scripts and agents
aegis doctor --terminal --json

# Print exact configuration recommendations for active emulator
aegis doctor --terminal --recommend
```

---

## 6. Verification & Quality Invariants

- **Zero External Dependencies:** Implemented in pure Python 3 using standard library (`os`, `sys`, `json`, `shutil`, `subprocess`, `platform`).
- **100% Test Pass Rate:** Unit tests covering all terminal heuristics, audio discovery fallbacks, and command-line arguments.
- **Autonomous Bot Gate:** Must pass all 4 phases of `scripts/bot_pr_check.py` with 0 warnings.
