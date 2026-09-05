import unittest
import sys
import os

# Agregar scripts al path y silenciar notificaciones en pruebas
os.environ["AGY_HOOK_SILENT"] = "1"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))
from agy_hook_handler import is_command_critical, handle_pre_tool_use, handle_stop

class TestHookClassifier(unittest.TestCase):
    def test_safe_read_tools(self):
        safe_tools = ["view_file", "list_dir", "grep_search", "find_by_name", "read_url_content"]
        for tool in safe_tools:
            payload = {"toolCall": {"name": tool, "args": {}}}
            res = handle_pre_tool_use(payload, "")
            self.assertEqual(res.get("decision"), "allow", f"Failed for {tool}")

    def test_safe_shell_commands(self):
        safe_commands = [
            "git status",
            "git diff HEAD~1",
            "pnpm test",
            "pnpm lint",
            "pytest",
            "cargo check",
            "ls -la",
            "cat README.md",
            "grep -rn 'foo' ."
        ]
        for cmd in safe_commands:
            self.assertFalse(is_command_critical(cmd), f"Should be safe: {cmd}")
            payload = {"toolCall": {"name": "run_command", "args": {"CommandLine": cmd}}}
            res = handle_pre_tool_use(payload, "")
            self.assertEqual(res.get("decision"), "allow", f"Failed decision for {cmd}")

    def test_critical_destructive_commands(self):
        critical_commands = [
            "rm -rf node_modules",
            "rm -fr /tmp/test",
            "rm -r -f build",
            "git push --force origin main",
            "git reset --hard HEAD~1",
            "docker rm -f container1",
            "docker stop my_service",
            "sudo apt-get update",
            "dd if=/dev/zero of=/dev/sda"
        ]
        for cmd in critical_commands:
            self.assertTrue(is_command_critical(cmd), f"Should be critical: {cmd}")
            payload = {"toolCall": {"name": "run_command", "args": {"CommandLine": cmd}}}
            res = handle_pre_tool_use(payload, "")
            self.assertEqual(res.get("decision"), "ask", f"Failed to block {cmd}")

    def test_workspace_file_edits(self):
        # Safe in-workspace file edit
        payload_safe = {"toolCall": {"name": "write_to_file", "args": {"TargetFile": "/home/n_n/projects/test.py"}}}
        res_safe = handle_pre_tool_use(payload_safe, "")
        self.assertEqual(res_safe.get("decision"), "allow")

        # Out-of-workspace file edit
        payload_crit = {"toolCall": {"name": "replace_file_content", "args": {"TargetFile": "/etc/resolv.conf"}}}
        res_crit = handle_pre_tool_use(payload_crit, "")
        self.assertEqual(res_crit.get("decision"), "ask")

    def test_stop_event_contract(self):
        payload = {"terminationReason": "model_stop", "fullyIdle": True, "conversationId": "test-uuid"}
        res = handle_stop(payload, "")
        self.assertEqual(res.get("decision"), "")

if __name__ == "__main__":
    unittest.main()
