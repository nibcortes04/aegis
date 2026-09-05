# ⚡ Aegis

[![CI Verification](https://github.com/nibcortes04/aegis/actions/workflows/ci.yml/badge.svg)](https://github.com/nibcortes04/aegis/actions/workflows/ci.yml)
[![Deploy Pages](https://github.com/nibcortes04/aegis/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/nibcortes04/aegis/actions/workflows/deploy-pages.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Antigravity](https://img.shields.io/badge/Antigravity-2.5%2B-blueviolet.svg)](https://antigravity.google)

> **High-performance runtime, live telemetry, and execution guardrails for autonomous terminal agents.** Smart Auto Mode, two-factor safety gate for destructive commands, clean cross-platform notifications without spam, Claude Code-grade 3-line statusline, and mobile Android PWA continuity.

---

## 🌟 Highlights

- **⚡ Smart Auto Mode without Delay**: Auto-approves safe read tools (`view_file`, `list_dir`, `grep_search`), in-workspace file edits, and safe test/build commands with **0s approval delay**.
- **🛡️ Graduated Trust Levels (Niveles de Confianza)**: 4 distinct runtime security profiles (`audit`, `workspace-safe` [default], `full-developer`, `subagent-worker`) allowing users to safely expand agent autonomy from read-only auditing to automated dependency installation and local dev servers.
- **🔒 Two-Factor Safety Gate (Doble Confirmación Obligatoria)**: Destructive commands (`rm -rf`, `docker rm/stop/volume rm`, `dd`, `mkfs`, `sudo`, `drop database`, `git push --force`) are intercepted in two mandatory phases (Step 1 denies execution and forces agent to ask user; Step 2 within 120s prompts physical `y/n` confirmation in terminal).
- **🔍 Autonomous Environment Inspector (`env_inspector.py`)**: Automatically scans host compilers, runtimes (Python, Node, Rust, Go, Java), package managers (pnpm, npm, cargo, pip), and devops tools at install time, auto-populating `settings.json` with personalized safe rules.
- **🤖 Native Multi-Agent Delegation**: 5 bundled subagents (`researcher`, `worker-backend`, `worker-frontend`, `qa-tester`, `reviewer-bot`) for Fork & Join, Worker Pool, and Reviewer Gate orchestration while preserving a clean context window.
- **🔌 Built-in MCP Documentation Server**: Zero-dependency stdio JSON-RPC 2.0 MCP server exposing tools (`powerpack_get_trust_levels`, `powerpack_get_surface_info`, `powerpack_get_delegation_guide`, `powerpack_verify_system`, `powerpack_inspect_environment`) for dynamic agent self-discovery.
- **🌐 100% Cross-Platform & Surface-Aware**:
  - **Operating Systems**: Native support for **Linux** (KDE Plasma, GNOME, Orca), **macOS** (AppleScript/terminal-notifier), and **Windows 10/11** (Windows Terminal, WinRT PowerShell Toasts).
  - **Antigravity Surfaces**: Automatically detects execution environment across **Antigravity CLI (`agy`)**, **Antigravity IDE (VS Code)**, and **Antigravity 2.0 (Electron Desktop App)**.
- **🔔 Single-Card & Strict Notifications (Cero Ruido Intermedio)**:
  - Notifications fire **ONLY** when waiting for human action (`decision: ask`) or final turn completion. Never during continuous intermediate execution or tool calls.
  - Eliminated duplicate Konsole alerts by stripping OSC 777 escape codes and maintaining pure terminal bell (`\a`).
  - In-place single notification replacement (`-r 9942` / `x-canonical-private-synchronous:aegis-notification` / `$toast.Tag`) preventing desktop alert stacking.
  - Test & batch silence detection (`AGY_HOOK_SILENT=1`, `pytest`, `unittest`) producing 0 notification popups during automated test runs.
- **📊 Claude Code-Grade 3-Line Statusline**:
  - **Line 1**: Model & reasoning effort (`🧠 high`), directory, Git branch, and live diff lines counter (`+42 -3`).
  - **Line 2**: Context window bar (`███░░░░░░░ 35%`), cost in USD (`💰 $0.0421`), duration (`⏱ 2m5s`), and 5h/7d quotas with local reset time (`5h:45%(🕦04:30) 7d:12%`).
  - **Line 3**: Interactive cycle mode indicator (`▶▶ auto (safe) (shift+tab to cycle) · ← for agents`).
- **📱 Android Remote Control via Official Google PWA**:
  - Monitor long-running agent tasks and resume sessions directly from your mobile device using the official web app at `https://antigravity.google`.
- **🌳 Git Worktree Isolation & Bot-Ready Contributions**:
  - Automated worktree management via `./scripts/dev-worktree.sh` for developing epics, fixes, and autonomous bot PRs without workspace collisions.

---

## 🖥️ Terminal Statusline Preview

```text
[Gemini-3.8 Flash] 📁 aegis 🌿 main +42-3 🧠 high 🏷️  Refactor Auto Mode Hooks…
███░░░░░░░ 35% │ 💰 $0.0421 │ ⏱ 2m5s │ 5h:45%(🕦04:30) 7d:12%
▶▶ auto mode on (shift+tab to cycle) · ← for agents
```

---

## 🚀 Quick Installation

### Universal (Linux, macOS, Windows)
```bash
# Clone the repository
git clone https://github.com/nibcortes04/aegis.git ~/.gemini/antigravity-cli/plugins/aegis
cd ~/.gemini/antigravity-cli/plugins/aegis

# Run Universal Python Installer
python3 install.py
# (On Windows: python install.py or powershell -File install.ps1)
# (On Linux/macOS: ./install.sh)
```

### Antigravity Plugin Manager
```bash
agy plugin install ./aegis
agy plugin validate aegis
```

### Verification & Live Diagnostics
```bash
# Validate plugin integrity
agy plugin validate ~/.gemini/antigravity-cli/plugins/aegis

# Run interactive notification & terminal bell diagnostic
python3 scripts/aegis_test_notify.py --all

# Run full automated test suite
cd ~/.gemini/antigravity-cli/plugins/aegis
python3 -m unittest discover -s tests -p "test_*.py"
./tests/test_hooks.sh
```

---

## 🏗️ Architecture & Component Layout

```
aegis/
├── plugin.json                 # Antigravity Plugin Manifest (passes agy plugin validate)
├── hooks.json                  # Hook declarations (PreToolUse & Stop)
├── mcp_config.json             # MCP server registration config
├── install.py                  # Cross-platform Python installer (idempotent)
├── install.sh                  # One-click POSIX installer
├── uninstall.sh                # Clean uninstaller
├── agents/                     # Bundled subagents catalog
│   ├── researcher/             # Read-only exploration & documentation search
│   ├── worker-backend/         # Backend implementation & unit tests
│   ├── worker-frontend/        # UI/UX & frontend implementation
│   ├── qa-tester/              # Automated QA suites & verification
│   └── reviewer-bot/           # Code review & compliance gating
├── mcp/                        # Built-in documentation & diagnostic MCP server
│   ├── mcp_server.py           # Stdio JSON-RPC 2.0 server
│   └── README.md               # MCP documentation
├── rules/
│   └── AGENTS.md               # Standard agent governance rule
├── skills/
│   └── aegis/
│       ├── SKILL.md            # Master operational skill
│       └── references/         # Deep architectural guides
│           ├── auto_mode.md    # Classifier design & critical command rules
│           ├── notifications.md# Terminal bell & single-card notifications
│           ├── statusline.md   # Statusline ANSI spec & quota schema
│           ├── remote_sessions.md # Android PWA & session continuity guide
│           └── multi_agent_delegation.md # Multi-agent orchestration patterns
├── scripts/
│   ├── agy_hook_handler.py     # Sub-10ms hook dispatcher & security gate
│   ├── trust_levels.py         # 4-tier graduated trust levels engine
│   ├── env_detector.py         # Cross-platform & surface detector with debounce
│   ├── aegis_test_notify.py    # Terminal bell & notification diagnostic tool
│   ├── agy-hook-dispatcher.sh  # Fast execution wrapper
│   ├── statusline_formatter.py # Claude Code statusline renderer
│   ├── statusline.sh           # Statusline wrapper
│   ├── agy-session.sh          # Session resume/inspect helper
│   ├── dev-worktree.sh         # Git worktree isolation utility
│   └── env_inspector.py        # Host tool & compiler inspector
├── tests/
│   ├── test_classifier.py      # Classifier unit test suite
│   ├── test_notifications.py   # Multi-session debounce & notification tests
│   ├── test_statusline.py      # Statusline formatting & quota test suite
│   ├── test_trust_levels.py    # Trust levels permissions test suite
│   ├── test_mcp_server.py      # MCP server tools unit test suite
│   └── test_hooks.sh           # End-to-end hook contract test
├── docs/                       # Documentation landing & guides
│   ├── index.html              # GitHub Pages dashboard
│   ├── TERMINALS.md            # Terminal setup guide (Konsole, Orca, Kitty, etc.)
│   └── COMPATIBILITY_CHECKLIST.md # OS & Surface verification checklist
└── .github/
    ├── PROJECT_TASKS.md        # Roadmap & task backlog board
    ├── workflows/
    │   ├── ci.yml              # CI verification pipeline
    │   ├── deploy-pages.yml    # Automated deploy gated on passing CI
    │   └── pr-bot-validator.yml# Automated PR validation & bot labeling
    ├── ISSUE_TEMPLATE/
    │   ├── bug_report.md       # Bug template
    │   ├── feature_request.md  # Feature template
    │   └── task.md             # Task template for Project boards
    └── PULL_REQUEST_TEMPLATE.md# Human & Autonomous Bot PR standard
```

---

## 🛡️ Auto Mode Trust Levels

Configure how much autonomy your agents have without ever risking catastrophic system damage:

| Level | Name | Autonomy Scope | Typical Commands |
| :--- | :--- | :--- | :--- |
| **0** | `audit` | **Read-Only** | `cat`, `ls`, `grep`, `find`, `git log/status/diff` |
| **1** | `workspace-safe` *(Default)* | **In-Workspace Edits & Standard Tests** | Level 0 + `git add/commit`, `pytest`, `npm test`, `cargo test`, workspace edits |
| **2** | `full-developer` | **Developer Autonomy** | Level 1 + `npm install`, `pip install`, `pnpm add`, `docker compose up`, local servers |
| **3** | `subagent-worker` | **Autonomous Subagent Pool** | Subagent isolation: in-workspace edits + compilation/linting; blocks git push & external ops |

> **Always Blocked (All Levels)**: Destructive commands (`rm -rf /`, `mkfs`, `dd`, `sudo`, `docker rm -f`, `git push --force`) always halt and require explicit interactive human approval.

### Setting Active Level
In `~/.gemini/antigravity-cli/settings.json`:
```json
{
  "autoModeLevel": "full-developer"
}
```
Or via environment variable:
```bash
export AGY_TRUST_LEVEL="full-developer"
```

---

## 🤖 Multi-Agent Delegation & Bundled Subagents

Run complex projects in parallel without context bloat using AGY's native subagent system:

- **`researcher`**: Read-only codebase explorer for searching files, analyzing AST, and checking documentation.
- **`worker-backend`**: Implements backend services, API endpoints, migrations, and unit tests.
- **`worker-frontend`**: Implements visual components, templates, styles, and client-side interactions.
- **`qa-tester`**: Redacts QA test plans, executes unit/integration suites, and diagnoses test failures.
- **`reviewer-bot`**: Independent reviewer for code compliance, security, and edge-case verification.

See the complete guide in [skills/agy-powerpack/references/multi_agent_delegation.md](file:///home/n_n/projects/agy-powerpack/skills/agy-powerpack/references/multi_agent_delegation.md).

---

## 🔌 Built-in Documentation MCP Server

The plugin includes a stdio JSON-RPC 2.0 MCP server (`mcp/mcp_server.py`) that agents can query dynamically:

- **`powerpack_get_trust_levels`**: Query available security profiles and permitted commands.
- **`powerpack_get_surface_info`**: Inspect current OS, terminal emulator, and Antigravity surface.
- **`powerpack_get_delegation_guide`**: Retrieve recommended multi-agent delegation architectures.
- **`powerpack_verify_system`**: Run quick health checks on local scripts and configs.

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
