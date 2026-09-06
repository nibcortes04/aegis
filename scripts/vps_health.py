#!/usr/bin/env python3
"""
Aegis VPS Production Health Inspector (vps_health.py)
Herramienta de diagnóstico rápido y no destructivo para servidores y orquestadores en producción.
Evalúa:
- Estado del demonio Docker y contenedores activos (Caddy, n8n, Chatwoot, Postgres, Redis).
- Capacidad de almacenamiento (disco raíz) y uso de memoria RAM.
- Carga del sistema (Load Average).
- Descriptores inotify del kernel.
- Resumen estructurado JSON para consumo de agentes y CLI amigable.
"""

import sys
import os
import json
import shutil
import subprocess
import time

try:
    from env_detector import get_inotify_capacity, get_os_type
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from env_detector import get_inotify_capacity, get_os_type

def get_disk_health(mount_point="/"):
    """Consulta la capacidad del disco en el punto de montaje principal."""
    try:
        usage = shutil.disk_usage(mount_point)
        total_gb = usage.total / (1024 ** 3)
        used_gb = usage.used / (1024 ** 3)
        free_gb = usage.free / (1024 ** 3)
        used_pct = (usage.used / usage.total) * 100
        return {
            "total_gb": round(total_gb, 2),
            "used_gb": round(used_gb, 2),
            "free_gb": round(free_gb, 2),
            "used_percent": round(used_pct, 1),
            "warning": used_pct > 85.0
        }
    except Exception as e:
        return {"error": str(e), "warning": False}

