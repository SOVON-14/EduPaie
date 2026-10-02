param(
    [switch]$Installer
)

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
if ($LASTEXITCODE -ne 0) {
    throw "La construction de l'application a échoué."
}

Write-Host "Build terminé. Le dossier dist/EduPaie contient l'application."

if ($Installer) {
    $compilerCandidates = @(
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
    )
    $compiler = $null
    foreach ($candidate in $compilerCandidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            $compiler = $candidate
            break
        }
    }

    if (-not $compiler) {
        throw "Inno Setup 6 est requis. Installez-le puis relancez ./scripts/build_app.ps1 -Installer."
    }

    & $compiler (Join-Path $PWD "installer\EduPaie.iss")
    if ($LASTEXITCODE -ne 0) {
        throw "La compilation de l'installateur a échoué."
    }
    Write-Host "Installateur créé : dist/EduPaie-Setup.exe"
}
