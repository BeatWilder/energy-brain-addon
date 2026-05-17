#!/usr/bin/env bash
set -euo pipefail

cd "$HOME/energy-brain/energy-brain-addon"

echo "=================================================="
echo "V2611-V2626 Hillview raw response diagnostics smoke"
echo "=================================================="

echo
echo "=== 1. syntax check ==="
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile energy_brain/web_ui.py energy_brain/ha_client.py

echo
echo "=== 2. web UI tests ==="
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_web_ui.py

echo
echo "=== 3. raw response diagnostics audit ==="
python3 - <<'PY'
from pathlib import Path

text = Path("energy_brain/web_ui.py").read_text(encoding="utf-8")

for marker in [
    "const responseText = await response.text()",
    "JSON.parse(responseText)",
    "non_json_response",
    "result.http_status = response.status",
    "result.http_ok = response.ok",
    "raw: result",
    '"route": "hillview_control"',
]:
    if marker not in text:
        raise SystemExit(f"FAIL: missing marker {marker}")

if text.count('"route": "hillview_control"') < 5:
    raise SystemExit("FAIL: expected at least 5 route markers")

print("PASS: raw response diagnostics markers present")
PY

echo
echo "=== 4. protected planner/controller/main diff check ==="
if git diff -- energy_brain/planner.py energy_brain/controller.py energy_brain/main.py | grep -q .; then
  echo "FAIL: protected planner/controller/main diff detected"
  exit 1
fi
echo "PASS: protected planner/controller/main diff empty"

echo
echo "=== 5. cleanup pycache ==="
find energy_brain tests -type d -name "__pycache__" -prune -exec rm -rf {} +

echo
echo "=== 6. status ==="
git status --short

echo
echo "PASS: V2611-V2626 Hillview raw response diagnostics smoke completed"
