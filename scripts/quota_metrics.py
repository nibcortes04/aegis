#!/usr/bin/env python3
"""
Aegis Quota & Telemetry Engine
- Gestiona la telemetría en tiempo real de tokens, costo y cuotas para la línea 2 del statusline.
- Resuelve métricas en vivo del payload del runtime AGY.
- Provee fallback ultra-rápido (<5ms) a SQLite cuando el entorno está desconectado o en subagentes.
- Aplica indicadores visuales de umbral (Green / Yellow ⚠️ / Red 🚨 / Magenta 💸).
"""

import os
import sys
import json
import time
import sqlite3
import datetime
import tempfile
import contextlib
import glob

# ANSI Colors
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

def get_telemetry_cache_path():
    """Retorna la ruta al archivo atómico de cache de telemetría."""
    return os.environ.get("AEGIS_TELEMETRY_FILE") or os.path.join(
        tempfile.gettempdir(), ".aegis_live_telemetry.json"
    )

def get_conversations_dir():
    """Retorna el directorio donde se almacenan las bases de datos SQLite por conversación."""
    override = os.environ.get("AEGIS_CONVERSATIONS_DIR")
    if override:
        return override
    return os.path.expanduser("~/.gemini/antigravity-cli/conversations")

def get_summaries_db_file():
    """Retorna la ruta al archivo conversation_summaries.db de SQLite."""
    override = os.environ.get("AEGIS_SUMMARIES_DB")
    if override:
        return override
    return os.path.expanduser("~/.gemini/antigravity-cli/conversation_summaries.db")

