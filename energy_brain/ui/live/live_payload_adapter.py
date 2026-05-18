from __future__ import annotations

from typing import Any


def build_live_payload(
    raw: dict[str, Any] | None = None,
) -> dict[str, Any]:

    raw = raw or {}

    return {
        "schema_version": "phase_ui_i.live_payload.v1",
        "observer_only": True,
        "soc_percent": raw.get("soc_percent", 68),
        "current_action": raw.get("current_action", "charge"),
        "price": raw.get("price", -0.12),
        "solar_kw": raw.get("solar_kw", 3.2),
        "house_kw": raw.get("house_kw", 2.1),
        "battery_kw": raw.get("battery_kw", 1.1),
        "grid_kw": raw.get("grid_kw", -0.6),
        "reserve_protected": raw.get("reserve_protected", True),
        "forecast_valid": raw.get("forecast_valid", True),
        "dispatch_allowed": False,
        "ha_writes_allowed": False,
    }
