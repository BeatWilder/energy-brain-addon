#!/usr/bin/env bash
set -euo pipefail

cd "$HOME/energy-brain/energy-brain-addon"

echo "=================================================="
echo "V2595-V2610 Hillview hard failure diagnostics smoke"
echo "=================================================="

echo
echo "=== 1. syntax check ==="
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile energy_brain/web_ui.py energy_brain/ha_client.py

echo
echo "=== 2. web UI tests ==="
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_web_ui.py

echo
echo "=== 3. hard failure diagnostics audit ==="
python3 - <<'PY'
from pathlib import Path

web = Path("energy_brain/web_ui.py").read_text(encoding="utf-8")

for marker in [
    '"failed_domain": result.get("domain", domain)',
    '"failed_service": result.get("service", service)',
    '"failed_entity_id": result.get("entity_id", payload.get("entity_id"))',
    '"failed_value": result.get("value", result.get("option", payload.get("value", payload.get("option"))))',
    '"failed_reason": result.get("reason", "unknown_guard_failure")',
    "const compactDebug = JSON.stringify",
    '"debug: " + compactDebug',
]:
    if marker not in web:
        raise SystemExit(f"FAIL: missing diagnostics marker {marker}")

print("PASS: hard failure diagnostics markers present")
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
echo "PASS: V2595-V2610 Hillview hard failure diagnostics smoke completed"
