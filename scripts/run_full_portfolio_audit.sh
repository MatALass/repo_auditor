#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BATCH_SCRIPT="${PROJECT_ROOT}/scripts/audit_all_targets.sh"
EXPORT_REVIEW_QUEUE_SCRIPT="${PROJECT_ROOT}/scripts/export_review_queue.py"
ANALYZE_REVIEW_QUEUE_SCRIPT="${PROJECT_ROOT}/scripts/analyze_review_queue.py"
VENV_PYTHON="${PROJECT_ROOT}/.venv/bin/python"
SRC_DIR="${PROJECT_ROOT}/src"

OUTPUT_ROOT="./reports"
TIMESTAMPED_OUTPUT=0
SKIP_REVIEW_ANALYSIS=0
declare -a ORGS=()
declare -a USERS=()

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

  echo "No usable Python interpreter found." >&2
  exit 1
}

get_batch_output_directory() {
  local root="$1"
  local timestamped="$2"

  if [[ "$timestamped" == "1" ]]; then
    local ts
    ts="$(date +%Y%m%d_%H%M%S)"
    printf '%s\n' "$(cd "$(dirname "$root")" 2>/dev/null && pwd)/$(basename "$root")/github_targets_audit_${ts}"
    return
  fi

  if [[ "$root" = /* ]]; then
    printf '%s\n' "$root"
  else
    printf '%s\n' "${PROJECT_ROOT}/${root#./}"
  fi
}

review_queue_has_reviewed_rows() {
  local csv_path="$1"

  [[ -f "$csv_path" ]] || return 1

  python_check='
import csv, sys
valid = {"validated", "adjust_policy", "adjust_detection", "needs_context"}
with open(sys.argv[1], "r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        status = (row.get("review_status") or "").strip().lower()
        if status in valid:
            raise SystemExit(0)
raise SystemExit(1)
'
  if "${PYTHON_CMD}" -c "$python_check" "$csv_path"; then
    return 0
  fi
  return 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output-root)
      OUTPUT_ROOT="$2"
      shift 2
      ;;
    --timestamped-output)
      TIMESTAMPED_OUTPUT=1
      shift
      ;;
    --skip-review-analysis)
      SKIP_REVIEW_ANALYSIS=1
      shift
      ;;
    --org)
      ORGS+=("$2")
      shift 2
      ;;
    --user)
      USERS+=("$2")
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

PYTHON_CMD="$(find_python)"
BATCH_OUTPUT_ROOT="$(get_batch_output_directory "$OUTPUT_ROOT" "$TIMESTAMPED_OUTPUT")"

echo "[full-audit] Starting full portfolio audit..."
echo "[full-audit] Batch output directory: ${BATCH_OUTPUT_ROOT}"

batch_args=()
batch_args+=("$OUTPUT_ROOT")

for org in "${ORGS[@]}"; do
  batch_args+=("$org")
done

if [[ ${#USERS[@]} -gt 0 ]]; then
  :
fi

if [[ "$TIMESTAMPED_OUTPUT" == "1" ]]; then
  echo "[full-audit] Timestamped output enabled."
fi

if [[ ${#ORGS[@]} -gt 0 || ${#USERS[@]} -gt 0 ]]; then
  echo "[full-audit] Note: custom org/user targeting is currently expected through environment or batch script options."
fi

"${BATCH_SCRIPT}" "${batch_args[@]}"

SUMMARY_JSON="${BATCH_OUTPUT_ROOT}/batch-summary.json"
REVIEW_QUEUE_CSV="${BATCH_OUTPUT_ROOT}/review-queue.csv"
REVIEW_ANALYSIS_JSON="${BATCH_OUTPUT_ROOT}/review-analysis.json"
REVIEW_ANALYSIS_MD="${BATCH_OUTPUT_ROOT}/review-analysis.md"

if [[ ! -f "${SUMMARY_JSON}" ]]; then
  echo "batch-summary.json not found after batch audit: ${SUMMARY_JSON}" >&2
  exit 1
fi

if [[ -n "${PYTHONPATH:-}" ]]; then
  export PYTHONPATH="${SRC_DIR}:${PYTHONPATH}"
else
  export PYTHONPATH="${SRC_DIR}"
fi

echo "[full-audit] Exporting review queue..."
"${PYTHON_CMD}" "${EXPORT_REVIEW_QUEUE_SCRIPT}" "${SUMMARY_JSON}" --output "${REVIEW_QUEUE_CSV}"

if [[ "$SKIP_REVIEW_ANALYSIS" == "0" ]]; then
  if review_queue_has_reviewed_rows "${REVIEW_QUEUE_CSV}"; then
    echo "[full-audit] Analyzing review queue..."
    "${PYTHON_CMD}" "${ANALYZE_REVIEW_QUEUE_SCRIPT}" "${REVIEW_QUEUE_CSV}" --json-output "${REVIEW_ANALYSIS_JSON}" --md-output "${REVIEW_ANALYSIS_MD}"
  else
    echo "[full-audit] Review queue exported, but no reviewed rows were found yet. Skipping review analysis."
  fi
fi

echo
echo "[full-audit] Done."
echo "Artifacts:"
echo " - ${SUMMARY_JSON}"
echo " - ${REVIEW_QUEUE_CSV}"
[[ -f "${REVIEW_ANALYSIS_MD}" ]] && echo " - ${REVIEW_ANALYSIS_MD}"
[[ -f "${REVIEW_ANALYSIS_JSON}" ]] && echo " - ${REVIEW_ANALYSIS_JSON}"