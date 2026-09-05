# 📋 AGY PowerPack — Project Tasks & Roadmap Dashboard

Welcome to the centralized task board and engineering roadmap for **AGY PowerPack**.
This dashboard tracks planned features, active epics, and bot-delegated maintenance tasks. Both human engineers and autonomous AI bots (Gemini, Codex, Claude) operate against this backlog.

---

## 🚦 Kanban Board & Pipeline Status

### 🟢 Completed (Done)
- [x] **EPIC-01: Terminal Notifications & Tab Bell**
  - Direct `\a` emit to `/dev/tty` for bell icon 🔔 on KDE Konsole, Orca, Kitty, iTerm2 tabs.
  - KDE Plasma transient notifications with auto-dismiss (`-t 4000 -h int:transient:1`).
  - Fixed sticky notification bug.
- [x] **EPIC-02: Claude Code-Grade 3-Line Statusline**
  - Line 1: Model with reasoning effort (`🧠 high`), Git branch with diff (`+X -Y`), session title from SQLite.
  - Line 2: Context window graphic bar, USD cost, duration, 5h quota with local reset time `(🕦HH:MM)` and 7d quota.
  - Line 3: Interactive cycle mode indicator (`▶▶ auto mode on`).
- [x] **EPIC-03: Cross-Platform & Multi-Surface Architecture (v1.1.0)**
  - Linux, macOS, and Windows 10/11 native adaptors (`scripts/env_detector.py`).
  - Automatic surface detection: pure CLI, Antigravity IDE (VS Code), and Antigravity 2.0 Desktop App.
  - Universal Python installer (`install.py`) and PowerShell script (`install.ps1`).

---

### 🟡 In Progress (Current Sprint)
- [ ] **EPIC-04: Auto Mode Trust Levels (Niveles de Confianza)**
  - [x] Implement 4 graduated security profiles: `audit` (0), `workspace-safe` (1), `full-developer` (2), `subagent-worker` (3).
  - [x] Dynamic level selection via `settings.json` and `AGY_AUTO_MODE_LEVEL`.
  - [x] Statusline indicator showing active trust level (`▶▶ auto (dev)`, `▶▶ auto (safe)`).
  - [x] Automated unit test suite (`tests/test_trust_levels.py`).
- [ ] **EPIC-05: Anti-Spam Notification Engine & Silent Test Mode**
  - [x] Replaced stacking notifications with single-card replacement (`-r 9942` and `x-canonical-private-synchronous`).
  - [x] Silent test mode (`AGY_HOOK_SILENT=1`) preventing popups during test execution.
  - [x] Windows Toast tag grouping (`Tag: agy-notification`) to prevent notification center clutter.
- [ ] **EPIC-06: Bundled Documentation MCP Server (`mcp/`)**
  - [x] Implement lightweight stdio JSON-RPC 2.0 server (`mcp/mcp_server.py`).
  - [x] Expose tools: `powerpack_get_trust_levels`, `powerpack_get_surface_info`, `powerpack_get_delegation_guide`, `powerpack_verify_system`.
  - [x] Register in `mcp_config.json` (passes `agy plugin validate`).
- [ ] **EPIC-07: Subagent Delegation Catalog (`agents/`)**
  - [x] Define 5 core agents: `researcher`, `worker-backend`, `worker-frontend`, `qa-tester`, `reviewer-bot`.
  - [x] Document Fork & Join and Worker Pool architectural patterns (`multi_agent_delegation.md`).

---

### 🔵 Backlog & Future Tasks (Next Sprints)
- [ ] **TASK-101: Autonomous Bot PR Validator GitHub Action**
  - Auto-triage pull requests opened with the `bot/...` prefix.
  - Verify worktree compliance and unit test pass rate automatically.
- [ ] **TASK-102: Terminal Profiles Auto-Configuration Helper**
  - Interactive CLI wizard to verify and turn on visual bell in KDE Konsole, iTerm2, and Windows Terminal.
- [ ] **TASK-103: Dynamic Model Swapping per Subagent in Settings**
  - Allow users to override default subagent models (`flash` vs `pro`) via `settings.json`.
- [ ] **TASK-104: Custom Notification Sounds & Audio Chimes**
  - Optional subtle sound themes for task completion and approval requests.

---

## 🤖 Protocol for Autonomous Bot Contributors

When an autonomous bot claims a task from this backlog:
1. **Create Worktree**: Run `./scripts/dev-worktree.sh create bot/<task-id>-<description>`.
2. **Execute inside Worktree**: Develop and run full test suite (`python3 -m unittest discover`, `./tests/test_hooks.sh`).
3. **Open Pull Request**: Use `.github/PULL_REQUEST_TEMPLATE.md`, set contributor type to `Autonomous Agent Bot`, link the task ID, and target branch `dev`.
