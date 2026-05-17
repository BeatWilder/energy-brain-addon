#!/usr/bin/env bash
set -euo pipefail

cd "$HOME/energy-brain/energy-brain-addon"

echo "=================================================="
echo "V2465-V2480 add-on cockpit polish smoke"
echo "=================================================="

echo
echo "=== 1. syntax check ==="
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile energy_brain/web_ui.py

echo
echo "=== 2. web UI tests ==="
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_web_ui.py

echo
echo "=== 3. forbidden write/service audit ==="
if grep -RInE "call_service\(|set_state\(|/api/services|method=.POST|method=.PUT|method=.PATCH|method=.DELETE|requests\.post|requests\.put|requests\.patch|requests\.delete|urllib\.request\.urlopen\(.*data=" \
  energy_brain/web_ui.py tests/test_web_ui.py 2>/dev/null; then
  echo "FAIL: forbidden write/service pattern found"
  exit 1
fi
echo "PASS: no forbidden write/service patterns found"

echo
echo "=== 4. protected planner/controller/main diff check ==="
if git diff -- energy_brain/planner.py energy_brain/controller.py energy_brain/main.py | grep -q .; then
  echo "FAIL: protected planner/controller/main diff detected"
  exit 1
fi
echo "PASS: protected planner/controller/main diff empty"

echo
echo "=== 5. polish markers ==="
grep -nE "render_energy_brain_cockpit_html_v2|Open Energy Brain EMS cockpit|/api/energy-brain-cockpit|if path == \"/cockpit\"" energy_brain/web_ui.py

echo
echo "=== 6. cleanup pycache ==="
find energy_brain tests -type d -name "__pycache__" -prune -exec rm -rf {} +

echo
echo "=== 7. status ==="
git status --short

echo
echo "PASS: V2465-V2480 add-on cockpit polish smoke completed"
