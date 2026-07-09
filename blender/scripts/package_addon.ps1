# Package the add-on for Blender: Install → select this zip.

param(
    [string]$OutZip = "kinect_pointcloud.zip"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$addon = Join-Path $root "kinect_pointcloud"
$staging = Join-Path $env:TEMP "kinect_pointcloud_zip_staging"
$zipPath = Join-Path $root $OutZip

if (-not (Test-Path (Join-Path $addon "__init__.py"))) {
    throw "Expected $addon\__init__.py"
}

Remove-Item $staging -Recurse -Force -ErrorAction SilentlyContinue
$dest = Join-Path $staging "kinect_pointcloud"
New-Item -ItemType Directory -Path $dest | Out-Null
Copy-Item -Path (Join-Path $addon "*") -Destination $dest -Recurse -Force

# Drop Python bytecode caches so the handoff zip is clean.
Get-ChildItem -Path $dest -Recurse -Include "__pycache__" -Directory -Force |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $dest -Recurse -Include "*.pyc" -File -Force |
    Remove-Item -Force -ErrorAction SilentlyContinue

Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
Compress-Archive -Path $dest -DestinationPath $zipPath -Force
Remove-Item $staging -Recurse -Force

Write-Host "Created $zipPath"
Write-Host "In Blender: Edit -> Preferences -> Add-ons -> Install -> pick this zip"
Write-Host "Then fully quit and restart Blender (required after updates)."
