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

def ring_terminal_bell():
    """
    Emite señal de campana (BEL ASCII 7) compatible con Linux, macOS y Windows.
    - Linux/macOS: Escribe en /dev/tty o sys.stderr.
    - Windows: Escribe en CONOUT$ o sys.stderr o usa Beep de kernel32.
    """
    os_type = get_os_type()

    if os_type == "windows":
        # 1. Intentar consola Windows
        try:
            with open("CONOUT$", "w", encoding="utf-8", errors="ignore") as con:
                con.write("\a")
                con.flush()
                return
        except Exception:
            pass
        # 2. Intentar beep nativo de Windows (sin sonido invasivo o fallback)
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_OK)
            return
        except Exception:
            pass
    else:
        # Linux / macOS: /dev/tty soporta secuencias OSC
        try:
            with open("/dev/tty", "w", encoding="utf-8", errors="ignore") as tty:
                tty.write("\a")
                tty.write("\033]9;AGY: Notificación\007")
                tty.write("\033]777;notify;AGY;Notificación\007")
                tty.flush()
                return
        except Exception:
            pass

    # Fallback universal a stderr
    try:
        sys.stderr.write("\a")
        sys.stderr.flush()
    except Exception:
        pass

def send_desktop_notification(title, message, urgency="normal", timeout_ms=4000, icon="utilities-terminal"):
    """
    Dispara notificación nativa de escritorio adaptada al sistema operativo:
    - Linux: notify-send con flag transitoria (-h int:transient:1)
    - macOS: osascript con display notification o terminal-notifier
    - Windows: PowerShell Toast Notification
    """
    os_type = get_os_type()

    # 1. Linux
    if os_type == "linux":
        if shutil.which("notify-send"):
            try:
                subprocess.run(
                    [
                        "notify-send",
                        "-a", "AGY",
                        "-u", urgency,
                        "-t", str(timeout_ms),
                        "-h", "int:transient:1",
                        "-i", icon,
                        title,
                        message
                    ],
                    capture_output=True,
                    timeout=1.0
                )
            except Exception:
                pass
        return

    # 2. macOS
    if os_type == "macos":
        # Probar primero terminal-notifier si está disponible
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

        # Fallback a AppleScript osascript
        if shutil.which("osascript"):
            safe_title = title.replace('"', '\\"')
            safe_msg = message.replace('"', '\\"')
            script = f'display notification "{safe_msg}" with title "{safe_title}" sound name "default"'
            try:
                subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True,
                    timeout=1.0
                )
            except Exception:
                pass
        return

    # 3. Windows
    if os_type == "windows":
        powershell_bin = shutil.which("powershell.exe") or shutil.which("powershell") or "powershell"
        safe_title = title.replace('"', '`"').replace("'", "''")
        safe_msg = message.replace('"', '`"').replace("'", "''")

        # Script PowerShell de una sola línea para Toast nativo de Windows 10/11
        ps_cmd = (
            f"$title = '{safe_title}'; $msg = '{safe_msg}'; "
            "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null; "
            "$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); "
            "$textNodes = $template.GetElementsByTagName('text'); "
            "$textNodes.Item(0).AppendChild($template.CreateTextNode($title)) > $null; "
            "$textNodes.Item(1).AppendChild($template.CreateTextNode($msg)) > $null; "
            "$toast = [Windows.UI.Notifications.ToastNotification]::new($template); "
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
