# 📋 Aegis — Project Tasks & Engineering Roadmap Dashboard

Welcome to the centralized task board and engineering roadmap for **Aegis**.
This dashboard tracks delivered capabilities, active epics, refactoring targets, and future roadmap items. Both human engineers and autonomous AI bots operate against this backlog.

- **System Architect & Orchestrator:** Nicolas Cortes ([@nibcortes04](https://github.com/nibcortes04))
- **Engineered with:** Gemini 3.8 Flash (High) & Google Antigravity (AGY)
- **Current Version:** `v1.5.0` (Production Ready)

---

## 🚦 Kanban Board & Pipeline Status

### 🟢 Completed Epics (Delivered & Verified in v1.5.0)

- [x] **[EPIC-01](https://github.com/nibcortes04/aegis/issues/7): Deterministic Auto Mode & Graduated Trust Levels**
  - [x] Sub-10ms hook classification engine in `scripts/agy_hook_handler.py`.
  - [x] 4 graduated security profiles: `audit` (0), `workspace-safe` (1), `full-developer` (2), `subagent-worker` (3) in `scripts/trust_levels.py`.
  - [x] Dynamic level selection via `settings.json` and `AGY_AUTO_MODE_LEVEL`.
  - [x] Automated unit test suite (`tests/test_trust_levels.py` and `tests/test_classifier.py`).

- [x] **[EPIC-02](https://github.com/nibcortes04/aegis/issues/8): Two-Factor Safety Gate (Doble Confirmación Obligatoria)**
  - [x] Mandatory 2-step intercept for critical commands (`rm -rf`, `docker stop/rm`, `drop database`, `mkfs`, `dd`, `sudo`, `git push --force`).
  - [x] Step 1 blocks (`decision: deny`) requiring agent-to-human explanation.
  - [x] Step 2 within 120s TTL prompts interactive terminal confirmation (`decision: ask`).
  - [x] Confirmation ledger persistence in `~/.gemini/antigravity-cli/.danger_confirmations.json`.
  - [x] Automated hook contract tests in `tests/test_hooks.sh`.

- [x] **[EPIC-03](https://github.com/nibcortes04/aegis/issues/9): Claude Code-Grade 3-Line Statusline**
  - [x] Line 1: Model (`[Gemini-3.8 Flash]`), reasoning effort (`🧠 high`), Git branch, live diff lines (`+X -Y`), session title from SQLite.
  - [x] Line 2: Context window graphic bar (`███░░░░░░░ 35%`), cost in USD, duration, 5h quota with local reset time `(🕦HH:MM)` and 7d quota.
  - [x] Line 3: Interactive cycle mode indicator (`▶▶ auto (safe) (shift+tab to cycle) · ← for agents`).
  - [x] Automated test suite in `tests/test_statusline.py`.

- [x] **[EPIC-04](https://github.com/nibcortes04/aegis/issues/10): Multi-Session Notification Telemetry & Tab Bell (🔔)**
  - [x] Direct `\a` emit to `/dev/tty` for bell icon 🔔 on KDE Konsole, Orca, Kitty, iTerm2 tabs without OSC 777 duplication.
  - [x] KDE Plasma transient notifications with strict auto-dismiss (`-t 4000/5000ms`, `-h int:transient:1`, `safe_urgency = "normal"`).
  - [x] Per-session isolation via `conversationId` in `/tmp/.aegis_notify_state.json` preventing cross-session silencing.
  - [x] Zero notification noise during intermediate tool execution; notification exclusively on turn completion or human action request.

- [x] **[EPIC-05](https://github.com/nibcortes04/aegis/issues/11): Kernel Inotify Capacity Telemetry & Leak Guard**
  - [x] Kernel telemetry scanner `get_inotify_capacity()` in `scripts/env_detector.py`.
  - [x] Real-time warning triggers when active instances exceed 80% and 95% of `/proc/sys/fs/inotify/max_user_instances`.
  - [x] Integrated into `scripts/aegis_test_notify.py --verify` and `scripts/env_inspector.py`.

- [x] **[EPIC-06](https://github.com/nibcortes04/aegis/issues/12): Autonomous Environment Inspector (`env_inspector.py`)**
  - [x] Host scanner for compilers (`gcc`, `clang`, `rustc`, `go`), runtimes (`python`, `node`, `bun`), and package managers (`pnpm`, `npm`, `cargo`, `pip`).
  - [x] Auto-generation of personalized safe rules for `settings.json`.

- [x] **[EPIC-07](https://github.com/nibcortes04/aegis/issues/13): Subagent Delegation Catalog (`agents/`) & Git Worktrees**
  - [x] 5 specialized agent definitions: `researcher`, `worker-backend`, `worker-frontend`, `qa-tester`, `reviewer-bot`.
  - [x] Worktree isolation script `./scripts/dev-worktree.sh` for collision-free branch development.

- [x] **[EPIC-08](https://github.com/nibcortes04/aegis/issues/14): Portal Web, Cyber Shield Branding & AEO/SEO Standard (v1.5.0)**
  - [x] Vector branding (`docs/logo.svg`, `docs/favicon.svg`).
  - [x] Responsive 2-column installation grid with centered verification banner (`docs/index.html`, `docs/styles.css`).
  - [x] Interactive Terminal Lab with tab switcher (Statusline, Auto Mode, Safety Gate, Multi-Session).
  - [x] Full attribution to `@nibcortes04` and Gemini 3.8 Flash (High).
  - [x] AI Engine Optimization (`docs/llms.txt`, `docs/robots.txt`, `docs/sitemap.xml`, Schema.org JSON-LD).
  - [x] Anthropic `frontend-design` skill integrated in AGY.

---

### 🟡 Maintenance & Refactoring Epics (Next Sprint)

- [x] **[EPIC-CORRECT-01](https://github.com/nibcortes04/aegis/issues/15): MCP Server Harmonization & Legacy Cleansing**
  - [x] Rename MCP server identifier to `aegis-mcp` in `mcp/mcp_server.py`.
  - [x] Expose native `aegis_*` tools (`aegis_get_trust_levels`, `aegis_get_surface_info`, `aegis_verify_system`, etc.) with backward-compatible aliases for `powerpack_*`.
  - [x] Clean remaining legacy references in `skills/aegis/references/*.md`, `docs/TRUST_LEVELS.md`, `docs/TERMINALS.md`, and `rules/AGENTS.md`.
  - [x] Update `tests/test_mcp_server.py`.

- [x] **[EPIC-CORRECT-02](https://github.com/nibcortes04/aegis/issues/16): Synchronize Community Contribution Templates**
  - [x] Update `.github/ISSUE_TEMPLATE/` and `.github/PULL_REQUEST_TEMPLATE.md` to reference Aegis exclusively.

---

### 🔵 Future Roadmap Epics (Backlog)

- [ ] **[EPIC-09](https://github.com/nibcortes04/aegis/issues/1): Dynamic Real Quota & Live Metrics Integration**
  - [ ] Connect statusline line 2 with real-time session tokens and live API usage telemetry when exposed by AGY.
  - [ ] Fallback gracefully to local SQLite estimates when offline.

- [ ] **[EPIC-10](https://github.com/nibcortes04/aegis/issues/2): Android Remote PWA Pairing & Tunnel Bridge (`aegis mobile`)**
  - [ ] Interactive CLI wizard (`aegis mobile --pair`) generating a local QR code and secure tunnel (Tailscale/Cloudflare/SSH) for mobile session continuity on `https://antigravity.google`.

- [ ] **[EPIC-11](https://github.com/nibcortes04/aegis/issues/3): Bot Contributor Automation & Autonomous PR Review Gate**
  - [ ] GitHub Action workflow auto-validating PRs opened by bots (`bot/*` branches).
  - [ ] Automatic check for worktree hygiene, linting, and 100% test pass rate before merge to `dev`.

- [ ] **[EPIC-12](https://github.com/nibcortes04/aegis/issues/4): Interactive Terminal Setup & Visual/Audio Bell Wizard**
  - [ ] CLI tool (`aegis doctor --terminal`) to inspect active terminal and auto-configure visual bell settings.
  - [ ] Optional subtle audio chimes for human approval requests.

- [ ] **[EPIC-13](https://github.com/nibcortes04/aegis/issues/5): Production VPS Agent Orchestration Guardrails**
  - [ ] Native `vps-production` profile for remote servers managing production containers (n8n, Chatwoot, Caddy).
  - [ ] Enforces double confirmation interactively on any docker compose or volume operations.

- [ ] **[EPIC-14](https://github.com/nibcortes04/aegis/issues/6): Official Antigravity Plugin Registry Packaging**
  - [ ] Prepare distribution bundle and automated release pipeline for `agy plugin publish`.

---

## 🤖 Protocol for Autonomous Bot Contributors

When an autonomous bot claims a task from this backlog:
1. **Create Worktree**: Run `./scripts/dev-worktree.sh new bot/<task-id>-<description>`.
2. **Execute inside Worktree**: Develop and run full test suite (`python3 -m unittest discover -s tests -p "test_*.py"`, `./tests/test_hooks.sh`).
3. **Open Pull Request**: Use `.github/PULL_REQUEST_TEMPLATE.md`, set contributor type to `Autonomous Agent Bot`, link the task ID, and target branch `dev`.
