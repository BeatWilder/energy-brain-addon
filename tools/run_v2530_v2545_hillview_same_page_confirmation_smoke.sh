#!/usr/bin/env bash
set -euo pipefail

cd "$HOME/energy-brain/energy-brain-addon"

echo "=================================================="
echo "V2530-V2545 Hillview same-page confirmation smoke"
echo "=================================================="

echo
echo "=== 1. syntax check ==="
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile energy_brain/web_ui.py energy_brain/ha_client.py

echo
echo "=== 2. web UI tests ==="
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_web_ui.py

echo
echo "=== 3. same-page redirect audit ==="
python3 - <<'PY'
from pathlib import Path

web = Path("energy_brain/web_ui.py").read_text(encoding="utf-8")
ha = Path("energy_brain/ha_client.py").read_text(encoding="utf-8")

for marker in [
    "def _hillview_notice_from_query",
    "def _render_hillview_notice",
    "self.send_response(303)",
    'self.send_header("Location", location)',
    "control_status",
    "Geblokkeerd",
    "Opgeslagen",
]:
    if marker not in web:
        raise SystemExit(f"FAIL: missing web marker {marker}")

for forbidden in [
    "Hillview control result",
    "result_json = html.escape",
    "<pre>{result_json}</pre>",
]:
    if forbidden in web:
        raise SystemExit(f"FAIL: old result page marker still present {forbidden}")

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

for forbidden in [
    "requests.put",
    "requests.patch",
    "requests.delete",
    "set_state(",
]:
    if forbidden in web or forbidden in ha:
        raise SystemExit(f"FAIL: forbidden broad write marker {forbidden}")

print("PASS: Hillview POST redirects back to same page with confirmation")
PY

echo
echo "=== 4. protected planner/controller/main diff check ==="
if git diff -- energy_brain/planner.py energy_brain/controller.py energy_brain/main.py | grep -q .; then
  echo "FAIL: protected planner/controller/main diff detected"
  exit 1
fi
echo "PASS: protected planner/controller/main diff empty"

echo
echo "=== 5. route/notice markers ==="
grep -nE "hillview_notice|control_status|send_response\(303\)|Location|Geblokkeerd|Opgeslagen|Dispatch aan|Instellingen opslaan" \
  energy_brain/web_ui.py tests/test_web_ui.py

echo
echo "=== 6. cleanup pycache ==="
find energy_brain tests -type d -name "__pycache__" -prune -exec rm -rf {} +

echo
echo "=== 7. status ==="
git status --short

echo
echo "PASS: V2530-V2545 Hillview same-page confirmation smoke completed"
