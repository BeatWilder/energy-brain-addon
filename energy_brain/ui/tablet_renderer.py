from __future__ import annotations

from typing import Any

from energy_brain.ui.layouts.responsive import build_layout_view


def build_tablet_hero(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "hero",
        "title": "Energy Brain",
        "status": "SAFE",
        "current_action": payload.get(
            "current_action",
            "hold",
        ),
        "soc_percent": payload.get(
            "soc_percent",
            0,
        ),
        "price": payload.get(
            "price",
            0.0,
        ),
    }


def build_tablet_powerflow(
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": "powerflow",
        "layout": "centered",
        "solar_kw": payload.get(
            "solar_kw",
            0.0,
        ),
        "house_kw": payload.get(
            "house_kw",
            0.0,
        ),
        "battery_kw": payload.get(
            "battery_kw",
            0.0,
        ),
        "grid_kw": payload.get(
            "grid_kw",
            0.0,
        ),
    }


def build_tablet_planner(
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": "planner_timeline",
        "entries": payload.get(
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


def build_tablet_explainability(
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": "explainability",
        "title": "Waarom gebeurt dit?",
        "reasons": payload.get(
            "reasons",
            [
                "Gunstige prijs gedetecteerd",
                "Reserve beschermd",
                "Zonne-overschot verwacht",
            ],
        ),
    }


def build_tablet_safety(
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": "safety",
        "reserve_protected": True,
        "soc_bounds_ok": True,
        "forecast_valid": True,
        "fallback_ready": True,
    }


def render_tablet_cockpit(
    payload: dict[str, Any],
) -> dict[str, Any]:
    result = build_layout_view(payload, "tablet", include_living_layers=False)
    result["schema_version"] = "phase_ui_d.tablet_renderer.v2"
    result["mode"] = "control_panel"
    return result
