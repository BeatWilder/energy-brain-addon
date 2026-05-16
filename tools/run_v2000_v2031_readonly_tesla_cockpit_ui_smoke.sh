#!/usr/bin/env sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "${ROOT_DIR}"

fail() {
  echo "FAIL: $1"
  exit 1
}

echo "== pytest =="
python3 -m pytest -q

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
  printf '%s\n' 'dispatch'
  printf '%s\n' 'execute'
} > "${FORBIDDEN_FILE}"

echo "== forbidden UI string scan =="
NEW_UI_FILES="app/v2000/read_only_tesla_cockpit.py"
for path in ${NEW_UI_FILES}; do
  [ -f "${path}" ] || fail "missing UI file ${path}"
  if grep -FInf "${FORBIDDEN_FILE}" "${path}"; then
    fail "forbidden string found in ${path}"
  fi
done

MODIFIED_UI_FILES="energy_brain/web_ui.py"
for path in ${MODIFIED_UI_FILES}; do
  [ -f "${path}" ] || fail "missing UI file ${path}"
  added="$(git diff -U0 -- "${path}" | sed -n '/^+++ /d; /^+/s/^+//p')"
  if [ -n "${added}" ] && printf '%s\n' "${added}" | grep -FInf "${FORBIDDEN_FILE}" -; then
    fail "forbidden string found in added UI lines for ${path}"
  fi
done
echo "PASS: forbidden UI string scan"

echo "== protected diff check =="
git diff --quiet -- energy_brain/controller.py || fail "energy_brain/controller.py has local diff"
git diff --quiet -- energy_brain/main.py || fail "energy_brain/main.py has local diff"
git diff --quiet -- energy_brain/ha_client.py || fail "energy_brain/ha_client.py has local diff"

if [ -e ../app/energy_brain_v5.py ]; then
  git -C .. diff --quiet -- app/energy_brain_v5.py || fail "../app/energy_brain_v5.py has local diff"
fi

echo "PASS: protected diffs are empty"
echo "PASS: V2000-V2031 read-only Tesla cockpit UI smoke"
