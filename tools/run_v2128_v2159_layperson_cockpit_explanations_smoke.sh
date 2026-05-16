#!/usr/bin/env sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "${ROOT_DIR}"

fail() {
  echo "FAIL: $1"
  exit 1
}

echo "== pytest =="
python3 -m pytest -q -o cache_dir=/tmp/energy_brain_v2128_pytest_cache
echo "PASS: pytest"

echo "== V1968 smoke =="
sh tools/run_v1968_v1999_predbat_inspired_ems_cockpit_and_benchmark_audit_smoke.sh
echo "PASS: V1968 smoke"

echo "== V2000 smoke =="
sh tools/run_v2000_v2031_readonly_tesla_cockpit_ui_smoke.sh
echo "PASS: V2000 smoke"

echo "== V2032 smoke =="
sh tools/run_v2032_v2063_interactive_readonly_cockpit_smoke.sh
echo "PASS: V2032 smoke"

echo "== V2064 smoke =="
sh tools/run_v2064_v2095_usable_interactive_cockpit_smoke.sh
echo "PASS: V2064 smoke"

echo "== V2128 focused tests =="
python3 -m pytest -q -o cache_dir=/tmp/energy_brain_v2128_pytest_cache tests/test_v2128_v2159_layperson_cockpit_explanations.py
echo "PASS: V2128 focused tests"

FORBIDDEN_FILE="$(mktemp)"
trap 'rm -f "${FORBIDDEN_FILE}"' EXIT
{
  printf '%s%s%s\n' 'call' '_service' '('
  printf '%s%s%s\n' 'hass' '.' 'services'
  printf '%s%s%s\n' 'set' '_state' '('
  printf '%s%s%s\n' 'input' '_boolean' '.'
  printf '%s%s%s\n' 'input' '_number' '.'
  printf '%s%s%s\n' 'input' '_select' '.'
  printf '%s%s\n' 'switch' '.'
  printf '%s%s\n' 'climate' '.'
  printf '%s%s\n' 'notify' '.'
  printf '%s%s%s\n' 'shell' '_command' '.'
  printf '%s%s\n' 'do_' 'POST'
  printf '%s%s\n' 'do_' 'PUT'
  printf '%s%s\n' 'do_' 'PATCH'
  printf '%s%s\n' 'do_' 'DELETE'
  printf '%s%s%s\n' 'dis' 'patch' '('
  printf '%s%s\n' 'execute' '('
  printf '%s%s\n' 'ap' 'ply'
  printf '%s%s\n' 'sa' 've'
  printf '%s%s%s\n' 'enable' ' ' 'control'
  printf '%s%s%s\n' 'start' ' ' 'control'
} > "${FORBIDDEN_FILE}"

echo "== forbidden changed/new surface scan =="
SCAN_FILES="
energy_brain/v2000/read_only_tesla_cockpit.py
tests/test_v2128_v2159_layperson_cockpit_explanations.py
tools/run_v2128_v2159_layperson_cockpit_explanations_smoke.sh
"
for path in ${SCAN_FILES}; do
  [ -f "${path}" ] || fail "missing scan file ${path}"
  if [ "${path}" = "tools/run_v2128_v2159_layperson_cockpit_explanations_smoke.sh" ]; then
    if sed '/printf/d' "${path}" | grep -FInf "${FORBIDDEN_FILE}" -; then
      fail "forbidden string found in ${path}"
    fi
  elif grep -FInf "${FORBIDDEN_FILE}" "${path}"; then
    fail "forbidden string found in ${path}"
  fi
done
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
echo "PASS: V2128-V2159 layperson cockpit explanations smoke"
