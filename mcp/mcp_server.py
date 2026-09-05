#!/usr/bin/env python3
"""
Documentation & Diagnostics MCP Server for Aegis
Implementa el protocolo JSON-RPC 2.0 del Model Context Protocol (MCP) sobre stdio
utilizando la biblioteca estándar de Python (sin dependencias externas).
Exprime herramientas para que cualquier agente o LLM consulte documentación,
niveles de confianza, estado del sistema y patrones de delegación multiagente.
"""

import sys
import os
import json
import platform

# Asegurar path a scripts para importar env_detector y trust_levels
SCRIPT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts"))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    import env_detector
    import trust_levels
except ImportError:
    env_detector = None
    trust_levels = None

TOOLS_DEFINITIONS = [
    # Aegis Primary Tools
    {
        "name": "aegis_get_trust_levels",
        "description": "Consulta la especificación de los 4 niveles de confianza de Auto Mode (audit, workspace-safe, full-developer, subagent-worker), qué comandos permite cada uno y cómo configurarlos.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "level": {
                    "type": "string",
                    "enum": ["audit", "workspace-safe", "full-developer", "subagent-worker", "all"],
                    "description": "Nivel específico a consultar o 'all' para la matriz completa."
                }
            },
            "required": []
        }
    },
    {
        "name": "aegis_get_surface_info",
        "description": "Detecta en tiempo real el sistema operativo (Linux, macOS, Windows), la superficie activa de Antigravity (CLI, IDE, Electron Desktop App) y el emulador de terminal.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "aegis_get_delegation_guide",
        "description": "Obtiene la guía técnica y plantillas de prompts para delegación concurrente de subagentes en Antigravity CLI manteniendo el contexto limpio.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "enum": ["fork-join", "worker-pool", "reviewer-gate", "all"],
                    "description": "Patrón de delegación agéntica solicitado."
                }
            }
        }
    },
    {
        "name": "aegis_verify_system",
        "description": "Ejecuta un diagnóstico completo del entorno de Aegis (hooks, statusline, dependencias de notificación, detección de superficie y permisos).",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "aegis_inspect_environment",
        "description": "Inspecciona de forma autónoma el host para detectar compiladores, runtimes, gestores de paquetes y herramientas DevOps, generando un perfil y recomendaciones de permisos para Auto Mode.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "apply": {
                    "type": "boolean",
                    "description": "Si es True, aplica automáticamente los comandos seguros detectados a settings.json."
                }
            }
        }
    },
    # Backward-compatibility aliases (powerpack_*)
    {
        "name": "powerpack_get_trust_levels",
        "description": "(Alias legacy) Consulta los 4 niveles de confianza de Auto Mode.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "level": {
                    "type": "string",
                    "enum": ["audit", "workspace-safe", "full-developer", "subagent-worker", "all"]
                }
            }
        }
    },
    {
        "name": "powerpack_get_surface_info",
        "description": "(Alias legacy) Detecta en tiempo real el OS, superficie Antigravity y terminal.",
        "inputSchema": { "type": "object", "properties": {} }
    },
    {
        "name": "powerpack_get_delegation_guide",
        "description": "(Alias legacy) Guía técnica y plantillas de subagentes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": { "type": "string", "enum": ["fork-join", "worker-pool", "reviewer-gate", "all"] }
            }
        }
    },
    {
        "name": "powerpack_verify_system",
        "description": "(Alias legacy) Diagnóstico completo del entorno Aegis.",
        "inputSchema": { "type": "object", "properties": {} }
    },
    {
        "name": "powerpack_inspect_environment",
        "description": "(Alias legacy) Inspección autónoma de compiladores, runtimes y herramientas.",
        "inputSchema": {
            "type": "object",
            "properties": { "apply": { "type": "boolean" } }
        }
    }
]

def handle_get_trust_levels(args):
    requested = args.get("level", "all")
    matrix = {
        "active_level": trust_levels.get_active_trust_level() if trust_levels else "workspace-safe",
        "levels": {
            "audit": {
                "description": "Zero-trust / Supervisión estricta",
                "reads": "Permitidas (view_file, list_dir, grep_search)",
                "file_edits": "Requiere confirmación siempre (decision: ask)",
                "commands": "Requiere confirmación siempre (decision: ask)",
                "use_case": "Auditorías de código, entornos de producción sensible, revisión de dependencias."
            },
            "workspace-safe": {
                "description": "Predeterminado: Desarrollo estándar seguro",
                "reads": "Permitidas sin confirmación",
                "file_edits": "Permitidas dentro del workspace o user home",
                "commands": "Inspección, tests y linters (git status/diff, pnpm test, pytest, ls, cat, etc.)",
                "blocked": "Mutaciones de paquetes, docker rm/stop, git push -f, rm -rf",
                "use_case": "Desarrollo diario habitual con balance perfecto entre fluidez y seguridad."
            },
            "full-developer": {
                "description": "Alta autonomía para iteración rápida",
                "reads": "Permitidas sin confirmación",
                "file_edits": "Permitidas dentro del workspace",
                "commands": "Instalación de paquetes (pnpm add, pip install), servidores locales (pnpm dev, python main.py), docker compose, commits/ramas git locales",
                "blocked": "Solo daño irreversible (rm -rf /, dd, mkfs, git push --force, drop database, sudo)",
                "use_case": "Prototipado rápido, construcción de características completas de inicio a fin."
            },
            "subagent-worker": {
                "description": "Autonomía acotada a un Git Worktree",
                "reads": "Permitidas dentro del worktree asignado",
                "file_edits": "Permitidas dentro del worktree",
                "commands": "Operaciones locales del worktree; bloquea escapes al sistema host",
                "use_case": "Subagentes invocados en paralelo para tareas específicas y aisladas."
            }
        },
        "how_to_configure": {
            "settings_json": "Añadir 'autoModeLevel': '<nivel>' en ~/.gemini/antigravity-cli/settings.json",
            "env_var": "export AGY_AUTO_MODE_LEVEL='<nivel>'"
        }
    }
    if requested in matrix["levels"]:
        return json.dumps({requested: matrix["levels"][requested], "active_level": matrix["active_level"]}, indent=2, ensure_ascii=False)
    return json.dumps(matrix, indent=2, ensure_ascii=False)

