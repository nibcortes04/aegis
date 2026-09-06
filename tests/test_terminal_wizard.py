import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json
import subprocess

os.environ["AGY_HOOK_SILENT"] = "1"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))

import terminal_wizard
import env_detector


class TestTerminalWizard(unittest.TestCase):
    def test_detect_terminal_all_profiles(self):
        """Verifica la detección heurística de todos los emuladores de terminal soportados."""
        cases = [
            ({"KONSOLE_VERSION": "240800"}, "konsole"),
            ({"ORCA_PANE_KEY": "pane-1"}, "orca"),
            ({"ORCA_TERMINAL": "1"}, "orca"),
            ({"KITTY_WINDOW_ID": "12"}, "kitty"),
            ({"ALACRITTY_LOG": "/tmp/alacritty.log"}, "alacritty"),
            ({"TERM": "alacritty-direct"}, "alacritty"),
            ({"WT_SESSION": "guid-123"}, "windows_terminal"),
            ({"GHOSTTY_RESOURCES_DIR": "/usr/share/ghostty"}, "ghostty"),
            ({"TERM": "xterm-ghostty"}, "ghostty"),
            ({"WEZTERM_PANE": "pane-0"}, "wezterm"),
            ({"GNOME_TERMINAL_SCREEN": "screen-1"}, "gnome_terminal"),
            ({"PTYXIS_VERSION": "47.0"}, "gnome_terminal"),
            ({"TERM_PROGRAM": "mintty"}, "mintty"),
            ({"MSYSTEM": "MINGW64"}, "mintty"),
            ({"ITERM_SESSION_ID": "iterm-123"}, "iterm"),
            ({"TERM_PROGRAM": "iTerm.app"}, "iterm"),
            ({"TERM_PROGRAM": "vscode"}, "vscode"),
            ({"TERM_PROGRAM": "Apple_Terminal"}, "apple_terminal"),
            ({"TMUX": "/tmp/tmux-1000/default,123,0"}, "tmux"),
            ({}, "generic"),
        ]

        for env_vars, expected_id in cases:
            with patch.dict(os.environ, env_vars, clear=True):
                detected = terminal_wizard.detect_terminal_id()
                self.assertEqual(detected, expected_id, f"Fallo al detectar con {env_vars}")

    def test_terminal_profiles_metadata_integrity(self):
        """Verifica que todos los perfiles de terminal contengan las claves y contratos esperados."""
        for term_id, profile in terminal_wizard.TERMINAL_PROFILES.items():
            self.assertIn("name", profile)
            self.assertIn("vendor", profile)
            self.assertIn("capabilities", profile)
            self.assertIn("config_path", profile)
            self.assertIn("config_snippet", profile)
            self.assertIn("tips", profile)
            self.assertIn("score", profile)

            caps = profile["capabilities"]
            for req_cap in ["ascii_bel", "tab_badge", "visual_flash", "osc_notification", "audio_bell"]:
                self.assertIn(req_cap, caps)

    def test_inspect_terminal_returns_valid_structure(self):
        """Verifica que inspect_terminal devuelva el esquema completo requerido."""
        res = terminal_wizard.inspect_terminal()
        self.assertIn("id", res)
        self.assertIn("name", res)
        self.assertIn("vendor", res)
        self.assertIn("capabilities", res)
        self.assertIn("config_path", res)
        self.assertIn("config_snippet", res)
        self.assertIn("tips", res)
        self.assertIn("compatibility_score", res)
        self.assertIn("has_dev_tty", res)
        self.assertIn("is_interactive", res)
        self.assertIn("environment_signals", res)

    def test_detect_audio_subsystem(self):
        """Verifica la detección del subsistema de audio y archivos de temas."""
        audio = terminal_wizard.detect_audio_subsystem()
        self.assertIn("supported", audio)
        self.assertIn("primary_backend", audio)
        self.assertIn("available_backends", audio)
        self.assertIn("sound_files", audio)
        self.assertIn("platform", audio)

    def test_play_subtle_chime_silent_mode(self):
        """Verifica que el chime se silencie automáticamente si AGY_HOOK_SILENT está activo."""
        with patch.dict(os.environ, {"AGY_HOOK_SILENT": "1"}, clear=False):
            res = terminal_wizard.play_subtle_chime("complete")
            self.assertFalse(res["success"])
            self.assertEqual(res["reason"], "silent_mode_active")

        with patch.dict(os.environ, {"AGY_HOOK_SILENT": "0", "AEGIS_SILENT": "1"}, clear=False):
            res = terminal_wizard.play_subtle_chime("complete")
            self.assertFalse(res["success"])
            self.assertEqual(res["reason"], "silent_mode_active")

    def test_test_terminal_bell(self):
        """Verifica que la emisión de BEL se complete sin lanzar excepciones."""
        res = terminal_wizard.test_terminal_bell()
        self.assertTrue(res["success"])
        self.assertIn(res["channel"], ["/dev/tty", "stderr"])

    def test_run_terminal_doctor_quiet_mode(self):
        """Verifica que run_terminal_doctor(quiet=True) no imprima nada y retorne el reporte."""
        report = terminal_wizard.run_terminal_doctor(quiet=True)
        self.assertIn("terminal", report)
        self.assertIn("audio", report)
        self.assertIn("tests", report)

    def test_cli_terminal_wizard_json(self):
        """Verifica la ejecución de terminal_wizard.py con bandera --json."""
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        script_path = os.path.join(repo_root, "scripts", "terminal_wizard.py")
        env = os.environ.copy()
        env["AGY_HOOK_SILENT"] = "1"
        res = subprocess.run(
            [sys.executable, script_path, "--json"],
            capture_output=True,
            text=True,
            timeout=10.0,
            env=env,
            cwd=repo_root,
        )
        self.assertEqual(res.returncode, 0, f"Error en CLI: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertIn("terminal", data)
        self.assertIn("audio", data)

    def test_aegis_cli_doctor_terminal(self):
        """Verifica que bin/aegis doctor --terminal --json despache correctamente."""
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        aegis_bin = os.path.join(repo_root, "bin", "aegis")
        env = os.environ.copy()
        env["AGY_HOOK_SILENT"] = "1"
        res = subprocess.run(
            [sys.executable, aegis_bin, "doctor", "--terminal", "--json"],
            capture_output=True,
            text=True,
            timeout=10.0,
            env=env,
            cwd=repo_root,
        )
        self.assertEqual(res.returncode, 0, f"Error en aegis dispatcher: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertIn("terminal", data)
        self.assertIn("audio", data)

    def test_env_detector_terminal_alignment(self):
        """Verifica que env_detector.get_terminal_type() esté alineado con terminal_wizard."""
        with patch.dict(os.environ, {"KITTY_WINDOW_ID": "123"}, clear=True):
            self.assertEqual(env_detector.get_terminal_type(), "kitty")
        with patch.dict(os.environ, {"TERM": "xterm-ghostty"}, clear=True):
            self.assertEqual(env_detector.get_terminal_type(), "ghostty")
        with patch.dict(os.environ, {"WEZTERM_PANE": "p1"}, clear=True):
            self.assertEqual(env_detector.get_terminal_type(), "wezterm")


if __name__ == "__main__":
    unittest.main()
