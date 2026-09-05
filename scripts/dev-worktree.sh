#!/bin/bash
# dev-worktree: Helper para crear y gestionar Git Worktrees aislados por epic, fix o bot
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

show_help() {
  cat << 'HELP'
Uso: dev-worktree <subcomando> [opciones]

Subcomandos:
  create <rama>       Crea un nuevo worktree aislado a partir de la rama 'dev'
  list                Lista todos los worktrees activos del repositorio
  remove <rama>       Elimina el worktree especificado y limpia las referencias
  help                Muestra esta ayuda

Convenciones de ramas:
  feat/<epic>         Para nuevas funcionalidades
  fix/<issue>-<desc>  Para corrección de bugs
  bot/<issue>-<task>  Para PRs automáticos de agentes o bots
  docs/<seccion>      Para mejoras de documentación

Ejemplo:
  ./scripts/dev-worktree.sh create feat/nueva-alerta
  ./scripts/dev-worktree.sh remove feat/nueva-alerta
HELP
}

create_worktree() {
  local branch_name="${1:-}"
  if [ -z "$branch_name" ]; then
    echo "Error: Debes especificar el nombre de la rama (ej. feat/nueva-mejora)"
    exit 1
  fi

  local safe_name
  safe_name=$(echo "$branch_name" | tr '/' '-')
  local target_dir="${REPO_ROOT}/../agy-powerpack-${safe_name}"

  # Asegurar que dev exista
  if ! git show-ref --verify --quiet refs/heads/dev; then
    if git show-ref --verify --quiet refs/heads/main; then
      git branch dev main 2>/dev/null || true
    fi
  fi

  echo "Creando worktree en: $target_dir"
  echo "Rama: $branch_name (basada en dev)"
  git worktree add -b "$branch_name" "$target_dir" dev 2>/dev/null || git worktree add "$target_dir" "$branch_name"
  echo "✔ Worktree creado con éxito."
  echo "Para empezar a trabajar:"
  echo "  cd $target_dir"
}

list_worktrees() {
  git worktree list
}

remove_worktree() {
  local branch_name="${1:-}"
  if [ -z "$branch_name" ]; then
    echo "Error: Debes especificar el nombre de la rama del worktree a eliminar"
    exit 1
  fi

  local safe_name
  safe_name=$(echo "$branch_name" | tr '/' '-')
  local target_dir="${REPO_ROOT}/../agy-powerpack-${safe_name}"

  if [ -d "$target_dir" ]; then
    git worktree remove "$target_dir"
    echo "✔ Worktree $target_dir eliminado."
  else
    git worktree prune
    echo "✔ Worktrees obsoletos podados (pruned)."
  fi
}

case "${1:-help}" in
  create)
    shift
    create_worktree "${1:-}"
    ;;
  list)
    list_worktrees
    ;;
  remove)
    shift
    remove_worktree "${1:-}"
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
