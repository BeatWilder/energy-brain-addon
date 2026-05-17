#!/usr/bin/env bash
set -euo pipefail

cd "$HOME/energy-brain/energy-brain-addon"

echo "=================================================="
echo "V2497-V2512 Hillview guarded dispatch control smoke"
echo "=================================================="

echo
echo "=== 1. syntax check ==="
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile energy_brain/web_ui.py energy_brain/ha_client.py

echo
echo "=== 2. web UI tests ==="
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_web_ui.py

echo
echo "=== 3. guarded control audit ==="
python3 - <<'PY'
from pathlib import Path

web = Path("energy_brain/web_ui.py").read_text(encoding="utf-8")
ha = Path("energy_brain/ha_client.py").read_text(encoding="utf-8")
cfg = Path("config.yaml").read_text(encoding="utf-8")

required_web = [
    'if path == "/api/hillview/control"',
    'def build_hillview_control_result',
    'def hillview_controls_enabled',
]
for marker in required_web:
    if marker not in web:
        raise SystemExit(f"FAIL: missing {marker}")

required_ha = [
    'def call_service_guarded',
    '("input_boolean", "turn_on", "input_boolean.alphaess_helper_dispatch")',
    '("input_boolean", "turn_off", "input_boolean.alphaess_helper_dispatch")',
]
for marker in required_ha:
    if marker not in ha:
        raise SystemExit(f"FAIL: missing {marker}")

if "hillview_controls_enabled: false" not in cfg:
    raise SystemExit("FAIL: hillview_controls_enabled default is not false")

for forbidden in [
    "requests.put",
    "requests.patch",
    "requests.delete",
    "set_state(",
]:
    if forbidden in web or forbidden in ha:
        raise SystemExit(f"FAIL: forbidden broad write marker {forbidden}")

print("PASS: guarded control surface limited to Hillview dispatch input_boolean")
PY

echo
echo "=== 4. protected planner/controller/main diff check ==="
if git diff -- energy_brain/planner.py energy_brain/controller.py energy_brain/main.py | grep -q .; then
  echo "FAIL: protected planner/controller/main diff detected"
  exit 1
fi
echo "PASS: protected planner/controller/main diff empty"

echo
echo "=== 5. route/control markers ==="
grep -nE "hillview_controls_enabled|build_hillview_control_result|call_service_guarded|/api/hillview/control|Control aan|Control uit" \
  config.yaml energy_brain/ha_client.py energy_brain/web_ui.py tests/test_web_ui.py

echo
echo "=== 6. cleanup pycache ==="
find energy_brain tests -type d -name "__pycache__" -prune -exec rm -rf {} +

echo
echo "=== 7. status ==="
git status --short

echo
echo "PASS: V2497-V2512 Hillview guarded dispatch control smoke completed"
