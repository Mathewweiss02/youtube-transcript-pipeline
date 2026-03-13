Write-Host "Installing Python dependencies for the transcript pipeline..."
python -m pip install -r yt_processor\requirements.txt

Write-Host ""
Write-Host "Running first-run environment checks..."
python yt_processor\pipeline_doctor.py --create-dirs --verify-examples
