# ⚡ AGY PowerPack

[![CI Verification](https://github.com/n-n/agy-powerpack/actions/workflows/ci.yml/badge.svg)](https://github.com/n-n/agy-powerpack/actions/workflows/ci.yml)
[![Deploy Pages](https://github.com/n-n/agy-powerpack/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/n-n/agy-powerpack/actions/workflows/deploy-pages.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Antigravity](https://img.shields.io/badge/Antigravity-2.5%2B-blueviolet.svg)](https://antigravity.google)

> **Supercharge Google Antigravity CLI (`agy`) with Smart Auto Mode, terminal tab notification bells, auto-dismissing desktop alerts, a Claude Code-grade 3-line statusline, cross-platform Android PWA continuity, and isolated Git Worktree development.**

---

## 🌟 Highlights

- **⚡ Smart Auto Mode without Delay**: Auto-approves safe read tools (`view_file`, `list_dir`, `grep_search`), in-workspace file edits, and safe test/build commands with **0s approval delay**.
- **🛡️ Fail-Closed Security Gate**: Strictly halts and requests human confirmation for destructive shell commands (`rm -rf`, `git push -f`, `docker rm/stop`, `dd`, `mkfs`, `sudo`) and file edits outside the workspace.
- **🌐 100% Cross-Platform & Surface-Aware**:
  - **Operating Systems**: Native support for **Linux** (KDE Plasma, GNOME, Orca), **macOS** (AppleScript/terminal-notifier), and **Windows 10/11** (Windows Terminal, WinRT PowerShell Toasts).
  - **Antigravity Surfaces**: Automatically detects execution environment across **Antigravity CLI (`agy`)**, **Antigravity IDE (VS Code)**, and **Antigravity 2.0 (Electron Desktop App)**.
- **🔔 Terminal Tab Bell & Auto-Dismiss Notifications**:
  - Emits ASCII 7 (`\a`) to `/dev/tty` (Linux/macOS) or `CONOUT$` (Windows), lighting up the bell icon on terminal tabs in KDE Konsole, Orca, iTerm2, Kitty, and Windows Terminal.
  - Triggers native desktop notifications: Linux (`notify-send -h int:transient:1`), macOS (`osascript`), and Windows (PowerShell WinRT Toast) with auto-dismissal to **never get stuck on screen**.
- **📊 Claude Code-Grade 3-Line Statusline**:
  - **Line 1**: Model & reasoning effort (`🧠 high`), directory, Git branch, and live diff lines counter (`+42 -3`).
  - **Line 2**: Context window bar (`███░░░░░░░ 35%`), cost in USD (`💰 $0.0421`), duration (`⏱ 2m5s`), and 5h/7d quotas with local reset time (`5h:45%(🕦04:30) 7d:12%`).
  - **Line 3**: Interactive cycle mode indicator (`▶▶ auto mode on (shift+tab to cycle) · ← for agents`).
- **📱 Android Remote Control via Official Google PWA**:
  - Monitor long-running agent tasks and resume sessions directly from your mobile device using the official web app at `https://antigravity.google`.
- **🌳 Git Worktree Isolation & Bot-Ready Contributions**:
  - Automated worktree management via `./scripts/dev-worktree.sh` for developing epics, fixes, and autonomous bot PRs without workspace collisions.

---

## 🖥️ Terminal Statusline Preview

```text
[Gemini-2.5 Pro] 📁 agy-powerpack 🌿 main +42-3 🧠 high 🏷️  Refactor Auto Mode Hooks…
███░░░░░░░ 35% │ 💰 $0.0421 │ ⏱ 2m5s │ 5h:45%(🕦04:30) 7d:12%
▶▶ auto mode on (shift+tab to cycle) · ← for agents
```

---

## 🚀 Quick Installation

### Universal (Linux, macOS, Windows)
```bash
# Clone the repository
git clone https://github.com/n-n/agy-powerpack.git ~/.gemini/antigravity-cli/plugins/agy-powerpack
cd ~/.gemini/antigravity-cli/plugins/agy-powerpack

# Run Universal Python Installer
python3 install.py
# (On Windows: python install.py or powershell -File install.ps1)
# (On Linux/macOS: ./install.sh)
```

### Antigravity Plugin Manager
```bash
agy plugin install ./agy-powerpack
agy plugin validate agy-powerpack
```

### Verification
```bash
# Validate plugin integrity
agy plugin validate ~/.gemini/antigravity-cli/plugins/agy-powerpack

# Run built-in test suite
cd ~/.gemini/antigravity-cli/plugins/agy-powerpack
python3 -m unittest discover -s tests -p "test_*.py"
./tests/test_hooks.sh
```

---

## 🏗️ Architecture & Component Layout

```
agy-powerpack/
├── plugin.json                 # Antigravity Plugin Manifest (passes agy plugin validate)
├── hooks.json                  # Hook declarations (PreToolUse & Stop)
├── install.sh                  # One-click installer & configuration updater
├── uninstall.sh                # Clean uninstaller
├── rules/
│   └── AGENTS.md               # Standard agent governance rule
├── skills/
│   └── agy-powerpack/
│       ├── SKILL.md            # Master operational skill
│       └── references/         # Deep architectural guides
│           ├── auto_mode.md    # Classifier design & critical command rules
│           ├── notifications.md# Terminal bell & KDE transient notifications
│           ├── statusline.md   # Statusline ANSI spec & quota schema
│           └── remote_sessions.md # Android PWA & session continuity guide
├── scripts/
│   ├── agy_hook_handler.py     # Sub-10ms hook dispatcher & classifier
│   ├── agy-hook-dispatcher.sh  # Fast execution wrapper
│   ├── statusline_formatter.py # Claude Code statusline renderer
│   ├── statusline.sh           # Statusline wrapper
│   ├── agy-session.sh          # Session resume/inspect helper
│   └── dev-worktree.sh         # Git worktree isolation utility
├── tests/
│   ├── test_classifier.py      # Classifier unit test suite
│   ├── test_statusline.py      # Statusline formatting & quota test suite
│   └── test_hooks.sh           # End-to-end hook contract test
├── docs/                       # GitHub Pages documentation landing
└── .github/
    ├── workflows/
    │   ├── ci.yml              # CI verification pipeline
    │   └── deploy-pages.yml    # Automated deploy strictly gated on passing CI
    ├── ISSUE_TEMPLATE/         # Bug & Feature templates
    └── PULL_REQUEST_TEMPLATE.md# Human & Autonomous Bot PR standard
```

---

## 📱 Google Antigravity Remote Control (Android PWA)

Google Antigravity provides an official Progressive Web App (PWA) to resume, supervise, and interact with CLI sessions from mobile devices:

1. **Start Remote Control on Host**:
   ```bash
   agy remote-control start
   ```
2. **Access the PWA on Mobile**:
   - Open **Chrome on Android** and go to `https://antigravity.google`.
   - Tap the three dots menu (**⋮**) in Chrome and tap **"Install app"** (or "Add to Home screen").
3. **Pair & Resume**:
   - Log into your Google account.
   - Your workstation sessions will appear in the dashboard. Tap to connect and view live agent output.

---

## 🌳 Git Worktree Collaboration Workflow

To maintain clean workspaces, avoid stash collisions, and ensure zero merge regressions, **all** development (both by humans and autonomous bots) uses isolated Git Worktrees:

```bash
# 1. Create an isolated worktree & branch from dev
./scripts/dev-worktree.sh new feat/my-enhancement

# 2. Enter worktree and perform development
cd worktrees/feat/my-enhancement

# 3. Validate before committing
python3 -m unittest discover -s tests -p "test_*.py"
./tests/test_hooks.sh

# 4. Commit and push to branch
git commit -am "feat: implement my enhancement"
git push origin feat/my-enhancement

# 5. Clean up worktree when done
cd ../..
./scripts/dev-worktree.sh remove feat/my-enhancement
```

---

## 🤝 Contributing

We welcome contributions from both human developers and autonomous AI bots (Codex, Claude, AGY, OpenCode).
Please read our [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md) guidelines before opening a Pull Request.

---

## 📄 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.
