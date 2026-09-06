#!/usr/bin/env python3
"""
Trust Levels Engine for AGY Auto Mode
Define y evalúa 4 niveles de confianza predeterminados para delegar autonomía gradual a los agentes:
- Nivel 0: 'audit' (Solo lectura, toda modificación y comando pide confirmación)
- Nivel 1: 'workspace-safe' (Predeterminado: lectura libre, edición en workspace y comandos de test/inspección)
- Nivel 2: 'full-developer' (Autonomía ágil: instalación de dependencias, servidores locales, git y docker dev)
- Nivel 3: 'subagent-worker' (Autonomía acotada estrictamente dentro de un Git Worktree o directorio de trabajo)
"""

import os
import re
import json
import sys
import hashlib
import time

# Importar detector de entorno para resolución de workspace y settings
try:
    from env_detector import is_path_in_workspace, get_app_data_dir
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from env_detector import is_path_in_workspace, get_app_data_dir

# Constantes de Niveles
LEVEL_AUDIT = "audit"
LEVEL_VPS_PRODUCTION = "vps-production"
LEVEL_WORKSPACE_SAFE = "workspace-safe"
LEVEL_FULL_DEVELOPER = "full-developer"
LEVEL_SUBAGENT_WORKER = "subagent-worker"

TRUST_LEVEL_HIERARCHY = {
    LEVEL_AUDIT: 0,
    LEVEL_VPS_PRODUCTION: 1,
    LEVEL_WORKSPACE_SAFE: 2,
    LEVEL_FULL_DEVELOPER: 3,
    LEVEL_SUBAGENT_WORKER: 4,
}

# 1. Herramientas de solo lectura (seguras en todos los niveles)
SAFE_READ_TOOLS = {
    "view_file",
    "list_dir",
    "grep_search",
    "find_by_name",
    "read_url_content",
    "search_web",
    "invoke_subagent",
    "send_message",
    "manage_subagents",
    "manage_task",
    "schedule",
    "ask_question",
}

# 2. Comandos de inspección y validación seguros (permitidos en Nivel 1, 2 y 3)
SAFE_READ_COMMAND_PATTERNS = [
    r"^\s*git\s+(status|diff|log|show|branch|rev-parse|symbolic-ref)\b",
    r"^\s*(pnpm|npm|yarn|bun)\s+(test|lint|typecheck|check)\b",
    r"^\s*(pytest|cargo\s+(test|check)|go\s+test|dotnet\s+test)\b",
    r"^\s*(ls|cat|head|tail|grep|find|pwd|which|echo|wc|uname|env)\b",
]

# 3. Comandos de desarrollo ampliados (permitidos en Nivel 2: full-developer)
DEVELOPER_EXTENDED_COMMAND_PATTERNS = [
    r"^\s*(pnpm|npm|yarn|bun)\s+(install|add|remove|run|dev|start|build)\b",
    r"^\s*pip\s+(install|uninstall|list|show)\b",
    r"^\s*cargo\s+(add|remove|build|run)\b",
    r"^\s*python3?\s+[\w\./-]+\b",
    r"^\s*node\s+[\w\./-]+\b",
    r"^\s*git\s+(commit|add|checkout|switch|merge|rebase|stash)\b",
    r"^\s*docker\s+(compose\s+(up|down|logs|ps)|ps|logs)\b",
]

