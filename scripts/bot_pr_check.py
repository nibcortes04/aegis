#!/usr/bin/env python3
"""
Aegis Autonomous Bot PR & Quality Gate Validator (bot_pr_check.py)
Herramienta de auto-certificación local y remota para contribuciones agénticas.
Ejecuta 4 fases de validación obligatorias:
1. Auditoría de Higiene Git (sin .pyc, __pycache__, .env, temporales o basura).
2. Conformance de Manifiesto y Empaquetado (package_plugin.py --dry-run).
3. Suite Completa de Tests Unitarios (unittest discover -s tests).
4. Contratos de Hooks de Ciclo de Vida (tests/test_hooks.sh).
"""

import sys
import os
import re
import json
import subprocess
import shutil

# Colores ANSI para salida en terminal
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

FORBIDDEN_FILE_PATTERNS = [
    r"\.pyc$",
    r"(?:^|/)__pycache__(?:/|$)",
    r"\.DS_Store$",
    r"Thumbs\.db$",
    r"\.(?:tmp|bak|swp|orig)$",
    r"(?:^|/)\.env$",
    r"(?:^|/)\.env\.(?:local|prod|production)$",
    r"(?:^|/)scratch/.*",
]

def check_worktree_hygiene(repo_root):
    """Verifica que el árbol de trabajo no contenga archivos prohibidos o basura."""
    violations = []
    
    # 1. Obtener lista de archivos rastreados por git
    try:
        res = subprocess.run(
            ["git", "ls-files"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5.0
        )
        tracked_files = [f.strip() for f in res.stdout.split("\n") if f.strip()]
        for f in tracked_files:
            for pattern in FORBIDDEN_FILE_PATTERNS:
                if re.search(pattern, f):
                    violations.append(f"Archivo prohibido rastreado en Git: {f}")
    except Exception as e:
        violations.append(f"Error al verificar git ls-files: {str(e)}")

    # 2. Verificar archivos no rastreados peligrosos
    try:
        res_untracked = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5.0
        )
        for line in res_untracked.stdout.split("\n"):
            line = line.strip()
            if not line:
                continue
            status_code = line[:2]
            filepath = line[3:].strip()
            for pattern in FORBIDDEN_FILE_PATTERNS:
                if re.search(pattern, filepath):
                    violations.append(f"Archivo prohibido sin seguimiento detectado: {filepath}")
    except Exception:
        pass

    return {
        "passed": len(violations) == 0,
        "violations": violations
    }

def check_manifest_and_packaging(repo_root):
    """Ejecuta el empaquetador en modo dry-run para validar manifest e integridad."""
    packager_script = os.path.join(repo_root, "scripts", "package_plugin.py")
    if not os.path.isfile(packager_script):
        return {"passed": False, "error": "Script scripts/package_plugin.py no encontrado"}

    try:
        res = subprocess.run(
            [sys.executable, packager_script, "--dry-run"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=10.0
        )
        passed = (res.returncode == 0) and ("Manifiesto validado" in res.stdout or "✔" in res.stdout)
        return {
            "passed": passed,
            "returncode": res.returncode,
            "output": res.stdout.strip() if passed else (res.stderr.strip() or res.stdout.strip())
        }
    except Exception as e:
        return {"passed": False, "error": str(e)}

def check_unit_tests(repo_root):
    """Ejecuta toda la suite de pruebas unitarias asegurando 100% pass rate."""
    try:
        env = os.environ.copy()
        env["AGY_HOOK_SILENT"] = "1"
        env["AEGIS_BOT_CHECK_ACTIVE"] = "1"
        res = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=60.0,
            env=env
        )
        passed = (res.returncode == 0)
        
        # Extraer total de tests ejecutados
        match = re.search(r"Ran (\d+) tests in", res.stderr + "\n" + res.stdout)
        total_tests = int(match.group(1)) if match else 0
        
        return {
            "passed": passed,
            "total_tests": total_tests,
            "returncode": res.returncode,
            "output": (res.stderr.strip() or res.stdout.strip())
        }
    except Exception as e:
        return {"passed": False, "total_tests": 0, "error": str(e)}

