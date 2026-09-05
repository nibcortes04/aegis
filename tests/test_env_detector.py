import unittest
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))
from env_detector import (
    get_os_type,
    get_surface_type,
    get_terminal_type,
    get_app_data_dir,
    get_summaries_db_path,
    is_path_in_workspace,
    ring_terminal_bell,
    send_desktop_notification
)

class TestEnvDetector(unittest.TestCase):
    def test_os_detection_type(self):
        os_type = get_os_type()
        self.assertIn(os_type, ["linux", "macos", "windows"])

    def test_surface_detection(self):
        # 1. Antigravity IDE detection via VSCODE envs
        with patch.dict(os.environ, {"VSCODE_PID": "12345"}, clear=True):
            self.assertEqual(get_surface_type(), "ide")
        with patch.dict(os.environ, {"TERM_PROGRAM": "vscode"}, clear=True):
            self.assertEqual(get_surface_type(), "ide")
        with patch.dict(os.environ, {"ANTIGRAVITY_IDE": "1"}, clear=True):
            self.assertEqual(get_surface_type(), "ide")

        # 2. Antigravity 2.0 Desktop App detection
        with patch.dict(os.environ, {"ANTIGRAVITY_APP": "1"}, clear=True):
            self.assertEqual(get_surface_type(), "desktop_app")
        with patch.dict(os.environ, {"ANTIGRAVITY_ELECTRON": "1"}, clear=True):
            self.assertEqual(get_surface_type(), "desktop_app")

        # 3. CLI default
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_surface_type(), "cli")

    def test_terminal_detection(self):
        with patch.dict(os.environ, {"KONSOLE_VERSION": "240800"}, clear=True):
            self.assertEqual(get_terminal_type(), "konsole")
        with patch.dict(os.environ, {"ORCA_PANE_KEY": "pane-1"}, clear=True):
            self.assertEqual(get_terminal_type(), "orca")
        with patch.dict(os.environ, {"ITERM_SESSION_ID": "iterm-1"}, clear=True):
            self.assertEqual(get_terminal_type(), "iterm")
        with patch.dict(os.environ, {"KITTY_WINDOW_ID": "kitty-1"}, clear=True):
            self.assertEqual(get_terminal_type(), "kitty")
        with patch.dict(os.environ, {"WT_SESSION": "wt-guid"}, clear=True):
            self.assertEqual(get_terminal_type(), "windows_terminal")

    def test_workspace_boundary_resolution(self):
        user_home = os.path.realpath(os.path.expanduser("~"))
        workspace_dir = os.path.join(user_home, "projects", "my-repo")

        # Relative paths are always safe inside workspace
        self.assertTrue(is_path_in_workspace("package.json", workspace_dir))
        self.assertTrue(is_path_in_workspace("./src/index.ts", workspace_dir))

        # Absolute paths inside workspace or home
        in_workspace_file = os.path.join(workspace_dir, "src", "index.ts")
        self.assertTrue(is_path_in_workspace(in_workspace_file, workspace_dir))
        in_home_file = os.path.join(user_home, "test.txt")
        self.assertTrue(is_path_in_workspace(in_home_file, workspace_dir))

        # Absolute paths strictly outside user home / system files
        if get_os_type() != "windows":
            self.assertFalse(is_path_in_workspace("/etc/passwd", workspace_dir))
            self.assertFalse(is_path_in_workspace("/var/log/syslog", workspace_dir))
            self.assertFalse(is_path_in_workspace("/boot/grub/grub.cfg", workspace_dir))
        else:
            self.assertFalse(is_path_in_workspace(r"C:\Windows\System32\cmd.exe", workspace_dir))

    def test_app_data_dir_resolution(self):
        # Default expands user home
        data_dir = get_app_data_dir()
        self.assertTrue(data_dir.endswith("antigravity-cli"))
        db_path = get_summaries_db_path()
        self.assertTrue(db_path.endswith("conversation_summaries.db"))

    def test_bell_and_notification_fallbacks(self):
        # Should not throw any exception regardless of environment
        ring_terminal_bell()
        send_desktop_notification("Test Title", "Test Message", urgency="low", timeout_ms=1000)

if __name__ == "__main__":
    unittest.main()
