# Security Policy

## 🛡️ Threat Model & Security Principles

**AGY PowerPack** is engineered for high-velocity software development while adhering to the principle of least privilege and strict local execution safety.

### 1. Fail-Closed Philosophy
Antigravity's hook subsystem is implemented in Go with a **fail-closed contract**. If any hook crashes, times out, or produces unexpected stdout, the tool execution is denied by default.
Our hook classifier (`scripts/agy_hook_handler.py`) rigorously follows this:
- If a command cannot be verified as safe, it automatically returns `{"decision": "ask"}` to hand control back to the human operator.
- Edits to files located outside the active workspace or user directory automatically trigger a human confirmation prompt.

### 2. Guardrails Against Destructive Commands
The following command families are hardcoded as **Critical** and will **NEVER** be auto-approved under Auto Mode:
- Recursive/forced deletions (`rm -rf`, `rm -fr`, `rm -r -f`, `rm --recursive --force`)
- Destructive Git operations (`git push --force`, `git reset --hard`, `git clean -f`)
- Container lifecycle terminations (`docker rm`, `docker kill`, `docker stop`, `docker system prune`)
- Disk and filesystem manipulation (`dd if=`, `mkfs`, `fdisk`, `parted`)
- System state altering commands (`shutdown`, `reboot`, `sudo`, `init 0`)
- Database structural deletions (`drop database`)

### 3. Local Isolation & Zero Telemetry
- No remote telemetry: statusline and notification scripts run 100% locally on your machine.
- No network requests are made during hook execution (sub-10ms performance requirement).
- All session titles and previews are queried strictly from your local SQLite cache (`conversation_summaries.db`).

---

## 🔒 Reporting a Security Vulnerability

If you discover a vulnerability or security bypass in the command classifier:
1. **Do not disclose publicly** in GitHub issues.
2. Please draft a report detailing:
   - The bypass command or scenario.
   - The unexpected behavior (`decision: allow` instead of `decision: ask`).
   - Suggested regex or classification fix.
3. Open a private security advisory on GitHub or email the repository maintainers.