def record_live_telemetry(conv_id, data):
    """
    Registra datos de telemetría en cache atómico para una sesión activa.
    Se utiliza desde hooks (PreToolUse, Stop) o llamadas manuales de CLI.
    """
    if not conv_id or not isinstance(data, dict):
        return False
    cache_path = get_telemetry_cache_path()
    now = time.time()
    try:
        current_data = {}
        if os.path.isfile(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        current_data = json.loads(content)
            except Exception:
                current_data = {}

        entry = dict(data)
        entry["timestamp"] = now
        current_data[conv_id] = entry

        # Limpiar entradas de más de 24 horas
        current_data = {k: v for k, v in current_data.items() if (now - v.get("timestamp", 0)) < 86400}

        temp_file = cache_path + f".tmp.{os.getpid()}"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(current_data, f)
        os.replace(temp_file, cache_path)
        return True
    except Exception:
        return False

def get_cached_telemetry(conv_id, max_age_seconds=600):
    """Lee la telemetría en cache para la conversación especificada si no ha expirado."""
    if not conv_id:
        return None
    cache_path = get_telemetry_cache_path()
    if not os.path.isfile(cache_path):
        return None
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return None
            data = json.loads(content)
            entry = data.get(conv_id)
            if entry and (time.time() - entry.get("timestamp", 0)) <= max_age_seconds:
                return entry
    except Exception:
        pass
    return None

def get_sqlite_telemetry_estimate(conv_id, model_name="Gemini"):
    """
    Consulta SQLite local (<5ms) para estimar tokens, costo, pasos y duración
    cuando no hay telemetría activa en el payload del runtime ni en cache.
    """
    now = time.time()
    est = {
        "source": "sqlite-fallback",
        "tokens": 0,
        "max_tokens": 1_000_000 if "gemini" in model_name.lower() else 200_000,
        "used_percentage": 0.0,
        "total_cost_usd": 0.0,
        "duration_ms": 0,
        "step_count": 0,
        "quota_5h": {"used_percentage": 0.0, "reset_time": None},
        "quota_7d": {"used_percentage": 0.0},
    }

    if not conv_id:
        return est

    # 1. Intentar leer la base de datos específica de la conversación
    conv_dir = get_conversations_dir()
    conv_db = os.path.join(conv_dir, f"{conv_id}.db")

    total_bytes = 0
    step_count = 0

    if os.path.isfile(conv_db):
        conn = None
        try:
            conn = sqlite3.connect(conv_db, timeout=0.08)
            cur = conn.cursor()
            # gen_metadata almacena el tamaño de cada generación
            try:
                cur.execute("SELECT count(*), sum(size) FROM gen_metadata;")
                row = cur.fetchone()
                if row and row[0] is not None:
                    total_bytes = row[1] or 0
            except Exception:
                pass

            # steps almacena el número total de pasos
            try:
                cur.execute("SELECT count(*) FROM steps;")
                row = cur.fetchone()
                if row and row[0] is not None:
                    step_count = row[0]
            except Exception:
                pass

            # Duración estimada a partir de marcas de tiempo del archivo
            try:
                stat = os.stat(conv_db)
                duration_secs = max(0, int(now - stat.st_mtime))
                est["duration_ms"] = duration_secs * 1000
            except Exception:
                pass
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    # 2. Si no hay datos en <conv_id>.db, consultar conversation_summaries.db
    if step_count == 0 and total_bytes == 0:
        sum_db = get_summaries_db_file()
        if os.path.isfile(sum_db):
            conn = None
            try:
                conn = sqlite3.connect(sum_db, timeout=0.08)
                cur = conn.cursor()
                cur.execute(
                    "SELECT step_count, last_modified_time FROM conversation_summaries WHERE conversation_id = ?",
                    (conv_id,)
                )
                row = cur.fetchone()
                if row:
                    step_count = row[0] or 0
                    mod_time_str = row[1]
                    if mod_time_str:
                        try:
                            dt = datetime.datetime.fromisoformat(mod_time_str.replace("Z", "+00:00"))
                            diff = (datetime.datetime.now(datetime.timezone.utc) - dt).total_seconds()
                            est["duration_ms"] = max(0, int(diff * 1000))
                        except Exception:
                            pass
            except Exception:
                pass
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

    # 3. Calcular estimaciones empíricas
    if total_bytes > 0:
        est_tokens = int(total_bytes / 4.0)
    elif step_count > 0:
        est_tokens = step_count * 1200
    else:
        est_tokens = 0

    max_tok = est["max_tokens"]
    used_pct = min(100.0, (est_tokens / max_tok) * 100.0) if max_tok > 0 else 0.0

    # Blended price: ~$0.15 por 1M tokens
    cost_usd = (est_tokens / 1_000_000.0) * 0.15

    # Estimación de cuota 5h basada en velocidad de tokens (límite estimado 1M tokens/5h)
    quota_5h_used = min(100.0, (est_tokens / 1_000_000.0) * 100.0)
    quota_7d_used = min(100.0, (est_tokens / 5_000_000.0) * 100.0)

    # Hora estimada de reset para 5h (ahora + 2h por defecto)
    reset_dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)

    est["tokens"] = est_tokens
    est["used_percentage"] = round(used_pct, 1)
    est["total_cost_usd"] = round(cost_usd, 4)
    est["step_count"] = step_count
    est["quota_5h"] = {
        "used_percentage": round(quota_5h_used, 1),
        "reset_time": reset_dt.isoformat()
    }
    est["quota_7d"] = {
        "used_percentage": round(quota_7d_used, 1)
    }

    return est

