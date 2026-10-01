$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot
Set-Location ..

$pythonExe = Join-Path $PWD ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    throw "L'environnement virtuel n'existe pas. Lancez d'abord ./scripts/setup_env.ps1"
}

Write-Host "Démarrage de EduPaie..."
& $pythonExe main.py
