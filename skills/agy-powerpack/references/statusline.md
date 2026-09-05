# Advanced Statusline Reference

The `agy-powerpack` statusline replicates the rich information density of Claude Code while remaining optimized for Antigravity's JSON payload.

---

## 1. Visual Layout

```text
[Gemini-3.8 Flash (High)] 📁 clortex-hermes 🌿 feat/powerpack +37-25 🧠 high 🏷️ 87c8834d
█░░░░░░░░░ 16% │ 💰 $0.0000 │ ⏱ 0m0s │ 5h:8%(🕦23:06) 7d:14%
▶▶ auto mode on (shift+tab to cycle) · ← for agents
```

### Breakdown:

#### Line 1: Identity & Version Control
- **`[Model]`**: Model display name in bold cyan.
- **`📁 Directory`**: Current workspace folder.
- **`🌿 Branch`**: Active Git branch in blue.
- **`+Add -Del`**: Live Git diff computed via `git diff --numstat HEAD` in green and red.
- **`🧠 Effort`**: Reasoning level (`low`, `med`, `high`, `xhigh`) from `.model.effort`.
- **`🏷️ Session`**: Session preview or custom name queried from `conversation_summaries.db`.

#### Line 2: Context Window, Cost & Quotas
- **`Context Bar`**: 10-block progress bar (`█` / `░`) color-coded:
  - Green: < 70%
  - Yellow: 70% - 90%
  - Red: >= 90%
- **`💰 Cost`**: Cumulative estimated session cost in USD.
- **`⏱ Duration`**: Total turn duration in minutes and seconds.
- **`5h Quota & Reset`**: Percentage of 5-hour quota used with local reset time `(🕦HH:MM)` converted from UTC.
- **`7d Quota`**: Percentage of weekly quota used.

#### Line 3: Execution Mode & Interaction
- **`▶▶ auto mode on (shift+tab to cycle)`**: Active when `cycle_mode` is `accept-edits`.
- **`⏸ plan mode`**: Active when in planning mode.
- **`▶ request-review`**: Active when in default review mode.

---

## 2. Performance Guarantee
The statusline script executes in under **10ms**, avoiding any flickering or lag in the bubbletea TUI.
