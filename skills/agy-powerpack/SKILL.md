---
name: agy-powerpack
description: Comprehensive powerpack for Google Antigravity CLI (agy). Provides Smart Auto Mode (safe tool auto-approval), terminal tab bell (🔔) and auto-closing desktop notifications, real-time statusline inspired by Claude Code, and multiplatform session continuity (CLI, IDE, Antigravity 2.0, and Android PWA Remote Control). Use when configuring agy, troubleshooting permissions, enhancing the statusline, or managing sessions across devices.
---

# Antigravity Powerpack (`agy-powerpack`)

`agy-powerpack` elevates the Google Antigravity CLI experience with features inspired by modern agentic workflows (like Claude Code and Codex), optimized specifically for Antigravity's architecture and Linux/Unix terminal environments (KDE Konsole, Orca, iTerm2, Kitty, Alacritty).

---

## 1. Core Modules

### A. Smart Auto Mode & Graduated Trust Levels
- **Zero-friction execution:** Automatically approves read-only tools (`view_file`, `list_dir`, `grep_search`), safe inspection and test commands (`git status`, `git diff`, `pnpm test`, `pytest`), and in-workspace file edits.
- **Graduated Trust Levels:** 4 security profiles (`audit`, `workspace-safe` [default], `full-developer`, `subagent-worker`) allowing users to safely expand agent permissions (package managers, local servers, isolated subagents) without ever risking catastrophic commands.
- **Fail-closed security:** Potentially destructive operations (`rm -rf`, `git push --force`, `docker rm/stop`, modifications outside workspace) trigger an interactive prompt, ring the terminal bell, and issue an auto-dismissing desktop notification.
- Read more: [references/auto_mode.md](references/auto_mode.md)

### B. Terminal Bell & Single-Card Desktop Notifications (🔔)
- **Tab Bell Icon:** Emits the standard POSIX ASCII BEL character (`\a`) and OSC 9/777 sequences to `/dev/tty` upon turn completion (`Stop` hook) and when approval is required. In KDE Konsole, Orca, and modern terminals, this renders the notification bell icon on the terminal tab.
- **In-Place Notification Replacement:** Replaces notifications in-place (`-r 9942` / `x-canonical-private-synchronous:agy-notification` / `$toast.Tag`), preventing notification stacking. Silences notifications during automated test suites.
- Read more: [references/notifications.md](references/notifications.md)

### C. Advanced Statusline (Claude Code Style)
- **Real-time 3-line status bar:**
  - **Line 1:** Model with reasoning effort (`🧠 high`), directory, Git branch with live line diff (`+X -Y`), and session name/preview.
  - **Line 2:** Graphic context window bar (`[████░░░░░░] 24%`), session cost, duration, 5-hour quota with local reset time (`(🕦18:30)`), and weekly 7-day quota.
  - **Line 3:** Interactive cycle mode indicator (`▶▶ auto (safe) (shift+tab to cycle) · ← for agents`).
- Read more: [references/statusline.md](references/statusline.md)

### D. Multiplatform Session Continuity & Android PWA
- **CLI Commands:** Resume quickly with `agy -c`, `agy --conversation <id>`, or the interactive `/resume` picker (`Ctrl+F` to group, `F2` to rename).
- **Google Antigravity Remote Control:** Background daemon (`agy remote-control start`) connected to `https://antigravity.google`.
- **Android PWA:** Step-by-step setup to install the official Progressive Web App on Android devices to monitor, approve, and continue sessions remotely.
- Read more: [references/remote_sessions.md](references/remote_sessions.md)

### E. Cross-Platform & Surface Portability (Linux, macOS, Windows | CLI, IDE, Desktop App)
- **Zero Hardcoding:** Dynamic resolution of user home (`os.path.expanduser("~")`), application data dir (`ANTIGRAVITY_APP_DATA_DIR`), and drive letters (`C:\`, `D:\`).
- **Surface Awareness:** Automatically detects whether it is running in pure CLI, Antigravity IDE (VS Code), or Antigravity 2.0 (Electron App).
- **Native Notifications:** Adapts between Linux (`notify-send` transient), macOS (`osascript`/`terminal-notifier`), and Windows (PowerShell WinRT Toast).
- Read more: [references/cross_platform.md](references/cross_platform.md)

### F. Multi-Agent Delegation & Subagent Catalog
- **Concurrent Subagents:** Native multi-agent patterns (Fork & Join, Worker Pool, Reviewer Gate) using `invoke_subagent`.
- **5 Bundled Subagents:** `researcher`, `worker-backend`, `worker-frontend`, `qa-tester`, `reviewer-bot`.
- Read more: [references/multi_agent_delegation.md](references/multi_agent_delegation.md)

### G. Built-in Documentation MCP Server
- **Zero-Dependency Stdio MCP Server:** Exposes `powerpack_get_trust_levels`, `powerpack_get_surface_info`, `powerpack_get_delegation_guide`, and `powerpack_verify_system` via stdio JSON-RPC 2.0.
- Registered via `mcp_config.json`.

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
