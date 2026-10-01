$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot
Set-Location ..

$pythonExe = Join-Path $PWD ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    throw "L'environnement virtuel n'existe pas. Lancez d'abord ./scripts/setup_env.ps1"
}

Write-Host "Construction de la version locale de EduPaie..."
$pyinstallerArgs = @(
    "--noconfirm",
    "--onedir",
    "--windowed",
    "--name", "EduPaie",
    "--add-data", "database;database",
    "--add-data", "resources;resources"
)

if (Test-Path "data\edupaie.db") {
    $pyinstallerArgs += @("--add-data", "data\edupaie.db;data")
} else {
    Write-Warning "data/edupaie.db absent : l'application démarrera avec une base vide."
}

& $pythonExe -m PyInstaller @pyinstallerArgs main.py

Write-Host "Build terminé. Le dossier dist/EduPaie contient l'application."
