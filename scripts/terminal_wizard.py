#!/usr/bin/env python3
"""
Aegis Terminal Wizard & Setup Doctor (terminal_wizard.py)
Inspecciona el emulador de terminal activo, detecta capacidades de campana visual,
tab badge e integración de audio sutil (PipeWire, PulseAudio, CoreAudio, PowerShell).
Ofrece diagnósticos interactivos y recomendaciones de configuración optimizadas.
"""

import os
import sys
import json
import shutil
import platform
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

TERMINAL_PROFILES = {
    "konsole": {
        "name": "KDE Konsole",
        "vendor": "KDE Community",
        "capabilities": {
            "ascii_bel": True,
            "tab_badge": True,
            "visual_flash": True,
            "osc_notification": True,
            "audio_bell": True,
        },
        "config_path": "~/.local/share/konsole/<Profile>.profile",
        "config_snippet": "[Terminal Features]\nBellMode=SystemNotification",
        "tips": [
            "Muestra el badge 🔔 automáticamente en la pestaña cuando el proceso finaliza.",
            "Para silenciar el altavoz de la placa madre y usar notificaciones de KDE Plasma:",
            "  Ajustes > Editar perfil actual > Avanzado > Modo de campana > 'Notificaciones del sistema'.",
        ],
        "score": "100% (Badge de pestaña nativo + Integración Plasma)",
    },
    "orca": {
        "name": "Orca Terminal",
        "vendor": "Orca",
        "capabilities": {
            "ascii_bel": True,
            "tab_badge": True,
            "visual_flash": True,
            "osc_notification": True,
            "audio_bell": False,
        },
        "config_path": "Integrado en Orca App / daemon IPC",
        "config_snippet": "# Orca sincroniza hooks y estados de sesión automáticamente",
        "tips": [
            "Orca recibe eventos de ciclo de vida de agentes de forma nativa vía endpoint.env.",
            "Los badges y estado de subagentes se reflejan en el panel lateral de forma nativa.",
        ],
        "score": "100% (Integración completa agéntica)",
    },
    "kitty": {
        "name": "Kitty Terminal",
        "vendor": "Kovid Goyal",
        "capabilities": {
            "ascii_bel": True,
            "tab_badge": True,
            "visual_flash": True,
            "osc_notification": True,
            "audio_bell": True,
        },
        "config_path": "~/.config/kitty/kitty.conf",
        "config_snippet": (
            "enable_audio_bell no\n"
            "window_alert_on_bell yes\n"
            "visual_bell_duration 0.1\n"
            "bell_on_tab '🔔 '"
        ),
        "tips": [
            "Desactiva el pitido molesto con 'enable_audio_bell no'.",
            "Activa 'window_alert_on_bell yes' para destacar pestañas en segundo plano.",
            "Usa 'bell_on_tab' para mostrar un emoji en el título de la pestaña.",
        ],
        "score": "95% (Campana visual y badge de pestaña configurables)",
    },
    "alacritty": {
        "name": "Alacritty",
        "vendor": "Alacritty Open Source",
        "capabilities": {
            "ascii_bel": True,
            "tab_badge": False,
            "visual_flash": True,
            "osc_notification": False,
            "audio_bell": False,
        },
        "config_path": "~/.config/alacritty/alacritty.toml",
        "config_snippet": (
            "[bell]\n"
            'animation = "EaseOut"\n'
            "duration = 150\n"
            'color = "#38bdf8"\n'
            'command = { program = "notify-send", args = ["Aegis", "Turno completado"] }'
        ),
        "tips": [
            "Alacritty no tiene pestañas nativas; usa destello visual suave de color.",
            "Puedes disparar notify-send directamente desde el bloque [bell].",
        ],
        "score": "85% (Destello de ventana de alto rendimiento)",
    },
    "iterm": {
        "name": "iTerm2",
        "vendor": "George Nachman",
        "capabilities": {
            "ascii_bel": True,
            "tab_badge": True,
            "visual_flash": True,
            "osc_notification": True,
            "audio_bell": True,
        },
        "config_path": "~/Library/Preferences/com.googlecode.iterm2.plist",
        "config_snippet": (
            "# En Preferencias > Perfiles > Terminal > Notificaciones:\n"
            "# 1. Marcar 'Silence bell' (silencia el audio)\n"
            "# 2. Marcar 'Show bell icon in tabs' (icono 🔔)\n"
            "# 3. Marcar 'Flash visual bell'"
        ),
        "tips": [
            "iTerm2 soporta icono nativo de campana en pestaña sin requerir scripts.",
            "Permite rebotar el icono del Dock si la ventana no tiene el foco.",
        ],
        "score": "100% (Soporte completo de badges y OSC en macOS)",
    },
    "windows_terminal": {
        "name": "Windows Terminal",
        "vendor": "Microsoft Corporation",
        "capabilities": {
            "ascii_bel": True,
            "tab_badge": True,
            "visual_flash": True,
            "osc_notification": True,
            "audio_bell": True,
        },
        "config_path": "%LOCALAPPDATA%\\Packages\\Microsoft.WindowsTerminal_...\\LocalState\\settings.json",
        "config_snippet": (
            '{\n'
            '  "profiles": {\n'
            '    "defaults": {\n'
            '      "bellStyle": ["taskbar", "window"]\n'
            '    }\n'
            '  }\n'
            '}'
        ),
        "tips": [
            "Con 'bellStyle': ['taskbar', 'window'], la barra de tareas parpadea en naranja suave.",
            "Desactiva el sonido beep clásico en la configuración de accesibilidad de Windows.",
        ],
        "score": "95% (Destello en barra de tareas y ventana)",
    },
    "ghostty": {
        "name": "Ghostty",
        "vendor": "Mitchell Hashimoto",
        "capabilities": {
            "ascii_bel": True,
            "tab_badge": True,
            "visual_flash": True,
            "osc_notification": True,
            "audio_bell": True,
        },
        "config_path": "~/.config/ghostty/config",
        "config_snippet": (
            "bell-action = visual,cursor\n"
            "desktop-notifications = true"
        ),
        "tips": [
            "Ghostty soporta 'bell-action = visual' para un pulso visual acelerado por GPU.",
            "Activa 'desktop-notifications = true' para emitir notificaciones nativas en segundo plano.",
        ],
        "score": "95% (GPU Visual Bell + Notificaciones nativas)",
    },
    "wezterm": {
        "name": "WezTerm",
        "vendor": "Wez Furlong",
        "capabilities": {
            "ascii_bel": True,
            "tab_badge": True,
            "visual_flash": True,
            "osc_notification": True,
            "audio_bell": False,
        },
        "config_path": "~/.config/wezterm/wezterm.lua",
        "config_snippet": (
            "local wezterm = require 'wezterm'\n"
            "local config = wezterm.config_builder()\n"
            "config.audible_bell = 'Disabled'\n"
            "config.visual_bell = {\n"
            "  fade_in_function = 'EaseIn',\n"
            "  fade_in_duration_ms = 75,\n"
            "  fade_out_function = 'EaseOut',\n"
            "  fade_out_duration_ms = 75,\n"
            "}\n"
            "return config"
        ),
        "tips": [
            "Desactiva 'audible_bell = Disabled' para evitar tonos estridentes.",
            "Configura 'visual_bell' para una suave transición visual.",
        ],
        "score": "95% (Lua-scriptable Visual Bell)",
    },
    "gnome_terminal": {
        "name": "GNOME Terminal / Ptyxis",
        "vendor": "GNOME Project",
        "capabilities": {
            "ascii_bel": True,
            "tab_badge": False,
            "visual_flash": True,
            "osc_notification": True,
            "audio_bell": True,
        },
        "config_path": "dconf / Preferencias de GNOME Terminal",
        "config_snippet": (
            "# En Preferencias > Perfiles > General:\n"
            "# 1. Activar 'Campana de la terminal'\n"
            "# 2. En GNOME Tweaks > Ventanas: Activar 'Alerta visual de campana'"
        ),
        "tips": [
            "GNOME integra la campana con el destello global de la pantalla.",
            "El sistema de notificaciones de GNOME Shell maneja los avisos de escritorio.",
        ],
        "score": "80% (Campana VTE e integración GNOME Shell)",
    },
    "mintty": {
        "name": "Mintty (Git Bash / MSYS2)",
        "vendor": "Mintty Project",
        "capabilities": {
            "ascii_bel": True,
            "tab_badge": False,
            "visual_flash": True,
            "osc_notification": True,
            "audio_bell": True,
        },
        "config_path": "~/.minttyrc",
        "config_snippet": (
            "BellType=2\n"
            "BellTaskbar=yes"
        ),
        "tips": [
            "BellType=2 activa el destello de ventana en lugar del altavoz de PC.",
            "BellTaskbar=yes ilumina el icono en la barra de tareas de Windows.",
        ],
        "score": "80% (Parpadeo de barra de tareas en Windows)",
    },
    "vscode": {
        "name": "VSCode Integrated Terminal",
        "vendor": "Microsoft Corporation",
        "capabilities": {
            "ascii_bel": True,
            "tab_badge": True,
            "visual_flash": True,
            "osc_notification": False,
            "audio_bell": True,
        },
        "config_path": ".vscode/settings.json",
        "config_snippet": (
            '{\n'
            '  "terminal.integrated.enableBell": true,\n'
            '  "audioCues.terminalBell": "on"\n'
            '}'
        ),
        "tips": [
            "Muestra una pequeña campana animada en la pestaña lateral del terminal.",
            "Soporta Audio Cues accesibles integrados en el propio VSCode.",
        ],
        "score": "90% (Campana de pestaña e integraciones de accesibilidad)",
    },
    "apple_terminal": {
        "name": "Apple Terminal.app",
        "vendor": "Apple Inc.",
        "capabilities": {
            "ascii_bel": True,
            "tab_badge": False,
            "visual_flash": True,
            "osc_notification": False,
            "audio_bell": True,
        },
        "config_path": "~/Library/Preferences/com.apple.Terminal.plist",
        "config_snippet": (
            "# En Terminal > Ajustes > Perfiles > Avanzado:\n"
            "# 1. Marcar 'Campana visual'\n"
            "# 2. Marcar 'Hacer rebotar el icono en el Dock'\n"
            "# 3. Desmarcar 'Campana acústica'"
        ),
        "tips": [
            "Rebota suavemente el icono en el Dock si la terminal no está en foco.",
            "El destello visual invierte brevemente el fondo de la pantalla.",
        ],
        "score": "80% (Dock bounce & Visual Flash en macOS)",
    },
    "tmux": {
        "name": "Tmux Multiplexer",
        "vendor": "Nicholas Marriott / OpenBSD",
        "capabilities": {
            "ascii_bel": True,
            "tab_badge": True,
            "visual_flash": True,
            "osc_notification": True,
            "audio_bell": False,
        },
        "config_path": "~/.tmux.conf",
        "config_snippet": (
            "set -g visual-bell off\n"
            "set -g bell-action any\n"
            "setw -g window-status-bell-style 'fg=colour232,bg=colour01,bold'"
        ),
        "tips": [
            "Tmux reenvía la campana a la ventana exterior si se configura 'bell-action any'.",
            "Muestra un badge de alerta en la barra de estado de la ventana activa.",
        ],
        "score": "90% (Multiplexación con reenvío de campana)",
    },
    "generic": {
        "name": "Generic ANSI Terminal",
        "vendor": "Unknown / Standard TTY",
        "capabilities": {
            "ascii_bel": True,
            "tab_badge": False,
            "visual_flash": False,
            "osc_notification": False,
            "audio_bell": True,
        },
        "config_path": "Depende del emulador",
        "config_snippet": "# Configura tu emulador para interceptar BEL (ASCII 7)",
        "tips": [
            "Emite BEL estándar (ASCII 7).",
            "Aegis complementa con notificaciones de escritorio para asegurar visibilidad.",
        ],
        "score": "60% (Soporte estándar BEL)",
    },
}


