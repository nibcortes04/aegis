# Smart Auto Mode Reference

The `Aegis` Auto Mode brings the seamless execution experience of Claude Code's Auto Mode to Antigravity CLI while preserving critical safety boundaries.

---

## 1. How It Works

Antigravity executes a lifecycle hook on every tool invocation (`PreToolUse`). The classifier in `scripts/agy_hook_handler.py` evaluates the incoming tool call and its arguments in under 5 milliseconds.

### Permission Decisions:
- **`allow`**: Auto-approves execution immediately without pausing for human interaction.
- **`ask`**: Pauses execution, presents the interactive confirmation prompt to the user, rings the terminal bell (`\a`), and dispatches a notification.

---

## 2. Graduated Trust Levels

Aegis implements 5 graduated trust profiles tailored to different operating contexts:

| Level | Identifier | Focus | Key Behavior |
| :--- | :--- | :--- | :--- |
| **0** | `audit` | Zero-Trust | Requires human confirmation for all file edits and shell commands. |
| **1** | `vps-production` | VPS Infrastructure | Non-destructive telemetry allowed; container/service lifecycle (`docker restart/stop`, `systemctl`) and critical configs (`Caddyfile`, `docker-compose`, `.env`) require 2FA. |
| **2** | `workspace-safe` | Standard Dev | Edits inside workspace and inspection commands allowed; mutating installs and destructive commands blocked. |
| **3** | `full-developer` | Agile Prototyping | Package installs (`pnpm add`, `pip install`), local servers, and git branches allowed; irreversible damage blocked. |
| **4** | `subagent-worker` | Multi-Agent Worktrees | Autonomy scoped strictly within assigned Git Worktree directory. |

---

## 3. Configuration in settings.json

Set your default auto mode level in `~/.gemini/antigravity-cli/settings.json`:
```json
{
  "mode": "accept-edits",
  "autoModeLevel": "vps-production"
}
```
Or via environment variable:
```bash
export AGY_AUTO_MODE_LEVEL="vps-production"
```
You can cycle execution modes on the fly using `Shift+Tab`:
`request-review` -> `accept-edits` -> `plan`.
