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
import time
import tempfile

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

try:
    from trust_levels import evaluate_trust, is_command_critical, get_active_trust_level
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from trust_levels import evaluate_trust, is_command_critical, get_active_trust_level

def handle_pre_tool_use(payload, raw_input):
    """
    Clasificador de Auto Mode basado en Niveles de Confianza (Trust Levels):
    - 'audit': Todo comando o mutación pide aprobación humana.
    - 'workspace-safe' (default): Lecturas y ediciones en workspace seguras, comandos dev permitidos.
    - 'full-developer': Autonomía para build, install y servers locales. Bloquea daño irreversible.
    - 'subagent-worker': Autonomía acotada al worktree asignado.
    - Protocolo de Doble Confirmación para comandos destructivos (deny en paso 1 -> ask en paso 2).
    """
    tool_call = payload.get("toolCall") or {}
    tool_name = tool_call.get("name", "")
    args = tool_call.get("args") or {}
    conv_id = payload.get("conversationId", "")
    workspace_root = payload.get("cwd") or payload.get("workspace", {}).get("current_dir")

    decision, reason = evaluate_trust(tool_name, args, workspace_root=workspace_root, session_id=conv_id)

    if decision == "ask":
        ring_terminal_bell()
        session_title = get_session_title(conv_id)
        send_desktop_notification(
            f"Aegis: {session_title}",
            f"Aprobación requerida: {reason[:65]}",
            urgency="normal",
            timeout_ms=5000,
            icon="dialog-warning",
            session_id=conv_id
        )
        return {"decision": "ask", "reason": reason}

    if decision == "deny":
        session_title = get_session_title(conv_id)
        send_desktop_notification(
            f"Aegis: {session_title}",
            f"Comando interceptado: {reason[:65]}",
            urgency="normal",
            timeout_ms=5000,
            icon="dialog-error",
            session_id=conv_id
        )
        return {"decision": "deny", "reason": reason}

    return {"decision": "allow"}

def handle_stop(payload, raw_input):
    """
    Manejo del evento Stop: El agente ha terminado su ejecución completa.
    - Emite notificación ÚNICAMENTE cuando la respuesta final ha concluido completamente
      y el agente queda libre esperando el siguiente prompt del usuario.
    - NO emite alertas en pasos intermedios, subagentes ni tareas en ejecución.
    """
    conv_id = payload.get("conversationId", "")
    termination_reason = payload.get("terminationReason", "")
    fully_idle = payload.get("fullyIdle")

    # Si hay herramientas pendientes o el estado sigue activo o es paso intermedio, NO es final
    has_pending = bool(
        payload.get("toolCalls") or
        payload.get("pendingToolCalls") or
        payload.get("status") == "running" or
        termination_reason in ("tool_use", "intermediate")
    )
    if has_pending:
        return {"decision": ""}

    # Si fullyIdle está explícitamente en False, todavía hay tareas en background corriendo
    if fully_idle is False:
        return {"decision": ""}

    # Debounce persistente en disco entre procesos aislado por sesión (mínimo 3.0s entre paradas para la misma sesión)
    stop_state_file = os.path.join(tempfile.gettempdir(), ".aegis_stop_notify_state.json")
    now = time.time()
    session_key = conv_id or "default"

    data = {"sessions": {}}
    try:
        if os.path.isfile(stop_state_file):
            with open(stop_state_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict) and "sessions" in loaded:
                    data = loaded
                elif isinstance(loaded, dict):
                    data = {"sessions": {"default": loaded}}
    except Exception:
        pass

    sessions = data.get("sessions", {})
    session_info = sessions.get(session_key, {})
    last_stop = float(session_info.get("time", 0.0))
    if (now - last_stop) < 3.0:
        return {"decision": ""}

    sessions[session_key] = {"time": now, "conv_id": conv_id}
    data["sessions"] = {k: v for k, v in sessions.items() if (now - v.get("time", 0)) < 3600}
    try:
        with open(stop_state_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass

    ring_terminal_bell()
    session_title = get_session_title(conv_id)
    send_desktop_notification(
        f"Aegis: {session_title}",
        "Respuesta completada.",
        urgency="normal",
        timeout_ms=4000,
        icon="utilities-terminal",
        session_id=conv_id
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
