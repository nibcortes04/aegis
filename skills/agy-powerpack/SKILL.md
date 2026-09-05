---
name: agy-powerpack
description: Comprehensive powerpack for Google Antigravity CLI (agy). Provides Smart Auto Mode (safe tool auto-approval), terminal tab bell (🔔) and auto-closing desktop notifications, real-time statusline inspired by Claude Code, and multiplatform session continuity (CLI, IDE, Antigravity 2.0, and Android PWA Remote Control). Use when configuring agy, troubleshooting permissions, enhancing the statusline, or managing sessions across devices.
---

# Antigravity Powerpack (`agy-powerpack`)

`agy-powerpack` elevates the Google Antigravity CLI experience with features inspired by modern agentic workflows (like Claude Code and Codex), optimized specifically for Antigravity's architecture and Linux/Unix terminal environments (KDE Konsole, Orca, iTerm2, Kitty, Alacritty).

---

## 1. Core Modules

### A. Smart Auto Mode
- **Zero-friction execution:** Automatically approves read-only tools (`view_file`, `list_dir`, `grep_search`), safe inspection and test commands (`git status`, `git diff`, `pnpm test`, `pytest`), and in-workspace file edits.
- **Fail-closed security:** Potentially destructive operations (`rm -rf`, `git push --force`, `docker rm/stop`, modifications outside workspace) trigger an interactive prompt, ring the terminal bell, and issue a transient desktop notification.
- Read more: [references/auto_mode.md](references/auto_mode.md)

### B. Terminal Bell & Desktop Notifications (🔔)
- **Tab Bell Icon:** Emits the standard POSIX ASCII BEL character (`\a`) and OSC 9/777 sequences to `/dev/tty` upon turn completion (`Stop` hook) and when approval is required. In KDE Konsole, Orca, and modern terminals, this renders the notification bell icon on the terminal tab.
- **Transient Desktop Popups:** Fires `notify-send` with `-t 4000`, `-u normal`, and `-h int:transient:1`, preventing sticky or persistent notification bubbles in KDE Plasma.
- Read more: [references/notifications.md](references/notifications.md)

### C. Advanced Statusline (Claude Code Style)
- **Real-time 3-line status bar:**
  - **Line 1:** Model with reasoning effort (`🧠 high`), directory, Git branch with live line diff (`+X -Y`), and session name/preview.
  - **Line 2:** Graphic context window bar (`[████░░░░░░] 24%`), session cost, duration, 5-hour quota with local reset time (`(🕦18:30)`), and weekly 7-day quota.
  - **Line 3:** Interactive cycle mode indicator (`▶▶ auto mode on (shift+tab to cycle) · ← for agents`).
- Read more: [references/statusline.md](references/statusline.md)

### D. Multiplatform Session Continuity & Android PWA
- **CLI Commands:** Resume quickly with `agy -c`, `agy --conversation <id>`, or the interactive `/resume` picker (`Ctrl+F` to group, `F2` to rename).
- **Google Antigravity Remote Control:** Background daemon (`agy remote-control start`) connected to `https://antigravity.google`.
- **Android PWA:** Step-by-step setup to install the official Progressive Web App on Android devices to monitor, approve, and continue sessions remotely.
- Read more: [references/remote_sessions.md](references/remote_sessions.md)

---

## 2. Quick Setup & Verification

To install or update the powerpack on any system:
```bash
./install.sh
```

To manage sessions from terminal:
```bash
./scripts/agy-session.sh list
./scripts/agy-session.sh resume
```

To work with Git Worktrees:
```bash
./scripts/dev-worktree.sh create feat/my-improvement
```
