# Specification: EPIC-13 — Production VPS Agent Orchestration Guardrails

**Status**: In Review  
**Target Milestone**: `v1.6.0 - Advanced Ecosystem & Packaging`  
**Related Issue**: [#5](https://github.com/nibcortes04/aegis/issues/5)  
**Author**: Nicolas Cortes ([@nibcortes04](https://github.com/nibcortes04)) & Antigravity AI Orchestrator  
**Date**: September 2026  

---

## 1. Overview & Problem Statement

Autonomous agents operating on remote Virtual Private Servers (VPS) manage critical, production-grade infrastructure including:
- Reverse proxies and TLS terminators (Caddy).
- Live workflow orchestration platforms (n8n).
- Customer communication backends (Chatwoot).
- Persistent datastores (PostgreSQL, Redis) and Docker volumes.

Operating in standard `workspace-safe` or `full-developer` modes on a live VPS introduces severe risks:
1. **Unintended Service Outages**: Accidental restarts or halts of reverse proxies or core workflow containers interrupt active business workflows.
2. **Persistent Data Loss**: Careless volume removals (`docker volume rm`, `docker system prune -a`) or database flushes cause irreversible downtime.
3. **Live Configuration Corruptions**: Unchecked edits to `Caddyfile` or production `docker-compose.yml` can break ingress routing and SSL certificate renewals.

To solve this, Aegis introduces a first-class, production-hardened trust profile: **`vps-production`**. This profile deterministically enforces the **VPS Double Verification Protocol** in sub-10ms hook evaluation, guaranteeing that no destructive or service-altering operation can execute without explicit human approval.

---

## 2. Goals & Non-Goals

### Goals
- **First-Class Trust Level (`LEVEL_VPS_PRODUCTION`)**: Add `vps-production` to `scripts/trust_levels.py` with tailored permission classification.
- **Zero-Friction Safe Telemetry**: Allow non-destructive inspection commands (`docker ps`, `docker logs`, `docker inspect`, `systemctl status`, `journalctl`, `caddy validate`, `df`, `free`) without interactive prompts.
- **Mandatory Two-Factor Safety Gate for Lifecycle Actions**:
  - Intercept container restart, stop, kill, and rebuild operations (`docker stop`, `docker restart`, `docker compose down`, `docker compose restart`, `docker compose up -d`).
  - Intercept database operations (`psql`, `redis-cli flush*`, migration scripts).
  - Intercept volume or pruning operations (`docker volume rm`, `docker system prune`).
  - First attempt (`stage 1`): Hard block (`decision: "deny"`) requiring the agent to explain the risk and proposed action to the human user.
  - Second attempt (`stage 2` within 120s TTL): Elevated to interactive human confirmation (`decision: "ask"`).
- **Critical Production File Safeguard**:
  - Editing files named `Caddyfile`, `docker-compose.yml`, `docker-compose.prod.yml`, or `.env*` in production workspaces always requires interactive approval (`decision: "ask"`).
- **VPS Diagnostic Health Suite (`scripts/vps_health.py`)**:
  - Fast, read-only diagnostic scanner checking container states, disk/memory headroom, and listening ports.
  - Expose via MCP tool `aegis_check_vps_health` and CLI `python3 scripts/vps_health.py`.
- **Comprehensive Test Coverage**: Unit tests in `tests/test_vps_guardrails.py` verifying all `vps-production` transitions and invariants.

### Non-Goals
- Modifying remote server SSH keys or network firewall rules automatically.
- Replacing external monitoring platforms (Grafana, Datadog).
- Permitting automatic execution of destructive commands under any heuristic.

---

## 3. Architecture & Trust Hierarchy

### 3.1 Trust Hierarchy Integration
The `vps-production` profile sits directly below `audit`, providing specialized infrastructure safety:

```text
[Level 0]: audit              (Zero autonomy, prompts for every action)
[Level 1]: vps-production     (Safe telemetry allowed; container/service lifecycle gated by 2FA)
[Level 2]: workspace-safe     (Standard local dev: workspace writes & safe commands allowed)
[Level 3]: full-developer     (Local package installs, dev servers, git mutations)
[Level 4]: subagent-worker    (Worktree-scoped autonomy)
```

### 3.2 Activation Mechanisms
The `vps-production` level is activated via:
1. Environment variable: `export AGY_AUTO_MODE_LEVEL=vps-production`
2. Configuration file: `"autoModeLevel": "vps-production"` in `~/.gemini/antigravity-cli/settings.json`
3. Session mode flag: `--level vps-production`

---

## 4. Permission Classification Rules

### 4.1 Safe VPS Inspection Commands (Allowed)
These commands are strictly read-only and telemetry-focused:
```text
docker (ps|logs|inspect|top|stats --no-stream|port)
systemctl (status|is-active|is-failed)
journalctl (-n|-u|--no-pager)
caddy (validate|version)
git (status|diff|log|show|branch)
df (-h|-k), free (-m|-h), uptime, top (-b -n 1), htop, ps (aux|ef)
curl (-I|-sS), ping (-c)
cat, head, tail, grep, find, ls, pwd, which
```

### 4.2 Lifecycle Operations (Gated by Two-Factor Safety Gate: Deny -> Ask)
Modifying the state of production containers or services:
```text
docker (stop|restart|kill|pause|unpause)
docker compose (down|restart|stop|up|build)
docker-compose (down|restart|stop|up|build)
systemctl (stop|restart|reload|disable|mask)
caddy (reload|stop)
docker volume (rm|prune)
docker system prune
drop (database|table), truncate (table)
redis-cli (flushall|flushdb)
```

### 4.3 Critical Configuration File Guards
Any `write_to_file` or `replace_file_content` targeting:
- `*Caddyfile*`
- `*docker-compose*.yml`
- `*docker-compose*.yaml`
- `*.env*`
will immediately return `decision: "ask"` with notification and terminal bell.

---

## 5. VPS Health Diagnostic Module (`scripts/vps_health.py`)

A non-destructive Python diagnostic tool that returns structured JSON:
```json
{
  "timestamp": "2026-09-05T22:50:00Z",
  "status": "healthy",
  "containers": [
    {"name": "caddy", "status": "running", "uptime": "14 days"},
    {"name": "n8n", "status": "running", "uptime": "5 days"},
    {"name": "chatwoot_web", "status": "running", "uptime": "5 days"},
    {"name": "postgres", "status": "running", "uptime": "20 days"},
    {"name": "redis", "status": "running", "uptime": "20 days"}
  ],
  "system": {
    "disk_used_percent": 42.5,
    "memory_used_percent": 58.1,
    "load_average": [0.35, 0.42, 0.38]
  },
  "inotify": {
    "active_instances": 48,
    "max_instances": 128,
    "usage_percent": 37.5
  },
  "warnings": []
}
```

---

## 6. Implementation Plan & Delivery Steps

1. **`scripts/trust_levels.py`**:
   - Define `LEVEL_VPS_PRODUCTION = "vps-production"`.
   - Update `TRUST_LEVEL_HIERARCHY` mapping.
   - Define `VPS_SAFE_INSPECTION_PATTERNS` and `VPS_LIFECYCLE_COMMAND_PATTERNS`.
   - Integrate `vps-production` evaluation branch in `evaluate_trust()`.
   - Add file mutation gate for production configuration files (`Caddyfile`, `docker-compose`, `.env`).
2. **`scripts/vps_health.py`**:
   - Implement read-only health check logic with CLI support (`python3 scripts/vps_health.py --json` and `--pretty`).
3. **`mcp/mcp_server.py`**:
   - Expose `aegis_check_vps_health` MCP tool.
4. **Documentation & Rules**:
   - Update `rules/AGENTS.md` and `skills/aegis/references/auto_mode.md`.
5. **Unit Testing**:
   - Create `tests/test_vps_guardrails.py` covering all positive, negative, and two-step transition cases.
