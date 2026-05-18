from __future__ import annotations

from typing import Any


def detect_layout_mode(
    screen_width: int,
    manual_override: str | None = None,
) -> str:
    if manual_override in {"desktop", "tablet", "mobile"}:
        return manual_override

    if screen_width >= 1400:
        return "desktop"

    if screen_width >= 700:
        return "tablet"

    return "mobile"


def build_responsive_payload(
    screen_width: int,
    manual_override: str | None = None,
) -> dict[str, Any]:
    layout = detect_layout_mode(
        screen_width=screen_width,
        manual_override=manual_override,
    )

    return {
        "schema_version": "phase_ui_g.responsive_router.v1",
        "observer_only": True,
        "auto_switching": manual_override is None,
        "screen_width": screen_width,
        "selected_layout": layout,
        "manual_override": manual_override,
        "breakpoints": {
            "mobile_max": 699,
            "tablet_max": 1399,
            "desktop_min": 1400,
        },
    }
