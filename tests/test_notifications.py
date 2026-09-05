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


if __name__ == "__main__":
    unittest.main()
