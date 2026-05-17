#!/usr/bin/env bash
set -euo pipefail

cd "$HOME/energy-brain/energy-brain-addon"

echo "=================================================="
echo "V2627-V2642 Hillview ingress POST route fix smoke"
echo "=================================================="

echo
echo "=== 1. syntax check ==="
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile energy_brain/web_ui.py energy_brain/ha_client.py

echo
echo "=== 2. web UI tests ==="
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_web_ui.py

echo
echo "=== 3. ingress route audit ==="
python3 - <<'PY'
from pathlib import Path

web = Path("energy_brain/web_ui.py").read_text(encoding="utf-8")

for marker in [
    'action="api/hillview/control"',
    'path.endswith("/api/hillview/control")',
    'if path == "/api/hillview/control" or path.endswith("/api/hillview/control")',
]:
    if marker not in web:
        raise SystemExit(f"FAIL: missing marker {marker}")

if 'action="/api/hillview/control"' in web:
    raise SystemExit("FAIL: absolute form action still present")

print("PASS: ingress-safe Hillview POST route markers present")
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
echo "PASS: V2627-V2642 Hillview ingress POST route fix smoke completed"