def get_memory_health():
    """Consulta el uso de memoria RAM a través de /proc/meminfo en Linux."""
    try:
        if os.path.isfile("/proc/meminfo"):
            mem_total = 0
            mem_available = 0
            with open("/proc/meminfo", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        mem_total = int(line.split()[1])
                    elif line.startswith("MemAvailable:"):
                        mem_available = int(line.split()[1])
            if mem_total > 0:
                used_kb = mem_total - mem_available
                used_pct = (used_kb / mem_total) * 100
                return {
                    "total_mb": round(mem_total / 1024, 1),
                    "used_mb": round(used_kb / 1024, 1),
                    "available_mb": round(mem_available / 1024, 1),
                    "used_percent": round(used_pct, 1),
                    "warning": used_pct > 90.0
                }
    except Exception:
        pass
    return {"warning": False, "note": "Telemetría de memoria no disponible en este entorno"}

def get_system_load():
    """Consulta el promedio de carga del sistema (Load Average)."""
    try:
        load1, load5, load15 = os.getloadavg()
        cpu_count = os.cpu_count() or 1
        return {
            "load_1m": round(load1, 2),
            "load_5m": round(load5, 2),
            "load_15m": round(load15, 2),
            "cpu_cores": cpu_count,
            "warning": load1 > (cpu_count * 2.0)
        }
    except Exception:
        return {"load_1m": 0.0, "load_5m": 0.0, "load_15m": 0.0, "warning": False}

def get_docker_containers_health():
    """Inspecciona los contenedores activos sin alterar el estado del sistema."""
    docker_bin = shutil.which("docker")
    if not docker_bin:
        return {"installed": False, "running": False, "containers": [], "error": "Docker no está instalado en PATH"}

    try:
        res = subprocess.run(
            [docker_bin, "ps", "--format", "{{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}"],
            capture_output=True,
            text=True,
            timeout=2.5
        )
        if res.returncode != 0:
            return {
                "installed": True,
                "running": False,
                "containers": [],
                "error": res.stderr.strip() or "Docker daemon no responde o permiso denegado"
            }

        containers = []
        for line in res.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("\t")
            name = parts[0] if len(parts) > 0 else "unknown"
            status = parts[1] if len(parts) > 1 else ""
            image = parts[2] if len(parts) > 2 else ""
            ports = parts[3] if len(parts) > 3 else ""
            containers.append({
                "name": name,
                "status": status,
                "image": image,
                "ports": ports,
                "is_healthy": "unhealthy" not in status.lower()
            })

        return {
            "installed": True,
            "running": True,
            "count": len(containers),
            "containers": containers
        }
    except subprocess.TimeoutExpired:
        return {"installed": True, "running": False, "containers": [], "error": "Timeout al consultar docker daemon (posible sobrecarga)"}
    except Exception as e:
        return {"installed": True, "running": False, "containers": [], "error": str(e)}

def inspect_vps_health():
    """Recopila el estado completo de salud del VPS en una estructura unificada."""
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    disk = get_disk_health()
    mem = get_memory_health()
    load = get_system_load()
    docker = get_docker_containers_health()
    inotify = get_inotify_capacity()

    warnings = []
    if disk.get("warning"):
        warnings.append(f"Disco crítico: {disk.get('used_percent')}% usado")
    if mem.get("warning"):
        warnings.append(f"Memoria RAM saturada: {mem.get('used_percent')}% usado")
    if load.get("warning"):
        warnings.append(f"Carga de CPU elevada: Load {load.get('load_1m')} en {load.get('cpu_cores')} núcleos")
    if inotify and inotify.get("warning"):
        warnings.append(f"Inotify elevado: {inotify.get('usage_percent')}% descriptores usados")
    if docker.get("installed") and not docker.get("running"):
        warnings.append(f"Docker Daemon inaccesible: {docker.get('error')}")

    status = "critical" if len(warnings) >= 2 else ("warning" if len(warnings) == 1 else "healthy")

    return {
        "timestamp": now_iso,
        "status": status,
        "disk": disk,
        "memory": mem,
        "load": load,
        "inotify": inotify,
        "docker": docker,
        "warnings": warnings
    }

def print_pretty_health(data):
    """Muestra el reporte formateado en la terminal con códigos ANSI."""
    status = data.get("status", "healthy")
    status_icon = "🟢 ÓPTIMO" if status == "healthy" else ("🟡 ADVERTENCIA" if status == "warning" else "🔴 CRÍTICO")

    print("\n" + "=" * 65)
    print(f"🛡️  AEGIS VPS PRODUCTION HEALTH MONITOR — {status_icon}")
    print("=" * 65)

    # 1. Almacenamiento y Recursos
    disk = data.get("disk", {})
    mem = data.get("memory", {})
    load = data.get("load", {})

    print(f"\n📊 Recursos del Sistema:")
    if "used_percent" in disk:
        print(f"  • Disco (/):     {disk.get('used_gb')} GB / {disk.get('total_gb')} GB ({disk.get('used_percent')}%)")
    if "used_percent" in mem:
        print(f"  • Memoria RAM:   {mem.get('used_mb')} MB / {mem.get('total_mb')} MB ({mem.get('used_percent')}%)")
    if "load_1m" in load:
        print(f"  • Carga CPU:     {load.get('load_1m')} (1m) | {load.get('load_5m')} (5m) | {load.get('load_15m')} (15m) [{load.get('cpu_cores')} cores]")

    # 2. Inotify
    inotify = data.get("inotify")
    if inotify:
        print(f"  • Inotify:       {inotify.get('active_instances')} / {inotify.get('max_instances')} instancias ({inotify.get('usage_percent')}%)")

    # 3. Docker & Contenedores
    docker = data.get("docker", {})
    print(f"\n🐳 Infraestructura Docker:")
    if not docker.get("installed"):
        print("  • Docker: No instalado en PATH.")
    elif not docker.get("running"):
        print(f"  • Docker: ⚠️ Inactivo o error: {docker.get('error')}")
    else:
        containers = docker.get("containers", [])
        print(f"  • Estado: Activo | {len(containers)} contenedores en ejecución")
        for c in containers:
            icon = "✔" if c.get("is_healthy") else "✖"
            print(f"    [{icon}] {c.get('name'):<22} {c.get('status'):<25} {c.get('image')}")

    # 4. Advertencias
    warnings = data.get("warnings", [])
    if warnings:
        print(f"\n⚠️  Alertas Activas ({len(warnings)}):")
        for w in warnings:
            print(f"  • {w}")
    else:
        print("\n✔ Ninguna alerta de infraestructura detectada.")

    print("=" * 65 + "\n")

def main():
    data = inspect_vps_health()
    if "--json" in sys.argv:
        print(json.dumps(data, indent=2))
    else:
        print_pretty_health(data)

if __name__ == "__main__":
    main()
