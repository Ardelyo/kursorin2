<#
.SYNOPSIS
Builds the KURSORIN application into a single-file executable.

.DESCRIPTION
This script uses PyInstaller and the provided kursorin.spec file to
generate a .exe bundle. It installs PyInstaller if it is missing,
cleans old build artifacts, and runs the build process.

.EXAMPLE
.\build_exe.ps1
#>

$ErrorActionPreference = "Stop"

# 1. Ensure Python is available
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed or not in PATH."
    exit 1
}

# 2. Ensure PyInstaller is installed
Write-Host "Checking for PyInstaller..." -ForegroundColor Cyan
try {
    python -m PyInstaller --version *>$null
} catch {
    Write-Host "PyInstaller not found. Installing..." -ForegroundColor Yellow
    python -m pip install pyinstaller
}

# 3. Clean previous build artifacts
Write-Host "Cleaning old build directories..." -ForegroundColor Cyan
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

# 4. Run the build
Write-Host "Starting PyInstaller build..." -ForegroundColor Cyan
Write-Host "Command: python -m PyInstaller kursorin.spec --clean" -ForegroundColor DarkGray

python -m PyInstaller kursorin.spec --clean

if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller build failed with exit code $LASTEXITCODE."
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=== BUILD SUCCESSFUL ===" -ForegroundColor Green
Write-Host "The frozen executable is located at: $(Resolve-Path dist\kursorin.exe)" -ForegroundColor White
Write-Host ""
Write-Host "Note: When launching the .exe, Windows will automatically prompt for Administrator privileges." -ForegroundColor Yellow
