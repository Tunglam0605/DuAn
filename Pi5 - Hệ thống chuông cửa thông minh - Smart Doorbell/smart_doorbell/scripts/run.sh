#!/usr/bin/env bash
set -euo pipefail

ENTRY="run_all.py"
MODE="auto"

show_help() {
  cat <<'USAGE'
Usage: ./scripts/run.sh [--mock] [--pi] [--gui] [--legacy]

Options:
  --mock     Run in mock mode (no GPIO/servo, webcam OpenCV)
  --pi       Force Pi mode (GPIO + Pi camera)
  --gui      Run GUI only (run_gui.py)
  --legacy   Run legacy flow (main.py)
  -h, --help Show this help
USAGE
}

for arg in "$@"; do
  case "$arg" in
    --mock) MODE="mock" ;; 
    --pi) MODE="pi" ;;
    --gui) ENTRY="run_gui.py" ;;
    --legacy) ENTRY="main.py" ;;
    -h|--help) show_help; exit 0 ;;
  esac
done

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python3 not found. Please install Python 3.9+" >&2
  exit 1
fi

python3 - <<'PY'
import sys
if sys.version_info < (3, 9):
    raise SystemExit("Python 3.9+ is required")
PY

if command -v git >/dev/null 2>&1; then
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    if command -v git-lfs >/dev/null 2>&1 || git lfs version >/dev/null 2>&1; then
      git lfs pull || true
    else
      echo "git-lfs not found. Install it to pull models: sudo apt install git-lfs" >&2
    fi
  fi
fi

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip

REQ_EXTRA="requirements-desktop.txt"
if [ "$MODE" = "pi" ]; then
  REQ_EXTRA="requirements-pi.txt"
elif [ "$MODE" = "auto" ]; then
  arch=$(uname -m)
  if [[ "$arch" == arm* || "$arch" == aarch64* ]]; then
    REQ_EXTRA="requirements-pi.txt"
  else
    REQ_EXTRA="requirements-desktop.txt"
  fi
fi

if [ "$MODE" = "mock" ]; then
  export SMART_DOORBELL_MODE="mock"
  export DOORBELL_GUI_LIVENESS="0"
fi

python -m pip install -r requirements.txt -r "$REQ_EXTRA"

python "$ENTRY"
