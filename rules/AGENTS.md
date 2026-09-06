# Aegis Agent Guidelines

When operating within a project using the Aegis plugin:

## 1. Auto Mode, Safe Execution & Two-Factor Safety Gate
- Favor safe, idempotent operations that can be automatically approved by the classifier.
- Keep commands prefix-matchable (`git status`, `git diff`, `pnpm test`, `pytest`, `cargo test`).
- **Protocolo de Doble Confirmación para Operaciones Destructivas (CRÍTICO):**
  - Queda estrictamente prohibido intentar ejecutar operaciones destructivas (`rm -rf`, `docker rm/stop/volume rm`, `dd`, `mkfs`, `sudo`, `drop database/table`, `git push --force`) sin solicitar y recibir la confirmación explícita del usuario **dos veces consecutivas**.
  - **Paso 1:** El agente debe explicar con total claridad el riesgo y preguntar al usuario en el chat (`"¿Estás seguro de que deseas proceder con la eliminación/modificación de X?"`).
  - **Paso 2:** El hook de seguridad del sistema intercepta y exige la confirmación final interactiva antes de autorizar la llamada a la herramienta.
- Si un comando requiere permisos de superusuario (`sudo`) o altera archivos fuera del workspace, exponga el motivo y solicite autorización previa.

## 2. Notification Awareness
- El usuario recibe alertas limpias (campana de pestaña `\a` y notificación flotante no apilable) **únicamente cuando se requiere acción interactiva o al concluir el turno final**.
- No ejecute bucles que saturen la terminal de alertas sonoras.

## 3. Inspección Autónoma del Entorno
- Utilice el inspector autónomo (`python3 scripts/env_inspector.py` o herramienta MCP `aegis_inspect_environment`) para verificar qué compiladores, runtimes y herramientas DevOps están presentes en el host antes de asumir disponibilidad de software.

## 4. Session Continuity & Worktrees
- Para tareas complejas, aislamiento de bugs o colaboración con bots autónomos, cree un Git Worktree dedicado con `./scripts/dev-worktree.sh` para preservar el contexto limpio y evitar conflictos en la rama principal.

## 5. Operaciones en VPS y Entornos de Producción (`vps-production`)
- Al operar sobre servidores VPS o infraestructura en producción (Caddy, n8n, Chatwoot, Docker Compose, Postgres, Redis):
  - Utilice comandos de telemetría y diagnóstico seguros (`docker ps`, `docker logs`, `systemctl status`, `caddy validate`, `python3 scripts/vps_health.py` o MCP `aegis_check_vps_health`).
  - Las acciones que alteren el ciclo de vida de contenedores o servicios (`docker restart`, `docker stop`, `docker compose down/up`, `systemctl restart/reload`) están protegidas por el protocolo de doble verificación (Paso 1: Bloqueo y explicación de impacto; Paso 2: Aprobación interactiva en terminal).
  - Toda mutación sobre archivos de infraestructura (`Caddyfile`, `docker-compose*.yml`, `.env*`) requiere confirmación humana interactiva.
