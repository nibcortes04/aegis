#!/usr/bin/env python3
"""
Antigravity CLI Hook Handler & Dispatcher
- Clasificador inteligente para Auto Mode (estilo Claude Code).
- Notificaciones del sistema no bloqueantes con auto-expiración (4s).
- Campana en terminal tab (\a + OSC 9/777 para Konsole / iTerm / Orca).
- Sincronización con Orca daemon si el endpoint está activo.
"""

import sys
import os
import json
import re
import subprocess
import sqlite3

# Importar detector de entorno y abstracciones multiplataforma
try:
    from env_detector import (
        ring_terminal_bell,
        send_desktop_notification,
        is_path_in_workspace,
        get_summaries_db_path,
        get_os_type,
        get_surface_type,
    )
except ImportError:
    # Fallback si se ejecuta fuera del directorio scripts/
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from env_detector import (
        ring_terminal_bell,
        send_desktop_notification,
        is_path_in_workspace,
        get_summaries_db_path,
        get_os_type,
        get_surface_type,
    )

def get_session_title(conversation_id):
    """Consulta el título o preview de la conversación en SQLite de forma portable."""
    if not conversation_id:
        return "Sesión activa"
    db_path = get_summaries_db_path()
    if not os.path.isfile(db_path):
        return f"Sesión {conversation_id[:8]}"
    try:
        con = sqlite3.connect(db_path, timeout=0.08)
        cur = con.cursor()
        cur.execute(
            "SELECT title, preview FROM conversation_summaries WHERE conversation_id = ?",
            (conversation_id,)
        )
        row = cur.fetchone()
        if row:
            title = row[0] or row[1]
            if title:
                return title
    except Exception:
        pass
    return f"Sesión {conversation_id[:8]}"

def forward_to_orca(event_name, raw_payload):
    """Reenvía el evento a Orca daemon si el endpoint está disponible."""
    endpoint_file = "/home/n_n/.config/orca/agent-hooks/endpoint.env"
    port, token = None, None
    
    # Leer endpoint.env si no están en variables de entorno
    if os.path.isfile(endpoint_file):
        try:
            with open(endpoint_file, "r") as f:
                for line in f:
                    if line.startswith("ORCA_AGENT_HOOK_PORT="):
                        port = line.strip().split("=", 1)[1]
                    elif line.startswith("ORCA_AGENT_HOOK_TOKEN="):
                        token = line.strip().split("=", 1)[1]
        except Exception:
            pass

    port = os.environ.get("ORCA_AGENT_HOOK_PORT", port)
    token = os.environ.get("ORCA_AGENT_HOOK_TOKEN", token)
    pane_key = os.environ.get("ORCA_PANE_KEY", "")

    if port and token and pane_key:
        try:
            subprocess.run(
                [
                    "curl", "-sS", "-X", "POST",
                    f"http://127.0.0.1:{port}/hook/antigravity",
                    "--connect-timeout", "0.3",
                    "--max-time", "0.8",
                    "-H", "Content-Type: application/x-www-form-urlencoded",
                    "-H", f"X-Orca-Agent-Hook-Token: {token}",
                    "--data-urlencode", f"paneKey={pane_key}",
                    "--data-urlencode", f"tabId={os.environ.get('ORCA_TAB_ID', '')}",
                    "--data-urlencode", f"launchToken={os.environ.get('ORCA_AGENT_LAUNCH_TOKEN', '')}",
                    "--data-urlencode", f"worktreeId={os.environ.get('ORCA_WORKTREE_ID', '')}",
                    "--data-urlencode", f"env={os.environ.get('ORCA_AGENT_HOOK_ENV', '')}",
                    "--data-urlencode", f"version={os.environ.get('ORCA_AGENT_HOOK_VERSION', '')}",
                    "--data-urlencode", f"hook_event_name={event_name}",
                    "--data-urlencode", f"payload={raw_payload}"
                ],
                capture_output=True,
                timeout=1.0
            )
        except Exception:
            pass

# Comandos y patrones de alto riesgo que NUNCA se auto-aprueban
CRITICAL_COMMAND_PATTERNS = [
    r"\brm\s+-(?:[a-zA-Z0-9]*r[a-zA-Z0-9]*f|[a-zA-Z0-9]*f[a-zA-Z0-9]*r)\b",
    r"\brm\s+.*-(?:r|R|-recursive)\b.*-(?:f|-force)\b",
    r"\brm\s+.*-(?:f|-force)\b.*-(?:r|R|-recursive)\b",
    r"\bgit\s+(?:push\s+(?:-[a-zA-Z0-9]*f|--force)|reset\s+--hard|clean\s+-(?:[a-zA-Z0-9]*f))\b",
    r"\bdocker\s+(?:rm|rmi|stop|kill|system\s+prune|volume\s+rm)\b",
    r"\b(?:mkfs|fdisk|parted)\b|\bdd\s+(?:if|of)=",
    r"\b(?:shutdown|reboot|poweroff|init\s+0)\b",
    r"\bdrop\s+database\b",
    r"\bsudo\b",
]

