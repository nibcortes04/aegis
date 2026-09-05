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

if ! command -v notify-send >/dev/null 2>&1; then
  echo "⚠️ Advertencia: notify-send no fue detectado. Las alertas de escritorio no se emitirán (la campana de terminal seguirá funcionando)."
fi

# 2. Crear directorios de destino
mkdir -p "$USER_SCRIPTS" "$GEMINI_CONFIG" "$GEMINI_CLI" "$GEMINI_SKILLS"

# 3. Copiar scripts ejecutables
echo "▶ Instalando scripts en $USER_SCRIPTS..."
cp "${SCRIPT_DIR}/scripts/agy_hook_handler.py" "$USER_SCRIPTS/"
cp "${SCRIPT_DIR}/scripts/agy-hook-dispatcher.sh" "$USER_SCRIPTS/"
cp "${SCRIPT_DIR}/scripts/statusline_formatter.py" "$USER_SCRIPTS/"
cp "${SCRIPT_DIR}/scripts/statusline.sh" "$USER_SCRIPTS/"
cp "${SCRIPT_DIR}/scripts/agy-session.sh" "$USER_SCRIPTS/"
chmod +x "${USER_SCRIPTS}"/agy*.py "${USER_SCRIPTS}"/agy*.sh "${USER_SCRIPTS}"/statusline*.py "${USER_SCRIPTS}"/statusline*.sh 2>/dev/null || true

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
HOOKS_FILE="${GEMINI_CONFIG}/hooks.json"
if [ -f "$HOOKS_FILE" ]; then
  cp "$HOOKS_FILE" "${HOOKS_FILE}.bak.$(date +%s)"
fi

python3 - << 'PY'
import json, os
hooks_path = os.path.expanduser("~/.gemini/config/hooks.json")
dispatcher = os.path.expanduser("~/scripts/agy-hook-dispatcher.sh")

data = {}
if os.path.isfile(hooks_path):
    try:
        with open(hooks_path, "r") as f:
            data = json.load(f)
    except Exception:
        data = {}

data["agy-powerpack"] = {
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

with open(hooks_path, "w") as f:
    json.dump(data, f, indent=2)
print("✔ Hooks registrados exitosamente en:", hooks_path)
PY

# 6. Configurar settings en ~/.gemini/antigravity-cli/settings.json
echo "▶ Configurando Statusline y Modo en settings.json..."
SETTINGS_FILE="${GEMINI_CLI}/settings.json"
if [ -f "$SETTINGS_FILE" ]; then
  cp "$SETTINGS_FILE" "${SETTINGS_FILE}.bak.$(date +%s)"
fi

python3 - << 'PY'
import json, os
settings_path = os.path.expanduser("~/.gemini/antigravity-cli/settings.json")
statusline_script = os.path.expanduser("~/scripts/statusline.sh")

data = {}
if os.path.isfile(settings_path):
    try:
        with open(settings_path, "r") as f:
            data = json.load(f)
    except Exception:
        data = {}

data["mode"] = "accept-edits"
data["statusLine"] = {
    "type": "command",
    "command": statusline_script,
    "enabled": True
}

allowlist = data.setdefault("permissions", {}).setdefault("allow", [])
standard_cmds = [
    "command(git)", "command(pnpm)", "command(npm)", "command(yarn)",
    "command(cargo)", "command(python3)", "command(python)", "command(pytest)",
    "command(node)", "command(npx)", "command(which)", "command(pwd)",
    "command(docker ps)", "command(docker logs)", "command(cat)", "command(tail)",
    "command(head)", "command(cp)", "command(echo)", "command(grep)", "command(cut)",
    "command(ls)", "command(find)", "command(mkdir)", "command(touch)", "command(wc)"
]
for cmd in standard_cmds:
    if cmd not in allowlist:
        allowlist.append(cmd)

with open(settings_path, "w") as f:
    json.dump(data, f, indent=2)
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
