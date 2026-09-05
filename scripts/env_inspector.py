#!/usr/bin/env python3
"""
Autonomous Environment & Tool Inspector for AGY PowerPack
Escanea de forma autónoma el host para detectar:
- Compiladores y runtimes (Python, Node, Rust, Go, C/C++, Java, PHP, etc.)
- Gestores de paquetes (npm, pnpm, yarn, pip, cargo, etc.)
- Herramientas de test y linters (pytest, jest, vitest, ruff, eslint, etc.)
- Contenedores y DevOps (Docker, Podman, kubectl, etc.)
- Genera un perfil personalizado de Auto Mode y puebla el allowlist en settings.json.
"""

import os
import sys
import json
import shutil
import platform
import subprocess

try:
    from env_detector import get_os_type, get_surface_type, get_terminal_type, get_app_data_dir
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from env_detector import get_os_type, get_surface_type, get_terminal_type, get_app_data_dir

TOOL_CATALOG = {
    "compilers_and_runtimes": [
        "python3", "python", "node", "deno", "bun", "rustc", "cargo", "go",
        "gcc", "g++", "clang", "make", "cmake", "ninja",
        "java", "javac", "mvn", "gradle", "php", "ruby", "dotnet", "elixir"
    ],
    "package_managers": [
        "pnpm", "npm", "yarn", "bun", "pip", "pipx", "poetry", "uv", "cargo", "composer", "gem"
    ],
    "testing_and_linters": [
        "pytest", "jest", "vitest", "mocha", "playwright", "cypress",
        "ruff", "flake8", "black", "eslint", "prettier", "biome", "golangci-lint"
    ],
    "containers_and_devops": [
        "docker", "podman", "docker-compose", "kubectl", "helm", "terraform"
    ],
    "vcs_and_utilities": [
        "git", "gh", "curl", "wget", "jq", "fd", "fzf", "rg", "tree", "tar", "unzip"
    ]
}

# Generación de comandos estándar seguros asociados a cada binario detectado
SAFE_COMMANDS_MAP = {
    "git": ["command(git)"],
    "pnpm": ["command(pnpm)", "command(pnpm test)", "command(pnpm lint)", "command(pnpm run)"],
    "npm": ["command(npm)", "command(npm test)", "command(npm run)"],
    "yarn": ["command(yarn)", "command(yarn test)"],
    "bun": ["command(bun)", "command(bun test)", "command(bun run)"],
    "cargo": ["command(cargo)", "command(cargo test)", "command(cargo check)", "command(cargo build)"],
    "python3": ["command(python3)", "command(python)"],
    "python": ["command(python)"],
    "pytest": ["command(pytest)"],
    "node": ["command(node)", "command(npx)"],
    "make": ["command(make)"],
    "cmake": ["command(cmake)"],
    "go": ["command(go)", "command(go test)", "command(go build)"],
    "docker": ["command(docker ps)", "command(docker logs)", "command(docker images)"],
    "podman": ["command(podman ps)", "command(podman logs)"],
    "docker-compose": ["command(docker-compose ps)", "command(docker-compose logs)"],
    "kubectl": ["command(kubectl get)", "command(kubectl logs)", "command(kubectl describe)"],
    "curl": ["command(curl)"],
    "wget": ["command(wget)"],
    "jq": ["command(jq)"],
    "rg": ["command(rg)", "command(grep)"],
    "fd": ["command(fd)", "command(find)"],
    "which": ["command(which)"],
    "pwd": ["command(pwd)"],
    "echo": ["command(echo)"],
    "ls": ["command(ls)"],
    "cat": ["command(cat)"],
    "tail": ["command(tail)"],
    "head": ["command(head)"],
    "cp": ["command(cp)"],
    "mkdir": ["command(mkdir)"],
    "touch": ["command(touch)"],
    "wc": ["command(wc)"],
}

