#!/usr/bin/env bash
set -euo pipefail

cd "$HOME/energy-brain/energy-brain-addon"

echo "=================================================="
echo "V2513 Hillview POST crash hotfix smoke"
echo "=================================================="

echo
echo "=== 1. syntax check ==="
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile energy_brain/web_ui.py energy_brain/ha_client.py

echo
echo "=== 2. web UI tests ==="
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_web_ui.py

echo
echo "=== 3. POST crash regression audit ==="
python3 - <<'PY'
from pathlib import Path

web = Path("energy_brain/web_ui.py").read_text(encoding="utf-8")
ha = Path("energy_brain/ha_client.py").read_text(encoding="utf-8")

for marker in [
    'if path == "/api/hillview/control"',
    'result_json = html.escape',
    'page = (',
]:
    if marker not in web:
        raise SystemExit(f"FAIL: missing {marker}")

if "html = (" in web:
    raise SystemExit("FAIL: local html variable still present in POST handler")

for marker in [
    '("input_boolean", "turn_on", "input_boolean.alphaess_helper_dispatch")',
    '("input_boolean", "turn_off", "input_boolean.alphaess_helper_dispatch")',
]:
    if marker not in ha:
        raise SystemExit(f"FAIL: missing guarded allowlist marker {marker}")

for forbidden in [
    "requests.put",
    "requests.patch",
    "requests.delete",
    "set_state(",
]:
    if forbidden in web or forbidden in ha:
        raise SystemExit(f"FAIL: forbidden broad write marker {forbidden}")

print("PASS: POST result rendering fixed and guarded control allowlist intact")
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
grep -nE "api/hillview/control|result_json = html.escape|page = \(|call_service_guarded|alphaess_helper_dispatch" \
  energy_brain/web_ui.py energy_brain/ha_client.py

echo
echo "=== 6. cleanup pycache ==="
find energy_brain tests -type d -name "__pycache__" -prune -exec rm -rf {} +

echo
echo "=== 7. status ==="
git status --short

echo
echo "PASS: V2513 Hillview POST crash hotfix smoke completed"
