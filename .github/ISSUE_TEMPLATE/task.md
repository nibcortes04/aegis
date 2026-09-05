---
name: Task / Sprint Item
about: Create a discrete engineering task for humans or autonomous agent bots
title: "[TASK] "
labels: ["task"]
assignees: ""
---

## Task Objective
Clear and concise description of the engineering objective.

## Epic / Backlog Link
- Linked Epic in `PROJECT_TASKS.md`: (e.g. `EPIC-04`, `TASK-102`)

## Scope & Target Surfaces
Check all that apply:
- [ ] Operating System: [ ] Linux [ ] macOS [ ] Windows
- [ ] Antigravity Surface: [ ] CLI [ ] IDE [ ] Desktop App
- [ ] Subsystem: [ ] Hooks [ ] Statusline [ ] MCP [ ] Agents [ ] Skills

## Acceptance Criteria
- [ ] Implementation complete and adheres to fail-closed principles.
- [ ] All unit and integration tests passing (`python3 -m unittest discover`).
- [ ] Zero unhandled exceptions on invalid JSON inputs.
- [ ] Developed inside dedicated Git worktree (`scripts/dev-worktree.sh`).
- [ ] Targeted at branch `dev`.
