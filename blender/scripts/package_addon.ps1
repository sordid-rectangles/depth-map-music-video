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
New-Item -ItemType Directory -Path (Join-Path $staging "kinect_pointcloud") | Out-Null
Copy-Item -Path (Join-Path $addon "*") -Destination (Join-Path $staging "kinect_pointcloud") -Recurse -Force
Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
Compress-Archive -Path (Join-Path $staging "kinect_pointcloud") -DestinationPath $zipPath -Force
Remove-Item $staging -Recurse -Force

Write-Host "Created $zipPath"
Write-Host "In Blender: Edit -> Preferences -> Add-ons -> Install -> pick this zip"
Write-Host "Then fully quit and restart Blender (required after updates)."
