#!/usr/bin/env python3
"""
Unit test suite for Aegis Quota & Telemetry Engine (EPIC-09)
Tests live runtime telemetry resolution, atomic cache storage,
sub-millisecond SQLite fallback, visual threshold alarms, and CLI/MCP surfaces.
"""

import os
import sys
import json
import time
import shutil
import sqlite3
import tempfile
import unittest
import subprocess

# Asegurar importación de scripts
SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import quota_metrics

class TestQuotaMetricsEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="aegis_quota_test_")
        self.telemetry_file = os.path.join(self.temp_dir, "live_telemetry.json")
        self.conv_dir = os.path.join(self.temp_dir, "conversations")
        os.makedirs(self.conv_dir, exist_ok=True)
        self.summaries_db = os.path.join(self.temp_dir, "conversation_summaries.db")

        # Configurar variables de entorno aisladas para la prueba
        self.orig_env = os.environ.copy()
        os.environ["AEGIS_TELEMETRY_FILE"] = self.telemetry_file
        os.environ["AEGIS_CONVERSATIONS_DIR"] = self.conv_dir
        os.environ["AEGIS_SUMMARIES_DB"] = self.summaries_db

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.orig_env)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_record_and_get_cached_telemetry(self):
        conv_id = "test-session-cache-01"
        data = {
            "context_window": {"used_percentage": 42.0, "current_tokens": 84000},
            "cost": {"total_cost_usd": 0.015, "total_duration_ms": 60000},
            "quota_5h": {"used_percentage": 25.0},
            "quota_7d": {"used_percentage": 5.0}
        }

        # Guardar telemetría
        ok = quota_metrics.record_live_telemetry(conv_id, data)
        self.assertTrue(ok)
        self.assertTrue(os.path.isfile(self.telemetry_file))

        # Recuperar telemetría en cache
        cached = quota_metrics.get_cached_telemetry(conv_id)
        self.assertIsNotNone(cached)
        self.assertEqual(cached["context_window"]["used_percentage"], 42.0)
        self.assertEqual(cached["cost"]["total_cost_usd"], 0.015)

        # Verificar sesión inexistente
        self.assertIsNone(quota_metrics.get_cached_telemetry("non-existent-id"))

    def test_resolve_telemetry_live_runtime(self):
        live_payload = {
            "conversation_id": "test-live-01",
            "model": {"id": "gemini-3.8-flash", "display_name": "Gemini 3.8 Flash"},
            "context_window": {"used_percentage": 65.4, "current_tokens": 654000, "max_tokens": 1000000},
            "cost": {"total_cost_usd": 0.0981, "total_duration_ms": 180000},
            "quota": {
                "gemini-5h": {"remaining_fraction": 0.35, "reset_time": "2026-09-07T05:00:00Z"},
                "gemini-weekly": {"remaining_fraction": 0.85}
            }
        }

        resolved = quota_metrics.resolve_telemetry(live_payload)
        self.assertEqual(resolved["source"], "live-runtime")
        self.assertEqual(resolved["tokens"], 654000)
        self.assertEqual(resolved["used_percentage"], 65.4)
        self.assertEqual(resolved["total_cost_usd"], 0.0981)
        self.assertEqual(resolved["duration_ms"], 180000)
        self.assertEqual(resolved["quota_5h"]["used_percentage"], 65.0)
        self.assertEqual(resolved["quota_7d"]["used_percentage"], 15.0)

    def test_resolve_telemetry_sqlite_fallback(self):
        conv_id = "test-sqlite-mock-conv"
        mock_db_path = os.path.join(self.conv_dir, f"{conv_id}.db")

        # Crear base de datos simulada con schema de AGY
        conn = sqlite3.connect(mock_db_path)
        cur = conn.cursor()
        cur.execute("CREATE TABLE gen_metadata (idx integer primary key, size integer);")
        cur.execute("CREATE TABLE steps (idx integer primary key);")
        # Insertar 10 generaciones de 40,000 bytes cada una = 400,000 bytes (~100k tokens)
        for i in range(10):
            cur.execute("INSERT INTO gen_metadata (idx, size) VALUES (?, ?);", (i, 40000))
            cur.execute("INSERT INTO steps (idx) VALUES (?);", (i,))
        conn.commit()
        conn.close()

        # Llamar a resolve_telemetry sin métricas en el payload
        payload = {
            "conversation_id": conv_id,
            "model": {"id": "gemini-3.8-flash"}
        }

        resolved = quota_metrics.resolve_telemetry(payload)
        self.assertEqual(resolved["source"], "sqlite-fallback")
        # 400,000 / 4 = 100,000 tokens
        self.assertEqual(resolved["tokens"], 100000)
        # 100,000 / 1,000,000 = 10%
        self.assertEqual(resolved["used_percentage"], 10.0)
        # 100,000 / 1,000,000 * 0.15 = 0.0150
        self.assertEqual(resolved["total_cost_usd"], 0.015)
        self.assertIn("used_percentage", resolved["quota_5h"])
        self.assertIn("used_percentage", resolved["quota_7d"])

    def test_format_context_bar_thresholds(self):
        # < 70% (Verde)
        bar_low = quota_metrics.format_context_bar(35.0, tokens=70000, max_tokens=200000)
        self.assertIn("\033[32m", bar_low) # Green
        self.assertIn("35%", bar_low)
        self.assertIn("70k/200k", bar_low)
        self.assertNotIn("⚠️", bar_low)
        self.assertNotIn("🚨", bar_low)

        # 70% - 89% (Amarillo + ⚠️)
        bar_med = quota_metrics.format_context_bar(75.0, tokens=750000, max_tokens=1000000)
        self.assertIn("\033[33m", bar_med) # Yellow
        self.assertIn("75%", bar_med)
        self.assertIn("⚠️", bar_med)

        # >= 90% (Rojo + 🚨)
        bar_high = quota_metrics.format_context_bar(94.0, tokens=940000, max_tokens=1000000)
        self.assertIn("\033[31m", bar_high) # Red
        self.assertIn("94%", bar_high)
        self.assertIn("🚨", bar_high)

        # exceeds_200k (Rojo + 🚨)
        bar_exceeds = quota_metrics.format_context_bar(50.0, exceeds=True)
        self.assertIn("\033[31m", bar_exceeds)
        self.assertIn("🚨", bar_exceeds)

    def test_format_cost_thresholds(self):
        # < $0.10: Verde
        cost_low = quota_metrics.format_cost(0.045)
        self.assertIn("\033[32m", cost_low) # Green
        self.assertIn("$0.0450", cost_low)
        self.assertNotIn("💸", cost_low)

        # $0.10 - $0.49: Amarillo
        cost_med = quota_metrics.format_cost(0.245)
        self.assertIn("\033[33m", cost_med) # Yellow
        self.assertIn("$0.2450", cost_med)

        # >= $0.50: Magenta + 💸 + ⚠️
        cost_high = quota_metrics.format_cost(0.685)
        self.assertIn("\033[35m", cost_high) # Magenta
        self.assertIn("💸", cost_high)
        self.assertIn("$0.6850", cost_high)
        self.assertIn("⚠️", cost_high)

    def test_format_quotas_and_duration(self):
        q5 = {"used_percentage": 85.0, "reset_time": "2026-09-07T06:30:00Z"}
        q7 = {"used_percentage": 25.0}

        quotas_str = quota_metrics.format_quotas(q5, q7)
        self.assertIn("5h:85%", quotas_str)
        self.assertIn("🚨", quotas_str)
        self.assertIn("7d:25%", quotas_str)

        # Duración
        dur_str_short = quota_metrics.format_duration(125000) # 2m5s
        self.assertEqual(dur_str_short, "⏱ 2m5s")

        dur_str_long = quota_metrics.format_duration(7500000) # 2h5m
        self.assertEqual(dur_str_long, "⏱ 2h5m")

    def test_cli_json_execution(self):
        script_path = os.path.join(SCRIPTS_DIR, "quota_metrics.py")
        res = subprocess.run(
            [sys.executable, script_path, "--json"],
            capture_output=True, text=True, timeout=5
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertIn("source", data)
        self.assertIn("context_window", data)
        self.assertIn("cost", data)
        self.assertIn("quotas", data)

    def test_cli_record_execution(self):
        script_path = os.path.join(SCRIPTS_DIR, "quota_metrics.py")
        record_json = json.dumps({"context_window": {"used_percentage": 88.0}})
        res = subprocess.run(
            [sys.executable, script_path, "--conv-id", "test-record-cli", "--record", record_json],
            capture_output=True, text=True, timeout=5
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertTrue(data.get("success"))

if __name__ == "__main__":
    unittest.main()
