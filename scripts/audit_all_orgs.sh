#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_SCRIPT="${PROJECT_ROOT}/scripts/run_repo_auditor.sh"
SUMMARY_SCRIPT="${PROJECT_ROOT}/scripts/build_batch_summary.py"
ENV_FILE="${PROJECT_ROOT}/.env"
OUTPUT_ROOT="${1:-./reports}"

load_env_file() {
  if [[ ! -f "${ENV_FILE}" ]]; then
    return
  fi

  while IFS= read -r line; do
    line="$(printf '%s' "${line}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "${line}" ]] && continue
    [[ "${line}" == \#* ]] && continue
    export "${line}"
  done < "${ENV_FILE}"
}

find_python() {
  if [[ -x "${PROJECT_ROOT}/.venv/bin/python" ]]; then
    printf '%s\n' "${PROJECT_ROOT}/.venv/bin/python"
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

  echo "No usable Python interpreter found." >&2
  exit 1
}

load_env_file

if [[ $# -gt 1 ]]; then
  ORGS=("${@:2}")
else
  if [[ -z "${GITHUB_ORGS:-}" ]]; then
    echo "No organizations provided. Pass them as arguments or define GITHUB_ORGS in .env." >&2
    exit 1
  fi
  IFS=',; ' read -r -a ORGS <<< "${GITHUB_ORGS}"
fi

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BATCH_OUTPUT_ROOT="${OUTPUT_ROOT}/github_orgs_audit_${TIMESTAMP}"
mkdir -p "${BATCH_OUTPUT_ROOT}"

FAILURES=()

for org in "${ORGS[@]}"; do
  [[ -z "${org}" ]] && continue
  echo
  echo "=== Auditing GitHub org: ${org} ==="
  ORG_OUTPUT="${BATCH_OUTPUT_ROOT}/${org}"
  mkdir -p "${ORG_OUTPUT}"

  if ! "${RUN_SCRIPT}" --github-org "${org}" --output "${ORG_OUTPUT}"; then
    FAILURES+=("${org}")
    echo "Audit failed for org: ${org}" >&2
  fi
done

PYTHON_CMD="$(find_python)"
if [[ -n "${PYTHONPATH:-}" ]]; then
  export PYTHONPATH="${PROJECT_ROOT}/src:${PYTHONPATH}"
else
  export PYTHONPATH="${PROJECT_ROOT}/src"
fi

"${PYTHON_CMD}" "${SUMMARY_SCRIPT}" "${BATCH_OUTPUT_ROOT}"

echo
echo "Batch output directory: ${BATCH_OUTPUT_ROOT}"
echo "Combined summary files:"
echo " - ${BATCH_OUTPUT_ROOT}/batch-summary.md"
echo " - ${BATCH_OUTPUT_ROOT}/batch-summary.json"

if [[ ${#FAILURES[@]} -gt 0 ]]; then
  echo "Failed orgs: ${FAILURES[*]}" >&2
  exit 1
fi

echo "All organization audits completed successfully."