def check_hook_contracts(repo_root):
    """Ejecuta los contratos de hooks de ciclo de vida (test_hooks.sh)."""
    hook_test_script = os.path.join(repo_root, "tests", "test_hooks.sh")
    if not os.path.isfile(hook_test_script):
        return {"passed": False, "error": "Script tests/test_hooks.sh no encontrado"}

    try:
        res = subprocess.run(
            ["bash", hook_test_script],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=15.0
        )
        passed = (res.returncode == 0) and ("All AGY Hook Contract Tests Passed" in res.stdout or "PASS" in res.stdout)
        return {
            "passed": passed,
            "returncode": res.returncode,
            "output": res.stdout.strip() if passed else (res.stderr.strip() or res.stdout.strip())
        }
    except Exception as e:
        return {"passed": False, "error": str(e)}

def run_all_checks(repo_root=None):
    """Ejecuta todas las fases del Quality Gate y devuelve un informe consolidado."""
    if repo_root is None:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    hygiene = check_worktree_hygiene(repo_root)
    packaging = check_manifest_and_packaging(repo_root)
    unit_tests = check_unit_tests(repo_root)
    hook_contracts = check_hook_contracts(repo_root)

    all_passed = (
        hygiene["passed"] and
        packaging["passed"] and
        unit_tests["passed"] and
        hook_contracts["passed"]
    )

    return {
        "all_passed": all_passed,
        "repo_root": repo_root,
        "phases": {
            "1_hygiene": hygiene,
            "2_packaging_manifest": packaging,
            "3_unit_tests": unit_tests,
            "4_hook_contracts": hook_contracts
        }
    }

def print_pretty_report(report):
    """Imprime el informe de calidad en consola de manera visual y profesional."""
    all_passed = report["all_passed"]
    status_badge = f"{GREEN}{BOLD}PASSED — READY FOR DEV MERGE{RESET}" if all_passed else f"{RED}{BOLD}FAILED — BLOCKED{RESET}"

    print("\n" + "=" * 68)
    print(f"🤖  AEGIS AUTONOMOUS BOT QUALITY GATE — {status_badge}")
    print("=" * 68)

    phases = report["phases"]

    # Fase 1: Higiene
    h = phases["1_hygiene"]
    icon1 = f"{GREEN}✔ PASS{RESET}" if h["passed"] else f"{RED}✖ FAIL{RESET}"
    print(f"\n1. Higiene del Árbol de Trabajo Git: {icon1}")
    if not h["passed"]:
        for v in h.get("violations", []):
            print(f"   {RED}• {v}{RESET}")
    else:
        print("   • Sin archivos basura (.pyc, temporales, secretos o scratch rastreados).")

    # Fase 2: Manifiesto y Empaquetado
    p = phases["2_packaging_manifest"]
    icon2 = f"{GREEN}✔ PASS{RESET}" if p["passed"] else f"{RED}✖ FAIL{RESET}"
    print(f"\n2. Manifiesto Antigravity & Integridad de Empaquetado: {icon2}")
    if not p["passed"]:
        print(f"   {RED}• Error: {p.get('error') or p.get('output')}{RESET}")
    else:
        print("   • plugin.json y estructura de distribución conformes con la especificación AGY.")

    # Fase 3: Tests Unitarios
    u = phases["3_unit_tests"]
    icon3 = f"{GREEN}✔ PASS{RESET}" if u["passed"] else f"{RED}✖ FAIL{RESET}"
    print(f"\n3. Suite Completa de Tests Unitarios: {icon3}")
    if not u["passed"]:
        print(f"   {RED}• Error en suite de tests:{RESET}\n{u.get('output')}")
    else:
        print(f"   • {u.get('total_tests', 0)} tests unitarios ejecutados con 100% de éxito.")

    # Fase 4: Contratos de Hooks
    k = phases["4_hook_contracts"]
    icon4 = f"{GREEN}✔ PASS{RESET}" if k["passed"] else f"{RED}✖ FAIL{RESET}"
    print(f"\n4. Contratos de Hooks de Ciclo de Vida: {icon4}")
    if not k["passed"]:
        print(f"   {RED}• Error en contratos:{RESET}\n{k.get('output')}")
    else:
        print("   • Todos los contratos sub-10ms (PreToolUse, Stop, 2FA Gate) verificados.")

    print("\n" + "=" * 68)
    if all_passed:
        print(f"{GREEN}✔ Certificación exitosa: El PR bot cumple con todas las directivas de calidad.{RESET}")
    else:
        print(f"{RED}✖ Acción requerida: Corrija los errores anteriores antes de solicitar merge a dev.{RESET}")
    print("=" * 68 + "\n")

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    report = run_all_checks(repo_root)

    if "--json" in sys.argv:
        print(json.dumps(report, indent=2))
    else:
        print_pretty_report(report)

    sys.exit(0 if report["all_passed"] else 1)

if __name__ == "__main__":
    main()
