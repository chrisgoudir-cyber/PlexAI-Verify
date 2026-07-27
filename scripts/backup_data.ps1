$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$target = Join-Path "backups" $stamp
New-Item -ItemType Directory -Force -Path $target | Out-Null
$items = @("data", "acquisition_config.json", "collection_catalog.json")
foreach ($item in $items) {
    if (Test-Path $item) { Copy-Item $item $target -Recurse -Force }
}
Write-Host "Sauvegarde créée : $target" -ForegroundColor Green