def resolve_telemetry(payload):
    """
    Resuelve el estado unificado de métricas a partir del payload del runtime,
    el cache atómico de telemetría y el motor SQLite de fallback.
    """
    if not isinstance(payload, dict):
        payload = {}

    conv_id = payload.get("conversation_id") or payload.get("session_id") or ""
    model_info = payload.get("model") or {}
    model_name = model_info.get("display_name") or model_info.get("id") or "Gemini"

    # 1. Inspeccionar si el runtime proveyó telemetría completa
    ctx_payload = payload.get("context_window") or {}
    cost_payload = payload.get("cost") or {}
    quota_payload = payload.get("quota") or {}

    has_live_ctx = "used_percentage" in ctx_payload or "current_tokens" in ctx_payload
    has_live_cost = "total_cost_usd" in cost_payload
    has_live_quota = bool(quota_payload.get("gemini-5h") or quota_payload.get("3p-5h"))

    if has_live_ctx and has_live_cost and has_live_quota:
        source = "live-runtime"
    else:
        source = "live-runtime+fallback"

    # Obtener cache o fallback si falta algún segmento
    cached = get_cached_telemetry(conv_id) if conv_id else None
    sqlite_est = None

    def get_fallback():
        nonlocal sqlite_est
        if sqlite_est is None:
            sqlite_est = get_sqlite_telemetry_estimate(conv_id, model_name=model_name)
        return sqlite_est

    # Context window
    has_ctx = "context_window" in payload and (
        "used_percentage" in ctx_payload or "current_tokens" in ctx_payload
    )
    tokens = ctx_payload.get("current_tokens")
    max_tokens = ctx_payload.get("max_tokens") or (1_000_000 if "gemini" in model_name.lower() else 200_000)
    used_pct = ctx_payload.get("used_percentage")
    exceeds_200k = payload.get("exceeds_200k_tokens", False)

    if not has_ctx:
        if cached and "context_window" in cached:
            used_pct = cached["context_window"].get("used_percentage", 0.0)
            tokens = cached["context_window"].get("current_tokens", tokens)
            source = "telemetry-cache"
        else:
            fb = get_fallback()
            used_pct = fb["used_percentage"]
            tokens = fb["tokens"]
            max_tokens = fb["max_tokens"]
            if source != "live-runtime":
                source = "sqlite-fallback"

    # Cost & duration
    has_cost = "cost" in payload and "total_cost_usd" in cost_payload
    if has_cost:
        total_cost = cost_payload.get("total_cost_usd", 0.0)
        duration_ms = cost_payload.get("total_duration_ms", 0)
    else:
        if cached and "cost" in cached:
            total_cost = cached["cost"].get("total_cost_usd", 0.0)
            duration_ms = cached["cost"].get("total_duration_ms", 0)
        else:
            fb = get_fallback()
            total_cost = fb["total_cost_usd"]
            duration_ms = fb["duration_ms"]

    # Quotas (5h y 7d)
    has_quota_payload = "quota" in payload
    q5 = quota_payload.get("gemini-5h") or quota_payload.get("3p-5h") or {}
    q7 = quota_payload.get("gemini-weekly") or quota_payload.get("3p-weekly") or {}

    quota_5h = {}
    quota_7d = {}

    if has_quota_payload:
        if q5.get("remaining_fraction") is not None:
            used_5h_pct = (1.0 - float(q5["remaining_fraction"])) * 100.0
            quota_5h = {
                "used_percentage": round(used_5h_pct, 1),
                "reset_time": q5.get("reset_time")
            }
        if q7.get("remaining_fraction") is not None:
            used_7d_pct = (1.0 - float(q7["remaining_fraction"])) * 100.0
            quota_7d = {
                "used_percentage": round(used_7d_pct, 1)
            }
    else:
        if cached and ("quota_5h" in cached or "quota_7d" in cached):
            quota_5h = cached.get("quota_5h", {})
            quota_7d = cached.get("quota_7d", {})
        else:
            fb = get_fallback()
            quota_5h = fb["quota_5h"]
            quota_7d = fb["quota_7d"]

    return {
        "source": source,
        "conversation_id": conv_id,
        "model_name": model_name,
        "tokens": int(tokens) if tokens is not None else 0,
        "max_tokens": int(max_tokens),
        "used_percentage": float(used_pct or 0.0),
        "exceeds_200k_tokens": bool(exceeds_200k),
        "total_cost_usd": float(total_cost or 0.0),
        "duration_ms": int(duration_ms),
        "quota_5h": quota_5h,
        "quota_7d": quota_7d,
    }

