#!/bin/bash
# agy-powerpack: Instalador automatizado para Antigravity CLI
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_SCRIPTS="${HOME}/scripts"
GEMINI_CONFIG="${HOME}/.gemini/config"
GEMINI_CLI="${HOME}/.gemini/antigravity-cli"
GEMINI_SKILLS="${GEMINI_CLI}/skills"

echo "===================================================="
echo "    Instalador de Antigravity Powerpack (agy)       "
echo "===================================================="

# 1. Comprobar dependencias básicas
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ Error: python3 es requerido pero no está instalado."
  exit 1
fi

if [ "$(uname)" = "Darwin" ]; then
  echo "✔ macOS detectado (notificaciones nativas vía osascript/terminal-notifier)."
elif ! command -v notify-send >/dev/null 2>&1; then
  echo "⚠️ Advertencia: notify-send no fue detectado. Las alertas de escritorio no se emitirán (la campana de terminal seguirá funcionando)."
fi

# 2. Crear directorios de destino
mkdir -p "$USER_SCRIPTS" "$GEMINI_CONFIG" "$GEMINI_CLI" "$GEMINI_SKILLS"

# 3. Copiar scripts ejecutables
echo "▶ Instalando scripts en $USER_SCRIPTS..."
cp "${SCRIPT_DIR}/scripts/env_detector.py" "$USER_SCRIPTS/"
cp "${SCRIPT_DIR}/scripts/trust_levels.py" "$USER_SCRIPTS/"
cp "${SCRIPT_DIR}/scripts/agy_hook_handler.py" "$USER_SCRIPTS/"
cp "${SCRIPT_DIR}/scripts/agy-hook-dispatcher.sh" "$USER_SCRIPTS/"
cp "${SCRIPT_DIR}/scripts/statusline_formatter.py" "$USER_SCRIPTS/"
cp "${SCRIPT_DIR}/scripts/statusline.sh" "$USER_SCRIPTS/"
cp "${SCRIPT_DIR}/scripts/agy-session.sh" "$USER_SCRIPTS/"
chmod +x "${USER_SCRIPTS}"/*.py "${USER_SCRIPTS}"/*.sh 2>/dev/null || true

# Opcional: enlazar agy-session a ~/.local/bin si existe
if [ -d "${HOME}/.local/bin" ]; then
  ln -sf "${USER_SCRIPTS}/agy-session.sh" "${HOME}/.local/bin/agy-session"
fi

# 4. Instalar la Skill en el entorno de AGY
echo "▶ Instalando Skill agy-powerpack en $GEMINI_SKILLS..."
rm -rf "${GEMINI_SKILLS}/agy-powerpack"
cp -r "${SCRIPT_DIR}/skills/agy-powerpack" "${GEMINI_SKILLS}/"

# 5. Configurar hooks en ~/.gemini/config/hooks.json
echo "▶ Configurando Lifecycle Hooks..."
python3 - << 'PY'
import json, os, shutil, time
hooks_path = os.path.expanduser("~/.gemini/config/hooks.json")
dispatcher = os.path.expanduser("~/scripts/agy-hook-dispatcher.sh")

data = {}
if os.path.isfile(hooks_path):
    try:
        with open(hooks_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}

expected_entry = {
    "PreToolUse": [
        {
            "matcher": "*",
            "hooks": [
                {
                    "type": "command",
                    "command": f"{dispatcher} PreToolUse",
                    "timeout": 10
                }
            ]
        }
    ],
    "Stop": [
        {
            "type": "command",
            "command": f"{dispatcher} Stop",
            "timeout": 10
        }
    ]
}

if data.get("agy-powerpack") == expected_entry:
    print("✔ Hooks ya configurados correctamente (idempotente, omitiendo escritura).")
else:
    if os.path.isfile(hooks_path):
        shutil.copy2(hooks_path, f"{hooks_path}.bak.{int(time.time())}")
    data["agy-powerpack"] = expected_entry
    with open(hooks_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("✔ Hooks registrados exitosamente en:", hooks_path)
PY

# 6. Configurar settings en ~/.gemini/antigravity-cli/settings.json
echo "▶ Configurando Statusline y Modo en settings.json..."
python3 - << 'PY'
import json, os, shutil, time
settings_path = os.path.expanduser("~/.gemini/antigravity-cli/settings.json")
statusline_script = os.path.expanduser("~/scripts/statusline.sh")

data = {}
if os.path.isfile(settings_path):
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}

expected_statusline = {
    "type": "command",
    "command": statusline_script,
    "enabled": True
}

standard_cmds = [
    "command(git)", "command(pnpm)", "command(npm)", "command(yarn)",
    "command(cargo)", "command(python3)", "command(python)", "command(pytest)",
    "command(node)", "command(npx)", "command(which)", "command(pwd)",
    "command(docker ps)", "command(docker logs)", "command(cat)", "command(tail)",
    "command(head)", "command(cp)", "command(echo)", "command(grep)", "command(cut)",
    "command(ls)", "command(find)", "command(mkdir)", "command(touch)", "command(wc)"
]

current_allow = data.get("permissions", {}).get("allow", [])
has_all_cmds = all(cmd in current_allow for cmd in standard_cmds)
is_mode_set = data.get("mode") == "accept-edits"
is_statusline_set = data.get("statusLine") == expected_statusline
is_trust_level_set = data.get("autoModeLevel") in ["audit", "workspace-safe", "full-developer", "subagent-worker"]

if is_mode_set and is_statusline_set and has_all_cmds and is_trust_level_set:
    print("✔ settings.json ya configurado correctamente (idempotente, omitiendo escritura).")
else:
    if os.path.isfile(settings_path):
        shutil.copy2(settings_path, f"{settings_path}.bak.{int(time.time())}")

    data["mode"] = "accept-edits"
    data["statusLine"] = expected_statusline
    if "autoModeLevel" not in data:
        data["autoModeLevel"] = "workspace-safe"

    allowlist = data.setdefault("permissions", {}).setdefault("allow", [])
    for cmd in standard_cmds:
        if cmd not in allowlist:
            allowlist.append(cmd)

    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("✔ settings.json actualizado con éxito.")
PY

# 7. Configurar enlace para Orca si existe
ORCA_HOOK="${HOME}/.orca/agent-hooks/antigravity-hook.sh"
if [ -d "$(dirname "$ORCA_HOOK")" ]; then
  cat << 'EOF_ORCA' > "$ORCA_HOOK"
#!/bin/sh
EVENT="${ORCA_ANTIGRAVITY_EVENT:-${1:-Stop}}"
exec /usr/bin/python3 "${HOME}/scripts/agy_hook_handler.py" "$EVENT"
EOF_ORCA
  chmod +x "$ORCA_HOOK"
  echo "✔ Hook para Orca IDE sincronizado."
fi

echo ""
echo "🎉 ¡Instalación completada exitosamente!"
echo "----------------------------------------------------"
echo "• Smart Auto Mode: Activo (Shift+Tab para ciclar)."
echo "• Notificaciones: Campana en terminal (🔔) y avisos de escritorio de 4s."
echo "• Statusline: Enriquecida con cuotas 5h/7d y diff git."
echo "• Gestor de sesiones: Ejecuta 'agy-session list' para ver tus sesiones."
echo "===================================================="
