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
        self.assertEqual(res["result"]["serverInfo"]["name"], "agy-powerpack-mcp")

    def test_tools_list(self):
        req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        res = process_message(req)
        tools = res["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        self.assertIn("powerpack_get_trust_levels", tool_names)
        self.assertIn("powerpack_get_surface_info", tool_names)
        self.assertIn("powerpack_get_delegation_guide", tool_names)
        self.assertIn("powerpack_verify_system", tool_names)

    def test_call_get_trust_levels(self):
        req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "powerpack_get_trust_levels",
                "arguments": {"level": "full-developer"}
            }
        }
        res = process_message(req)
        content_text = res["result"]["content"][0]["text"]
        data = json.loads(content_text)
        self.assertIn("full-developer", data)

    def test_call_verify_system(self):
        req = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "powerpack_verify_system",
                "arguments": {}
            }
        }
        res = process_message(req)
        content_text = res["result"]["content"][0]["text"]
        data = json.loads(content_text)
        self.assertEqual(data["status"], "healthy")

if __name__ == "__main__":
    unittest.main()
