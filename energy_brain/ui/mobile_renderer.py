from __future__ import annotations

from typing import Any

from energy_brain.ui.layouts.responsive import build_layout_view


def build_mobile_hero(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "hero",
        "status": "SAFE",
        "action": payload.get("current_action", "Wachten"),
        "price": payload.get("price"),
        "soc_percent": payload.get("soc_percent"),
    }


def build_mobile_powerflow(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "compact_powerflow",
        "solar_kw": payload.get("solar_kw", 0.0),
        "house_kw": payload.get("house_kw", 0.0),
        "battery_kw": payload.get("battery_kw", 0.0),
        "grid_kw": payload.get("grid_kw", 0.0),
    }


def build_mobile_explainability(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "explainability",
        "title": "Waarom gebeurt dit?",
        "reasons": payload.get(
            "reasons",
            [
                "Negative price detected",
                "Reserve blijft beschermd",
                "PV surplus expected",
            ],
        ),
    }


def build_mobile_timeline(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "timeline_cards",
        "cards": payload.get(
            "timeline",
            [
                {
                    "time": "20:00",
                    "action": "charge",
                },
                {
                    "time": "23:00",
                    "action": "hold",
                },
                {
                    "time": "07:00",
                    "action": "discharge",
                },
            ],
        ),
    }


def build_mobile_statusbar(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "sticky_statusbar",
        "status": "SAFE",
        "action": payload.get("current_action"),
        "price": payload.get("price"),
    }


def render_mobile_cockpit(
    payload: dict[str, Any],
) -> dict[str, Any]:
    result = build_layout_view(payload, "mobile")
    result["schema_version"] = "phase_ui_c.mobile_renderer.v2"
    result["mode"] = "operator_companion"
    return result
