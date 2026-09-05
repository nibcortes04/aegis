#!/usr/bin/env python3
"""
Environment and Platform Detector for Antigravity CLI & Ecosystem
Identifica el sistema operativo, superficie de ejecución (CLI, IDE, Electron Desktop App)
y emulador de terminal, proporcionando abstracciones portables para campanas y notificaciones.
"""

import sys
import os
import platform
import subprocess
import shutil
import time
import json
import tempfile

def get_os_type():
    """
    Retorna el sistema operativo normalizado:
    - 'linux'
    - 'macos'
    - 'windows'
    """
    system = platform.system().lower()
    if "darwin" in system:
        return "macos"
    elif "win" in system:
        return "windows"
    return "linux"

def get_surface_type():
    """
    Identifica la superficie de Antigravity en la que se ejecuta:
    - 'ide': Antigravity IDE / VS Code extension
    - 'desktop_app': Antigravity 2.0 (Electron Desktop App)
    - 'cli': Terminal pura o PTY interactivo
    """
    # 1. Indicadores de Antigravity IDE / VS Code
    if (
        os.environ.get("ANTIGRAVITY_IDE") == "1"
        or os.environ.get("TERM_PROGRAM") == "vscode"
        or "VSCODE_PID" in os.environ
        or "VSCODE_CWD" in os.environ
    ):
        return "ide"

    # 2. Indicadores de Antigravity 2.0 Desktop App
    if (
        os.environ.get("ANTIGRAVITY_ELECTRON") == "1"
        or os.environ.get("ANTIGRAVITY_APP") == "1"
        or "ELECTRON_RUN_AS_NODE" in os.environ
    ):
        return "desktop_app"

    # 3. Default: CLI
    return "cli"

def get_terminal_type():
    """
    Identifica el emulador de terminal activo:
    - 'konsole': KDE Konsole
    - 'orca': Orca Terminal
    - 'iterm': iTerm2
    - 'kitty': Kitty
    - 'windows_terminal': Windows Terminal
    - 'generic': Terminal genérica
    """
    if "KONSOLE_VERSION" in os.environ or "KONSOLE_DBUS_SERVICE" in os.environ:
        return "konsole"
    if "ORCA_PANE_KEY" in os.environ or "ORCA_AGENT_LAUNCH_TOKEN" in os.environ:
        return "orca"
    if "ITERM_SESSION_ID" in os.environ:
        return "iterm"
    if "KITTY_WINDOW_ID" in os.environ:
        return "kitty"
    if "WT_SESSION" in os.environ:
        return "windows_terminal"
    return "generic"

def get_app_data_dir():
    """
    Retorna el directorio de datos de Antigravity según el sistema operativo:
    1. Si ANTIGRAVITY_APP_DATA_DIR o GEMINI_CLI_HOME está definida, se usa con prioridad.
    2. Fallback estándar: ~/.gemini/antigravity-cli (resuelto mediante expanduser)
    """
    custom = os.environ.get("ANTIGRAVITY_APP_DATA_DIR") or os.environ.get("GEMINI_CLI_HOME")
    if custom and os.path.isdir(custom):
        return os.path.abspath(custom)
    return os.path.expanduser("~/.gemini/antigravity-cli")

def get_summaries_db_path():
    """Retorna la ruta al archivo conversation_summaries.db de SQLite."""
    data_dir = get_app_data_dir()
    return os.path.join(data_dir, "conversation_summaries.db")

