from __future__ import annotations

from typing import Any


def hero_component() -> dict[str, Any]:
    return {
        "type": "hero",
        "title": "Energy Brain",
        "status": "SAFE",
        "soc_percent": 68,
        "current_action": "charge",
        "price": -0.12,
    }


def powerflow_component() -> dict[str, Any]:
    return {
        "type": "powerflow",
        "layout": "tesla_style",
        "solar_kw": 3.2,
        "house_kw": 2.1,
        "battery_kw": 1.1,
        "grid_kw": -0.6,
    }


def tesla_powerflow_component() -> dict[str, Any]:
    payload = powerflow_component().copy()
    payload["type"] = "tesla_powerflow"
    return payload


def explainability_component() -> dict[str, Any]:
    return {
        "type": "explainability",
        "title": "Waarom gebeurt dit?",
        "reasons": [
            "Negative energy price",
            "Battery below target",
            "Reserve remains protected",
        ],
    }


def timeline_component() -> dict[str, Any]:
    return {
        "type": "planner_timeline",
        "entries": [
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
    }


def safety_component() -> dict[str, Any]:
    return {
        "type": "safety",
        "reserve_protected": True,
        "soc_bounds_ok": True,
        "forecast_valid": True,
        "fallback_ready": True,
    }


def runtime_component() -> dict[str, Any]:
    return {
        "type": "runtime",
        "controller_state": "observer_only",
        "dispatch_allowed": False,
        "ha_writes_allowed": False,
    }