# 4. Comandos de daño irreversible (bloqueados con DOBLE CONFIRMACIÓN obligatoria en TODOS los niveles)
CRITICAL_COMMAND_PATTERNS = [
    r"\brm\s+-(?:[a-zA-Z0-9]*r[a-zA-Z0-9]*f|[a-zA-Z0-9]*f[a-zA-Z0-9]*r)\b",
    r"\brm\s+.*-(?:r|R|-recursive)\b.*-(?:f|-force)\b",
    r"\brm\s+.*-(?:f|-force)\b.*-(?:r|R|-recursive)\b",
    r"\brm\s+-(?:r|R|f)\b",
    r"\b(?:shred|wipe)\b",
    r"\bgit\s+(?:push\s+(?:-[a-zA-Z0-9]*f|--force)|reset\s+--hard|clean\s+-(?:[a-zA-Z0-9]*f))\b",
    r"\bdocker\s+(?:rm|rmi|stop|kill|system\s+prune|volume\s+rm)\b",
    r"\b(?:mkfs|fdisk|parted|sfdisk|mkswap)\b|\bdd\s+(?:if|of)=",
    r"\b(?:shutdown|reboot|poweroff|init\s+0)\b",
    r"\bsystemctl\s+(?:stop|disable|mask)\b",
    r"\b(?:drop\s+database|drop\s+table|truncate\s+table)\b",
    r"\b(?:sudo|su\s+-?)\b",
    r"\bchmod\s+.*-R\s+777\b",
]

# 5. Patrones de telemetría e inspección seguros en VPS (permitidos en vps-production)
VPS_SAFE_INSPECTION_PATTERNS = [
    r"^\s*docker\s+(?:ps|logs|inspect|top|port|stats(?:\s+--no-stream)?)\b",
    r"^\s*docker\s+compose\s+(?:ps|logs|top)\b",
    r"^\s*docker-compose\s+(?:ps|logs|top)\b",
    r"^\s*systemctl\s+(?:status|is-active|is-failed)\b",
    r"^\s*journalctl\b",
    r"^\s*caddy\s+(?:validate|version)\b",
    r"^\s*(?:df|free|uptime|uname|top|htop|ps|netstat|ss|lsof)\b",
    r"^\s*curl\s+(?:-[a-zA-Z0-9]*\s+)?https?://",
    r"^\s*ping\s+-c\s+\d+\b",
]

# 6. Patrones de ciclo de vida de VPS (requieren DOBLE CONFIRMACIÓN en vps-production)
VPS_LIFECYCLE_COMMAND_PATTERNS = [
    r"\bdocker\s+(?:stop|restart|kill|pause|unpause|rm|run)\b",
    r"\bdocker\s+compose\s+(?:down|restart|stop|kill|up|build)\b",
    r"\bdocker-compose\s+(?:down|restart|stop|kill|up|build)\b",
    r"\bsystemctl\s+(?:restart|stop|reload|disable|mask)\b",
    r"\bcaddy\s+(?:reload|stop)\b",
    r"\bdocker\s+volume\s+(?:rm|prune)\b",
    r"\bdocker\s+system\s+prune\b",
    r"\bredis-cli\s+(?:flushall|flushdb)\b",
    r"\b(?:psql|mysql)\b",
]

# 7. Archivos críticos de infraestructura en VPS
VPS_CRITICAL_CONFIG_FILES = [
    r"(?:^|/)Caddyfile(?:\.|$)",
    r"(?:^|/)docker-compose(?:\.[a-zA-Z0-9_-]+)?\.ya?ml$",
    r"(?:^|/)\.env(?:\.[a-zA-Z0-9_-]+)?$",
]

def is_vps_safe_inspection(cmd):
    """Verifica si el comando es de inspección/telemetría segura en entorno VPS."""
    if not cmd:
        return False
    if is_command_safe_read(cmd):
        return True
    for pattern in VPS_SAFE_INSPECTION_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return True
    return False

def is_vps_lifecycle_command(cmd):
    """Verifica si el comando afecta el ciclo de vida de contenedores o servicios en producción."""
    if not cmd:
        return False
    for pattern in VPS_LIFECYCLE_COMMAND_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return True
    return False

def is_vps_critical_file(filepath):
    """Verifica si el archivo es un archivo de configuración crítica en producción VPS."""
    if not filepath:
        return False
    norm_path = filepath.replace("\\", "/")
    for pattern in VPS_CRITICAL_CONFIG_FILES:
        if re.search(pattern, norm_path, re.IGNORECASE):
            return True
    return False

