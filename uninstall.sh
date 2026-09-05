#!/bin/bash
# agy-powerpack: Desinstalador limpio
set -euo pipefail

GEMINI_CONFIG="${HOME}/.gemini/config"
GEMINI_CLI="${HOME}/.gemini/antigravity-cli"
USER_SCRIPTS="${HOME}/scripts"

echo "Desinstalando agy-powerpack..."

# Eliminar hook de hooks.json
HOOKS_FILE="${GEMINI_CONFIG}/hooks.json"
if [ -f "$HOOKS_FILE" ]; then
  python3 - << 'PY'
import json, os
p = os.path.expanduser("~/.gemini/config/hooks.json")
try:
    with open(p, "r") as f:
        d = json.load(f)
    if "agy-powerpack" in d:
        del d["agy-powerpack"]
    with open(p, "w") as f:
        json.dump(d, f, indent=2)
    print("✔ Hooks de agy-powerpack removidos.")
except Exception as e:
    print("Aviso al remover hooks:", e)
PY
fi

# Eliminar Skill
rm -rf "${GEMINI_CLI}/skills/agy-powerpack"

# Eliminar enlace binario
rm -f "${HOME}/.local/bin/agy-session"

echo "✔ Desinstalación completada."
