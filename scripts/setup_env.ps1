$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot
Set-Location ..

if (-not (Test-Path ".venv")) {
    Write-Host "Création de l'environnement virtuel..."
    py -3 -m venv .venv
}

$pythonExe = Join-Path $PWD ".venv\Scripts\python.exe"

Write-Host "Installation des dépendances..."
& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install -r requirements.txt

Write-Host "Environnement prêt."
Write-Host "Pour lancer l'application : ./scripts/run_app.ps1"
