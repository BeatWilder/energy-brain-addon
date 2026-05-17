#!/usr/bin/env sh
set -u
set -e

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
app/v2224/__init__.py
app/v2224/planner_promotion_gate_contract.py
app/v2225/__init__.py
app/v2225/planner_promotion_gate.py
docs/v2224_v2255_planner_promotion_gate.md
tests/test_v2224_v2255_planner_promotion_gate.py
tools/run_v2224_v2255_planner_promotion_gate_smoke.sh
"

echo "== forbidden runtime/write surface scan =="
for path in ${NEW_FILES}; do
  [ -f "${path}" ] || fail "missing file ${path}"
  if grep -FIn -f "${PATTERN_FILE}" "${path}"; then
    fail "forbidden runtime/write surface found in ${path}"
  fi
done
echo "PASS: forbidden runtime/write surface scan"

echo "== dependency smoke: V2192-V2223 =="
if [ -x tools/run_v2192_v2223_scenario_regression_scoreboard_smoke.sh ]; then
  tools/run_v2192_v2223_scenario_regression_scoreboard_smoke.sh
else
  fail "missing dependency smoke tools/run_v2192_v2223_scenario_regression_scoreboard_smoke.sh"
fi

echo "== pytest =="
python3 -m pytest -q tests/test_v2224_v2255_planner_promotion_gate.py

echo "== git status =="
git status --short

echo "PASS: V2224-V2255 planner promotion gate smoke"
