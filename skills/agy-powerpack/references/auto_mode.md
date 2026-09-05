# Smart Auto Mode Reference

The `agy-powerpack` Auto Mode brings the seamless execution experience of Claude Code's Auto Mode to Antigravity CLI while preserving critical safety boundaries.

---

## 1. How It Works

Antigravity executes a lifecycle hook on every tool invocation (`PreToolUse`). The classifier in `scripts/agy_hook_handler.py` evaluates the incoming tool call and its arguments in under 5 milliseconds.

### Permission Decisions:
- **`allow`**: Auto-approves execution immediately without pausing for human interaction.
- **`ask`**: Pauses execution, presents the interactive confirmation prompt to the user, rings the terminal bell (`\a`), and dispatches a notification.

---

## 2. Policy Matrix

| Category | Tools / Commands | Decision | Rationale |
| :--- | :--- | :--- | :--- |
| **Read-Only Tools** | `view_file`, `list_dir`, `grep_search`, `find_by_name`, `read_url_content`, `read_browser_page`, `search_web` | `allow` | Zero risk of state mutation. |
| **Workspace File Edits** | `write_to_file`, `replace_file_content` targeting paths within workspace (`/home/<user>/...`) | `allow` | Safe development edits in project workspace. |
| **Out-of-Workspace Edits** | File writes targeting system directories (`/etc/`, `/boot/`, etc.) | `ask` | Prevents unauthorized system modifications. |
| **Safe Shell Commands** | `git status/diff/log/branch`, `pnpm test/lint`, `pytest`, `cargo check`, `ls`, `cat`, `grep`, `pwd` | `allow` | Standard developer inspection and validation workflows. |
| **Destructive Commands** | `rm -rf`, `git push --force`, `git reset --hard`, `docker rm/stop`, `dd`, `mkfs`, `sudo`, `drop database` | `ask` | Irreversible or service-impacting operations require human consent. |

---

## 3. Configuration in settings.json

Ensure `settings.json` has:
```json
{
  "mode": "accept-edits"
}
```
You can cycle execution modes on the fly using `Shift+Tab`:
`request-review` -> `accept-edits` -> `plan`.
