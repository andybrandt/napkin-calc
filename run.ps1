# run.ps1 - Launch Napkin Calculator, setting up virtual environment if needed.

$VenvPath = ".venv"
$PythonExe = "$VenvPath\Scripts\python.exe"

# If the venv's Python executable is missing, treat this as a fresh setup.
if (-not (Test-Path $PythonExe)) {
    Write-Host "Virtual environment not found. Creating..."
    python -m venv $VenvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment. Make sure Python 3.12+ is on your PATH."
        exit 1
    }

    Write-Host "Installing dependencies..."
    & "$VenvPath\Scripts\pip.exe" install -e ".[dev]"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install dependencies."
        exit 1
    }
}

# Launch the app via the installed entry point.
Write-Host "Starting Napkin Calculator..."
& "$VenvPath\Scripts\napkin-calc.exe"
