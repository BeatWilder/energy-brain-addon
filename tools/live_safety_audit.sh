#!/usr/bin/env sh
set -eu

ADDON_SLUG="${1:-bb2014bd_energy_brain}"
RESERVE_PERCENT="${2:-20.0}"

echo "=== Energy Brain live safety audit ==="
echo "addon_slug: ${ADDON_SLUG}"
echo "reserve_percent: ${RESERVE_PERCENT}"

echo
echo "=== add-on version ==="
ha addons info "${ADDON_SLUG}" 2>/dev/null | grep -E "version|name|slug" || true

echo
echo "=== latest logs safety summary ==="
ha addons logs "${ADDON_SLUG}" | tail -250 | python3 - "${RESERVE_PERCENT}" <<'PY'
import json
import sys

reserve = float(sys.argv[1])
last_cycle = None

for line in sys.stdin:
    line = line.strip()
    if not line.startswith("{"):
        continue
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        continue
    if obj.get("event") == "cycle":
        last_cycle = obj

if last_cycle is None:
    print("FAIL: no cycle event found in recent logs")
    raise SystemExit(1)

plan = last_cycle.get("plan") or {}
controller = last_cycle.get("controller") or {}
execution = last_cycle.get("execution") or {}
trajectory = plan.get("soc_trajectory") or []
steps = plan.get("steps") or []

min_soc = min(trajectory) if trajectory else None
last_soc = trajectory[-1] if trajectory else None
first_setpoint = controller.get("setpoint_kw")
execute = controller.get("execute")
attempted = execution.get("attempted")

print(f"mode: {last_cycle.get('mode')}")
print(f"execute: {execute}")
print(f"attempted: {attempted}")
print(f"plan_valid: {plan.get('valid')}")
print(f"first_setpoint_kw: {first_setpoint}")
print(f"min_soc: {min_soc}")
print(f"last_soc: {last_soc}")
print(f"steps: {len(steps)}")

reason_counts = {}
for step in steps:
    reason = step.get("reason")
    reason_counts[reason] = reason_counts.get(reason, 0) + 1

print("reasons:")
for reason, count in sorted(reason_counts.items()):
    print(f"  {reason}: {count}")

errors = []
if last_cycle.get("mode") not in {"observer", "shadow"}:
    errors.append("not_observer_or_shadow")
if execute is not False:
    errors.append("controller_execute_not_false")
if attempted is not False:
    errors.append("execution_attempted_not_false")
if plan.get("valid") is not True:
    errors.append("plan_not_valid")
if min_soc is None:
    errors.append("missing_soc_trajectory")
elif min_soc < reserve - 1e-6:
    errors.append("soc_below_reserve")
if len(steps) != 96:
    errors.append("unexpected_step_count")

if errors:
    print("FAIL:", ",".join(errors))
    raise SystemExit(1)

print("PASS: observer cycle is safe")
PY
