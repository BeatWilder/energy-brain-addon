#!/usr/bin/env bash
set -euo pipefail

cd "$HOME/energy-brain/energy-brain-addon"

echo "=================================================="
echo "V2578-V2593 Hillview inline UX cleanup smoke"
echo "=================================================="

echo
echo "=== 1. syntax check ==="
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile energy_brain/web_ui.py energy_brain/ha_client.py

echo
echo "=== 2. web UI tests ==="
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_web_ui.py

echo
echo "=== 3. UX audit ==="
python3 - <<'PY'
from pathlib import Path

web = Path("energy_brain/web_ui.py").read_text(encoding="utf-8")
ha = Path("energy_brain/ha_client.py").read_text(encoding="utf-8")

for marker in [
    "Legacy redirect notice intentionally hidden",
    'id="hillview-inline-notice"',
    "nestedFailed",
    "controle geweigerd of onvolledige invoer",
    "Dispatch aan slaat deze waarden eerst op",
    "event.preventDefault()",
    "fetch(form.action",
]:
    if marker not in web:
        raise SystemExit(f"FAIL: missing UX marker {marker}")

for marker in [
    '("input_select", "select_option", "input_select.alphaess_helper_dispatch_mode")',
    '("input_number", "set_value", "input_number.alphaess_helper_dispatch_duration")',
    '("input_number", "set_value", "input_number.alphaess_helper_dispatch_power")',
    '("input_number", "set_value", "input_number.alphaess_helper_dispatch_cutoff_soc")',
    '("input_boolean", "turn_on", "input_boolean.alphaess_helper_dispatch")',
    '("input_boolean", "turn_off", "input_boolean.alphaess_helper_dispatch")',
]:
    if marker not in ha:
        raise SystemExit(f"FAIL: missing allowlist marker {marker}")

print("PASS: Hillview inline UX cleanup markers present")
PY

echo
echo "=== 4. protected planner/controller/main diff check ==="
if git diff -- energy_brain/planner.py energy_brain/controller.py energy_brain/main.py | grep -q .; then
  echo "FAIL: protected planner/controller/main diff detected"
  exit 1
fi
echo "PASS: protected planner/controller/main diff empty"

echo
echo "=== 5. markers ==="
grep -nE "Legacy redirect|nestedFailed|controle geweigerd|Dispatch aan slaat|hillview-inline-notice|preventDefault|fetch\(form.action" \
  energy_brain/web_ui.py tests/test_web_ui.py

echo
echo "=== 6. cleanup pycache ==="
find energy_brain tests -type d -name "__pycache__" -prune -exec rm -rf {} +

echo
echo "=== 7. status ==="
git status --short

echo
echo "PASS: V2578-V2593 Hillview inline UX cleanup smoke completed"
