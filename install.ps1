# AGY PowerPack Windows PowerShell Installer
# Requires PowerShell 5.1+ and Python 3.8+

$ErrorActionPreference = "Stop"

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "   AGY PowerPack PowerShell Installer (Windows)     " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# 1. Comprobar Python
$PythonPath = Get-Command python.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
if (-not $PythonPath) {
    $PythonPath = Get-Command py.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
}

if (-not $PythonPath) {
    Write-Error "Error: Python 3 no fue encontrado en el PATH. Por favor instala Python 3.8+ desde python.org."
    exit 1
}

Write-Host "✔ Python detectado: $PythonPath" -ForegroundColor Green

# 2. Ejecutar install.py
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$InstallerPy = Join-Path $ScriptDir "install.py"

Write-Host "▶ Ejecutando instalador universal..." -ForegroundColor Yellow
& $PythonPath "$InstallerPy"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✔ Instalación en Windows completada." -ForegroundColor Green
} else {
    Write-Error "Ocurrió un error durante la instalación."
}
