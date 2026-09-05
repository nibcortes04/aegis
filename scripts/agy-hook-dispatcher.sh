#!/bin/sh
# AGY Hook Dispatcher
# Envía eventos de ciclo de vida al handler Python para Auto Mode y Notificaciones
EVENT="${1:-${ORCA_ANTIGRAVITY_EVENT:-Stop}}"
exec /usr/bin/python3 /home/n_n/scripts/agy_hook_handler.py "$EVENT"
