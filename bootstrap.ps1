$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $RepoRoot ".venv"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Host "Creating local virtual environment at $VenvDir..."
    python -m venv $VenvDir
}

Write-Host "Upgrading pip in the local virtual environment..."
& $PythonExe -m pip install --upgrade pip

Write-Host ""
Write-Host "Installing youtube-transcript-pipeline in editable mode..."
& $PythonExe -m pip install -e $RepoRoot

Write-Host ""
Write-Host "Running first-run environment checks..."
& $PythonExe -m yt_processor.pipeline_doctor --create-dirs --verify-examples

Write-Host ""
Write-Host "Bootstrap complete."
Write-Host "Activate the environment with:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
