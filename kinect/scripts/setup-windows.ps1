# Azure Kinect + operator setup for Windows (native — not WSL).
# Run from an elevated PowerShell if installing the SDK for the first time:
#   Set-ExecutionPolicy -Scope Process Bypass -Force
#   .\setup-windows.ps1

$ErrorActionPreference = "Stop"

$SdkVersion = "1.4.2"
$SdkInstallerUrl = "https://download.microsoft.com/download/d/c/1/dc1f8a76-1ef2-4a1a-ac89-a7e22b3da491/Azure%20Kinect%20SDK%201.4.2.exe"
$SdkRecorder = "C:\Program Files\Azure Kinect SDK v$SdkVersion\tools\k4arecorder.exe"
$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$OperatorDir = Join-Path $RepoRoot "kinect\operator"
$OperatorExe = Join-Path $RepoRoot "kinect\operator.exe"

function Test-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p = New-Object Security.Principal.WindowsPrincipal($id)
    $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

Write-Host "`n=== Depth Map Music Video — Kinect Windows Setup ===`n" -ForegroundColor Cyan

# 1. Go (for building operator.exe)
if (-not (Get-Command go -ErrorAction SilentlyContinue)) {
    Write-Host "Go not found. Install with: winget install GoLang.Go" -ForegroundColor Yellow
    exit 1
}
Write-Host "[ok] Go: $(go version)"

# 2. Azure Kinect SDK (requires a real admin install — Cursor/non-elevated shells cannot do this)
if (-not (Test-Path $SdkRecorder)) {
    $installBat = Join-Path $PSScriptRoot "install-sdk.bat"
    Write-Host "[!!] Azure Kinect SDK $SdkVersion is not installed." -ForegroundColor Yellow
    Write-Host "     Run this as Administrator (right-click > Run as administrator):" -ForegroundColor Yellow
    Write-Host "     $installBat" -ForegroundColor White
    if (Test-Admin) {
        Write-Host "     (elevated shell detected — launching installer now)" -ForegroundColor Yellow
        & $installBat
    }
}
if (-not (Test-Path $SdkRecorder)) {
    Write-Host "[!!] k4arecorder not found. Install the SDK, then re-run this script." -ForegroundColor Red
    exit 1
}
Write-Host "[ok] Azure Kinect SDK: $SdkRecorder"

# 3. Build operator.exe
Write-Host "Building operator.exe..."
Push-Location $OperatorDir
go build -o $OperatorExe .
Pop-Location
Write-Host "[ok] Built: $OperatorExe"

# 4. Device check
Write-Host "`nChecking for connected Kinect (plug into USB 3 first)..."
& $SdkRecorder --list

Write-Host "`nDone. Double-click kinect\operator.exe or run: $OperatorExe`n" -ForegroundColor Green
