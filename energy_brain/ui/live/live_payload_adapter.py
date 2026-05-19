from __future__ import annotations

from typing import Any


UNKNOWN = "onbekend"


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _pick(source: dict[str, Any], *paths: tuple[str, ...]) -> Any:
    for path in paths:
        current: Any = source
        for part in path:
            if not isinstance(current, dict) or part not in current:
                current = None
                break
            current = current[part]
        if current not in (None, "", "unknown", "unavailable", "none", "None"):
            return current
    return None


def _number(value: Any) -> float | None:
    if value in (None, "", "unknown", "unavailable", "none", "None", "—"):
        return None
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _action_from_setpoint(value: Any) -> str:
    number = _number(value)
    if number is None:
        return "Wachten op live plandata"
    if number > 0.05:
        return "Laden gepland"
    if number < -0.05:
        return "Huis voeden gepland"
    return "Vasthouden"


def _reason_from_live_data(payload: dict[str, Any]) -> str:
    price = _number(payload.get("grid_price"))
    pv = _number(payload.get("pv_power_kw"))
    load = _number(payload.get("household_load_kw"))
    soc = _number(payload.get("battery_soc_percent"))
    battery = _number(payload.get("battery_power_kw"))

    if battery is not None and battery > 0.05:
        return "De batterij neemt nu energie op."
    if battery is not None and battery < -0.05:
        return "De batterij ondersteunt het huis of beperkt dure netafname."
    if price is not None and price < 0:
        return "De stroomprijs is gunstig; Energy Brain bewaakt een laadkans."
    if pv is not None and load is not None and pv > load:
        return "Er is zonne-overschot beschikbaar voor laden of terugleveren."
    if soc is not None and soc < 25:
        return "De batterijreserve krijgt prioriteit."
    return "Energy Brain bewaakt de actuele meetdata en wacht op een beter moment."


def _timeline(summary: dict[str, Any]) -> list[dict[str, Any]]:
    plan = _dict(summary.get("plan"))
    rows = _list(plan.get("steps")) or _list(summary.get("plan_windows")) or _list(summary.get("timeline"))
    preview: list[dict[str, Any]] = []
    for index, row in enumerate(rows[:8]):
        if not isinstance(row, dict):
            continue
        setpoint = row.get("battery_setpoint_kw")
        action = row.get("action") or row.get("kind") or _action_from_setpoint(setpoint)
        preview.append(
            {
                "time": row.get("start") or row.get("time") or ("nu" if index == 0 else "straks"),
                "action": action,
                "reason": row.get("reason") or _reason_from_live_data(
                    {
                        "grid_price": _pick(summary, ("grid_price",), ("price_now",)) or _pick(_dict(summary.get("snapshot")), ("grid_price",)),
                        "pv_power_kw": _pick(summary, ("pv_power_kw",), ("pv_now_kw",)) or _pick(_dict(summary.get("snapshot")), ("pv_power_kw",)),
                        "household_load_kw": _pick(summary, ("household_load_kw",), ("home_load_kw",)) or _pick(_dict(summary.get("snapshot")), ("household_load_kw",)),
                        "battery_soc_percent": _pick(summary, ("battery_soc_percent",), ("soc_percent",)) or _pick(_dict(summary.get("snapshot")), ("battery_soc_percent",)),
                        "battery_power_kw": _pick(summary, ("battery_power_kw",), ("battery_kw",)),
                    }
                ),
                "soc_percent": row.get("soc_percent"),
                "price": row.get("price"),
                "pv_forecast": row.get("pv_forecast"),
                "load_forecast": row.get("load_forecast"),
            }
        )
    return preview


