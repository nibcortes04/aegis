# Antigravity Powerpack Guidelines

When operating within a project using the `agy-powerpack` plugin:

## 1. Auto Mode and Safe Execution
- Favor safe, idempotent operations that can be automatically approved by the classifier.
- Keep commands prefix-matchable (`git status`, `git diff`, `pnpm test`, `pytest`).
- Avoid running compound dangerous commands (e.g. `rm -rf`, `git push --force`) unless explicitly instructed by the user.
- If a command requires root/sudo or alters files outside the workspace, state the risk clearly before attempting execution.

## 2. Notification Awareness
- The user is automatically notified via terminal bell (`\a`) and desktop notifications when a turn completes or when approval is needed.
- Keep user-facing prompts concise and direct.

## 3. Session Continuity
- When switching tasks or working on separate features, guide the user to create a dedicated Git worktree or resume prior sessions with `/resume` or `agy -c`.
