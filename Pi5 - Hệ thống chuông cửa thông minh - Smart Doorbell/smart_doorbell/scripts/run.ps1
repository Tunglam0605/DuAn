param(
    [switch]$Mock,
    [switch]$Pi,
    [switch]$Gui,
    [switch]$Legacy,
    [switch]$Help
)

if ($Help) {
    Write-Host "Usage: .\scripts\run.ps1 [-Mock] [-Pi] [-Gui] [-Legacy]"
    exit 0
}

$entry = "run_all.py"
if ($Gui) { $entry = "run_gui.py" }
if ($Legacy) { $entry = "main.py" }

$mode = "auto"
if ($Mock) { $mode = "mock" }
elseif ($Pi) { $mode = "pi" }

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Error "Python not found. Install Python 3.9+ and try again."
    exit 1
}

python -c "import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Python 3.9+ is required."
    exit 1
}

if (Get-Command git -ErrorAction SilentlyContinue) {
    git rev-parse --is-inside-work-tree | Out-Null
    if ($LASTEXITCODE -eq 0) {
        git lfs version | Out-Null
        if ($LASTEXITCODE -eq 0) {
            git lfs pull | Out-Null
        } else {
            Write-Warning "git-lfs not found. Install Git LFS to pull models."
        }
    }
}

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip

$reqExtra = "requirements-desktop.txt"
if ($mode -eq "pi") { $reqExtra = "requirements-pi.txt" }

if ($mode -eq "mock") {
    $env:SMART_DOORBELL_MODE = "mock"
    $env:DOORBELL_GUI_LIVENESS = "0"
}

python -m pip install -r requirements.txt -r $reqExtra
python $entry
