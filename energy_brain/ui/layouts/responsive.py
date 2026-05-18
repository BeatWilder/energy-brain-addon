from __future__ import annotations

from typing import Any

from energy_brain.ui.state.layout_state import DEFAULT_LAYOUT_MODE, VALID_LAYOUT_MODES


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


def _timeline_entries(payload: dict[str, Any]) -> list[dict[str, str]]:
    windows = payload.get("plan_windows")
    if not isinstance(windows, list):
        windows = payload.get("timeline")
    if not isinstance(windows, list):
        windows = []

    entries: list[dict[str, str]] = []
    for item in windows[:4]:
        if not isinstance(item, dict):
            continue
        entries.append(
            {
                "time": _text_value(item.get("start") or item.get("time"), "nu"),
                "action": _text_value(item.get("kind") or item.get("action"), "hold"),
                "reason": _text_value(
                    item.get("reason"),
                    "Observer-plan uit laatste cyclus.",
                ),
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
    mode = layout_mode if layout_mode in VALID_LAYOUT_MODES else DEFAULT_LAYOUT_MODE
    compact = mode == "mobile"
    tablet = mode == "tablet"
    return {
        "schema_version": "energy_brain.ui.layout.v1",
        "layout": mode,
        "observer_only": True,
        "density": "compact" if compact else "balanced" if tablet else "wide",
        "sections": [
            {
                "type": "powerflow_hero",
                "title": "Energy Brain",
                "status": "Observer",
                "soc_percent": _float_value(
                    payload.get("soc_percent") or payload.get("battery_soc_percent"),
                    0.0,
                ),
                "solar_kw": _float_value(payload.get("pv_power_kw") or payload.get("pv_now_kw")),
                "house_kw": _float_value(
                    payload.get("household_load_kw") or payload.get("home_load_kw")
                ),
                "battery_kw": _float_value(payload.get("battery_power_kw")),
                "grid_kw": _float_value(payload.get("grid_power_kw")),
                "price": _float_value(payload.get("grid_price") or payload.get("price_now")),
                "decision": _text_value(payload.get("decision"), "Wachten"),
                "updated": _text_value(payload.get("last_update"), "laatste cyclus"),
            },
            {
                "type": "planner_summary",
                "title": "Planner",
                "mode": _text_value(payload.get("mode"), "observer"),
                "execution": _text_value(payload.get("execution"), "Geen aansturing"),
                "entries": _timeline_entries(payload),
            },
            {
                "type": "explainability",
                "title": "Waarom",
                "reasons": _reasons(payload),
            },
            {
                "type": "safety",
                "title": "Safety",
                "reserve_status": _text_value(payload.get("reserve_status"), "Reserve onbekend"),
                "fault_status": _text_value(payload.get("fault_status"), "geen bekende melding"),
                "readonly": True,
                "blocked_reason": _text_value(
                    payload.get("execution_blocked_reason"),
                    "UI is read-only.",
                ),
            },
        ],
    }


def build_layout(layout_mode: str, payload: dict[str, Any]) -> dict[str, Any]:
    return build_layout_view(payload, layout_mode)

