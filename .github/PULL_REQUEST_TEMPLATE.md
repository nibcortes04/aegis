## Pull Request Type
Select the option that applies:
- [ ] 🐛 Bug Fix (`fix/...`)
- [ ] ✨ Feature Addition (`feat/...`)
- [ ] 🤖 Bot Autonomous Fix (`bot/...`)
- [ ] 📚 Documentation (`docs/...`)
- [ ] ♻️ Refactor / Performance (`refactor/...`)

---

## Author & Agent Metadata
- **Contributor Type**: [ ] Human Developer / [ ] Autonomous Agent Bot
- **Agent Name / CLI Version (if bot)**: (e.g. `Gemini Antigravity 2.5`, `Codex CLI`, `Claude Code`)
- **Git Worktree Path**: `worktrees/<branch-name>`
- **Source Branch**: `<type>/<short-description>` (targeting `dev`)

---

## Linked Issue
Closes # (or References #)

---

## Description of Changes
A concise summary of what this PR introduces, modifies, or fixes:
- 

---

## Development & Worktree Protocol Verification
Please confirm that the contribution complies with our development protocol:
- [ ] **Git Worktree Isolation**: Developed and tested in an isolated worktree created via `./scripts/dev-worktree.sh new <branch>` (main workspace left intact).
- [ ] **Target Branch**: PR targets branch `dev` (direct PRs to `main` are restricted).
- [ ] **Syntax Checks**: Passed `python3 -m py_compile` and `bash -n`.
- [ ] **Unit Tests**: Passed `python3 -m unittest discover -s tests -p "test_*.py"`.
- [ ] **Hook Contract Integration**: Passed `./tests/test_hooks.sh`.
- [ ] **Plugin Schema**: Verified with `agy plugin validate .`.
- [ ] **Documentation**: Updated `docs/` or `skills/agy-powerpack/references/` if behavior changed.

---

## Verification Logs
```text
Paste test output or execution evidence here
```
