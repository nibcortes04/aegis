import unittest
import sys
import os
import json
import tempfile
import shutil
import subprocess

os.environ["AGY_HOOK_SILENT"] = "1"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))

import bot_pr_check


class TestBotPRGate(unittest.TestCase):
    def setUp(self):
        self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_worktree_hygiene_clean_repository(self):
        """Verifica que el repositorio actual pase la auditoría de higiene."""
        res = bot_pr_check.check_worktree_hygiene(self.repo_root)
        self.assertTrue(res["passed"], f"Violaciones encontradas en repo: {res.get('violations')}")
        self.assertEqual(len(res["violations"]), 0)

    def test_worktree_hygiene_detects_forbidden_patterns(self):
        """Verifica que se detecten archivos prohibidos temporales o basura."""
        # Inicializar un repo git temporal
        subprocess.run(["git", "init"], cwd=self.temp_dir, capture_output=True)
        
        # Crear archivos prohibidos
        forbidden_file = os.path.join(self.temp_dir, "leak.pyc")
        with open(forbidden_file, "w") as f:
            f.write("byte-code")

        res = bot_pr_check.check_worktree_hygiene(self.temp_dir)
        self.assertFalse(res["passed"])
        self.assertTrue(any("leak.pyc" in v for v in res["violations"]))

    def test_manifest_and_packaging_check(self):
        """Verifica la fase de validación de manifiesto con el script empaquetador."""
        res = bot_pr_check.check_manifest_and_packaging(self.repo_root)
        self.assertTrue(res["passed"], f"Error en empaquetador: {res.get('error') or res.get('output')}")
        self.assertEqual(res["returncode"], 0)

    @unittest.skipIf(os.environ.get("AEGIS_BOT_CHECK_ACTIVE") == "1", "Evita recursión en subproceso de auditoría")
    def test_unit_tests_phase(self):
        """Verifica que la ejecución de tests pase y reporte el conteo correcto."""
        res = bot_pr_check.check_unit_tests(self.repo_root)
        self.assertTrue(res["passed"], f"Fallo en tests unitarios: {res.get('output')}")
        self.assertGreaterEqual(res["total_tests"], 50)
        self.assertEqual(res["returncode"], 0)

    def test_hook_contracts_phase(self):
        """Verifica que la fase de contratos de hooks sea exitosa."""
        res = bot_pr_check.check_hook_contracts(self.repo_root)
        self.assertTrue(res["passed"], f"Fallo en contratos de hooks: {res.get('output')}")
        self.assertEqual(res["returncode"], 0)

    @unittest.skipIf(os.environ.get("AEGIS_BOT_CHECK_ACTIVE") == "1", "Evita recursión en subproceso de auditoría")
    def test_run_all_checks_aggregation(self):
        """Verifica que run_all_checks agregue todas las fases y certifique el repositorio."""
        report = bot_pr_check.run_all_checks(self.repo_root)
        self.assertTrue(report["all_passed"])
        self.assertIn("1_hygiene", report["phases"])
        self.assertIn("2_packaging_manifest", report["phases"])
        self.assertIn("3_unit_tests", report["phases"])
        self.assertIn("4_hook_contracts", report["phases"])

    @unittest.skipIf(os.environ.get("AEGIS_BOT_CHECK_ACTIVE") == "1", "Evita recursión en subproceso de auditoría")
    def test_bot_pr_check_cli_json_mode(self):
        """Verifica que la CLI de bot_pr_check devuelva JSON válido y código de salida 0."""
        script_path = os.path.join(self.repo_root, "scripts", "bot_pr_check.py")
        env = os.environ.copy()
        env["AGY_HOOK_SILENT"] = "1"
        res = subprocess.run(
            [sys.executable, script_path, "--json"],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            timeout=40.0,
            env=env
        )
        self.assertEqual(res.returncode, 0, f"Error en CLI bot_pr_check: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertTrue(data.get("all_passed"))


if __name__ == "__main__":
    unittest.main()
