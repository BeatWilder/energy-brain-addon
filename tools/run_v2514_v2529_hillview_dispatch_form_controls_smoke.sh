#!/usr/bin/env bash
set -euo pipefail

cd "$HOME/energy-brain/energy-brain-addon"

echo "=================================================="
echo "V2514-V2529 Hillview dispatch form controls smoke"
echo "=================================================="

echo
echo "=== 1. syntax check ==="
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile energy_brain/web_ui.py energy_brain/ha_client.py

echo
echo "=== 2. web UI tests ==="
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_web_ui.py

echo
echo "=== 3. guarded form audit ==="
python3 - <<'PY'
from pathlib import Path

web = Path("energy_brain/web_ui.py").read_text(encoding="utf-8")
ha = Path("energy_brain/ha_client.py").read_text(encoding="utf-8")

web_markers = [
    "def hillview_dispatch_current_values",
    "def _render_hillview_dispatch_form",
    "mode_input",
    'number_input("duration"',
    'number_input("power"',
    'number_input("cutoff_soc"',
    "Instellingen opslaan",
    "Dispatch aan",
    "Dispatch uit",
    'fields = {',
    '"mode": (form.get("mode") or [""])[0]',
    '"duration": (form.get("duration") or [""])[0]',
    '"power": (form.get("power") or [""])[0]',
    '"cutoff_soc": (form.get("cutoff_soc") or [""])[0]',
]
for marker in web_markers:
    if marker not in web:
        raise SystemExit(f"FAIL: missing web marker {marker}")

ha_markers = [
    '("input_boolean", "turn_on", "input_boolean.alphaess_helper_dispatch")',
    '("input_boolean", "turn_off", "input_boolean.alphaess_helper_dispatch")',
    '("input_select", "select_option", "input_select.alphaess_helper_dispatch_mode")',
    '("input_number", "set_value", "input_number.alphaess_helper_dispatch_duration")',
    '("input_number", "set_value", "input_number.alphaess_helper_dispatch_power")',
    '("input_number", "set_value", "input_number.alphaess_helper_dispatch_cutoff_soc")',
    "def _validate_guarded_payload",
    "option_not_allowed",
    "value_outside_bounds",
]
for marker in ha_markers:
    if marker not in ha:
        raise SystemExit(f"FAIL: missing HA guard marker {marker}")

for forbidden in [
    "requests.put",
    "requests.patch",
    "requests.delete",
    "set_state(",
]:
    if forbidden in web or forbidden in ha:
        raise SystemExit(f"FAIL: forbidden broad write marker {forbidden}")

print("PASS: Hillview form controls are guarded and allowlisted")
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
grep -nE "hillview_dispatch_current_values|_render_hillview_dispatch_form|Instellingen opslaan|Dispatch aan|Dispatch uit|select_option|set_value|option_not_allowed|value_outside_bounds" \
  energy_brain/web_ui.py energy_brain/ha_client.py tests/test_web_ui.py

echo
echo "=== 6. cleanup pycache ==="
find energy_brain tests -type d -name "__pycache__" -prune -exec rm -rf {} +

echo
echo "=== 7. status ==="
git status --short

echo
echo "PASS: V2514-V2529 Hillview dispatch form controls smoke completed"
