#!/usr/bin/env python3
"""
Advanced Statusline Formatter for Antigravity CLI (agy)
Replica el estilo visual de Claude Code:
- Modelo y esfuerzo de razonamiento (🧠)
- Directorio y rama git con diff de líneas (+X -Y)
- Nombre de sesión / preview desde SQLite
- Barra gráfica de ventana de contexto (%) con alertas por color
- Costo acumulado ($) y duración de la sesión (⏱)
- Cuotas 5h (con hora local de reset 🕦) y semanal 7d (%)
- Indicador de ciclo de modo interactivo (▶▶ auto mode on)
"""

import sys
import os
import json
import sqlite3
import datetime
import subprocess
import time
import tempfile

# Códigos de color ANSI
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

def get_git_info(directory):
    if not directory or not os.path.isdir(directory):
        return "", 0, 0
    branch = ""
    add, sub = 0, 0
    try:
        p = subprocess.run(
            ["git", "-C", directory, "--no-optional-locks", "symbolic-ref", "--short", "HEAD"],
            capture_output=True, text=True, timeout=0.08
        )
        if p.returncode == 0:
            branch = p.stdout.strip()
        else:
            # Fallback a rev-parse si es detached HEAD
            p = subprocess.run(
                ["git", "-C", directory, "--no-optional-locks", "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, timeout=0.08
            )
            if p.returncode == 0:
                branch = p.stdout.strip()

        if branch:
            # Diff numstat para staged + unstaged vs HEAD
            p_diff = subprocess.run(
                ["git", "-C", directory, "--no-optional-locks", "diff", "--numstat", "HEAD"],
                capture_output=True, text=True, timeout=0.15
            )
            if p_diff.returncode == 0:
                for line in p_diff.stdout.splitlines():
                    parts = line.split()
                    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                        add += int(parts[0])
                        sub += int(parts[1])
    except Exception:
        pass
    return branch, add, sub

try:
    from env_detector import get_summaries_db_path, get_surface_type
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from env_detector import get_summaries_db_path, get_surface_type

def get_session_name(conv_id):
    if not conv_id:
        return ""
    db_path = get_summaries_db_path()
    if not os.path.isfile(db_path):
        return conv_id[:8]
    try:
        con = sqlite3.connect(db_path, timeout=0.05)
        cur = con.cursor()
        cur.execute(
            "SELECT title, preview FROM conversation_summaries WHERE conversation_id = ?",
            (conv_id,)
        )
        row = cur.fetchone()
        if row:
            title = row[0] or row[1]
            if title:
                # Truncar si es muy largo
                return title[:30] + ("…" if len(title) > 30 else "")
    except Exception:
        pass
def record_session_mode(conv_id, cycle_mode):
    """Guarda en cache atómico el cycle_mode de la sesión para sincronización con PreToolUse."""
    if not conv_id or not cycle_mode:
        return
    cache_file = os.path.join(tempfile.gettempdir(), ".aegis_session_modes.json")
    try:
        data = {}
        if os.path.isfile(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        data[conv_id] = {
            "cycle_mode": cycle_mode,
            "timestamp": time.time()
        }
        # Limpiar entradas antiguas de más de 48 horas
        now = time.time()
        data = {k: v for k, v in data.items() if (now - v.get("timestamp", 0)) < 172800}
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass

def get_session_mode(conv_id):
    """Obtiene el último cycle_mode registrado para una sesión específica."""
    if not conv_id:
        return "accept-edits"
    cache_file = os.path.join(tempfile.gettempdir(), ".aegis_session_modes.json")
    try:
        if os.path.isfile(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                entry = data.get(conv_id)
                if entry and isinstance(entry, dict):
                    return entry.get("cycle_mode", "accept-edits")
    except Exception:
        pass
    return "accept-edits"

def format_statusline(payload):
    # Registrar modo de ciclo de la sesión
    conv_id = payload.get("conversation_id") or payload.get("session_id") or ""
    cycle_mode = payload.get("cycle_mode", "accept-edits")
    if conv_id and cycle_mode:
        record_session_mode(conv_id, cycle_mode)
    # 1. Modelo y Esfuerzo
    model_info = payload.get("model") or {}
    model_name = model_info.get("display_name") or model_info.get("id") or "Gemini"
    # Acortar nombre largo si es necesario
    if "Gemini" in model_name:
        model_display = model_name.replace("Gemini ", "Gemini-")
    else:
        model_display = model_name

    effort = model_info.get("effort") or payload.get("effort", {}).get("level", "")
    effort_str = ""
    if effort:
        eff_lower = effort.lower()
        if eff_lower == "xhigh":
            effort_str = f" {MAGENTA}🧠 xhigh{RESET}"
        elif eff_lower == "high":
            effort_str = f" {YELLOW}🧠 high{RESET}"
        elif eff_lower in ("med", "medium"):
            effort_str = f" {BLUE}🧠 med{RESET}"
        elif eff_lower == "low":
            effort_str = f" {DIM}🧠 low{RESET}"
        else:
            effort_str = f" 🧠 {effort}"

    # 2. Directorio y Git
    cwd = payload.get("cwd") or payload.get("workspace", {}).get("current_dir", "")
    dir_name = os.path.basename(os.path.abspath(cwd)) if cwd else "workspace"
    branch, lines_add, lines_sub = get_git_info(cwd)

    branch_str = f" {BLUE}🌿 {branch}{RESET}" if branch else ""
    lines_str = ""
    if lines_add > 0 or lines_sub > 0:
        lines_str = f" {GREEN}+{lines_add}{RESET}{RED}-{lines_sub}{RESET}"

    # 3. Nombre de la Sesión
    conv_id = payload.get("conversation_id") or payload.get("session_id") or ""
    session_title = get_session_name(conv_id)
    session_str = f" {DIM}🏷️  {session_title}{RESET}" if session_title else ""

    # Línea 1
    line1 = f"{CYAN}{BOLD}[{model_display}]{RESET} 📁 {dir_name}{branch_str}{lines_str}{effort_str}{session_str}"

    # 4. Ventana de Contexto (Barra gráfica)
    ctx = payload.get("context_window") or {}
    pct_float = ctx.get("used_percentage", 0.0)
    pct_int = int(round(pct_float))
    exceeds = payload.get("exceeds_200k_tokens", False)

    if pct_int >= 90 or exceeds:
        bar_color = RED
    elif pct_int >= 70:
        bar_color = YELLOW
    else:
        bar_color = GREEN

    filled = max(0, min(10, pct_int // 10))
    empty = 10 - filled
    bar = "█" * filled + "░" * empty
    bar_str = f"{bar_color}{bar}{RESET} {pct_int}%"

    # 5. Costo y Tiempo
    cost_info = payload.get("cost") or {}
    total_cost = cost_info.get("total_cost_usd", 0.0)
    cost_str = f"{YELLOW}💰 ${total_cost:.4f}{RESET}"

    duration_ms = cost_info.get("total_duration_ms", 0)
    dur_secs = duration_ms // 1000
    mins = dur_secs // 60
    secs = dur_secs % 60
    time_str = f"⏱ {mins}m{secs}s"

    # 6. Cuotas (5h y semanal 7d)
    quota = payload.get("quota") or {}
    q5 = quota.get("gemini-5h") or quota.get("3p-5h") or {}
    q7 = quota.get("gemini-weekly") or quota.get("3p-weekly") or {}

    rem_5h = q5.get("remaining_fraction")
    rem_7d = q7.get("remaining_fraction")

    rate_str = ""
    if rem_5h is not None:
        used_5h = int(round((1.0 - float(rem_5h)) * 100.0))
        c5 = RED if used_5h >= 80 else (YELLOW if used_5h >= 50 else GREEN)
        
        # Hora de reset en local time
        reset_str = ""
        reset_time = q5.get("reset_time")
        if reset_time:
            try:
                dt = datetime.datetime.fromisoformat(reset_time.replace("Z", "+00:00")).astimezone()
                reset_str = f"{DIM}(🕦{dt.strftime('%H:%M')}){RESET}"
            except Exception:
                pass
        rate_str = f"{c5}5h:{used_5h}%{RESET}{reset_str}"

    if rem_7d is not None:
        used_7d = int(round((1.0 - float(rem_7d)) * 100.0))
        c7 = RED if used_7d >= 80 else (YELLOW if used_7d >= 50 else GREEN)
        if rate_str:
            rate_str += " "
        rate_str += f"{c7}7d:{used_7d}%{RESET}"

    quota_segment = f" │ {rate_str}" if rate_str else ""

    # Línea 2
    line2 = f"{bar_str} │ {cost_str} │ {time_str}{quota_segment}"

    # 7. Línea 3: Modo de Ejecución y Nivel de Confianza (Auto Mode / Shift+Tab)
    cycle_mode = payload.get("cycle_mode", "accept-edits")
    try:
        from trust_levels import get_active_trust_level, LEVEL_AUDIT, LEVEL_FULL_DEVELOPER, LEVEL_SUBAGENT_WORKER
        t_level = get_active_trust_level()
    except Exception:
        t_level = "workspace-safe"

    if cycle_mode in ("accept-edits", "auto", "always-proceed"):
        if t_level == "full-developer":
            mode_label = "auto mode (dev)"
        elif t_level == "audit":
            mode_label = "auto mode (audit)"
        elif t_level == "subagent-worker":
            mode_label = "auto mode (worker)"
        else:
            mode_label = "auto mode on"
        mode_icon = f"{YELLOW}▶▶{RESET}"
    elif cycle_mode in ("plan", "plan-only"):
        mode_label = "plan mode"
        mode_icon = f"{CYAN}⏸{RESET}"
    else:
        mode_label = "request-review"
        mode_icon = f"{DIM}▶{RESET}"

    line3 = f"{mode_icon} {mode_label} {DIM}(shift+tab to cycle) · ← for agents{RESET}"

    return f"{line1}\n{line2}\n{line3}"

def main():
    raw_input = sys.stdin.read()
    if not raw_input.strip():
        return
    try:
        payload = json.loads(raw_input)
    except Exception:
        return
    print(format_statusline(payload))

if __name__ == "__main__":
    main()
