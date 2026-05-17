#!/usr/bin/env sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "${ROOT_DIR}"

fail() {
  echo "FAIL: $1"
  exit 1
}

PATTERN_FILE="$(mktemp)"
trap 'rm -f "${PATTERN_FILE}"' EXIT
{
  printf '%s\n' 'call''_service'
  printf '%s\n' 'set''_state'
  printf '%s\n' 'req''uests'
  printf '%s\n' 'aio''http'
  printf '%s\n' 'm''qtt'
  printf '%s\n' 'pa''ho'
  printf '%s\n' 'Alpha''ESS'
  printf '%s\n' 'home''assistant'
  printf '%s\n' 'ha''ss.'
  printf '%s\n' 'write''_and''_poll'
  printf '%s\n' 'rest''_set'
  printf '%s\n' 'rest''_post'
  printf '%s\n' 'rest''_get'
} > "${PATTERN_FILE}"

NEW_FILES="
app/v2000/predbat_lesson_simulation_contract.py
app/v2001/__init__.py
app/v2001/canonical_self_consumption_simulator.py
docs/v2000_v2031_predbat_lesson_simulation_contract.md
tests/test_v2000_v2031_predbat_lesson_simulation_contract.py
tools/run_v2000_v2031_predbat_lesson_simulation_contract_smoke.sh
"

echo "== forbidden runtime/write surface scan =="
for path in ${NEW_FILES}; do
  [ -f "${path}" ] || fail "missing file ${path}"
  if grep -FIn -f "${PATTERN_FILE}" "${path}"; then
    fail "forbidden runtime/write surface found in ${path}"
  fi
done
echo "PASS: forbidden runtime/write surface scan"

echo "== pytest =="
python3 -m pytest -q tests/test_v2000_v2031_predbat_lesson_simulation_contract.py

echo "== git status =="
git status --short

echo "PASS: V2000-V2031 offline simulator contract smoke"
