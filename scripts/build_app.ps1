$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot
Set-Location ..

$pythonExe = Join-Path $PWD ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    throw "L'environnement virtuel n'existe pas. Lancez d'abord ./scripts/setup_env.ps1"
}

Write-Host "Construction de la version locale de EduPaie..."
& $pythonExe -m PyInstaller --noconfirm --onedir --windowed `
    --name "EduPaie" `
    --add-data "database;database" `
    --add-data "resources;resources" `
    main.py

Write-Host "Build terminé. Le dossier dist/EduPaie contient l'application."
