import unittest
import sys
import os
from unittest.mock import patch

os.environ["AGY_HOOK_SILENT"] = "1"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))
from trust_levels import (
    evaluate_trust,
    get_active_trust_level,
    LEVEL_AUDIT,
    LEVEL_WORKSPACE_SAFE,
    LEVEL_FULL_DEVELOPER,
    LEVEL_SUBAGENT_WORKER
)

class TestTrustLevels(unittest.TestCase):
    def test_level_audit_blocks_all_mutations(self):
        # Read tools allowed
        dec, _ = evaluate_trust("view_file", {"AbsolutePath": "/tmp/test"}, level=LEVEL_AUDIT)
        self.assertEqual(dec, "allow")

        # In-workspace edit blocked in audit
        dec, _ = evaluate_trust("write_to_file", {"TargetFile": "/home/n_n/project/a.py"}, level=LEVEL_AUDIT)
        self.assertEqual(dec, "ask")

        # Safe read command blocked in audit
        dec, _ = evaluate_trust("run_command", {"CommandLine": "git status"}, level=LEVEL_AUDIT)
        self.assertEqual(dec, "ask")

    def test_level_workspace_safe_permissions(self):
        # Reads allowed
        dec, _ = evaluate_trust("list_dir", {}, level=LEVEL_WORKSPACE_SAFE)
        self.assertEqual(dec, "allow")

        # Safe dev commands allowed
        for cmd in ["git status", "git diff", "pnpm test", "pytest", "ls -la"]:
            dec, _ = evaluate_trust("run_command", {"CommandLine": cmd}, level=LEVEL_WORKSPACE_SAFE)
            self.assertEqual(dec, "allow", f"Expected allow for {cmd}")

        # Mutating package installs blocked in workspace-safe (requires dev level)
        dec, _ = evaluate_trust("run_command", {"CommandLine": "pnpm add lodash"}, level=LEVEL_WORKSPACE_SAFE)
        self.assertEqual(dec, "ask")

        # Critical commands blocked
        dec, _ = evaluate_trust("run_command", {"CommandLine": "rm -rf build"}, level=LEVEL_WORKSPACE_SAFE)
        self.assertEqual(dec, "ask")

    def test_level_full_developer_permissions(self):
        # Developer extended commands allowed
        dev_cmds = [
            "pnpm add express",
            "pnpm install",
            "pip install requests",
            "cargo add serde",
            "pnpm dev",
            "git commit -m 'feat: update'",
            "git branch new-feat",
            "docker compose up -d"
        ]
        for cmd in dev_cmds:
            dec, _ = evaluate_trust("run_command", {"CommandLine": cmd}, level=LEVEL_FULL_DEVELOPER)
            self.assertEqual(dec, "allow", f"Expected allow for {cmd}")

        # Irreversible destruction commands still blocked
        crit_cmds = [
            "rm -rf /",
            "git push --force origin main",
            "git reset --hard HEAD~1",
            "dd if=/dev/zero of=/dev/sda",
            "sudo apt-get update",
            "drop database production"
        ]
        for cmd in crit_cmds:
            dec, _ = evaluate_trust("run_command", {"CommandLine": cmd}, level=LEVEL_FULL_DEVELOPER)
            self.assertEqual(dec, "ask", f"Expected ask for {cmd}")

    def test_dynamic_trust_level_env_detection(self):
        with patch.dict(os.environ, {"AGY_AUTO_MODE_LEVEL": "audit"}):
            self.assertEqual(get_active_trust_level(), LEVEL_AUDIT)

        with patch.dict(os.environ, {"AGY_AUTO_MODE_LEVEL": "full-developer"}):
            self.assertEqual(get_active_trust_level(), LEVEL_FULL_DEVELOPER)

        with patch.dict(os.environ, {"AGY_AUTO_MODE_LEVEL": "dev"}):
            self.assertEqual(get_active_trust_level(), LEVEL_FULL_DEVELOPER)

        with patch.dict(os.environ, {"AGY_AUTO_MODE_LEVEL": "workspace-safe"}):
            self.assertEqual(get_active_trust_level(), LEVEL_WORKSPACE_SAFE)

if __name__ == "__main__":
    unittest.main()
