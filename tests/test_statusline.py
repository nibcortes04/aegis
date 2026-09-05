import unittest
import sys
import os
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))
from statusline_formatter import format_statusline

def strip_ansi(text):
    ansi_regex = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_regex.sub("", text)

class TestStatuslineFormatter(unittest.TestCase):
    def setUp(self):
        self.mock_payload = {
            "model": {
                "display_name": "Gemini 2.5 Pro",
                "effort": "high"
            },
            "cwd": "/home/n_n/projects/agy-powerpack",
            "conversation_id": "test-1234-abcd",
            "context_window": {
                "used_percentage": 35.0
            },
            "cost": {
                "total_cost_usd": 0.0421,
                "total_duration_ms": 125000
            },
            "quota": {
                "gemini-5h": {
                    "remaining_fraction": 0.45,
                    "reset_time": "2026-09-05T04:30:00Z"
                },
                "gemini-weekly": {
                    "remaining_fraction": 0.88
                }
            },
            "cycle_mode": "accept-edits"
        }

    def test_full_statusline_rendering(self):
        output = format_statusline(self.mock_payload)
        self.assertIsNotNone(output)
        lines = output.splitlines()
        self.assertEqual(len(lines), 3)

        clean_l1 = strip_ansi(lines[0])
        clean_l2 = strip_ansi(lines[1])
        clean_l3 = strip_ansi(lines[2])

        # Line 1: Model, directory, effort
        self.assertIn("[Gemini-2.5 Pro]", clean_l1)
        self.assertIn("📁 agy-powerpack", clean_l1)
        self.assertIn("🧠 high", clean_l1)

        # Line 2: Context bar, cost, duration, 5h and 7d quota
        self.assertIn("35%", clean_l2)
        self.assertIn("$0.0421", clean_l2)
        self.assertIn("⏱ 2m5s", clean_l2)
        # 1.0 - 0.45 = 55% used
        self.assertIn("5h:55%", clean_l2)
        # 1.0 - 0.88 = 12% used
        self.assertIn("7d:12%", clean_l2)

        # Line 3: Cycle mode
        self.assertIn("auto mode on", clean_l3)
        self.assertIn("(shift+tab to cycle)", clean_l3)

    def test_high_context_and_quota_alerts(self):
        alert_payload = {
            "model": {"id": "gemini-flash"},
            "context_window": {"used_percentage": 92.0},
            "quota": {
                "gemini-5h": {"remaining_fraction": 0.10} # 90% used
            }
        }
        output = format_statusline(alert_payload)
        lines = output.splitlines()
        # Should contain ANSI RED (\033[31m) for 92% context and 90% quota
        self.assertIn("\033[31m", lines[1])
        clean_l2 = strip_ansi(lines[1])
        self.assertIn("92%", clean_l2)
        self.assertIn("5h:90%", clean_l2)

    def test_empty_and_fallback_resilience(self):
        # Empty dict should not raise exception and output 3 lines
        output = format_statusline({})
        self.assertIsNotNone(output)
        lines = output.splitlines()
        self.assertEqual(len(lines), 3)
        clean_l3 = strip_ansi(lines[2])
        self.assertIn("auto mode on", clean_l3)

    def test_plan_mode_indicator(self):
        plan_payload = {"cycle_mode": "plan"}
        output = format_statusline(plan_payload)
        clean_l3 = strip_ansi(output.splitlines()[2])
        self.assertIn("plan mode", clean_l3)

if __name__ == "__main__":
    unittest.main()
