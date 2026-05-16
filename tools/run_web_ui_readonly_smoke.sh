#!/usr/bin/env sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "${ROOT_DIR}"

python3 -m pytest -q tests/test_web_ui.py

PATTERN="$(printf '%s' 'call_service|set_state|/api/services|dis')"
PATTERN="${PATTERN}$(printf '%s' 'patch|execute=true|battery_write|set_battery')"

if grep -RInE "${PATTERN}" energy_brain/web_ui.py tests/test_web_ui.py; then
  echo "FAIL: forbidden write/control string found in UI-related files"
  exit 1
fi

echo "PASS"
