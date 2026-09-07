#!/usr/bin/env python3
"""
Aegis Mobile Companion & Pairing Wizard (mobile_wizard.py)
Asistente interactivo para emparejar dispositivos Android con la PWA oficial
de Google Antigravity Remote Control (https://antigravity.google).
"""

import os
import sys
import json
import shutil
import subprocess
import argparse

# Configuración de colores ANSI
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

OFFICIAL_PWA_URL = "https://antigravity.google"

# Representación ASCII QR compacta y estética para la URL oficial
QR_ASCII_ART = """
██████████████  ██    ██  ██████████████
██          ██  ████  ██  ██          ██
██  ██████  ██  ██    ██  ██  ██████  ██
██  ██████  ██  ████████  ██  ██████  ██
██  ██████  ██  ██  ██    ██  ██████  ██
██          ██  ████  ██  ██          ██
██████████████  ██  ██    ██████████████
                ██  ██                  
████  ██████████████  ██████  ██████████
██████  ██  ██    ██████  ██████  ██████
██  ████████████  ████████████  ██  ████
████    ██  ████████  ████████████    ██
                ██████████  ██    ██████
██████████████  ██    ██  ██  ██  ██    
██          ██  ██  ██████    ██████  ██
██  ██████  ██  ████████  ████  ████  ██
██  ██████  ██  ████  ██  ██  ██  ██████
██  ██████  ██  ██  ████████████  ██████
██          ██  ██  ████  ██  ██  ██  ██
██████████████  ████████████  ██████████
"""

def check_daemon_status():
    """Verifica si el comando 'agy' está disponible y si el daemon remote-control está activo."""
    agy_path = shutil.which("agy")
    if not agy_path:
        return {
            "installed": False,
            "running": False,
            "detail": "CLI 'agy' no encontrado en el PATH del sistema."
        }

    try:
        res = subprocess.run(
            [agy_path, "remote-control", "status"],
            capture_output=True,
            text=True,
            timeout=3.0
        )
        output = (res.stdout + "\n" + res.stderr).strip()
        is_running = (res.returncode == 0) and ("running" in output.lower() or "active" in output.lower())
        return {
            "installed": True,
            "running": is_running,
            "detail": output if output else ("Activo" if is_running else "Inactivo")
        }
    except Exception as e:
        return {
            "installed": True,
            "running": False,
            "detail": f"Error al consultar estado del daemon: {str(e)}"
        }

def get_pairing_info():
    """Retorna la información y guía completa de emparejamiento móvil en formato estructurado."""
    daemon = check_daemon_status()
    return {
        "pwa_url": OFFICIAL_PWA_URL,
        "platform": "Android (Official Google Antigravity PWA)",
        "daemon": daemon,
        "steps": [
            {
                "step": 1,
                "title": "Abrir navegador en Android",
                "instruction": "Abre Google Chrome o cualquier navegador Chromium en tu teléfono."
            },
            {
                "step": 2,
                "title": "Ir al portal de emparejamiento",
                "instruction": f"Navega a {OFFICIAL_PWA_URL} o escanea el código QR."
            },
            {
                "step": 3,
                "title": "Iniciar sesión con tu cuenta Google",
                "instruction": "Inicia sesión con la misma cuenta de Google configurada en tu terminal/IDE."
            },
            {
                "step": 4,
                "title": "Instalar la aplicación PWA",
                "instruction": "Toca el menú de tres puntos (⋮) en Chrome y selecciona 'Instalar aplicación' (o 'Agregar a la pantalla principal')."
            }
        ],
        "daemon_commands": {
            "start": "agy remote-control start",
            "status": "agy remote-control status",
            "stop": "agy remote-control stop"
        },
        "features": [
            "Supervisión y lectura de sesiones activas en tiempo real.",
            "Aprobación y denegación remota de acciones críticas (Two-Factor Safety Gate).",
            "Notificaciones push nativas en Android al completar tareas."
        ]
    }

def print_pairing_wizard(show_qr=True):
    """Muestra el asistente visual interactivo en la terminal."""
    info = get_pairing_info()

    print(f"\n{BOLD}{CYAN}╔════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{CYAN}║     📱  AEGIS MOBILE COMPANION & ANDROID PWA PAIRING WIZARD        ║{RESET}")
    print(f"{BOLD}{CYAN}╚════════════════════════════════════════════════════════════════════╝{RESET}\n")

    print(f"  {BOLD}Portal Oficial PWA:{RESET}  {GREEN}{OFFICIAL_PWA_URL}{RESET}")
    daemon = info["daemon"]
    status_str = f"{GREEN}Activo (Listo para conectar){RESET}" if daemon["running"] else f"{YELLOW}Inactivo (Ejecuta: agy remote-control start){RESET}"
    print(f"  {BOLD}Estado del Daemon:{RESET}   {status_str}")

    if show_qr:
        print(f"\n{BOLD}Escanea este código QR desde tu teléfono Android:{RESET}")
        for line in QR_ASCII_ART.strip().split("\n"):
            print(f"  {line}")

    print(f"\n{BOLD}Instrucciones de Instalación en Android (PWA Oficial):{RESET}")
    for item in info["steps"]:
        print(f"  {BLUE}{item['step']}.{RESET} {BOLD}{item['title']}:{RESET} {item['instruction']}")

    print(f"\n{BOLD}Comandos de Control del Daemon (Host / VPS):{RESET}")
    print(f"  • {CYAN}agy remote-control start{RESET}   Inicia el servicio en segundo plano.")
    print(f"  • {CYAN}agy remote-control status{RESET}  Verifica conexiones activas.")
    print(f"  • {CYAN}agy remote-control stop{RESET}    Detiene el daemon de control remoto.")

    print(f"\n{BOLD}Capacidades Habilitadas en Móvil:{RESET}")
    for feat in info["features"]:
        print(f"  {GREEN}✔{RESET} {feat}")
    print()

def main():
    parser = argparse.ArgumentParser(
        description="Aegis Mobile Companion & Pairing Wizard (Official Android PWA)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--pair",
        action="store_true",
        help="Muestra el código QR y las instrucciones de emparejamiento con Android."
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Verifica el estado del daemon local 'agy remote-control'."
    )
    parser.add_argument(
        "--guide",
        action="store_true",
        help="Muestra la guía completa de instalación sin código QR grande."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Devuelve la información estructurada en formato JSON."
    )

    args = parser.parse_args()

    if args.json:
        print(json.dumps(get_pairing_info(), indent=2, ensure_ascii=False))
        return

    if args.status:
        daemon = check_daemon_status()
        print(f"\n{BOLD}Estado del Daemon Remote Control:{RESET}")
        print(f"  Instalado: {'Sí' if daemon['installed'] else 'No'}")
        print(f"  En ejecución: {'Sí' if daemon['running'] else 'No'}")
        print(f"  Detalle: {daemon['detail']}\n")
        return

    show_qr = not args.guide
    print_pairing_wizard(show_qr=show_qr)

if __name__ == "__main__":
    main()
