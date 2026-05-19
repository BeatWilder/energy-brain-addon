from __future__ import annotations

from typing import Any

from energy_brain.ui.state.display_values import sanitize_percent, sanitize_power_kw
from energy_brain.ui.state.layout_state import effective_layout_mode


def _float_value(value: Any, default: float = 0.0) -> float:
    if value in (None, "", "unknown", "unavailable", "none", "None", "—"):
        return default
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return default


def _text_value(value: Any, default: str) -> str:
    if value in (None, "", "unknown", "unavailable", "none", "None"):
        return default
    return str(value)


def _money_value(value: Any, default: str = "calculating") -> str:
    if value in (None, "", "unknown", "unavailable", "none", "None", "—"):
        return default
    try:
        number = float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return str(value)
    sign = "-" if number < 0 else ""
    return f"{sign}€{abs(number):.2f}"


def _percent_value(value: Any, default: str = "medium") -> str:
    if value in (None, "", "unknown", "unavailable", "none", "None", "—"):
        return default
    try:
        return f"{float(str(value).replace(',', '.')):.0f}%"
    except (TypeError, ValueError):
        return str(value)


def _strategy_text(payload: dict[str, Any]) -> str:
    explicit = _text_value(payload.get("decision"), "")
    if explicit:
        lower = explicit.lower()
        if any(word in lower for word in ("charge", "laden")):
            return "Charging from the best available energy window"
        if any(word in lower for word in ("discharge", "export", "ontladen")):
            return "Using stored energy during an expensive window"
        if any(word in lower for word in ("hold", "wacht", "wait")):
            return "Holding battery until conditions improve"
        return explicit

    solar = _float_value(payload.get("pv_power_kw") or payload.get("pv_now_kw"))
    battery = _float_value(payload.get("battery_power_kw"))
    grid = _float_value(payload.get("grid_power_kw"))
    price = _float_value(payload.get("grid_price") or payload.get("price_now"))
    if solar > 0.4 and battery > 0.1:
        return "Charging from solar surplus"
    if grid < -0.1:
        return "Exporting surplus to the grid"
    if price < 0:
        return "Waiting for cheaper electricity"
    return "Protecting reserve while observing the next window"


def _display_power(payload: dict[str, Any], *keys: str, pv_generation: bool = False) -> dict[str, Any]:
    for key in keys:
        if key in payload:
            return sanitize_power_kw(payload.get(key), pv_generation=pv_generation)
    return sanitize_power_kw(None)


def _timeline_entries(payload: dict[str, Any]) -> list[dict[str, str]]:
    windows = payload.get("plan_windows")
    if not isinstance(windows, list):
        windows = payload.get("timeline")
    if not isinstance(windows, list):
        windows = []

    entries: list[dict[str, str]] = []
    for index, item in enumerate(windows[:8]):
        if not isinstance(item, dict):
            continue
        action = _text_value(item.get("kind") or item.get("action"), "hold")
        lower = action.lower()
        if "charge" in lower or "laden" in lower:
            tone = "charge"
        elif "discharge" in lower or "export" in lower or "ontladen" in lower:
            tone = "discharge"
        elif "cheap" in lower or "negative" in lower:
            tone = "cheap"
        elif "expensive" in lower or "peak" in lower:
            tone = "expensive"
        else:
            tone = "hold"
        entries.append(
            {
                "time": _text_value(item.get("start") or item.get("time"), "nu"),
                "action": action,
                "reason": _text_value(
                    item.get("reason"),
                    "Observer-plan uit laatste cyclus.",
                ),
                "tone": tone,
                "width": str(12 + (index % 3) * 4),
            }
        )
    if entries:
        return entries
    return [
        {
            "time": "nu",
            "action": _text_value(payload.get("decision"), "observer"),
            "reason": _text_value(
                payload.get("decision_reason"),
                "Geen planregels beschikbaar.",
            ),
            "tone": "hold",
            "width": "18",
        }
    ]


def _reasons(payload: dict[str, Any]) -> list[str]:
    values = [
        payload.get("decision_reason"),
        payload.get("predbat_summary"),
        payload.get("degraded_text"),
    ]
    return [_text_value(value, "") for value in values if _text_value(value, "")]


