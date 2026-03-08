#!/usr/bin/env bash
set -euo pipefail

if [ ! -f ".env" ]; then
  echo "Missing .env file at project root."
  exit 1
fi

set -a
source .env
set +a

if [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "GITHUB_TOKEN is missing in .env"
  exit 1
fi

OUTPUT_ROOT="${AUDIT_OUTPUT_DIR:-./reports}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
OUTPUT_DIR="${OUTPUT_ROOT}/multi-github-${TIMESTAMP}"

mkdir -p "${OUTPUT_DIR}"

echo "Output directory: ${OUTPUT_DIR}"

if [ -n "${GITHUB_USER:-}" ]; then
  echo "Auditing GitHub user: ${GITHUB_USER}"
  python -m repo_auditor.cli --github-user "${GITHUB_USER}" --output "${OUTPUT_DIR}"
fi

IFS=',' read -r -a ORG_ARRAY <<< "${GITHUB_ORGS:-}"

for raw_org in "${ORG_ARRAY[@]}"; do
  org="$(echo "${raw_org}" | xargs)"
  if [ -n "${org}" ]; then
    echo "Auditing GitHub org: ${org}"
    python -m repo_auditor.cli --github-org "${org}" --output "${OUTPUT_DIR}"
  fi
done

echo "Done. Reports written to ${OUTPUT_DIR}"