def is_path_in_workspace(target_file, workspace_root=None):
    r"""
    Evalúa de forma segura y portable si un archivo está dentro del workspace
    o dentro del home del usuario.
    Funciona uniformemente en Linux, macOS y Windows (manejando drive letters C:\).
    """
    if not target_file:
        return True

    # Si es ruta relativa, está implícitamente dentro del cwd
    if not os.path.isabs(target_file):
        return True

    try:
        norm_target = os.path.realpath(os.path.abspath(target_file))
        user_home = os.path.realpath(os.path.expanduser("~"))

        # Determinar raíz de workspace
        if not workspace_root:
            workspace_root = os.getcwd()
        norm_workspace = os.path.realpath(os.path.abspath(workspace_root))

        # En Windows, si están en discos distintos (ej. C: vs D:), commonpath lanza ValueError
        try:
            if os.path.commonpath([norm_workspace, norm_target]) == norm_workspace:
                return True
        except ValueError:
            pass

        try:
            if os.path.commonpath([user_home, norm_target]) == user_home:
                return True
        except ValueError:
            pass

        return False
    except Exception:
        # En caso de error de resolución, fallar de forma segura
        return False

# Cache simple en memoria para anti-spam y rate-limiting (en segundos)
_LAST_NOTIFICATION_TIME = 0.0
_LAST_NOTIFICATION_CONTENT = ""

def is_silent_mode():
    """Determina si las notificaciones y campanas deben silenciarse (tests, CI, batch)."""
    if os.environ.get("AGY_HOOK_SILENT") == "1" or os.environ.get("AGY_TESTING") == "1":
        return True
    if "unittest" in sys.modules or "pytest" in sys.modules:
        return True
    return False

def get_notification_channel():
    """
    Determina el canal de notificación configurado:
    - 'all' (default): Notificación de escritorio + campana de pestaña de terminal.
    - 'desktop': Solo notificación de escritorio (sin campana en terminal).
    - 'bell': Solo campana en terminal (sin popups de escritorio).
    - 'none': Silenciado total.
    """
    env_ch = os.environ.get("AGY_NOTIFICATION_CHANNEL", "").strip().lower()
    if env_ch in ("all", "desktop", "bell", "none"):
        return env_ch

    try:
        settings_file = os.path.join(get_app_data_dir(), "settings.json")
        if os.path.isfile(settings_file):
            with open(settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                ch = data.get("notificationChannel") or data.get("notifications", {}).get("channel")
                if ch and str(ch).lower() in ("all", "desktop", "bell", "none"):
                    return str(ch).lower()
    except Exception:
        pass

    return "all"

def ring_terminal_bell():
    """
    Emite señal de campana (BEL ASCII 7) para iluminar el icono de pestaña en Konsole, Orca, iTerm2, etc.
    - Linux/macOS: Escribe en /dev/tty o sys.stderr.
    - Windows: Escribe en CONOUT$ o sys.stderr o usa Beep de kernel32.
    Silenciado automáticamente durante tests, con AGY_HOOK_SILENT=1 o si el canal es 'none' o 'desktop'.
    """
    if is_silent_mode():
        return

    channel = get_notification_channel()
    if channel in ("none", "desktop"):
        return

    os_type = get_os_type()

    if os_type == "windows":
        try:
            with open("CONOUT$", "w", encoding="utf-8", errors="ignore") as con:
                con.write("\a")
                con.flush()
                return
        except Exception:
            pass
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_OK)
            return
        except Exception:
            pass
    else:
        try:
            with open("/dev/tty", "w", encoding="utf-8", errors="ignore") as tty:
                # BEL puro para encender el badge 🔔 de la pestaña del terminal
                tty.write("\a")
                tty.flush()
        except Exception:
            pass

    try:
        sys.stderr.write("\a")
        sys.stderr.flush()
    except Exception:
        pass

