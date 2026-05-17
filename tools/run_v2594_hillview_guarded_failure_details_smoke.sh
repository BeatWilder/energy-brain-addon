#!/usr/bin/env bash
set -euo pipefail

cd "$HOME/energy-brain/energy-brain-addon"

echo "=================================================="
echo "V2594 Hillview guarded failure details smoke"
echo "=================================================="

echo
echo "=== 1. syntax check ==="
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile energy_brain/web_ui.py energy_brain/ha_client.py

echo
echo "=== 2. web UI tests ==="
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_web_ui.py

echo
echo "=== 3. failure detail audit ==="
python3 - <<'PY'
from pathlib import Path

web = Path("energy_brain/web_ui.py").read_text(encoding="utf-8")
ha = Path("energy_brain/ha_client.py").read_text(encoding="utf-8")

for marker in [
    "failedService",
    "failedEntity",
    "failedValue",
    "service: ",
    "entity: ",
    "waarde: ",
    'result.setdefault("domain", domain)',
    'result.setdefault("service", service)',
    'result.setdefault("entity_id", payload.get("entity_id"))',
    'result.setdefault("payload", payload)',
    'result.setdefault("value", payload.get("value"))',
    'result.setdefault("option", payload.get("option"))',
]:
    if marker not in web:
        raise SystemExit(f"FAIL: missing detail marker {marker}")

for marker in [
    '("input_boolean", "turn_on", "input_boolean.alphaess_helper_dispatch")',
    '("input_boolean", "turn_off", "input_boolean.alphaess_helper_dispatch")',
    '("input_select", "select_option", "input_select.alphaess_helper_dispatch_mode")',
    '("input_number", "set_value", "input_number.alphaess_helper_dispatch_duration")',
    '("input_number", "set_value", "input_number.alphaess_helper_dispatch_power")',
    '("input_number", "set_value", "input_number.alphaess_helper_dispatch_cutoff_soc")',
]:
    if marker not in ha:
        raise SystemExit(f"FAIL: missing allowlist marker {marker}")

print("PASS: guarded failure details present")
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
grep -nE "failedService|failedEntity|failedValue|service: |entity: |waarde: |setdefault\\(\"domain\"|setdefault\\(\"service\"|setdefault\\(\"entity_id\"|setdefault\\(\"payload\"|setdefault\\(\"value\"|setdefault\\(\"option\"" \
  energy_brain/web_ui.py tests/test_web_ui.py

echo
echo "=== 6. cleanup pycache ==="
find energy_brain tests -type d -name "__pycache__" -prune -exec rm -rf {} +

echo
echo "=== 7. status ==="
git status --short

echo
echo "PASS: V2594 Hillview guarded failure details smoke completed"
