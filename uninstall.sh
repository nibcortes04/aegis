#!/bin/bash
# Aegis: Desinstalador limpio
set -euo pipefail

GEMINI_CONFIG="${HOME}/.gemini/config"
GEMINI_CLI="${HOME}/.gemini/antigravity-cli"
USER_SCRIPTS="${HOME}/scripts"

echo "Desinstalando Aegis..."

# Eliminar hook de hooks.json
HOOKS_FILE="${GEMINI_CONFIG}/hooks.json"
if [ -f "$HOOKS_FILE" ]; then
  python3 - << 'PY'
import json, os
p = os.path.expanduser("~/.gemini/config/hooks.json")
try:
    with open(p, "r") as f:
        d = json.load(f)
    for key in ("aegis", "agy-powerpack"):
        if key in d:
            del d[key]
    with open(p, "w") as f:
        json.dump(d, f, indent=2)
    print("✔ Hooks de Aegis removidos.")
except Exception as e:
    print("Aviso al remover hooks:", e)
PY
fi

# Eliminar Skills
rm -rf "${GEMINI_CLI}/skills/aegis" "${GEMINI_CLI}/skills/agy-powerpack"

# Eliminar enlace binario
rm -f "${HOME}/.local/bin/agy-session"

echo "✔ Desinstalación completada."
