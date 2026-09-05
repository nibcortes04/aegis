import unittest
import sys
import os
import time
import json
import tempfile
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))
from env_detector import (
    check_persistent_debounce,
    send_desktop_notification,
    get_notification_channel,
    ring_terminal_bell,
)
from agy_hook_handler import handle_stop, handle_pre_tool_use
import aegis_test_notify


class TestNotifications(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(tempfile.gettempdir(), ".aegis_notify_state.json")
        self.stop_file = os.path.join(tempfile.gettempdir(), ".aegis_stop_notify_state.json")

    def tearDown(self):
        # Clean up temporary test entries
        pass

    def test_multi_session_debounce_isolation(self):
        """Verifica que dos sesiones concurrentes no se bloqueen mutuamente."""
        session_a = "session-tab-alpha"
        session_b = "session-tab-beta"

        # Permitir ejecución desactivando el modo silencioso de tests temporalmente
        with patch("env_detector.is_silent_mode", return_value=False):
            # Sesión A envía notificación
            allowed_a1 = check_persistent_debounce("Title", "Message A", session_id=session_a, min_interval=2.0)
            self.assertTrue(allowed_a1, "Primera notificación de Sesión A debe permitirse")

            # Sesión B envía notificación casi de inmediato
            allowed_b1 = check_persistent_debounce("Title", "Message B", session_id=session_b, min_interval=2.0)
            self.assertTrue(allowed_b1, "Sesión B no debe ser bloqueada por la actividad de Sesión A")

            # Sesión A intenta spammear dentro de los 2.0s
            allowed_a2 = check_persistent_debounce("Title", "Message A2", session_id=session_a, min_interval=2.0)
            self.assertFalse(allowed_a2, "Segunda notificación de Sesión A dentro de intervalo debe ser bloqueada")

    def test_handle_stop_multi_session(self):
        """Verifica que el hook Stop aísle el debounce por session_id (conv_id)."""
        payload_1 = {
            "hookEventName": "Stop",
            "conversationId": "conv-101",
            "terminationReason": "model_stop",
        }
        payload_2 = {
            "hookEventName": "Stop",
            "conversationId": "conv-202",
            "terminationReason": "model_stop",
        }

        with patch("agy_hook_handler.send_desktop_notification") as mock_notify:
            res1 = handle_stop(payload_1, json.dumps(payload_1))
            self.assertEqual(res1, {"decision": ""})
            self.assertTrue(mock_notify.called)

            mock_notify.reset_mock()
            # Segunda sesión distinta debe notificar de inmediato
            res2 = handle_stop(payload_2, json.dumps(payload_2))
            self.assertEqual(res2, {"decision": ""})
            self.assertTrue(mock_notify.called)

    def test_handle_stop_skips_intermediate_tool_calls(self):
        """Verifica que no notifique si el evento Stop es intermedio o hay tareas pendientes."""
        payload_running = {
            "hookEventName": "Stop",
            "conversationId": "conv-run",
            "status": "running",
            "toolCalls": [{"name": "run_command"}],
        }
        with patch("agy_hook_handler.send_desktop_notification") as mock_notify:
            res = handle_stop(payload_running, json.dumps(payload_running))
            self.assertEqual(res, {"decision": ""})
            mock_notify.assert_not_called()

    def test_diagnostic_tool_execution(self):
        """Verifica que las funciones de diagnóstico se ejecuten sin lanzar excepciones."""
        with patch("sys.stdout"):
            aegis_test_notify.run_verify()
            aegis_test_notify.run_bell()
            aegis_test_notify.run_desktop()
            aegis_test_notify.run_simulate_stop("unit-test-session")

    def test_notification_timer_and_safe_urgency_enforcement(self):
        """Verifica que ninguna notificación quede fija: critical se mapea a normal con timeout."""
        with patch("env_detector.is_silent_mode", return_value=False), \
             patch("subprocess.run") as mock_run:
            send_desktop_notification(
                "Critical Test",
                "Should have timer",
                urgency="critical",
                timeout_ms=3500,
                session_id="test-timer-unit",
            )
            self.assertTrue(mock_run.called)
            called_cmd = mock_run.call_args[0][0]
            cmd_str = " ".join(called_cmd)
            self.assertIn("-u normal", cmd_str, "Debe mapear 'critical' a 'normal' para evitar quedarse fija en KDE")
            self.assertIn("-t 3500", cmd_str, "Debe pasar el timer de auto-cierre")
            self.assertIn("-h int:transient:1", cmd_str, "Debe marcarse como transient")

    def test_inotify_capacity_telemetry(self):
        """Verifica la función de telemetría de inotify."""
        from env_detector import get_inotify_capacity
        info = get_inotify_capacity()
        if sys.platform.startswith("linux"):
            self.assertIsNotNone(info)
            self.assertIn("max_instances", info)
            self.assertIn("active_instances", info)
            self.assertIn("usage_percent", info)
    def test_ask_question_emits_bell_and_notification(self):
        """Verifica que ask_question active campana y notificación pero retorne allow."""
        payload = {
            "hookEventName": "PreToolUse",
            "conversationId": "conv-ask-q",
            "toolCall": {
                "name": "ask_question",
                "args": {"questions": [{"question": "¿Continuar?"}]}
            }
        }
        with patch("agy_hook_handler.ring_terminal_bell") as mock_bell, \
             patch("agy_hook_handler.send_desktop_notification") as mock_notify:
            res = handle_pre_tool_use(payload, json.dumps(payload))
            self.assertEqual(res, {"decision": "allow"})
            self.assertTrue(mock_bell.called)
            self.assertTrue(mock_notify.called)
            notify_args = mock_notify.call_args[0]
            self.assertIn("Pregunta interactiva", notify_args[1])

    def test_plan_mode_file_write_emits_bell_and_ask_decision(self):
        """Verifica que en plan mode la creación o edición de archivo exija confirmación interactiva."""
        payload = {
            "hookEventName": "PreToolUse",
            "conversationId": "conv-plan-test",
            "cycle_mode": "plan",
            "cwd": self.temp_dir,
            "toolCall": {
                "name": "write_to_file",
                "args": {
                    "TargetFile": os.path.join(self.temp_dir, "test.txt"),
                    "CodeContent": "hello"
                }
            }
        }
        with patch("agy_hook_handler.ring_terminal_bell") as mock_bell, \
             patch("agy_hook_handler.send_desktop_notification") as mock_notify:
            res = handle_pre_tool_use(payload, json.dumps(payload))
            self.assertEqual(res.get("decision"), "ask")
            self.assertIn("Modo plan", res.get("reason", ""))
            self.assertTrue(mock_bell.called)
            self.assertTrue(mock_notify.called)

    def test_session_mode_recording_and_retrieval(self):
        """Verifica la persistencia de modos de sesión en statusline_formatter."""
        from statusline_formatter import record_session_mode, get_session_mode
        test_conv = "conv-mode-tracker-99"
        record_session_mode(test_conv, "plan")
        self.assertEqual(get_session_mode(test_conv), "plan")
        record_session_mode(test_conv, "accept-edits")
        self.assertEqual(get_session_mode(test_conv), "accept-edits")


if __name__ == "__main__":
    unittest.main()
