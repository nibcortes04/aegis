#!/usr/bin/env python3
"""
Aegis Notification & Terminal Bell Diagnostic Tool
Permite verificar y depurar de forma interactiva y en vivo:
1. Campana de terminal (\\a BEL) para iluminar el icono de campana (🔔) en pestañas de Konsole / terminal.
2. Notificaciones de escritorio (notify-send en Linux, terminal-notifier en macOS, BurntToast/PowerShell en Windows).
3. Aislamiento multi-sesión y rate-limiting persistente en disco.
4. Simulación end-to-end de eventos de hooks de AGY (Stop, PreToolUse con aprobación).
"""

import os
import sys
import time
import json
import shutil
import argparse
import subprocess

# Local imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    from env_detector import (
        ring_terminal_bell,
        send_desktop_notification,
        get_notification_channel,
        get_os_type,
        get_surface_type,
        get_terminal_type,
        get_app_data_dir,
    )
    from agy_hook_handler import handle_stop, handle_pre_tool_use
except ImportError:
    sys.path.insert(0, "/home/n_n/scripts")
    from env_detector import (
        ring_terminal_bell,
        send_desktop_notification,
        get_notification_channel,
        get_os_type,
        get_surface_type,
        get_terminal_type,
        get_app_data_dir,
    )
    from agy_hook_handler import handle_stop, handle_pre_tool_use

# Formato visual en terminal
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_status(label, ok=True, detail=""):
    mark = f"{GREEN}[OK]{RESET}" if ok else f"{RED}[FAIL]{RESET}"
    if not ok and detail:
        print(f"  {mark} {BOLD}{label}{RESET}: {detail}")
    elif detail:
        print(f"  {mark} {BOLD}{label}{RESET} ({detail})")
    else:
        print(f"  {mark} {BOLD}{label}{RESET}")


def run_verify():
    """Diagnóstica la configuración del entorno para notificaciones y campanas."""
    print(f"\n{BOLD}{BLUE}=== Diagnóstico del Entorno Aegis ==={RESET}\n")

    os_type = get_os_type()
    surface = get_surface_type()
    term = get_terminal_type()
    channel = get_notification_channel()

    print(f"  Sistema Operativo: {BOLD}{os_type}{RESET}")
    print(f"  Entorno / Superficie: {BOLD}{surface}{RESET}")
    print(f"  Terminal Detectado: {BOLD}{term}{RESET}")
    print(f"  Canal de Notificación Activo: {BOLD}{channel}{RESET} (AGY_NOTIFICATION_CHANNEL / settings.json)")

    print(f"\n{BOLD}Verificación de Componentes:{RESET}")

    # 1. TTY & Terminal Bell
    has_dev_tty = os.path.exists("/dev/tty")
    stderr_isatty = sys.stderr.isatty()
    print_status(
        "Acceso a Dispositivo TTY (/dev/tty)",
        ok=has_dev_tty,
        detail="permite enviar señal BEL directamente a la pestaña" if has_dev_tty else "no disponible (posible contenedor)",
    )
    print_status(
        "Salida Estándar de Error (stderr.isatty)",
        ok=stderr_isatty,
        detail="canal interactivo directo" if stderr_isatty else "salida redirigida o subproceso no-TTY",
    )

    # 2. Daemon de Notificaciones de Escritorio
    if os_type == "linux":
        has_notify_send = shutil.which("notify-send") is not None
        print_status(
            "Herramienta notify-send",
            ok=has_notify_send,
            detail=shutil.which("notify-send") or "no instalada (ejecutar sudo apt install libnotify-bin)",
        )

        dbus_active = False
        if has_notify_send:
            try:
                res = subprocess.run(
                    ["notify-send", "-v"],
                    capture_output=True,
                    text=True,
                    timeout=1.0,
                )
                dbus_active = res.returncode == 0
            except Exception:
                dbus_active = False
        print_status(
            "Servidor de Notificaciones D-Bus (KDE/GNOME/Dunst/Mako)",
            ok=dbus_active,
            detail="responde a llamadas de notificación" if dbus_active else "no se detectó respuesta rápida",
        )
    elif os_type == "macos":
        has_notifier = shutil.which("terminal-notifier") is not None
        has_osascript = shutil.which("osascript") is not None
        print_status("terminal-notifier", ok=has_notifier)
        print_status("osascript", ok=has_osascript)
    elif os_type == "windows":
        has_powershell = shutil.which("powershell.exe") is not None or shutil.which("pwsh") is not None
        print_status("PowerShell Notifier", ok=has_powershell)

    # 3. Archivos de Estado y Configuración
    app_data = get_app_data_dir()
    settings_file = os.path.join(app_data, "settings.json")
    print_status(
        "Directorio de Configuración Antigravity",
        ok=os.path.isdir(app_data),
        detail=app_data,
    )
    print_status(
        "Archivo de Ajustes (settings.json)",
        ok=os.path.isfile(settings_file),
        detail=settings_file if os.path.isfile(settings_file) else "opcional (usa valores predeterminados)",
    )

    hooks_json = os.path.expanduser("~/.gemini/config/hooks.json")
    print_status(
        "Configuración de Hooks (~/.gemini/config/hooks.json)",
        ok=os.path.isfile(hooks_json),
        detail="activo y enlazado a Aegis" if os.path.isfile(hooks_json) else "no encontrado",
    )

    print(f"\n{GREEN}{BOLD}Diagnóstico completado.{RESET}\n")


