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
  tools/run_v2319a_clean_overview_routing_cache_smoke.sh
)

for smoke in "${previous_smokes[@]}"; do
  if [ -f "$smoke" ]; then
    echo "== previous smoke: $smoke =="
    bash "$smoke"
    echo "PASS: $smoke"
  fi
done

echo "== V2320 focused tests =="
PYTHONPATH=. python3 -m pytest -q tests/test_v2320_v2351_animated_readonly_powerflow.py
echo "PASS: V2320 focused tests"

echo "== forbidden changed/new surface scan =="
changed_files="$(git diff --name-only; git ls-files --others --exclude-standard)"
scan_files="$(printf '%s\n' "$changed_files" | grep -E '^(energy_brain/|tests/).*' || true)"

if [ -n "$scan_files" ]; then
  SCAN_FILES="$scan_files" python3 - <<'PYSCAN'
from __future__ import annotations

import os
from pathlib import Path

parts = [
    ("call", "_", "service", "("),
    ("hass", ".", "services"),
    ("set", "_", "state", "("),
    ("input", "_", "boolean", "."),
    ("input", "_", "number", "."),
    ("input", "_", "select", "."),
    ("sw", "itch", "."),
    ("cli", "mate", "."),
    ("not", "ify", "."),
    ("shell", "_", "command", "."),
    ("do", "_", "POST"),
    ("do", "_", "PUT"),
    ("do", "_", "PATCH"),
    ("do", "_", "DELETE"),
    ("dis", "patch", "("),
    ("exe", "cute", "("),
    ("enable", " ", "control"),
    ("start", " ", "control"),
]

needles = ["".join(part) for part in parts]
files = [line.strip() for line in os.environ.get("SCAN_FILES", "").splitlines() if line.strip()]
hits: list[str] = []

for name in files:
    path = Path(name)
    if not path.exists() or not path.is_file():
        continue
    body = path.read_text(encoding="utf-8", errors="ignore")
    for needle in needles:
        if needle in body:
            hits.append(f"{name}: contains blocked runtime surface")
            break

if hits:
    print("\n".join(hits))
    raise SystemExit(1)
PYSCAN
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
echo "PASS: V2320-V2351 animated read-only powerflow smoke"
