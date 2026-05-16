#!/usr/bin/env bash
set -euo pipefail

echo "== pytest =="
PYTHONPATH=. python3 -m pytest -q
echo "PASS: pytest"

previous_smokes=(
  tools/run_v1968_v1999_predbat_inspired_ems_cockpit_and_benchmark_audit_smoke.sh
  tools/run_v2000_v2031_readonly_tesla_cockpit_ui_smoke.sh
  tools/run_v2032_v2063_interactive_readonly_cockpit_smoke.sh
  tools/run_v2064_v2095_usable_interactive_cockpit_smoke.sh
  tools/run_v2128_v2159_layperson_cockpit_explanations_smoke.sh
  tools/run_v2160_v2191_predbat_inspired_layperson_planner_cockpit_smoke.sh
  tools/run_v2256_v2287_predbat_ux_reverse_spec_no_code_copy_smoke.sh
  tools/run_v2288_v2319_predbat_style_energy_brain_plan_card_smoke.sh
)

for smoke in "${previous_smokes[@]}"; do
  if [ -f "$smoke" ]; then
    echo "== previous smoke: $smoke =="
    bash "$smoke"
    echo "PASS: $smoke"
  fi
done

echo "== V2319-A focused tests =="
PYTHONPATH=. python3 -m pytest -q tests/test_v2319a_clean_overview_routing_cache.py
echo "PASS: V2319-A focused tests"

echo "== forbidden changed/new surface scan =="
changed_files="$(git diff --name-only; git ls-files --others --exclude-standard)"
scan_files="$(printf '%s\n' "$changed_files" | grep -E '^(energy_brain/|tests/|tools/).*' || true)"
if [ -n "$scan_files" ]; then
  if printf '%s\n' "$scan_files" | xargs grep -nE \
    'call_service\(|hass\.services|set_state\(|input_boolean\.|input_number\.|input_select\.|switch\.|climate\.|notify\.|shell_command\.|do_POST|do_PUT|do_PATCH|do_DELETE|dispatch\(|execute\(|enable control|start control' \
    ; then
    echo "FAIL: forbidden write/control string found"
    exit 1
  fi
fi
echo "PASS: forbidden changed/new surface scan"

echo "== protected diff check =="
for f in energy_brain/controller.py energy_brain/main.py energy_brain/ha_client.py; do
  if git diff --quiet -- "$f"; then
    echo "PASS: $f protected diff empty"
  else
    echo "FAIL: $f changed"
    git diff -- "$f"
    exit 1
  fi
done

if [ -f ../app/energy_brain_v5.py ]; then
  if git -C .. diff --quiet -- app/energy_brain_v5.py; then
    echo "PASS: ../app/energy_brain_v5.py protected diff empty"
  else
    echo "FAIL: ../app/energy_brain_v5.py changed"
    git -C .. diff -- app/energy_brain_v5.py
    exit 1
  fi
else
  echo "SKIP: ../app/energy_brain_v5.py not accessible"
fi

echo "PASS: protected diffs are empty"
echo "PASS: V2319-A clean overview routing/cache smoke"