def detect_terminal_id(env=None):
    """Detecta el ID del emulador de terminal según las variables de entorno."""
    if env is None:
        env = os.environ

    if "KONSOLE_VERSION" in env or "KONSOLE_DBUS_SERVICE" in env:
        return "konsole"
    if "ORCA_PANE_KEY" in env or "ORCA_AGENT_LAUNCH_TOKEN" in env or "ORCA_TERMINAL" in env:
        return "orca"
    if "KITTY_WINDOW_ID" in env or "KITTY_PID" in env:
        return "kitty"
    if (
        "ALACRITTY_LOG" in env
        or "ALACRITTY_WINDOW_ID" in env
        or "ALACRITTY_SOCKET" in env
        or env.get("TERM", "").startswith("alacritty")
    ):
        return "alacritty"
    if "WT_SESSION" in env or "WT_PROFILE_ID" in env:
        return "windows_terminal"
    if "GHOSTTY_RESOURCES_DIR" in env or env.get("TERM") == "xterm-ghostty":
        return "ghostty"
    if "WEZTERM_PANE" in env or "WEZTERM_EXECUTABLE" in env or "WEZTERM_CONFIG_FILE" in env:
        return "wezterm"
    if "GNOME_TERMINAL_SCREEN" in env or "GNOME_TERMINAL_SERVICE" in env or "PTYXIS_VERSION" in env:
        return "gnome_terminal"
    if env.get("TERM_PROGRAM") == "mintty" or ("MSYSTEM" in env and "WT_SESSION" not in env):
        return "mintty"
    if "ITERM_SESSION_ID" in env or env.get("TERM_PROGRAM") == "iTerm.app":
        return "iterm"
    if env.get("TERM_PROGRAM") == "vscode":
        return "vscode"
    if env.get("TERM_PROGRAM") == "Apple_Terminal":
        return "apple_terminal"
    if "TMUX" in env or "TMUX_PANE" in env:
        return "tmux"

    return "generic"


