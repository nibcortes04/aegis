# Specification: EPIC-11 — Bot Contributor Automation & Autonomous PR Review Gate

**Status**: In Review  
**Target Milestone**: `v1.6.0 - Advanced Ecosystem & Packaging`  
**Related Issue**: [#3](https://github.com/nibcortes04/aegis/issues/3)  
**Author**: Nicolas Cortes ([@nibcortes04](https://github.com/nibcortes04)) & Antigravity AI Orchestrator  
**Date**: September 2026  

---

## 1. Overview & Problem Statement

Aegis embraces multi-agent and autonomous bot contributors. Under the Aegis engineering protocol, specialized bots (such as `worker-backend`, `worker-frontend`, and `qa-tester`) operate inside isolated Git Worktrees (`./scripts/dev-worktree.sh new bot/<task-id>-<description>`) and submit Pull Requests targeting the `dev` branch.

Without an automated, deterministic quality gate, bot contributions risk introducing:
1. **Repository Hygiene Pollution**: Stray `.pyc` files, local scratch notes, or temporary cache files.
2. **Manifest Inconsistencies**: Broken `plugin.json` schemas or outdated version references.
3. **Silent Regressions**: Broken hook contracts or failing unit tests.
4. **Uncertain Merges**: Human maintainers spending valuable time manually re-running tests for every bot contribution.

To solve this, Aegis introduces the **Autonomous PR Review Gate**:
- A local pre-flight validator (`scripts/bot_pr_check.py`) for bots to self-certify their work before creating a PR.
- A GitHub Actions workflow (`.github/workflows/bot-pr-gate.yml`) that automatically runs full audits, verifies 100% test pass rates, applies `bot-verified` labels, and posts structured review reports.

---

## 2. Goals & Non-Goals

### Goals
- **Local Pre-Flight Validator (`scripts/bot_pr_check.py`)**:
  - Python CLI tool executing all quality gates locally with clean console output and exit codes (`0` for pass, `1` for fail).
- **Automated GitHub Actions Gate (`.github/workflows/bot-pr-gate.yml`)**:
  - Triggers on pull requests targeting `dev` (and `main`) when the head branch matches `bot/**` or contains the `bot` label.
  - Multi-stage pipeline:
    1. **Hygiene Audit**: Scans diff for forbidden patterns (scratch files, secrets, `.pyc`, cache artifacts).
    2. **Manifest Conformance**: Validates `plugin.json` and packaging integrity (`package_plugin.py --dry-run`).
    3. **Test Suite Execution**: Executes the full unit test suite with 100% pass requirement.
    4. **Hook Contracts**: Verifies all sub-10ms hook contracts via `tests/test_hooks.sh`.
    5. **Automated Feedback & Labeling**: Posts a standardized GitHub review comment and attaches the `bot-verified` label.
- **Bot Contributor Protocol Synchronization**:
  - Formalize worktree lifecycle and PR requirements in `.github/PROJECT_TASKS.md` and `rules/AGENTS.md`.
- **Comprehensive Test Coverage**:
  - Unit tests in `tests/test_bot_gate.py` verifying all audit logic and validator behaviors.

### Non-Goals
- Allowing bots to merge directly into `main` without human review.
- Modifying branch protection rules on GitHub.

---

## 3. Architecture & Verification Stages

```text
[Autonomous Bot in Git Worktree]
       │
       ▼
1. scripts/bot_pr_check.py (Local Self-Certification)
       │  (Must pass 100% before push)
       ▼
2. git push origin bot/<task-id>-<description>
       │
       ▼
3. Pull Request targeting 'dev'
       │
       ▼
4. GitHub Action: .github/workflows/bot-pr-gate.yml
   ├── Stage 1: Hygiene Audit (Zero-debris check)
   ├── Stage 2: Manifest & Packaging Check (package_plugin.py --dry-run)
   ├── Stage 3: Python Unit Test Suite (unittest discover -s tests)
   ├── Stage 4: Hook Contract Tests (tests/test_hooks.sh)
   └── Stage 5: Label 'bot-verified' & Post Structured Review
```

---

## 4. Local Pre-Flight Validator (`scripts/bot_pr_check.py`)

The validator executes the following checks in sequence:
1. **Git Worktree Hygiene**:
   - Verifies working directory is clean (`git status --porcelain`).
   - Ensures no forbidden file patterns exist in the git index or untracked tree:
     - `*.pyc`, `__pycache__`
     - `*.tmp`, `*.bak`, `*.swp`
     - `.DS_Store`, `Thumbs.db`
     - `scratch/*`, `*.log`
2. **Plugin Manifest Conformance**:
   - Invokes `package_plugin.py --dry-run`.
3. **Unit Test Suite**:
   - Runs `python3 -m unittest discover -s tests -p "test_*.py"`.
4. **Hook Contract Tests**:
   - Runs `./tests/test_hooks.sh`.

CLI usage:
```bash
python3 scripts/bot_pr_check.py
python3 scripts/bot_pr_check.py --json
```

---

## 5. GitHub Actions Workflow (`.github/workflows/bot-pr-gate.yml`)

The workflow runs on `ubuntu-latest`:
- Sets up Python 3.12/3.13.
- Runs `scripts/bot_pr_check.py`.
- If successful, uses `actions/github-script` to add the `bot-verified` label and comment on the PR.

---

## 6. Implementation Plan & Delivery Steps

1. **`scripts/bot_pr_check.py`**:
   - Implement local gate checker with hygiene, manifest, unit test, and hook contract verification.
2. **`.github/workflows/bot-pr-gate.yml`**:
   - Create GitHub Actions workflow file.
3. **`tests/test_bot_gate.py`**:
   - Unit tests for hygiene scanning, check execution, and result formatting.
4. **Documentation**:
   - Update `.github/PROJECT_TASKS.md` and `rules/AGENTS.md`.