def inspect_environment():
    """Realiza un escaneo exhaustivo de herramientas instaladas en el sistema."""
    detected = {}
    found_binaries = set()

    for category, tools in TOOL_CATALOG.items():
        detected[category] = []
        for tool in tools:
            path = shutil.which(tool)
            if path:
                detected[category].append({
                    "name": tool,
                    "path": path,
                })
                found_binaries.add(tool)

    # Construir lista de permisos seguros
    recommended_allowlist = set()
    # Comandos POSIX básicos siempre disponibles
    for base in ["which", "pwd", "echo", "ls", "cat", "tail", "head", "cp", "mkdir", "touch", "wc"]:
        for cmd in SAFE_COMMANDS_MAP.get(base, []):
            recommended_allowlist.add(cmd)

    for tool in found_binaries:
        if tool in SAFE_COMMANDS_MAP:
            for cmd in SAFE_COMMANDS_MAP[tool]:
                recommended_allowlist.add(cmd)

    # Información general del sistema
    os_type = get_os_type()
    surface = get_surface_type()
    terminal = get_terminal_type()

    desktop_env = os.environ.get("XDG_CURRENT_DESKTOP") or os.environ.get("DESKTOP_SESSION") or "unknown"
    distro_name = platform.platform()
    if os.path.isfile("/etc/os-release"):
        try:
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        distro_name = line.strip().split("=", 1)[1].strip('"')
                        break
        except Exception:
            pass

    recommended_level = "workspace-safe"

    profile = {
        "system": {
            "os_type": os_type,
            "distro": distro_name,
            "kernel": platform.release(),
            "arch": platform.machine(),
            "desktop": desktop_env,
            "terminal": terminal,
            "surface": surface,
        },
        "detected_tools": detected,
        "total_tools_found": len(found_binaries),
        "recommended_level": recommended_level,
        "safe_allowlist": sorted(list(recommended_allowlist)),
    }
    return profile

def apply_profile(profile=None, settings_path=None):
    """Aplica las herramientas detectadas directamente a settings.json sin destruir configs previas."""
    if profile is None:
        profile = inspect_environment()

    app_dir = get_app_data_dir()
    os.makedirs(app_dir, exist_ok=True)

    # 1. Guardar system_profile.json
    profile_file = os.path.join(app_dir, "system_profile.json")
    with open(profile_file, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)

    # 2. Actualizar settings.json con el allowlist detectado
    if settings_path is None:
        settings_path = os.path.join(app_dir, "settings.json")

    data = {}
    if os.path.isfile(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

    current_allow = data.setdefault("permissions", {}).setdefault("allow", [])
    added = 0
    for cmd in profile["safe_allowlist"]:
        if cmd not in current_allow:
            current_allow.append(cmd)
            added += 1

    if "autoModeLevel" not in data:
        data["autoModeLevel"] = profile["recommended_level"]

    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return profile_file, added

def print_report(profile):
    """Muestra un resumen formateado y limpio en la terminal."""
    sys_info = profile["system"]
    print("====================================================")
    print("    AGY PowerPack — Autonomous Environment Inspector")
    print("====================================================")
    print(f"• Sistema Operativo : {sys_info['os_type'].upper()} ({sys_info['distro']})")
    print(f"• Kernel / Arch     : {sys_info['kernel']} ({sys_info['arch']})")
    print(f"• Entorno Gráfico   : {sys_info['desktop']}")
    print(f"• Emulador Terminal : {sys_info['terminal'].upper()}")
    print(f"• Superficie AGY    : {sys_info['surface'].upper()}")
    print(f"• Total Herramientas: {profile['total_tools_found']} binarios detectados")
    print("----------------------------------------------------")
    print("▶ Herramientas Detectadas por Categoría:")
    for cat, items in profile["detected_tools"].items():
        if items:
            names = [it["name"] for it in items]
            cat_label = cat.replace("_", " ").title()
            print(f"  • {cat_label:<24}: {', '.join(names)}")
    print("----------------------------------------------------")
    print(f"• Nivel Recomendado : {profile['recommended_level']}")
    print(f"• Comandos Seguros  : {len(profile['safe_allowlist'])} reglas generadas para Auto Mode")
    print("====================================================")

def main():
    profile = inspect_environment()

    if "--json" in sys.argv:
        print(json.dumps(profile, indent=2, ensure_ascii=False))
        return

    print_report(profile)

    if "--apply" in sys.argv or "-a" in sys.argv:
        profile_file, added = apply_profile(profile)
        print(f"\n✔ Perfil guardado en: {profile_file}")
        print(f"✔ Se agregaron {added} nuevos comandos seguros a settings.json.")

if __name__ == "__main__":
    main()
