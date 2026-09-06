import unittest
import sys
import os
import json

os.environ["AGY_HOOK_SILENT"] = "1"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../mcp")))
from mcp_server import process_message

class TestMCPServer(unittest.TestCase):
    def test_initialize_handshake(self):
        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"}
        }
        res = process_message(req)
        self.assertIsNotNone(res)
        self.assertEqual(res["result"]["serverInfo"]["name"], "aegis-mcp")
        self.assertEqual(res["result"]["serverInfo"]["version"], "1.5.0")

    def test_tools_list(self):
        req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        res = process_message(req)
        tools = res["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        # Primary Aegis tools
        self.assertIn("aegis_get_trust_levels", tool_names)
        self.assertIn("aegis_get_surface_info", tool_names)
        self.assertIn("aegis_get_delegation_guide", tool_names)
        self.assertIn("aegis_verify_system", tool_names)
        self.assertIn("aegis_inspect_environment", tool_names)
        self.assertIn("aegis_doctor_terminal", tool_names)
        # Backward compatibility aliases
        self.assertIn("powerpack_get_trust_levels", tool_names)
        self.assertIn("powerpack_get_surface_info", tool_names)
        self.assertIn("powerpack_get_delegation_guide", tool_names)
        self.assertIn("powerpack_verify_system", tool_names)
        self.assertIn("powerpack_inspect_environment", tool_names)

    def test_call_get_trust_levels_native(self):
        req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "aegis_get_trust_levels",
                "arguments": {"level": "full-developer"}
            }
        }
        res = process_message(req)
        content_text = res["result"]["content"][0]["text"]
        data = json.loads(content_text)
        self.assertIn("full-developer", data)

    def test_call_get_trust_levels_alias(self):
        req = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "powerpack_get_trust_levels",
                "arguments": {"level": "audit"}
            }
        }
        res = process_message(req)
        content_text = res["result"]["content"][0]["text"]
        data = json.loads(content_text)
        self.assertIn("audit", data)

    def test_call_verify_system(self):
        req = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "aegis_verify_system",
                "arguments": {}
            }
        }
        res = process_message(req)
        content_text = res["result"]["content"][0]["text"]
        data = json.loads(content_text)
        self.assertEqual(data["status"], "healthy")

    def test_call_inspect_environment(self):
        req = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "aegis_inspect_environment",
                "arguments": {"apply": False}
            }
        }
        res = process_message(req)
        content_text = res["result"]["content"][0]["text"]
        data = json.loads(content_text)
        self.assertIn("system", data)
        self.assertIn("detected_tools", data)

    def test_call_doctor_terminal(self):
        req = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "aegis_doctor_terminal",
                "arguments": {"test_bell": False, "test_chime": False}
            }
        }
        res = process_message(req)
        content_text = res["result"]["content"][0]["text"]
        data = json.loads(content_text)
        self.assertIn("terminal", data)
        self.assertIn("audio", data)

if __name__ == "__main__":
    unittest.main()
