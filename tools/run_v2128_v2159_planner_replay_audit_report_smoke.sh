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
app/v2128/__init__.py
app/v2128/planner_replay_audit_contract.py
app/v2129/__init__.py
app/v2129/planner_replay_audit_report.py
docs/v2128_v2159_planner_replay_audit_report.md
tests/test_v2128_v2159_planner_replay_audit_report.py
tools/run_v2128_v2159_planner_replay_audit_report_smoke.sh
"

echo "== forbidden runtime/write surface scan =="
for path in ${NEW_FILES}; do
  [ -f "${path}" ] || fail "missing file ${path}"
  if grep -FIn -f "${PATTERN_FILE}" "${path}"; then
    fail "forbidden runtime/write surface found in ${path}"
  fi
done
echo "PASS: forbidden runtime/write surface scan"

if [ -x tools/run_v2000_v2031_predbat_lesson_simulation_contract_smoke.sh ]; then
  echo "== dependency smoke: V2000-V2031 =="
  tools/run_v2000_v2031_predbat_lesson_simulation_contract_smoke.sh
fi

if [ -x tools/run_v2032_v2063_fixture_replay_strategy_comparison_smoke.sh ]; then
  echo "== dependency smoke: V2032-V2063 =="
  tools/run_v2032_v2063_fixture_replay_strategy_comparison_smoke.sh
fi

if [ -x tools/run_v2064_v2095_controlled_action_intent_simulator_smoke.sh ]; then
  echo "== dependency smoke: V2064-V2095 =="
  tools/run_v2064_v2095_controlled_action_intent_simulator_smoke.sh
fi

if [ -x tools/run_v2096_v2127_controlled_strategy_replay_integration_smoke.sh ]; then
  echo "== dependency smoke: V2096-V2127 =="
  tools/run_v2096_v2127_controlled_strategy_replay_integration_smoke.sh
fi

echo "== pytest =="
python3 -m pytest -q tests/test_v2128_v2159_planner_replay_audit_report.py

echo "== git status =="
git status --short

echo "PASS: V2128-V2159 planner replay audit report smoke"
