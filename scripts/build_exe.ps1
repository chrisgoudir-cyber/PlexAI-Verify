$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
& .\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --windowed --name "PlexAI Verify" --paths src src\plexai_verify\__main__.py
Write-Host "Exécutable généré dans dist\PlexAI Verify." -ForegroundColor Green