def check_persistent_debounce(title, message, session_id="", min_interval=2.5):
    """Garantiza rate-limiting aislado por cada sesión de AGY mediante un archivo atómico en /tmp."""
    if is_silent_mode():
        return False

    state_file = os.path.join(tempfile.gettempdir(), ".aegis_notify_state.json")
    now = time.time()
    session_key = session_id or "default"

    data = {"sessions": {}}
    try:
        if os.path.isfile(state_file):
            with open(state_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict) and "sessions" in loaded:
                    data = loaded
                elif isinstance(loaded, dict):
                    data = {"sessions": {"default": loaded}}
    except Exception:
        pass

    sessions = data.get("sessions", {})
    session_info = sessions.get(session_key, {})
    last_time = float(session_info.get("time", 0.0))

    # Debounce específico de la sesión actual
    if (now - last_time) < min_interval:
        return False

    sessions[session_key] = {"time": now, "content": f"{title}:{message}"}
    data["sessions"] = {k: v for k, v in sessions.items() if (now - v.get("time", 0)) < 3600}

    try:
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass

    return True

def send_desktop_notification(title, message, urgency="normal", timeout_ms=4000, icon="utilities-terminal", replace_id=9942, session_id=""):
    """
    Dispara notificación nativa de escritorio adaptada al sistema operativo.
    Utiliza ID de reemplazo y tags sincronizados por sesión para que no se apilen dentro
    de la misma sesión pero no interfieran con sesiones concurrentes.
    Silenciado automáticamente durante tests, con AGY_HOOK_SILENT=1 o si el canal es 'bell'/'none'.
    """
    if is_silent_mode():
        return

    channel = get_notification_channel()
    if channel in ("none", "bell"):
        return

    if not check_persistent_debounce(title, message, session_id=session_id, min_interval=2.5):
        return

    os_type = get_os_type()

    # 1. Linux: Usar replace_id y x-canonical-private-synchronous por sesión
    if os_type == "linux":
        if shutil.which("notify-send"):
            try:
                target_replace_id = replace_id
                if session_id and replace_id == 9942:
                    target_replace_id = 9940 + (abs(hash(session_id)) % 30)
                sync_tag = f"aegis-{session_id}" if session_id else "aegis-notification"
                cmd = [
                    "notify-send",
                    "-a", "Aegis",
                    "-r", str(target_replace_id),
                    "-u", urgency,
                    "-t", str(timeout_ms),
                    "-h", "int:transient:1",
                    "-h", f"string:x-canonical-private-synchronous:{sync_tag}",
                    "-i", icon,
                    title,
                    message
                ]
                subprocess.run(cmd, capture_output=True, timeout=1.0)
            except Exception:
                pass
        return

    # 2. macOS
    if os_type == "macos":
        if shutil.which("terminal-notifier"):
            try:
                subprocess.run(
                    [
                        "terminal-notifier",
                        "-title", title,
                        "-message", message,
                        "-group", "antigravity"
                    ],
                    capture_output=True,
                    timeout=1.0
                )
                return
            except Exception:
                pass

        if shutil.which("osascript"):
            safe_title = title.replace('"', '\\"')
            safe_msg = message.replace('"', '\\"')
            script = f'display notification "{safe_msg}" with title "{safe_title}" sound name "default"'
            try:
                subprocess.run(["osascript", "-e", script], capture_output=True, timeout=1.0)
            except Exception:
                pass
        return

    # 3. Windows
    if os_type == "windows":
        powershell_bin = shutil.which("powershell.exe") or shutil.which("powershell") or "powershell"
        safe_title = title.replace('"', '`"').replace("'", "''")
        safe_msg = message.replace('"', '`"').replace("'", "''")

        ps_cmd = (
            f"$title = '{safe_title}'; $msg = '{safe_msg}'; "
            "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null; "
            "$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); "
            "$textNodes = $template.GetElementsByTagName('text'); "
            "$textNodes.Item(0).AppendChild($template.CreateTextNode($title)) > $null; "
            "$textNodes.Item(1).AppendChild($template.CreateTextNode($msg)) > $null; "
            "$toast = [Windows.UI.Notifications.ToastNotification]::new($template); "
            "$toast.Tag = 'agy-notification'; $toast.Group = 'agy'; "
            "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Antigravity').Show($toast);"
        )
        try:
            subprocess.run(
                [powershell_bin, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                capture_output=True,
                timeout=1.5
            )
        except Exception:
            pass
