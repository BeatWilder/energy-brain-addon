from __future__ import annotations

from typing import Any

from energy_brain.ui.live.live_payload_adapter import (
    build_live_payload,
)
from energy_brain.ui.layouts.responsive import build_layout_view as build_responsive_layout_view
from energy_brain.ui.state.layout_state import select_layout_mode


def build_layout(layout: str = "desktop", payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return build_layout_view(payload or build_live_payload(), layout)


def build_layout_view(
    payload: dict[str, Any],
    layout: str,
) -> dict[str, Any]:
    return build_responsive_layout_view(payload, select_layout_mode({"layout": layout}))
