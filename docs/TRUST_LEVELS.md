# 🛡️ Auto Mode Trust Levels & Two-Factor Safety Gate

Este documento detalla la arquitectura de seguridad y niveles de confianza graduados de **Aegis**, permitiendo a los desarrolladores y agentes de IA seleccionar el equilibrio perfecto entre autonomía y protección del sistema.

---

## 🔒 1. Two-Factor Safety Gate (Protocolo de Doble Confirmación)

Para garantizar la estabilidad del sistema y evitar pérdidas catastróficas de datos, **ningún comando crítico o destructivo puede ejecutarse con una sola confirmación o click accidental**.

### Funcionamiento del Two-Factor Safety Gate:
1. **Intento 1 (Interceptado por el Hook):**
   - Cuando un agente intenta ejecutar un comando crítico (ej: `rm -rf`, `docker rm`, `drop table`, `dd`, `git push --force`):
   - El clasificador consulta el ledger de confirmaciones (`~/.gemini/antigravity-cli/.danger_confirmations.json`).
   - Al no existir una confirmación previa, **el hook retorna `decision: deny`** con un mensaje explícito:
     `⚠️ [DOBLE CONFIRMACIÓN REQUERIDA - PASO 1 DE 2]: El comando '...' está clasificado como CRÍTICO/DESTRUCTIVO. El agente DEBE solicitar al usuario confirmación explícita antes de proceder.`
   - Se registra un token temporal en el ledger con **TTL de 120 segundos**.
2. **Paso Intermedio (Human-in-the-Loop):**
   - El agente recibe el bloqueo e interactúa en el chat con el usuario:
     `"El comando '...' es destructivo. ¿Estás seguro de que deseas autorizar esta acción?"`
   - El usuario responde: `"Sí, confirmo"`.
3. **Intento 2 (Aprobación Final):**
   - El agente reintenta el comando idéntico dentro de la ventana de 120 segundos.
   - El hook valida que el Paso 1 se registró correctamente y eleva la solicitud a **`decision: ask`**:
     `⚠️ [CONFIRMACIÓN DEFINITIVA - PASO 2 DE 2]: Se detectó la segunda confirmación. ¿Autorizas la ejecución definitiva?`
   - El usuario confirma con `y` en la terminal interactiva de AGY.
   - El token se consume e invalida inmediatamente.

### Comandos Bajo Doble Confirmación Obligatoria:
- **Borrado Masivo:** `rm -rf`, `rm -r`, `rm -f`, `shred`, `wipe`.
- **Almacenamiento / Particiones:** `dd`, `mkfs`, `fdisk`, `parted`, `sfdisk`, `mkswap`.
- **Contenedores y Volúmenes:** `docker rm`, `docker rmi`, `docker stop`, `docker kill`, `docker system prune`, `docker volume rm`.
- **Bases de Datos:** `drop database`, `drop table`, `truncate table`.
- **Git Destructivo:** `git push --force`, `git push -f`, `git reset --hard`, `git clean -f`, `git branch -D`.
- **Sistema y Privilegios:** `shutdown`, `reboot`, `poweroff`, `init 0`, `systemctl stop`, `sudo`, `su`, `chmod -R 777`.

---

## 🎚️ 2. Niveles de Confianza (Trust Levels)

| Nivel | Identificador | Badge en Statusline | Permisos de Lectura | Edición de Archivos | Comandos Bash Permitidos |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **0** | `audit` | `▶▶ auto (audit)` | ✅ Libres | ❌ Requiere confirmación siempre | ❌ Requiere confirmación siempre |
| **1** | `workspace-safe` *(Default)* | `▶▶ auto (safe)` | ✅ Libres | ✅ En workspace/home | Comandos de inspección, git diff/status, tests y linters |
| **2** | `full-developer` | `▶▶ auto (dev)` | ✅ Libres | ✅ En workspace/home | Todo Nivel 1 + `npm/pnpm/pip/cargo install`, servidores locales, git commit, Docker compose |
| **3** | `subagent-worker` | `▶▶ auto (worker)` | ✅ En worktree | ✅ En worktree asignado | Tests y builds locales del worktree; bloquea `git push` y escapes |

---

## 🔍 3. Inspector Autónomo del Entorno (`env_inspector.py`)

Aegis incluye un motor de detección autónoma que inspecciona las herramientas instaladas en la máquina host y personaliza la configuración de Auto Mode:

```bash
# Inspeccionar herramientas instaladas y estado del sistema
python3 scripts/env_inspector.py

# Aplicar automáticamente los comandos seguros detectados a settings.json
python3 scripts/env_inspector.py --apply
```

El perfil generado se almacena en `~/.gemini/antigravity-cli/system_profile.json` y puede ser consultado por agentes mediante la herramienta MCP `aegis_inspect_environment`.