def handle_get_surface_info(args):
    if not env_detector:
        return json.dumps({"error": "env_detector no disponible"}, ensure_ascii=False)
    info = {
        "os": env_detector.get_os_type(),
        "platform_release": platform.release(),
        "surface": env_detector.get_surface_type(),
        "terminal": env_detector.get_terminal_type(),
        "app_data_dir": env_detector.get_app_data_dir(),
        "summaries_db": env_detector.get_summaries_db_path(),
        "silent_mode": env_detector.is_silent_mode()
    }
    return json.dumps(info, indent=2, ensure_ascii=False)

def handle_get_delegation_guide(args):
    pattern = args.get("pattern", "all")
    guide = {
        "core_principle": "Mantener limpio el contexto del orquestador delegando tareas de investigación y codificación pesada a subagentes paralelos.",
        "subagent_catalog": [
            {"role": "researcher", "model": "flash", "scope": "Búsquedas web, lectura de código y síntesis"},
            {"role": "worker-backend", "model": "inherit", "scope": "Implementación backend en Git Worktree dedicado"},
            {"role": "worker-frontend", "model": "inherit", "scope": "Implementación de vistas y estilos UI"},
            {"role": "qa-tester", "model": "flash", "scope": "Ejecución de test suites y cobertura"},
            {"role": "reviewer-bot", "model": "flash/pro", "scope": "Análisis de compliance y diffs antes del merge"}
        ],
        "patterns": {
            "fork-join": "El orquestador divide un epic en 3 tareas independientes, lanza los 3 subagentes con invoke_subagent, y espera el retorno sin bucles activos (wakeup reactivo).",
            "worker-pool": "Reutilizar subagentes existentes enviando nuevos mensajes con send_message para amortizar el arranque de contexto.",
            "reviewer-gate": "Un subagente implementa y otro ejecuta el pase de verificación antes de proponer el PR al humano."
        }
    }
    return json.dumps(guide, indent=2, ensure_ascii=False)

def handle_verify_system(args):
    results = {
        "status": "healthy",
        "checks": {}
    }
    # Chequeo Python
    results["checks"]["python_version"] = platform.python_version()
    # Chequeo rutas
    if env_detector:
        results["checks"]["os"] = env_detector.get_os_type()
        results["checks"]["surface"] = env_detector.get_surface_type()
        app_dir = env_detector.get_app_data_dir()
        results["checks"]["app_data_dir_exists"] = os.path.isdir(app_dir)
        db_path = env_detector.get_summaries_db_path()
        results["checks"]["db_found"] = os.path.isfile(db_path)
    # Chequeo Trust Levels
    if trust_levels:
        results["checks"]["active_trust_level"] = trust_levels.get_active_trust_level()

    return json.dumps(results, indent=2, ensure_ascii=False)

def handle_inspect_environment(args):
    try:
        import env_inspector
    except ImportError:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
        import env_inspector

    profile = env_inspector.inspect_environment()
    should_apply = args.get("apply", False)
    if should_apply:
        profile_file, added = env_inspector.apply_profile(profile)
        profile["applied"] = {
            "profile_file": profile_file,
            "commands_added": added
        }
    return json.dumps(profile, indent=2, ensure_ascii=False)

def process_message(msg):
    method = msg.get("method")
    msg_id = msg.get("id")

    # 1. initialize
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "aegis-mcp",
                    "version": "1.5.0"
                }
            }
        }

    # 2. notifications/initialized
    if method == "notifications/initialized":
        return None

    # 3. tools/list
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "tools": TOOLS_DEFINITIONS
            }
        }

    # 4. tools/call
    if method == "tools/call":
        params = msg.get("params") or {}
        tool_name = params.get("name")
        tool_args = params.get("arguments") or {}

        if tool_name in ("aegis_get_trust_levels", "powerpack_get_trust_levels"):
            out_text = handle_get_trust_levels(tool_args)
        elif tool_name in ("aegis_get_surface_info", "powerpack_get_surface_info"):
            out_text = handle_get_surface_info(tool_args)
        elif tool_name in ("aegis_get_delegation_guide", "powerpack_get_delegation_guide"):
            out_text = handle_get_delegation_guide(tool_args)
        elif tool_name in ("aegis_verify_system", "powerpack_verify_system"):
            out_text = handle_verify_system(tool_args)
        elif tool_name in ("aegis_inspect_environment", "powerpack_inspect_environment"):
            out_text = handle_inspect_environment(tool_args)
        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Herramienta desconocida: {tool_name}"
                }
            }

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": out_text
                    }
                ]
            }
        }

    # Unknown method
    if msg_id is not None:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {
                "code": -32601,
                "message": f"Método no implementado: {method}"
            }
        }
    return None

def main():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            continue

        resp = process_message(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
