from __future__ import annotations

from typing import Any

from energy_brain.ui.live.live_payload_adapter import (
    build_live_payload,
)

from energy_brain.ui.renderers.desktop_renderer import (
    build_desktop_renderer,
)

from energy_brain.ui.mobile_renderer import (
    render_mobile_cockpit,
)

from energy_brain.ui.tablet_renderer import (
    render_tablet_cockpit,
)


def build_layout(layout: str) -> dict[str, Any]:
    payload = build_live_payload()
    return build_layout_view(payload, layout)


def build_layout_view(
    payload: dict[str, Any],
    layout: str,
) -> dict[str, Any]:

    if layout == "mobile":
        result = render_mobile_cockpit(payload)
        result["layout"] = "mobile"
        return result

    if layout == "tablet":
        result = render_tablet_cockpit(payload)
        result["layout"] = "tablet"
        return result

    if layout == "auto":
        return {
            "layout": "auto",
            "auto_detect": True,
            "available_layouts": [
                "mobile",
                "tablet",
                "desktop",
            ],
            "selected_default": "desktop",
        }

    result = build_desktop_renderer()
    result["layout"] = "desktop"
    return result
