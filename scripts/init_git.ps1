$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path ".git")) { git init }
git add .
git commit -m "PlexAI Verify Enterprise 2027.1.0 - Professional Foundation"
Write-Host "Dépôt Git initialisé." -ForegroundColor Green
