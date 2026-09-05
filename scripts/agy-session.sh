#!/bin/bash
# agy-session: Helper CLI para gestionar y continuar sesiones de Antigravity
set -euo pipefail

DB_PATH="${HOME}/.gemini/antigravity-cli/conversation_summaries.db"

show_help() {
  cat << 'HELP'
Uso: agy-session <subcomando> [opciones]

Subcomandos:
  list                Lista las sesiones recientes de AGY con título y workspace
  resume [id]         Reanuda una sesión por UUID (o la última si se omite el ID)
  remote              Muestra el estado del daemon de control remoto (PWA / Web)
  help                Muestra esta ayuda

Ejemplos:
  agy-session list
  agy-session resume
  agy-session resume 81241e33-f2ae-4698-b906-9d3607e2062f
  agy-session remote
HELP
}

list_sessions() {
  if [ ! -f "$DB_PATH" ]; then
    echo "No se encontró base de datos de sesiones en $DB_PATH"
    exit 1
  fi
  python3 - << 'PY'
import sqlite3, os
db = os.path.expanduser("~/.gemini/antigravity-cli/conversation_summaries.db")
con = sqlite3.connect(db)
cur = con.cursor()
rows = cur.execute("""
  SELECT conversation_id, title, preview, last_modified_time, workspace_uris
  FROM conversation_summaries
  ORDER BY last_modified_time DESC
  LIMIT 15
""").fetchall()

print(f"{'ID':<10} {'TÍTULO / PREVIEW':<35} {'FECHA':<20} {'WORKSPACE'}")
print("-" * 90)
for r in rows:
    cid = r[0][:8]
    title = (r[1] or r[2] or "Sin título")[:33]
    date = str(r[3])[:19]
    ws = r[4].replace('["file://', '').replace('"]', '').replace('file://', '')
    print(f"{cid:<10} {title:<35} {date:<20} {ws}")
PY
}

resume_session() {
  local target_id="${1:-}"
  if [ -n "$target_id" ]; then
    echo "Reanudando conversación: $target_id"
    exec agy --conversation "$target_id"
  else
    echo "Reanudando última sesión en este workspace..."
    exec agy -c
  fi
}

remote_status() {
  agy remote-control status || true
  echo ""
  echo "Accede a la PWA / Web Dashboard en: https://antigravity.google"
}

case "${1:-help}" in
  list)
    list_sessions
    ;;
  resume)
    shift
    resume_session "${1:-}"
    ;;
  remote)
    remote_status
    ;;
  help|--help|-h)
    show_help
    ;;
  *)
    echo "Comando no reconocido: $1"
    show_help
    exit 1
    ;;
esac
