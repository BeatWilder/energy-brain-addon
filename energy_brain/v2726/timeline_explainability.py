from __future__ import annotations

from typing import Any


HUMAN_REASON_MAP = {
    "charge_from_pv_surplus":
        "Charging because forecast PV exceeds household demand.",
    "discharge_to_load":
        "Discharging to reduce expensive grid import.",
    "reserve_hold":
        "Battery reserve reached; discharge paused.",
    "reserve_clamped_discharge":
        "Discharge reduced to protect reserve SOC.",
    "max_soc_clamped_charge":
        "Charging reduced because max SOC is near.",
    "max_soc_hold":
        "Charging paused because battery reached max SOC.",
    "shadow_hold":
        "Observer-only fallback hold state.",
    "baseline_compare":
        "Baseline comparison informational timestep.",
}


CONSTRAINT_REASON_MAP = {
    "reserve_hold": "min_soc_floor",
    "reserve_clamped_discharge": "min_soc_floor",
    "max_soc_clamped_charge": "max_soc_ceiling",
    "max_soc_hold": "max_soc_ceiling",
}


ACTION_MAP = {
    "charge_from_pv_surplus": "charge",
    "discharge_to_load": "discharge",
    "reserve_hold": "hold",
    "reserve_clamped_discharge": "discharge",
    "max_soc_clamped_charge": "charge",
    "max_soc_hold": "hold",
    "shadow_hold": "hold",
    "baseline_compare": "compare",
}


def build_timeline_explainability(
    plan: dict[str, Any],
) -> list[dict[str, Any]]:

    steps = plan.get("steps") or []

    result: list[dict[str, Any]] = []

    for step in steps:

        if not isinstance(step, dict):
            continue

        reason = str(step.get("reason") or "unknown")

        result.append({
            "index": step.get("index"),
            "action": ACTION_MAP.get(reason, "unknown"),
            "reason_code": reason,
            "human_reason": HUMAN_REASON_MAP.get(
                reason,
                "No human explanation available."
            ),
            "constraint": CONSTRAINT_REASON_MAP.get(reason),
            "soc_percent": step.get("soc_percent"),
            "battery_setpoint_kw": step.get("battery_setpoint_kw"),
            "observer_only": True,
            "write_allowed": False,
        })

    return result
