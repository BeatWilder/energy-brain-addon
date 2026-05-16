#!/usr/bin/env sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "${ROOT_DIR}"

fail() {
  echo "FAIL: $1"
  exit 1
}

echo "== pytest =="
python3 -m pytest -q -o cache_dir=/tmp/energy_brain_v2032_pytest_cache
echo "PASS: pytest"

echo "== existing V1968 smoke =="
sh tools/run_v1968_v1999_predbat_inspired_ems_cockpit_and_benchmark_audit_smoke.sh
echo "PASS: existing V1968 smoke"

echo "== existing V2000 smoke =="
sh tools/run_v2000_v2031_readonly_tesla_cockpit_ui_smoke.sh
echo "PASS: existing V2000 smoke"

echo "== V2032 focused tests =="
python3 -m pytest -q -o cache_dir=/tmp/energy_brain_v2032_pytest_cache tests/test_v2032_v2063_interactive_readonly_cockpit.py
echo "PASS: V2032 focused tests"

FORBIDDEN_FILE="$(mktemp)"
trap 'rm -f "${FORBIDDEN_FILE}"' EXIT
{
  printf '%s\n' 'call_service('
  printf '%s\n' 'hass.services'
  printf '%s\n' 'set_state('
  printf '%s\n' 'input_boolean.'
  printf '%s\n' 'input_number.'
  printf '%s\n' 'input_select.'
  printf '%s\n' 'switch.'
  printf '%s\n' 'climate.'
  printf '%s\n' 'notify.'
  printf '%s\n' 'shell_command.'
  printf '%s\n' 'do_POST'
  printf '%s\n' 'do_PUT'
  printf '%s\n' 'do_PATCH'
  printf '%s\n' 'do_DELETE'
  printf '%s\n' 'dispatch('
  printf '%s\n' 'execute('
  printf '%s\n' 'write_service'
  printf '%s\n' 'control_service'
} > "${FORBIDDEN_FILE}"

echo "== forbidden changed/new surface scan =="
SCAN_FILES="
energy_brain/v2000/read_only_tesla_cockpit.py
tests/test_v2032_v2063_interactive_readonly_cockpit.py
"
for path in ${SCAN_FILES}; do
  [ -f "${path}" ] || fail "missing scan file ${path}"
  if grep -FInf "${FORBIDDEN_FILE}" "${path}"; then
    fail "forbidden string found in ${path}"
  fi
done

WEB_ADDED="$(git diff -U0 -- energy_brain/web_ui.py | sed -n '/^+++ /d; /^+/s/^+//p')"
if [ -n "${WEB_ADDED}" ] && printf '%s\n' "${WEB_ADDED}" | grep -FInf "${FORBIDDEN_FILE}" -; then
  fail "forbidden string found in added energy_brain/web_ui.py lines"
fi
echo "PASS: forbidden changed/new surface scan"

echo "== protected diff check =="
git diff --quiet -- energy_brain/controller.py || fail "energy_brain/controller.py has local diff"
echo "PASS: energy_brain/controller.py protected diff empty"
git diff --quiet -- energy_brain/main.py || fail "energy_brain/main.py has local diff"
echo "PASS: energy_brain/main.py protected diff empty"
git diff --quiet -- energy_brain/ha_client.py || fail "energy_brain/ha_client.py has local diff"
echo "PASS: energy_brain/ha_client.py protected diff empty"

if git -C .. rev-parse --show-toplevel >/dev/null 2>&1 && [ -e ../app/energy_brain_v5.py ]; then
  if git -C .. diff --quiet -- app/energy_brain_v5.py; then
    echo "PASS: ../app/energy_brain_v5.py protected diff empty"
  else
    fail "../app/energy_brain_v5.py has local diff"
  fi
else
  echo "SKIP: ../app/energy_brain_v5.py protected diff unavailable outside this repo"
fi

echo "PASS: protected diffs are empty"
echo "PASS: V2032-V2063 interactive read-only cockpit smoke"
