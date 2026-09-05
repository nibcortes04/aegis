# Specification: EPIC-14 — Official Antigravity Plugin Registry Packaging

**Status**: In Progress  
**Target Milestone**: `v1.6.0 - Advanced Ecosystem & Packaging`  
**Related Issue**: [#6](https://github.com/nibcortes04/aegis/issues/6)  
**Author**: nibcortes04 / Antigravity AI Orchestrator  
**Date**: September 2026  

---

## 1. Overview & Problem Statement

Antigravity CLI plugins require a standardized, self-contained bundle structure to enable seamless distribution, validation, and installation across machines.

Currently, Aegis is installed either via Git repository clone (`install.sh`) or manual link. To support the upcoming **Google Antigravity Plugin Registry** (`agy plugin publish`) and direct archive installations (`agy plugin install <url|archive>`), Aegis requires:
1. An automated packaging utility (`scripts/package_plugin.py`).
2. Manifest validation adhering strictly to Google Antigravity Plugin specifications.
3. Cryptographic integrity guarantees via SHA-256 checksums.
4. An automated continuous release pipeline (`.github/workflows/release.yml`) triggering on version tags (`v*`).

---

## 2. Goals & Non-Goals

### Goals
- **Manifest Conformance**: Validate `plugin.json` schema (name, version, author, description, license, keywords) before packaging.
- **Zero-Artifact Hygiene**: Ensure distribution archives exclude all local development scratch, cache directories, git history, test suites, and temporary files.
- **Dual Archive Format**: Generate both `.tar.gz` (Unix/Linux/macOS) and `.zip` (Windows/Universal).
- **Cryptographic Verification**: Compute and output `dist/checksums.sha256` matching standard GNU coreutils `sha256sum` format.
- **Bundle Self-Integrity Check**: The packaging script must perform a self-test by extracting the generated bundle into an isolated temporary directory and validating that all required runtime files exist and can be loaded.
- **Automated GitHub Release**: Deploy GitHub Actions workflow to publish releases with compiled assets upon tag push.

### Non-Goals
- Hosting a standalone proprietary registry server.
- Modifying local user configurations during packaging.

---

## 3. Bundle Structure & Ingestion Rules

### 3.1 Included Files (Allowlist / Essential Runtime)
The distribution bundle MUST include:
```text
aegis/
├── plugin.json               # Required manifest
├── hooks.json                # Lifecycle hooks configuration
├── README.md                 # Documentation
├── LICENSE                   # MIT License
├── rules/
│   └── AGENTS.md             # Global agent rules and security policies
├── skills/
│   └── aegis/
│       ├── SKILL.md          # Skill definitions
│       └── references/       # Modular documentation guides
├── mcp/
│   └── mcp_server.py         # MCP Server exposing aegis_* tools
└── scripts/
    ├── agy_hook_handler.py    # Auto mode, notifications, bell dispatcher
    ├── statusline_formatter.py # Visual statusline engine
    ├── env_detector.py        # Cross-platform environment detector
    ├── trust_levels.py        # Graduated trust levels engine
    ├── env_inspector.py       # Diagnostic inspection tool
    ├── dev-worktree.sh        # Git worktree orchestration script
    └── agy-hook-dispatcher.sh # Shell hook wrapper
```

### 3.2 Excluded Files (Denylist / Dev Junk)
The packaging tool MUST strictly exclude:
- `.git/` and git submodules
- `.github/` (CI workflows and templates)
- `tests/` and test mock files
- `docs/` (Web landing page assets; hosted separately on GitHub Pages)
- `__pycache__/`, `*.pyc`, `*.pyo`
- `.pytest_cache/`, `.coverage`
- `.user_uploaded/`, `.tempmediaStorage/`, `scratch/`
- `.env*`, `*.log`
- `dist/`, `build/`

---

## 4. Technical Architecture

### 4.1 Packaging Utility (`scripts/package_plugin.py`)
The packaging script is a zero-dependency Python 3 utility with CLI arguments:
- `--output-dir / -o`: Output directory (defaults to `dist/`).
- `--verify`: Run self-test extraction after building archives (enabled by default).
- `--dry-run`: Validate manifest and list files to be packaged without writing archives.
- `--version`: Display manifest version.

**Exit Codes**:
- `0`: Validation and packaging succeeded.
- `1`: Manifest validation error or missing required file.
- `2`: Bundle integrity verification failure.

### 4.2 Release CI/CD Workflow (`.github/workflows/release.yml`)
1. **Trigger**: `push: tags: ['v*']`.
2. **Environment**: `ubuntu-latest`, Python 3.10+.
3. **Steps**:
   - Checkout code.
   - Run unit test discovery (`python3 -m unittest discover -s tests`).
   - Run hook contract tests (`./tests/test_hooks.sh`).
   - Run packager: `python3 scripts/package_plugin.py --output-dir dist/`.
   - Create GitHub Release using `gh release create` or `softprops/action-gh-release@v2`.
   - Upload `dist/aegis-*.tar.gz`, `dist/aegis-*.zip`, and `dist/checksums.sha256`.

---

## 5. Verification Plan

1. **Unit Tests (`tests/test_packager.py`)**:
   - `test_manifest_validation`: Verifies required keys (`name`, `version`, `author`, `license`).
   - `test_archive_generation`: Verifies creation of `.tar.gz` and `.zip`.
   - `test_exclusions_respected`: Verifies `tests/`, `.git/`, and `__pycache__` are absent in the archive.
   - `test_checksum_validity`: Verifies `checksums.sha256` correctly validates against generated archives.
2. **End-to-End Dry Run**:
   - Execute `python3 scripts/package_plugin.py`.
   - Inspect tarball contents with `tar -tzf`.
   - Run `sha256sum -c dist/checksums.sha256`.
