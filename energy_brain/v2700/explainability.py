from __future__ import annotations

from typing import Any


def build_planner_explainability(summary: dict[str, Any]) -> dict[str, Any]:
    snapshot = summary.get("snapshot") or {}
    plan = summary.get("plan") or {}

    price = _float(snapshot.get("grid_price"))
    pv = _float(snapshot.get("pv_power_kw"))
    load = _float(snapshot.get("household_load_kw"))
    soc = _float(snapshot.get("battery_soc_percent"))

    reasons: list[str] = []
    constraints: list[str] = []
    badges: list[str] = []

    if price is not None:
        if price >= 0.30:
            reasons.append("high_import_price")
            badges.append("expensive_grid")

        elif price <= 0.05:
            reasons.append("cheap_energy_window")
            badges.append("cheap_grid")

    if pv is not None:
        if pv < 1.0:
            reasons.append("low_expected_pv")

        elif pv > 4.0:
            reasons.append("high_pv_available")
            badges.append("solar_surplus")

    if load is not None:
        if load > 3.5:
            reasons.append("high_household_load")

    if soc is not None:
        if soc <= 25:
            constraints.append("reserve_soc_floor")
            badges.append("reserve_protection")

        elif soc >= 90:
            constraints.append("battery_near_full")

    for step in plan.get("steps", []):
        reason = str(step.get("reason", "")).strip()

        if "reserve" in reason:
            if "reserve_soc_floor" not in constraints:
                constraints.append("reserve_soc_floor")

            if "reserve_protection" not in badges:
                badges.append("reserve_protection")

        if "clamp" in reason:
            constraints.append("power_clamp_active")

    decision = "idle"

    first = (plan.get("steps") or [{}])[0]

    setpoint = _float(first.get("battery_setpoint_kw"))

    if setpoint is not None:
        if setpoint > 0.1:
            decision = "charge"

        elif setpoint < -0.1:
            decision = "discharge"

    return {
        "decision": decision,
        "reasons": sorted(set(reasons)),
        "constraints": sorted(set(constraints)),
        "badges": sorted(set(badges)),
        "observer_only": True,
        "write_allowed": False,
    }


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None