def inspect_terminal(env=None):
    """
    Inspecciona a fondo el emulador de terminal, su soporte de campana y capacidades.
    Devuelve un diccionario estructurado completo.
    """
    term_id = detect_terminal_id(env)
    profile = TERMINAL_PROFILES.get(term_id, TERMINAL_PROFILES["generic"])

    has_tty = os.path.exists("/dev/tty")
    is_interactive = sys.stdin.isatty() or sys.stderr.isatty()

    return {
        "id": term_id,
        "name": profile["name"],
        "vendor": profile["vendor"],
        "capabilities": profile["capabilities"],
        "config_path": profile["config_path"],
        "config_snippet": profile["config_snippet"],
        "tips": profile["tips"],
        "compatibility_score": profile["score"],
        "has_dev_tty": has_tty,
        "is_interactive": is_interactive,
        "environment_signals": {
            "TERM": os.environ.get("TERM", ""),
            "TERM_PROGRAM": os.environ.get("TERM_PROGRAM", ""),
            "COLORTERM": os.environ.get("COLORTERM", ""),
        },
    }


def detect_audio_subsystem():
    """
    Detecta utilidades y servidores de sonido para chimes discretos (no invasivos):
    Linux: paplay (PulseAudio/PipeWire), pw-cat (PipeWire), canberra-gtk-play, aplay (ALSA).
    macOS: afplay.
    Windows: powershell SystemSounds.
    """
    system = platform.system()
    backends = []
    sound_files = {}

    if system == "Linux":
        for cmd in ["paplay", "pw-cat", "canberra-gtk-play", "aplay"]:
            path = shutil.which(cmd)
            if path:
                backends.append(cmd)

        # Buscar archivos estándar de audio freedesktop / ocean
        search_dirs = [
            "/usr/share/sounds/freedesktop/stereo",
            "/usr/share/sounds/ocean/stereo",
            "/usr/share/sounds/gnome/default/alerts",
        ]
        sound_names = ["complete", "bell", "message", "window-attention", "dialog-information"]
        for d in search_dirs:
            if os.path.isdir(d):
                for s in sound_names:
                    if s not in sound_files:
                        for ext in [".oga", ".ogg", ".wav"]:
                            full_path = os.path.join(d, s + ext)
                            if os.path.isfile(full_path):
                                sound_files[s] = full_path
                                break

    elif system == "Darwin":
        if shutil.which("afplay"):
            backends.append("afplay")
            mac_sounds = [
                ("/System/Library/Sounds/Tink.aiff", "complete"),
                ("/System/Library/Sounds/Ping.aiff", "bell"),
                ("/System/Library/Sounds/Pop.aiff", "message"),
            ]
            for path, name in mac_sounds:
                if os.path.isfile(path):
                    sound_files[name] = path

    elif system == "Windows":
        if shutil.which("powershell") or shutil.which("pwsh"):
            backends.append("powershell")
            sound_files["complete"] = "SystemAsterisk"
            sound_files["bell"] = "SystemBeep"

    primary = backends[0] if backends else None

    return {
        "supported": bool(backends),
        "primary_backend": primary,
        "available_backends": backends,
        "sound_files": sound_files,
        "platform": system,
    }