def build_live_payload(
    raw: dict[str, Any] | None = None,
) -> dict[str, Any]:

    raw = raw or {}
    snapshot = _dict(raw.get("snapshot"))
    plan = _dict(raw.get("plan"))
    controller = _dict(raw.get("controller"))
    execution = _dict(raw.get("execution"))
    energy_flow = _dict(raw.get("energy_flow"))
    data_quality = _dict(raw.get("data_quality"))

    soc = _pick(raw, ("battery_soc_percent",), ("soc_percent",), ("battery", "soc_percent")) or _pick(snapshot, ("battery_soc_percent",))
    pv = _pick(raw, ("pv_power_kw",), ("pv_now_kw",), ("solar_kw",)) or _pick(snapshot, ("pv_power_kw",)) or _pick(energy_flow, ("pv_kw",), ("pv_power_kw",))
    load = _pick(raw, ("household_load_kw",), ("home_load_kw",), ("house_kw",)) or _pick(snapshot, ("household_load_kw",)) or _pick(energy_flow, ("load_kw",), ("household_load_kw",))
    grid_power = _pick(raw, ("grid_power_kw",), ("grid_kw",)) or _pick(snapshot, ("grid_power_kw",)) or _pick(energy_flow, ("grid_kw",), ("grid_power_kw",))
    battery_power = _pick(raw, ("battery_power_kw",), ("battery_kw",)) or _pick(snapshot, ("battery_power_kw",)) or _pick(energy_flow, ("battery_kw",), ("battery_power_kw",))
    price = _pick(raw, ("grid_price",), ("price_now",), ("price",)) or _pick(snapshot, ("grid_price",)) or _pick(energy_flow, ("grid_price",))
    setpoint = _pick(controller, ("setpoint_kw",))
    decision = _pick(raw, ("decision",), ("current_action",), ("recommended_action",)) or _action_from_setpoint(setpoint)

    missing = [
        label
        for label, value in (
            ("batterij SOC", soc),
            ("PV", pv),
            ("huisverbruik", load),
            ("netvermogen", grid_power),
            ("batterijvermogen", battery_power),
            ("stroomprijs", price),
        )
        if value in (None, "", "unknown", "unavailable", "none", "None")
    ]
    degraded = bool(missing) or raw.get("valid_cycle") is False or bool(raw.get("degraded"))
    timeline = _timeline(raw) if raw else []

    return {
        "schema_version": "phase_ui_i.live_payload.v1",
        "observer_only": True,
        "read_only": True,
        "mode": raw.get("mode") or "observer",
        "valid_cycle": raw.get("valid_cycle", True),
        "soc_percent": soc,
        "battery_soc_percent": soc,
        "pv_power_kw": pv,
        "pv_now_kw": pv,
        "solar_kw": pv,
        "household_load_kw": load,
        "home_load_kw": load,
        "house_kw": load,
        "battery_power_kw": battery_power,
        "battery_kw": battery_power,
        "grid_power_kw": grid_power,
        "grid_kw": grid_power,
        "grid_price": price,
        "price_now": price,
        "current_action": decision,
        "decision": decision,
        "decision_reason": raw.get("decision_reason") or _reason_from_live_data(
            {
                "grid_price": price,
                "pv_power_kw": pv,
                "household_load_kw": load,
                "battery_soc_percent": soc,
                "battery_power_kw": battery_power,
            }
        ),
        "expected_savings": plan.get("delta_vs_baseline") or raw.get("expected_savings"),
        "forecast_confidence": raw.get("forecast_confidence") or data_quality.get("confidence"),
        "timeline": timeline,
        "plan_windows": timeline,
        "reserve_protected": raw.get("reserve_protected", True),
        "reserve_status": raw.get("reserve_status") or "Reserve beschermd",
        "forecast_valid": not degraded,
        "degraded": degraded,
        "degraded_text": (
            "Meetdata ontbreekt: " + ", ".join(missing)
            if missing
            else "Realtime meetdata beschikbaar. Aansturing blijft geblokkeerd."
        ),
        "missing_data_flags": missing,
        "last_update": raw.get("last_update") or raw.get("updated_at") or raw.get("timestamp") or "laatste cyclus",
        "execution": "Geen aansturing actief",
        "execution_attempted": execution.get("attempted"),
        "execution_blocked_reason": "Alleen observeren. Geen Home Assistant schrijfacties of dienstaanroepen.",
        "shadow_state": raw.get("shadow_state") or raw.get("mode") or "observer",
        "dispatch_allowed": False,
        "ha_writes_allowed": False,
        "service_calls_allowed": False,
    }