def build_layout_view(payload: dict[str, Any], layout_mode: str) -> dict[str, Any]:
    mode = effective_layout_mode(layout_mode)
    compact = mode == "mobile"
    tablet = mode == "tablet"
    timeline = _timeline_entries(payload)
    strategy = _strategy_text(payload)
    price = _float_value(payload.get("grid_price") or payload.get("price_now"))
    solar = _display_power(payload, "pv_power_kw", "pv_now_kw", pv_generation=True)
    house = _display_power(payload, "household_load_kw", "home_load_kw")
    battery = _display_power(payload, "battery_power_kw")
    grid = _display_power(payload, "grid_power_kw")
    soc = sanitize_percent(payload.get("soc_percent") or payload.get("battery_soc_percent"))
    return {
        "schema_version": "energy_brain.ui.layout.v2",
        "layout": mode,
        "layout_preference": layout_mode if layout_mode in {"auto", "mobile", "tablet", "desktop"} else "auto",
        "observer_only": True,
        "density": "compact" if compact else "balanced" if tablet else "wide",
        "responsive": {
            "mobile_first": True,
            "breakpoints": {
                "mobile_max": 767,
                "tablet_min": 768,
                "tablet_max": 1199,
                "desktop_min": 1200,
            },
        },
        "sections": [
            {
                "type": "powerflow_hero",
                "title": "Energy Brain",
                "status": "Observer",
                "strategy": strategy,
                "soc_percent": soc["value"],
                "soc_label": soc["label"],
                "soc_known": soc["known"],
                "solar_kw": solar["value"],
                "solar_label": solar["label"],
                "solar_known": solar["known"],
                "house_kw": house["value"],
                "house_label": house["label"],
                "house_known": house["known"],
                "battery_kw": battery["value"],
                "battery_label": battery["label"],
                "battery_known": battery["known"],
                "grid_kw": grid["value"],
                "grid_label": grid["label"],
                "grid_known": grid["known"],
                "data_quality": {
                    "clamped": [
                        name
                        for name, value in {
                            "solar": solar,
                            "home": house,
                            "battery": battery,
                            "grid": grid,
                            "battery_soc": soc,
                        }.items()
                        if value["clamped"]
                    ],
                    "unknown": [
                        name
                        for name, value in {
                            "solar": solar,
                            "home": house,
                            "battery": battery,
                            "grid": grid,
                            "battery_soc": soc,
                        }.items()
                        if not value["known"]
                    ],
                },
                "price": price,
                "decision": strategy,
                "updated": _text_value(payload.get("last_update"), "laatste cyclus"),
            },
            {
                "type": "planner_summary",
                "title": "Now / next",
                "mode": _text_value(payload.get("mode"), "observer"),
                "execution": _text_value(payload.get("execution"), "Geen aansturing"),
                "headline": strategy,
                "confidence": _percent_value(payload.get("forecast_confidence")),
                "expected_savings": _money_value(
                    payload.get("expected_savings")
                    or payload.get("delta_vs_baseline")
                    or payload.get("savings")
                ),
                "next_action_time": timeline[0]["time"] if timeline else "next cycle",
                "entries": timeline,
            },
            {
                "type": "explainability",
                "title": "Why",
                "reasons": _reasons(payload),
            },
            {
                "type": "safety",
                "title": "System health",
                "observer_state": _text_value(payload.get("shadow_state"), "observer/shadow"),
                "forecast_valid": "valid" if not payload.get("degraded") else "degraded",
                "reserve_status": _text_value(payload.get("reserve_status"), "reserve protected"),
                "fault_status": _text_value(payload.get("fault_status"), "no active faults"),
                "last_update": _text_value(payload.get("last_update"), "latest cycle"),
                "readonly": True,
                "blocked_reason": _text_value(
                    payload.get("execution_blocked_reason"),
                    "Write protection active. UI is read-only.",
                ),
            },
        ],
    }


def build_layout(layout_mode: str, payload: dict[str, Any]) -> dict[str, Any]:
    return build_layout_view(payload, layout_mode)