def run_bell():
    """Emite la señal de campana para activar el icono 🔔 en la pestaña actual."""
    print(f"\n{YELLOW}Enviando señal BEL (ASCII 7) a la pestaña del terminal...{RESET}")
    ring_terminal_bell()
    print(f"{GREEN}Señal emitida a /dev/tty y stderr.{RESET}")
    print(f"  {BOLD}Nota:{RESET} En Konsole / iTerm2 / WezTerm / Terminal, verifica si el icono de campana (🔔) o indicador de actividad apareció en la pestaña.")


def run_desktop():
    """Envía una notificación de escritorio de prueba."""
    print(f"\n{BLUE}Enviando notificación de escritorio de prueba...{RESET}")
    session_id = f"test-diag-{int(time.time())}"
    send_desktop_notification(
        title="Aegis: Diagnóstico",
        message="Notificación de prueba interactiva ejecutada correctamente.",
        urgency="normal",
        timeout_ms=5000,
        icon="utilities-terminal",
        session_id=session_id,
    )
    print(f"{GREEN}Notificación disparada (session_id={session_id}).{RESET}")


def run_simulate_stop(session_id=None):
    """Simula el evento Stop de AGY que marca la respuesta final."""
    sid = session_id or f"test-stop-{int(time.time()) % 10000}"
    print(f"\n{BLUE}Simulando evento 'Stop' de AGY (finalización de respuesta) para sesión: {BOLD}{sid}{RESET}...")

    payload = {
        "hookEventName": "Stop",
        "conversationId": sid,
        "terminationReason": "model_stop",
        "fullyIdle": True,
    }
    raw_input = json.dumps(payload)
    res = handle_stop(payload, raw_input)
    print(f"{GREEN}Evento procesado exitosamente por handler.{RESET} Resultado hook: {res}")
    print(f"  - Campana de pestaña 🔔 activada.")
    print(f"  - Notificación de escritorio enviada con ID y tag de sesión aislado.")


def run_simulate_ask(session_id=None):
    """Simula un evento PreToolUse que requiere aprobación humana."""
    sid = session_id or f"test-ask-{int(time.time()) % 10000}"
    print(f"\n{YELLOW}Simulando evento 'PreToolUse' requiriendo confirmación para sesión: {BOLD}{sid}{RESET}...")

    payload = {
        "hookEventName": "PreToolUse",
        "conversationId": sid,
        "toolCall": {
            "name": "run_command",
            "args": {
                "CommandLine": "systemctl restart critical-service"
            }
        }
    }
    raw_input = json.dumps(payload)
    res = handle_pre_tool_use(payload, raw_input)
    print(f"{GREEN}Evento de aprobación interceptado.{RESET} Resultado hook: {res}")
    print(f"  - Campana de pestaña 🔔 activada.")
    print(f"  - Notificación de alerta emitida.")


def main():
    parser = argparse.ArgumentParser(
        description="Aegis Notification & Terminal Bell Diagnostic Suite"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verifica el entorno, dependencias y configuración del sistema.",
    )
    parser.add_argument(
        "--bell",
        action="store_true",
        help="Emite la campana de terminal (ASCII 7) para probar el icono de pestaña 🔔.",
    )
    parser.add_argument(
        "--desktop",
        action="store_true",
        help="Envía una notificación de escritorio de prueba vía notify-send.",
    )
    parser.add_argument(
        "--simulate-stop",
        nargs="?",
        const="test-stop-sim",
        metavar="SESSION_ID",
        help="Simula el hook Stop al finalizar una respuesta.",
    )
    parser.add_argument(
        "--simulate-ask",
        nargs="?",
        const="test-ask-sim",
        metavar="SESSION_ID",
        help="Simula el hook PreToolUse que requiere confirmación humana.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Ejecuta la suite completa (verificación, campana, escritorio y simulación).",
    )

    args = parser.parse_args()

    # Si no se pasó ningún argumento, ejecutar --all por defecto
    if not any([args.verify, args.bell, args.desktop, args.simulate_stop, args.simulate_ask, args.all]):
        args.all = True

    if args.all or args.verify:
        run_verify()

    if args.all or args.bell:
        run_bell()

    if args.all or args.desktop:
        run_desktop()

    if args.simulate_ask:
        run_simulate_ask(args.simulate_ask)

    if args.all or args.simulate_stop:
        sid = args.simulate_stop if args.simulate_stop and args.simulate_stop != "test-stop-sim" else None
        run_simulate_stop(sid)


if __name__ == "__main__":
    main()