def play_subtle_chime(sound_name="complete", timeout=3.0):
    """
    Reproduce un sonido sutil de aviso (turn_complete o human_confirm).
    Es completamente no bloqueante o con timeout estricto, sin colgar la terminal.
    """
    if os.environ.get("AGY_HOOK_SILENT") == "1" or os.environ.get("AEGIS_SILENT") == "1":
        return {"success": False, "reason": "silent_mode_active"}

    audio = detect_audio_subsystem()
    if not audio["supported"]:
        return {"success": False, "reason": "no_audio_backend_detected"}

    backend = audio["primary_backend"]
    sound_file = audio["sound_files"].get(sound_name) or audio["sound_files"].get("bell")

    try:
        if backend == "paplay" and sound_file:
            subprocess.Popen(["paplay", sound_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True, "backend": "paplay", "sound": sound_file}

        elif backend == "pw-cat" and sound_file:
            subprocess.Popen(["pw-cat", "-p", sound_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True, "backend": "pw-cat", "sound": sound_file}

        elif backend == "canberra-gtk-play":
            event_id = "complete" if sound_name == "complete" else "bell"
            subprocess.Popen(["canberra-gtk-play", "-i", event_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True, "backend": "canberra-gtk-play", "sound": event_id}

        elif backend == "aplay" and sound_file and sound_file.endswith(".wav"):
            subprocess.Popen(["aplay", "-q", sound_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True, "backend": "aplay", "sound": sound_file}

        elif backend == "afplay" and sound_file:
            subprocess.Popen(["afplay", sound_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True, "backend": "afplay", "sound": sound_file}

        elif backend == "powershell":
            ps_cmd = "[System.Media.SystemSounds]::Asterisk.Play()"
            subprocess.Popen(["powershell", "-NoProfile", "-Command", ps_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True, "backend": "powershell", "sound": "SystemAsterisk"}

        return {"success": False, "reason": "no_compatible_sound_file_or_runner"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_terminal_bell():
    """Emite la campana de terminal ASCII BEL (\a) directamente a /dev/tty o stderr."""
    try:
        if os.path.exists("/dev/tty"):
            with open("/dev/tty", "w") as tty:
                tty.write("\a")
                tty.flush()
            return {"success": True, "channel": "/dev/tty"}
        else:
            sys.stderr.write("\a")
            sys.stderr.flush()
            return {"success": True, "channel": "stderr"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_terminal_doctor(test_bell=False, test_chime=False, recommend=False, json_output=False, quiet=False):
    """
    Ejecuta el asistente de diagnóstico de terminal.
    Genera informe visual en consola o estructura JSON.
    """
    term_info = inspect_terminal()
    audio_info = detect_audio_subsystem()

    bell_result = None
    if test_bell:
        bell_result = test_terminal_bell()

    chime_result = None
    if test_chime:
        chime_result = play_subtle_chime("complete")

    report = {
        "terminal": term_info,
        "audio": audio_info,
        "tests": {
            "bell": bell_result,
            "chime": chime_result,
        },
    }

    if quiet:
        return report

    if json_output:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return report

    # Formato visual elegante en terminal
    print(f"\n{BOLD}{CYAN}╔════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{CYAN}║     🛡️  AEGIS TERMINAL DOCTOR & VISUAL/AUDIO BELL WIZARD          ║{RESET}")
    print(f"{BOLD}{CYAN}╚════════════════════════════════════════════════════════════════════╝{RESET}\n")

    print(f"  {BOLD}Terminal Activo:{RESET}    {GREEN}{term_info['name']}{RESET} ({term_info['vendor']})")
    print(f"  {BOLD}Compatibilidad:{RESET}     {YELLOW}{term_info['compatibility_score']}{RESET}")
    print(f"  {BOLD}Canal TTY Directo:{RESET}  {GREEN if term_info['has_dev_tty'] else RED}{'/dev/tty activo' if term_info['has_dev_tty'] else 'No disponible'}{RESET}")
    print(f"  {BOLD}Modo Interactivo:{RESET}   {'Sí (TTY)' if term_info['is_interactive'] else 'No (Batch / Subproceso)'}")

    print(f"\n{BOLD}Capacidades del Emulador:{RESET}")
    caps = term_info["capabilities"]
    def cap_mark(val):
        return f"{GREEN}✔ Soportado{RESET}" if val else f"{DIM}✘ No nativo{RESET}"

    print(f"  • Campana ASCII (BEL \\a):           {cap_mark(caps['ascii_bel'])}")
    print(f"  • Badge 🔔 en Pestaña:             {cap_mark(caps['tab_badge'])}")
    print(f"  • Destello Visual (Visual Flash):   {cap_mark(caps['visual_flash'])}")
    print(f"  • Notificaciones OSC (OSC 9/777):   {cap_mark(caps['osc_notification'])}")
    print(f"  • Alerta Acústica (Audio Bell):     {cap_mark(caps['audio_bell'])}")

    print(f"\n{BOLD}Subsistema de Audio (Chimes Discretos):{RESET}")
    if audio_info["supported"]:
        print(f"  • Servidor / Motor: {GREEN}{audio_info['primary_backend']}{RESET} (Disponibles: {', '.join(audio_info['available_backends'])})")
        print(f"  • Sonidos Detectados: {', '.join(audio_info['sound_files'].keys()) if audio_info['sound_files'] else 'Predeterminado del sistema'}")
    else:
        print(f"  • {YELLOW}Sin servidor de audio detectado (Modo campana visual pura){RESET}")

    if test_bell:
        print(f"\n{BOLD}Prueba de Campana en Terminal:{RESET}")
        if bell_result and bell_result.get("success"):
            print(f"  {GREEN}✔ Señal BEL enviada vía {bell_result['channel']}.{RESET}")
            print(f"  {DIM}Verifica si apareció el icono 🔔 o destelló la pestaña de tu terminal.{RESET}")
        else:
            print(f"  {RED}✘ Error al emitir BEL: {bell_result.get('error')}{RESET}")

    if test_chime:
        print(f"\n{BOLD}Prueba de Audio Chime Sutil:{RESET}")
        if chime_result and chime_result.get("success"):
            print(f"  {GREEN}✔ Chime reproducido usando '{chime_result['backend']}'.{RESET}")
        else:
            print(f"  {YELLOW}⚠ Chime omitido o no disponible: {chime_result.get('reason') or chime_result.get('error')}{RESET}")

    if recommend or not (test_bell or test_chime):
        print(f"\n{BOLD}Recomendaciones y Configuración Óptima:{RESET}")
        for tip in term_info["tips"]:
            print(f"  {BLUE}•{RESET} {tip}")

        print(f"\n{BOLD}Ruta de Configuración:{RESET} {CYAN}{term_info['config_path']}{RESET}")
        print(f"{DIM}Fragmento sugerido:{RESET}")
        print(f"{CYAN}{'─'*50}{RESET}")
        for line in term_info["config_snippet"].split("\n"):
            print(f"  {line}")
        print(f"{CYAN}{'─'*50}{RESET}\n")

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Aegis Terminal Doctor & Visual/Audio Bell Setup Wizard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--terminal",
        action="store_true",
        help="Ejecuta el diagnóstico completo del terminal activo.",
    )
    parser.add_argument(
        "--test-bell",
        action="store_true",
        help="Emite señal BEL (\\a) para probar el badge 🔔 en la pestaña del emulador.",
    )
    parser.add_argument(
        "--test-chime",
        action="store_true",
        help="Prueba la reproducción de un chime sutil y no invasivo en el sistema de audio.",
    )
    parser.add_argument(
        "--recommend",
        action="store_true",
        help="Muestra exclusivamente las recomendaciones y fragmentos de configuración para este terminal.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Devuelve los resultados en formato JSON estructurado.",
    )

    args = parser.parse_args()

    # Si no se pasa ningún argumento, ejecutar el wizard completo por defecto
    test_bell = args.test_bell
    test_chime = args.test_chime
    recommend = args.recommend or (not args.test_bell and not args.test_chime)

    run_terminal_doctor(
        test_bell=test_bell,
        test_chime=test_chime,
        recommend=recommend,
        json_output=args.json,
    )


if __name__ == "__main__":
    main()
