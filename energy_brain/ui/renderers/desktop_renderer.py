from __future__ import annotations

from typing import Any

from energy_brain.ui.components.shared_components import (
    explainability_component,
    powerflow_component,
    runtime_component,
    safety_component,
)


def build_desktop_renderer() -> dict[str, Any]:
    return {
        "schema_version": "phase_ui_e.desktop_renderer.v1",
        "layout": "desktop",
        "mode": "mission_control",
        "observer_only": True,
        "sections": [
            {
                "type": "topbar",
                "title": "Energy Brain",
            },
            {
                "left": powerflow_component(),
                "center": {
                    "type": "planner_timeline",
                },
                "right": [
                    explainability_component(),
                    safety_component(),
                    runtime_component(),
                ],
            },
        ],
    }