def format_context_bar(used_percentage, tokens=None, max_tokens=None, exceeds=False):
    """Genera la barra gráfica de contexto de 10 bloques con código de color y alertas de umbral."""
    pct_int = int(round(used_percentage))
    if pct_int >= 90 or exceeds:
        color = RED
        alert = " 🚨"
    elif pct_int >= 70:
        color = YELLOW
        alert = " ⚠️"
    else:
        color = GREEN
        alert = ""

    filled = max(0, min(10, pct_int // 10))
    empty = 10 - filled
    bar = "█" * filled + "░" * empty

    # Badge de tokens si están disponibles
    tokens_str = ""
    if tokens and tokens > 0:
        if tokens >= 1_000_000:
            tok_fmt = f"{tokens / 1_000_000:.1f}M"
        else:
            tok_fmt = f"{int(tokens / 1000)}k"
        if max_tokens and max_tokens >= 1_000_000:
            max_fmt = f"{int(max_tokens / 1_000_000)}M"
        elif max_tokens:
            max_fmt = f"{int(max_tokens / 1000)}k"
        else:
            max_fmt = ""
        tokens_str = f" {DIM}({tok_fmt}{'/' + max_fmt if max_fmt else ''}){RESET}"

    return f"{color}{bar}{RESET} {pct_int}%{alert}{tokens_str}"

def format_cost(total_cost_usd):
    """Genera el segmento formateado de gasto con indicadores de umbral (Green / Yellow / Magenta 💸)."""
    cost = float(total_cost_usd)
    if cost >= 0.50:
        return f"{MAGENTA}{BOLD}💸 ${cost:.4f} ⚠️{RESET}"
    elif cost >= 0.10:
        return f"{YELLOW}💰 ${cost:.4f}{RESET}"
    else:
        return f"{GREEN}💰 ${cost:.4f}{RESET}"

def format_duration(duration_ms):
    """Formatea la duración en formato compacto (m s o h m)."""
    dur_secs = max(0, int(duration_ms // 1000))
    hours = dur_secs // 3600
    mins = (dur_secs % 3600) // 60
    secs = dur_secs % 60

    if hours > 0:
        return f"⏱ {hours}h{mins}m"
    return f"⏱ {mins}m{secs}s"

def format_quotas(quota_5h, quota_7d):
    """Formatea las cuotas 5h y semanal 7d con colores de umbral y hora local de reset."""
    parts = []

    used_5h = quota_5h.get("used_percentage")
    if used_5h is not None:
        u5 = int(round(float(used_5h)))
        c5 = RED if u5 >= 80 else (YELLOW if u5 >= 50 else GREEN)
        alert5 = " 🚨" if u5 >= 80 else ""

        reset_str = ""
        reset_time = quota_5h.get("reset_time")
        if reset_time:
            try:
                dt = datetime.datetime.fromisoformat(reset_time.replace("Z", "+00:00")).astimezone()
                reset_str = f"{DIM}(🕦{dt.strftime('%H:%M')}){RESET}"
            except Exception:
                pass
        parts.append(f"{c5}5h:{u5}%{alert5}{RESET}{reset_str}")

    used_7d = quota_7d.get("used_percentage")
    if used_7d is not None:
        u7 = int(round(float(used_7d)))
        c7 = RED if u7 >= 80 else (YELLOW if u7 >= 50 else GREEN)
        alert7 = " 🚨" if u7 >= 80 else ""
        parts.append(f"{c7}7d:{u7}%{alert7}{RESET}")

    return " ".join(parts)

def get_metrics_summary(payload):
    """Retorna un diccionario completo listo para exportar o serializar en JSON."""
    resolved = resolve_telemetry(payload)
    return {
        "source": resolved["source"],
        "conversation_id": resolved["conversation_id"],
        "model": resolved["model_name"],
        "context_window": {
            "used_percentage": resolved["used_percentage"],
            "tokens": resolved["tokens"],
            "max_tokens": resolved["max_tokens"],
            "exceeds_200k": resolved["exceeds_200k_tokens"],
            "formatted": format_context_bar(
                resolved["used_percentage"],
                tokens=resolved["tokens"],
                max_tokens=resolved["max_tokens"],
                exceeds=resolved["exceeds_200k_tokens"]
            )
        },
        "cost": {
            "total_usd": resolved["total_cost_usd"],
            "formatted": format_cost(resolved["total_cost_usd"])
        },
        "duration": {
            "total_ms": resolved["duration_ms"],
            "formatted": format_duration(resolved["duration_ms"])
        },
        "quotas": {
            "5h": resolved["quota_5h"],
            "7d": resolved["quota_7d"],
            "formatted": format_quotas(resolved["quota_5h"], resolved["quota_7d"])
        }
    }

def get_active_conversation_id():
    """Detecta el ID de la conversación activa o más reciente en el sistema."""
    env_id = (
        os.environ.get("AGY_CONVERSATION_ID") or 
        os.environ.get("CONVERSATION_ID") or 
        os.environ.get("ORCA_CONVERSATION_ID")
    )
    if env_id:
        return env_id

    conv_dir = get_conversations_dir()
    if os.path.isdir(conv_dir):
        files = [
            f for f in glob.glob(os.path.join(conv_dir, "*.db"))
            if not f.endswith("-wal") and not f.endswith("-shm")
        ]
        if files:
            try:
                latest = max(files, key=os.path.getmtime)
                base = os.path.basename(latest)
                if base.endswith(".db"):
                    return base[:-3]
            except Exception:
                pass

    sum_db = get_summaries_db_file()
    if os.path.isfile(sum_db):
        conn = None
        try:
            conn = sqlite3.connect(sum_db, timeout=0.08)
            cur = conn.cursor()
            cur.execute("SELECT conversation_id FROM conversation_summaries ORDER BY last_modified_time DESC LIMIT 1")
            row = cur.fetchone()
            if row and row[0]:
                return row[0]
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
    return ""

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Aegis Live Telemetry & Real Quota Engine (EPIC-09)")
    parser.add_argument("--json", action="store_true", help="Salida en formato JSON estructurado.")
    parser.add_argument("--conv-id", type=str, default="", help="ID de la conversación a inspeccionar.")
    parser.add_argument("--record", type=str, default="", help="JSON string de telemetría a registrar.")
    args = parser.parse_args()

    conv_id = args.conv_id or get_active_conversation_id()

    if args.record:
        try:
            rec_data = json.loads(args.record)
            ok = record_live_telemetry(conv_id, rec_data)
            print(json.dumps({"success": ok, "conversation_id": conv_id}))
            return
        except Exception as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
            sys.exit(1)

    payload = {
        "conversation_id": conv_id,
        "model": {"id": "gemini-3.8-flash", "display_name": "Gemini 3.8 Flash"}
    }
    summary = get_metrics_summary(payload)

    if args.json:
        print(json.dumps(summary, indent=2))
        return

    # Renderizado interactivo en tarjeta de consola
    print(f"\n{BOLD}{CYAN}╔════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{CYAN}║     📊  AEGIS REAL-TIME QUOTA & TELEMETRY ENGINE (EPIC-09)        ║{RESET}")
    print(f"{BOLD}{CYAN}╚════════════════════════════════════════════════════════════════════╝{RESET}\n")

    src = summary["source"]
    src_badge = f"{GREEN}● Live Runtime{RESET}" if src == "live-runtime" else (
        f"{BLUE}● Telemetry Cache{RESET}" if src == "telemetry-cache" else f"{YELLOW}● SQLite Engine Fallback{RESET}"
    )

    print(f"  {BOLD}Sesión Activa:{RESET}       {summary['conversation_id'] or 'No detectada'}")
    print(f"  {BOLD}Fuente de Datos:{RESET}     {src_badge}")
    print(f"  {BOLD}Modelo Activo:{RESET}       {summary['model']}")
    print(f"")
    print(f"  {BOLD}Ventana de Contexto:{RESET} {summary['context_window']['formatted']}")
    print(f"  {BOLD}Gasto Acumulado:{RESET}     {summary['cost']['formatted']}")
    print(f"  {BOLD}Duración de Sesión:{RESET}  {summary['duration']['formatted']}")
    if summary['quotas']['formatted']:
        print(f"  {BOLD}Cuotas en Vivo:{RESET}      {summary['quotas']['formatted']}")
    print(f"")
    print(f"  {BOLD}Vista Previa Statusline (Línea 2):{RESET}")
    q_seg = f" │ {summary['quotas']['formatted']}" if summary['quotas']['formatted'] else ""
    print(f"  {summary['context_window']['formatted']} │ {summary['cost']['formatted']} │ {summary['duration']['formatted']}{q_seg}\n")

if __name__ == "__main__":
    main()
