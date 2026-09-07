import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json
import subprocess

os.environ["AGY_HOOK_SILENT"] = "1"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))

import mobile_wizard


class TestMobileWizard(unittest.TestCase):
    def test_pairing_info_structure(self):
        """Verifica que get_pairing_info devuelva el esquema completo requerido."""
        info = mobile_wizard.get_pairing_info()
        self.assertIn("pwa_url", info)
        self.assertEqual(info["pwa_url"], "https://antigravity.google")
        self.assertIn("platform", info)
        self.assertIn("daemon", info)
        self.assertIn("steps", info)
        self.assertGreaterEqual(len(info["steps"]), 4)
        self.assertIn("daemon_commands", info)
        self.assertIn("features", info)

    def test_check_daemon_status_when_agy_not_found(self):
        """Verifica el fallback limpio cuando agy no está en PATH."""
        with patch("shutil.which", return_value=None):
            status = mobile_wizard.check_daemon_status()
            self.assertFalse(status["installed"])
            self.assertFalse(status["running"])
            self.assertIn("no encontrado", status["detail"])

    def test_check_daemon_status_running(self):
        """Verifica la detección de daemon activo."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "Daemon status: active (running)"
        mock_proc.stderr = ""

        with patch("shutil.which", return_value="/usr/bin/agy"), \
             patch("subprocess.run", return_value=mock_proc):
            status = mobile_wizard.check_daemon_status()
            self.assertTrue(status["installed"])
            self.assertTrue(status["running"])

    def test_cli_json_mode(self):
        """Verifica que scripts/mobile_wizard.py --json retorne código 0 y JSON válido."""
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        script_path = os.path.join(repo_root, "scripts", "mobile_wizard.py")
        env = os.environ.copy()
        env["AGY_HOOK_SILENT"] = "1"
        res = subprocess.run(
            [sys.executable, script_path, "--json"],
            capture_output=True,
            text=True,
            timeout=10.0,
            env=env,
            cwd=repo_root
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["pwa_url"], "https://antigravity.google")

    def test_bin_aegis_mobile_dispatcher(self):
        """Verifica que bin/aegis mobile --json despache correctamente."""
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        aegis_bin = os.path.join(repo_root, "bin", "aegis")
        env = os.environ.copy()
        env["AGY_HOOK_SILENT"] = "1"
        res = subprocess.run(
            [sys.executable, aegis_bin, "mobile", "--json"],
            capture_output=True,
            text=True,
            timeout=10.0,
            env=env,
            cwd=repo_root
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertIn("steps", data)


if __name__ == "__main__":
    unittest.main()
