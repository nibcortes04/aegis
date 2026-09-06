import unittest
import sys
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

os.environ["AGY_HOOK_SILENT"] = "1"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../mcp")))

import trust_levels
from trust_levels import (
    evaluate_trust,
    get_active_trust_level,
    LEVEL_AUDIT,
    LEVEL_VPS_PRODUCTION,
    LEVEL_WORKSPACE_SAFE,
    is_vps_safe_inspection,
    is_vps_lifecycle_command,
    is_vps_critical_file,
    DangerousConfirmationLedger,
)
import vps_health
import mcp_server


class TestVPSGuardrails(unittest.TestCase):
    def setUp(self):
        DangerousConfirmationLedger().clear()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        DangerousConfirmationLedger().clear()

    def test_vps_level_definition_and_hierarchy(self):
        """Verifica que LEVEL_VPS_PRODUCTION esté registrado en la jerarquía."""
        self.assertEqual(LEVEL_VPS_PRODUCTION, "vps-production")
        self.assertIn(LEVEL_VPS_PRODUCTION, trust_levels.TRUST_LEVEL_HIERARCHY)
        self.assertEqual(trust_levels.TRUST_LEVEL_HIERARCHY[LEVEL_VPS_PRODUCTION], 1)

    def test_active_level_resolution_with_vps_aliases(self):
        """Verifica la resolución de nivel activo por variable de entorno y alias."""
        aliases = ["vps-production", "vps", "vps-prod", "production-vps"]
        for alias in aliases:
            with patch.dict(os.environ, {"AGY_AUTO_MODE_LEVEL": alias}):
                self.assertEqual(
                    get_active_trust_level(),
                    LEVEL_VPS_PRODUCTION,
                    f"Fallo al resolver alias {alias} para vps-production"
                )

    def test_vps_safe_inspection_commands_allowed(self):
        """Verifica que los comandos de telemetría y lectura segura en VPS se aprueben de inmediato."""
        safe_commands = [
            "docker ps",
            "docker ps -a",
            "docker logs caddy",
            "docker logs -f --tail 100 n8n",
            "docker inspect chatwoot",
            "docker compose ps",
            "docker-compose logs",
            "systemctl status caddy",
            "systemctl is-active postgresql",
            "journalctl -n 50 -u caddy",
            "caddy validate --config /etc/caddy/Caddyfile",
            "caddy version",
            "df -h",
            "free -m",
            "uptime",
            "top -b -n 1",
            "curl -I https://n8n.ecomsofia.xyz",
            "curl -sS https://api.chatwoot.com",
            "ping -c 3 1.1.1.1",
            "cat /var/log/caddy.log",
        ]
        for cmd in safe_commands:
            self.assertTrue(is_vps_safe_inspection(cmd), f"Esperado seguro para: {cmd}")
            dec, reason = evaluate_trust("run_command", {"CommandLine": cmd}, level=LEVEL_VPS_PRODUCTION)
            self.assertEqual(dec, "allow", f"Esperado 'allow' para '{cmd}', obtenido '{dec}' ({reason})")

    def test_vps_lifecycle_commands_gated_by_two_factor_safety(self):
        """Verifica que las mutaciones de contenedores y servicios en VPS requieran doble confirmación."""
        lifecycle_commands = [
            "docker restart n8n",
            "docker stop chatwoot_web",
            "docker kill caddy",
            "docker compose down",
            "docker compose restart",
            "docker-compose restart n8n",
            "systemctl restart caddy",
            "systemctl stop caddy",
            "systemctl reload caddy",
            "caddy reload",
            "docker volume rm n8n_data",
            "docker system prune",
            "redis-cli flushall",
        ]
        for cmd in lifecycle_commands:
            self.assertTrue(is_vps_lifecycle_command(cmd), f"Esperado lifecycle para: {cmd}")
            # Paso 1: Denegado forzando explicación humana
            dec1, reason1 = evaluate_trust("run_command", {"CommandLine": cmd}, level=LEVEL_VPS_PRODUCTION)
            self.assertEqual(dec1, "deny", f"Paso 1 debe ser 'deny' para '{cmd}'")
            self.assertTrue(
                "PROTOCOLO VPS" in reason1 or "DOBLE CONFIRMACIÓN REQUERIDA" in reason1,
                f"Mensaje de paso 1 inesperado: {reason1}"
            )

            # Paso 2 dentro de TTL: Elevado a confirmación interactiva
            dec2, reason2 = evaluate_trust("run_command", {"CommandLine": cmd}, level=LEVEL_VPS_PRODUCTION)
            self.assertEqual(dec2, "ask", f"Paso 2 debe ser 'ask' para '{cmd}'")
            self.assertTrue(
                "CONFIRMACIÓN VPS" in reason2 or "CONFIRMACIÓN DEFINITIVA" in reason2,
                f"Mensaje de paso 2 inesperado: {reason2}"
            )

    def test_vps_critical_config_file_protection(self):
        """Verifica que la edición de Caddyfile, docker-compose o .env requiera confirmación en VPS."""
        critical_files = [
            "/etc/caddy/Caddyfile",
            "/home/n_n/agency-infra/Caddyfile",
            "/home/n_n/agency-infra/docker-compose.yml",
            "/home/n_n/agency-infra/docker-compose.prod.yaml",
            "/home/n_n/agency-infra/.env",
            "/home/n_n/agency-infra/.env.production",
        ]
        for fpath in critical_files:
            self.assertTrue(is_vps_critical_file(fpath), f"Esperado crítico: {fpath}")
            dec, reason = evaluate_trust(
                "write_to_file",
                {"TargetFile": fpath},
                workspace_root="/home/n_n/agency-infra",
                level=LEVEL_VPS_PRODUCTION
            )
            self.assertEqual(dec, "ask", f"Edición de {fpath} debe retornar 'ask'")
            self.assertIn("Archivo crítico", reason)

        # Archivo regular no crítico dentro del workspace sí se permite
        regular_file = "/home/n_n/agency-infra/README.md"
        self.assertFalse(is_vps_critical_file(regular_file))
        dec_reg, _ = evaluate_trust(
            "write_to_file",
            {"TargetFile": regular_file},
            workspace_root="/home/n_n/agency-infra",
            level=LEVEL_VPS_PRODUCTION
        )
        self.assertEqual(dec_reg, "allow")

    def test_vps_health_inspection_module(self):
        """Verifica que vps_health genere un reporte consistente de recursos y contenedores."""
        health = vps_health.inspect_vps_health()
        self.assertIsInstance(health, dict)
        self.assertIn("timestamp", health)
        self.assertIn("status", health)
        self.assertIn(health["status"], ["healthy", "warning", "critical"])
        self.assertIn("disk", health)
        self.assertIn("memory", health)
        self.assertIn("load", health)
        self.assertIn("docker", health)
        self.assertIn("warnings", health)

    def test_mcp_aegis_check_vps_health(self):
        """Verifica que el servidor MCP exponga y ejecute aegis_check_vps_health."""
        msg = {
            "jsonrpc": "2.0",
            "id": 42,
            "method": "tools/call",
            "params": {
                "name": "aegis_check_vps_health",
                "arguments": {}
            }
        }
        resp = mcp_server.process_message(msg)
        self.assertIsNotNone(resp)
        self.assertEqual(resp.get("id"), 42)
        content = resp.get("result", {}).get("content", [])
        self.assertTrue(len(content) > 0)
        out_json = json.loads(content[0]["text"])
        self.assertIn("status", out_json)
        self.assertIn("disk", out_json)


if __name__ == "__main__":
    unittest.main()
