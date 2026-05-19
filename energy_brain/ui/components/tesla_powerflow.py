from __future__ import annotations

from typing import Any


def calculate_flow_direction(value: float) -> str:
    if value > 0:
        return "forward"

    if value < 0:
        return "reverse"

    return "idle"


def build_tesla_powerflow() -> dict[str, Any]:
    solar_kw = 3.2
    house_kw = 2.1
    battery_kw = 1.1
    grid_kw = -0.6

    return {
        "schema_version": "phase_ui_h.tesla_powerflow.v1",
        "type": "tesla_powerflow",
        "observer_only": True,
        "animated": True,
        "layout": "center_hub",
        "nodes": {
            "solar": {
                "label": "Zon",
                "kw": solar_kw,
                "active": solar_kw > 0,
            },
            "house": {
                "label": "Huis",
                "kw": house_kw,
                "active": house_kw > 0,
            },
            "battery": {
                "label": "Batterij",
                "kw": battery_kw,
                "soc_percent": 68,
                "state": "charging",
            },
            "grid": {
                "label": "Net",
                "kw": grid_kw,
                "state": "exporting",
            },
        },
        "flows": [
            {
                "from": "solar",
                "to": "house",
                "kw": 2.1,
                "direction": calculate_flow_direction(2.1),
                "animated": True,
            },
            {
                "from": "solar",
                "to": "battery",
                "kw": 1.1,
                "direction": calculate_flow_direction(1.1),
                "animated": True,
            },
            {
                "from": "solar",
                "to": "grid",
                "kw": 0.6,
                "direction": calculate_flow_direction(0.6),
                "animated": True,
            },
        ],
        "ui": {
            "style": "tesla_inspired",
            "rounded_nodes": True,
            "dynamic_ring_colors": True,
            "minimal_labels": True,
        },
    }