class DangerousConfirmationLedger:
    """
    Registro de estado para la DOBLE CONFIRMACIÓN OBLIGATORIA de comandos peligrosos.
    - Intento 1: Devuelve 'deny' instruyendo al agente a solicitar confirmación explícita
      al usuario antes de reintentar. Se registra un token con TTL de 120s.
    - Intento 2: Si el comando se reintenta dentro de 120s, se eleva a 'ask' para que el usuario
      confirme de forma física e interactiva en la terminal (y/n).
    - Tras ser procesado o expirar el TTL, el token se invalida para evitar reusabilidad.
    """
    def __init__(self, ledger_file=None, ttl_seconds=120):
        self.ttl_seconds = ttl_seconds
        if ledger_file is None:
            env_ledger = os.environ.get("AGY_DANGER_LEDGER_FILE")
            if env_ledger:
                self.ledger_file = env_ledger
            else:
                self.ledger_file = os.path.join(get_app_data_dir(), ".danger_confirmations.json")
        else:
            self.ledger_file = ledger_file

    def _normalize_command(self, cmd):
        return re.sub(r"\s+", " ", cmd.strip().lower())

    def _get_hash(self, cmd):
        normalized = self._normalize_command(cmd)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]

    def _read_ledger(self):
        if not os.path.isfile(self.ledger_file):
            return {}
        try:
            with open(self.ledger_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_ledger(self, data):
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.ledger_file)), exist_ok=True)
            with open(self.ledger_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def check_and_advance(self, cmd, session_id=""):
        """
        Retorna (stage, reason):
        - stage 1: Primer intento. Denegado con instrucción obligatoria de solicitar confirmación.
        - stage 2: Segundo intento válido dentro del TTL. Autorizado para prompt interactivo 'ask'.
        """
        if os.environ.get("AGY_DANGER_SKIP_DOUBLE_CONFIRM") == "1":
            return 2, "Doble confirmación omitida por entorno de prueba"

        now = time.time()
        cmd_hash = self._get_hash(cmd)
        data = self._read_ledger()

        # Limpiar tokens expirados
        data = {k: v for k, v in data.items() if (now - v.get("timestamp", 0)) < self.ttl_seconds}

        entry = data.get(cmd_hash)
        if entry:
            stage_current = entry.get("stage", 1)
            if stage_current == 1:
                # Paso 2 alcanzado dentro de la ventana de TTL
                entry["stage"] = 2
                entry["stage2_time"] = now
                self._write_ledger(data)
                return 2, (
                    f"⚠️ [CONFIRMACIÓN DEFINITIVA - PASO 2 DE 2]: Se ha recibido la primera confirmación. "
                    f"El comando '{cmd}' modificará o eliminará datos permanentemente. "
                    f"¿Autorizas la ejecución definitiva en el sistema?"
                )
            elif stage_current == 2:
                # Si se invoca en la misma ráfaga de hooks (< 1.5s), mantener stage 2 para evitar desacuerdo
                if (now - entry.get("stage2_time", 0)) < 1.5:
                    return 2, (
                        f"⚠️ [CONFIRMACIÓN DEFINITIVA - PASO 2 DE 2]: Se ha recibido la primera confirmación. "
                        f"El comando '{cmd}' modificará o eliminará datos permanentemente. "
                        f"¿Autorizas la ejecución definitiva en el sistema?"
                    )
                else:
                    # Token ya consumido en una llamada previa; reiniciar ciclo a stage 1
                    del data[cmd_hash]

        # Paso 1: Registrar nuevo intento y denegar para forzar confirmación en chat
        data[cmd_hash] = {
            "command": cmd,
            "stage": 1,
            "timestamp": now,
            "session_id": session_id
        }
        self._write_ledger(data)
        return 1, (
            f"⚠️ [DOBLE CONFIRMACIÓN REQUERIDA - PASO 1 DE 2]: El comando '{cmd}' está clasificado como "
            f"CRÍTICO/DESTRUCTIVO. Por directiva estricta de seguridad, el agente DEBE solicitar al usuario "
            f"confirmación explícita antes de proceder. Se ha registrado la intención (Paso 1). "
            f"Reintente la ejecución dentro de los próximos {self.ttl_seconds}s solo tras recibir la aprobación del usuario."
        )

    def clear(self):
        try:
            if os.path.isfile(self.ledger_file):
                os.remove(self.ledger_file)
        except Exception:
            pass

def get_active_trust_level():
    """
    Determina el nivel de confianza activo consultando:
    1. Variable de entorno AGY_AUTO_MODE_LEVEL
    2. Archivo de configuración ~/.gemini/antigravity-cli/settings.json ("autoModeLevel")
    3. Fallback predeterminado: 'workspace-safe'
    """
    env_level = os.environ.get("AGY_AUTO_MODE_LEVEL", "").strip().lower()
    if env_level in TRUST_LEVEL_HIERARCHY:
        return env_level
    if env_level in ("vps", "vps-prod", "production-vps"):
        return LEVEL_VPS_PRODUCTION
    if env_level in ("safe", "default"):
        return LEVEL_WORKSPACE_SAFE
    if env_level in ("dev", "developer", "full"):
        return LEVEL_FULL_DEVELOPER

    # Consultar settings.json
    try:
        app_dir = get_app_data_dir()
        settings_file = os.path.join(app_dir, "settings.json")
        if os.path.isfile(settings_file):
            with open(settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                configured = data.get("autoModeLevel") or data.get("trust_level")
                if configured and configured.lower() in TRUST_LEVEL_HIERARCHY:
                    return configured.lower()
    except Exception:
        pass

    return LEVEL_WORKSPACE_SAFE

def is_command_critical(cmd):
    """Verifica si el comando contiene patrones de riesgo crítico irreversible."""
    if not cmd:
        return False
    for pattern in CRITICAL_COMMAND_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return True
    return False

def is_command_safe_read(cmd):
    """Verifica si el comando es de inspección / solo lectura."""
    if not cmd:
        return False
    for pattern in SAFE_READ_COMMAND_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return True
    return False

def is_command_dev_allowed(cmd):
    """Verifica si el comando es de desarrollo permitido en full-developer."""
    if not cmd:
        return False
    if is_command_safe_read(cmd):
        return True
    for pattern in DEVELOPER_EXTENDED_COMMAND_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return True
    return False

def get_settings_permissions_allow():
    """Consulta la lista de comandos explícitamente autorizados en settings.json."""
    try:
        app_dir = get_app_data_dir()
        settings_file = os.path.join(app_dir, "settings.json")
        if os.path.isfile(settings_file):
            with open(settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                perms = data.get("permissions", {}).get("allow", [])
                commands = []
                for p in perms:
                    if isinstance(p, str) and p.startswith("command(") and p.endswith(")"):
                        commands.append(p[8:-1].strip())
                return commands
    except Exception:
        pass
    return []

def is_command_allowed_by_settings(cmd):
    """Evalúa si un comando coincide con las autorizaciones explícitas de settings.json."""
    if not cmd:
        return False
    allowed_list = get_settings_permissions_allow()
    if not allowed_list:
        return False
    cmd_clean = cmd.strip()
    for allowed in allowed_list:
        if not allowed:
            continue
        # Coincidencia exacta o comando seguido de argumentos/espacios
        if cmd_clean == allowed or cmd_clean.startswith(allowed + " "):
            return True
        # Coincidencia por binario base (ej: 'python3' para 'python3 -m unittest')
        if re.match(rf"^\s*(?:sudo\s+)?{re.escape(allowed)}\b", cmd_clean):
            return True
    return False

def evaluate_trust(tool_name, args, workspace_root=None, level=None, session_id="", ledger=None, check_settings=False):
    """
    Evalúa si la herramienta solicitada se aprueba automáticamente o requiere confirmación.
    Retorna: (decision, reason)
    - decision: 'allow', 'ask', o 'deny'
    """
    if level is None:
        level = get_active_trust_level()

    # 1. Herramientas de solo lectura -> Permitidas en todos los niveles
    if tool_name in SAFE_READ_TOOLS:
        return "allow", "Herramienta de solo lectura permitida"

    # 2. Nivel 0: 'audit' -> Cualquier modificación o comando pide confirmación
    if level == LEVEL_AUDIT:
        return "ask", "Modo auditoría: toda modificación o comando requiere aprobación"

    # 3. Herramientas de edición de archivos
    if tool_name in ("write_to_file", "replace_file_content"):
        target_file = args.get("TargetFile", "")
        if level == LEVEL_VPS_PRODUCTION and is_vps_critical_file(target_file):
            return "ask", f"⚠️ Archivo crítico de infraestructura VPS en producción: {os.path.basename(target_file)}"
        if not is_path_in_workspace(target_file, workspace_root):
            return "ask", f"Edición fuera del espacio de trabajo: {target_file}"
        return "allow", "Edición permitida dentro del espacio de trabajo"

    # 4. Comandos de terminal (run_command)
    if tool_name == "run_command":
        cmd = args.get("CommandLine", "").strip()
        if not cmd:
            return "allow", "Comando vacío"

        # Daño irreversible bloqueado SIEMPRE con protocolo de DOBLE CONFIRMACIÓN
        if is_command_critical(cmd):
            conf_ledger = ledger or DangerousConfirmationLedger()
            stage, reason = conf_ledger.check_and_advance(cmd, session_id=session_id)
            if stage == 1:
                return "deny", reason
            else:
                return "ask", reason

        # Comandos explícitamente autorizados por el usuario en settings.json (si se habilita)
        if check_settings and is_command_allowed_by_settings(cmd):
            return "allow", "Comando autorizado explícitamente en configuración de permisos"

        # Nivel 1: 'vps-production' (Blindaje de servidores y contenedores de producción)
        if level == LEVEL_VPS_PRODUCTION:
            if is_vps_lifecycle_command(cmd):
                conf_ledger = ledger or DangerousConfirmationLedger()
                stage, reason = conf_ledger.check_and_advance(cmd, session_id=session_id)
                if stage == 1:
                    return "deny", (
                        f"🛡️ [PROTOCOLO VPS - PASO 1 DE 2]: El comando de ciclo de vida '{cmd}' puede alterar o detener "
                        f"servicios de producción. El agente DEBE explicar el impacto y solicitar autorización explícita. "
                        f"Reintente en {conf_ledger.ttl_seconds}s tras confirmación del usuario."
                    )
                else:
                    return "ask", (
                        f"⚠️ [CONFIRMACIÓN VPS - PASO 2 DE 2]: Se ha recibido la primera autorización. "
                        f"¿Confirmas definitivamente ejecutar '{cmd}' en el VPS de producción?"
                    )
            if is_vps_safe_inspection(cmd):
                return "allow", "Comando de telemetría e inspección seguro en VPS"
            return "ask", f"Comando requiere confirmación en modo vps-production: {cmd}"

        # Nivel 2: 'workspace-safe'
        if level == LEVEL_WORKSPACE_SAFE:
            if is_command_safe_read(cmd):
                return "allow", "Comando de inspección seguro"
            return "ask", f"Comando no clasificado como seguro en modo workspace-safe: {cmd}"

        # Nivel 2: 'full-developer'
        if level == LEVEL_FULL_DEVELOPER:
            if is_command_dev_allowed(cmd):
                return "allow", "Comando de desarrollo permitido en modo full-developer"
            return "ask", f"Comando requiere confirmación en modo developer: {cmd}"

        # Nivel 3: 'subagent-worker'
        if level == LEVEL_SUBAGENT_WORKER:
            # En worker, las operaciones dentro del worktree están permitidas salvo escapes del sistema
            if is_command_safe_read(cmd) or is_command_dev_allowed(cmd):
                return "allow", "Acción permitida para subagente worker"
            return "ask", f"Comando requiere autorización para el worker: {cmd}"

    # Default seguro
    return "ask", f"Herramienta {tool_name} requiere confirmación"