# Herramientas de solo lectura (siempre seguras en auto mode)
SAFE_READ_TOOLS = {
    "view_file",
    "list_dir",
    "grep_search",
    "find_by_name",
    "read_url_content",
    "read_browser_page",
    "search_web",
    "ask_question",
    "schedule",
    "manage_task",
    "manage_subagents",
    "invoke_subagent",
}

def is_command_critical(cmd):
    """Evalúa si un comando es crítico o destructivo."""
    if not cmd:
        return False
    for pattern in CRITICAL_COMMAND_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return True
    return False

def handle_pre_tool_use(payload, raw_input):
    """
    Clasificador de Auto Mode:
    - Retorna 'allow' para herramientas seguras y comandos no destructivos.
    - Retorna 'ask' si el comando es crítico o requiere autorización humana.
    """
    tool_call = payload.get("toolCall") or {}
    tool_name = tool_call.get("name", "")
    args = tool_call.get("args") or {}
    conv_id = payload.get("conversationId", "")

    # 1. Herramientas de solo lectura -> Auto-Allow
    if tool_name in SAFE_READ_TOOLS:
        return {"decision": "allow"}

    # 2. Herramientas de edición de archivos en workspace
    if tool_name in ("write_to_file", "replace_file_content"):
        target_file = args.get("TargetFile", "")
        workspace_root = payload.get("cwd") or payload.get("workspace", {}).get("current_dir")
        # Si el archivo está fuera del workspace o del home del usuario -> Pedir confirmación
        if not is_path_in_workspace(target_file, workspace_root):
            ring_terminal_bell()
            session_title = get_session_title(conv_id)
            send_desktop_notification(
                f"AGY: {session_title}",
                f"Aprobación requerida para editar fuera de workspace: {target_file}",
                urgency="normal",
                timeout_ms=5000,
                icon="dialog-warning"
            )
            return {"decision": "ask", "reason": "Edición en archivo fuera de workspace"}
        return {"decision": "allow"}

    # 3. Comandos de terminal (run_command)
    if tool_name == "run_command":
        cmd = args.get("CommandLine", "").strip()

        # Si es destructivo -> Pedir aprobación + notificar (5s) + campanita
        if is_command_critical(cmd):
            ring_terminal_bell()
            session_title = get_session_title(conv_id)
            send_desktop_notification(
                f"AGY: {session_title}",
                f"Aprobación requerida: {cmd[:50]}...",
                urgency="normal",
                timeout_ms=5000,
                icon="dialog-warning"
            )
            return {"decision": "ask", "reason": "Comando potencialmente destructivo"}

        # De lo contrario -> Auto-Allow
        return {"decision": "allow"}

    # 4. Por defecto en Auto Mode -> allow
    return {"decision": "allow"}

def handle_stop(payload, raw_input):
    """
    Manejo del evento Stop: AGY ha terminado de responder.
    - Emite campanita en TTY (icono de campana en la tab de Konsole / Orca).
    - Muestra notificación en el escritorio que desaparece a los 4 segundos.
    """
    conv_id = payload.get("conversationId", "")
    termination_reason = payload.get("terminationReason", "")
    fully_idle = payload.get("fullyIdle", True)

    if fully_idle or termination_reason in ("model_stop", ""):
        ring_terminal_bell()
        session_title = get_session_title(conv_id)
        send_desktop_notification(
            f"AGY: {session_title}",
            "Respuesta completada.",
            urgency="normal",
            timeout_ms=4000,
            icon="utilities-terminal"
        )

    return {"decision": ""}

def main():
    raw_input = sys.stdin.read()
    
    payload = {}
    if raw_input.strip():
        try:
            payload = json.loads(raw_input)
        except Exception:
            payload = {}

    event_name = sys.argv[1] if len(sys.argv) > 1 else (
        payload.get("hookEventName") or 
        payload.get("hook_event_name") or 
        os.environ.get("ORCA_ANTIGRAVITY_EVENT", "Stop")
    )

    response = {}
    if event_name == "PreToolUse":
        response = handle_pre_tool_use(payload, raw_input)
    elif event_name == "Stop":
        response = handle_stop(payload, raw_input)
    else:
        # PreInvocation, PostInvocation, PostToolUse
        response = {}

    # Sincronización en segundo plano con Orca si está disponible
    try:
        forward_to_orca(event_name, raw_input)
    except Exception:
        pass

    # Imprimir respuesta JSON obligatoria en stdout para AGY
    print(json.dumps(response))

if __name__ == "__main__":
    main()
