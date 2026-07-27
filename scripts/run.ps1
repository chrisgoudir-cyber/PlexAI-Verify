$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Environnement absent. Lance d'abord scripts\install_dev.ps1"
}
& .\.venv\Scripts\python.exe -m plexai_verify
