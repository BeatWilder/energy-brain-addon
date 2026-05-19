from __future__ import annotations

from typing import Any

from energy_brain.ui.state.layout_state import (
    MOBILE_MAX_WIDTH,
    TABLET_MAX_WIDTH,
    effective_layout_mode,
    select_layout_mode,
)


def detect_layout_mode(
    screen_width: int,
    manual_override: str | None = None,
) -> str:
    selected = select_layout_mode({"layout": manual_override or "auto"})
    return effective_layout_mode(selected, viewport_width=screen_width)


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
        "auto_switching": manual_override in (None, "auto"),
        "screen_width": screen_width,
        "selected_layout": layout,
        "manual_override": select_layout_mode({"layout": manual_override or "auto"}),
        "preference_storage_key": "energy-brain.layout",
        "breakpoints": {
            "mobile_max": MOBILE_MAX_WIDTH,
            "tablet_min": MOBILE_MAX_WIDTH + 1,
            "tablet_max": TABLET_MAX_WIDTH,
            "desktop_min": TABLET_MAX_WIDTH + 1,
        },
    }
