
# Enter script directory
$scriptpath = $MyInvocation.MyCommand.Path
$dir = Split-Path $scriptpath
Set-Location $dir

# Create virtual environment
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual enviroment"
    python -m venv .venv
    .venv/Scripts/activate.ps1

    Write-Host "Installing requirements"
    pip install -r requirements.txt
}
else {
    .venv/Scripts/activate.ps1
}

# Run application (assuming python is in path)
python run.py