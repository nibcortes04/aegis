import unittest
import os
import sys
import tempfile
import json

os.environ["AGY_HOOK_SILENT"] = "1"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))
import env_inspector

class TestEnvInspector(unittest.TestCase):
    def test_inspect_environment_structure(self):
        profile = env_inspector.inspect_environment()
        self.assertIn("system", profile)
        self.assertIn("detected_tools", profile)
        self.assertIn("total_tools_found", profile)
        self.assertIn("safe_allowlist", profile)
        self.assertIn("recommended_level", profile)

        # Verificar campos de sistema
        sys_info = profile["system"]
        self.assertIn("os_type", sys_info)
        self.assertIn("terminal", sys_info)
        self.assertIn("surface", sys_info)

        # Debe contener herramientas base en allowlist
        self.assertIn("command(git)", profile["safe_allowlist"])
        self.assertIn("command(ls)", profile["safe_allowlist"])

    def test_apply_profile_idempotent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = os.path.join(tmpdir, "settings.json")
            initial_settings = {
                "mode": "accept-edits",
                "permissions": {
                    "allow": ["command(git)", "command(ls)"]
                }
            }
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(initial_settings, f)

            profile = env_inspector.inspect_environment()
            profile_file, added = env_inspector.apply_profile(profile, settings_path=settings_path)

            self.assertTrue(os.path.isfile(settings_path))
            with open(settings_path, "r", encoding="utf-8") as f:
                updated = json.load(f)

            self.assertIn("permissions", updated)
            self.assertIn("allow", updated["permissions"])
            self.assertTrue(len(updated["permissions"]["allow"]) >= len(initial_settings["permissions"]["allow"]))

            # Segunda aplicación: no debe añadir duplicados
            _, second_added = env_inspector.apply_profile(profile, settings_path=settings_path)
            self.assertEqual(second_added, 0)

if __name__ == "__main__":
    unittest.main()
