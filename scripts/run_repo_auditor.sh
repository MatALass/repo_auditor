#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="${PROJECT_ROOT}/src"
VENV_PYTHON="${PROJECT_ROOT}/.venv/bin/python"

find_python() {
  if [[ -x "${VENV_PYTHON}" ]]; then
    printf '%s\n' "${VENV_PYTHON}"
    return
  fi

  if command -v python3 >/dev/null 2>&1; then
    printf '%s\n' "python3"
    return
  fi

  if command -v python >/dev/null 2>&1; then
    printf '%s\n' "python"
    return
  fi

  echo "No usable Python interpreter found. Install Python or restore .venv." >&2
  exit 1
}

PYTHON_CMD="$(find_python)"

if ! "${PYTHON_CMD}" -c "import requests, dotenv" >/dev/null 2>&1; then
  cat >&2 <<'EOF'
Missing required dependencies for repo-auditor in the selected Python environment.

Install them once with:
  python3 -m pip install requests python-dotenv
EOF
  exit 1
fi

if [[ -n "${PYTHONPATH:-}" ]]; then
  export PYTHONPATH="${SRC_DIR}:${PYTHONPATH}"
else
  export PYTHONPATH="${SRC_DIR}"
fi

exec "${PYTHON_CMD}" -m repo_auditor.cli "$@"