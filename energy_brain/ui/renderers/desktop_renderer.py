from __future__ import annotations

from typing import Any

from energy_brain.ui.layouts.responsive import build_layout_view


def build_desktop_renderer(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    result = build_layout_view(payload or {}, "desktop")
    result["schema_version"] = "phase_ui_e.desktop_renderer.v2"
    result["mode"] = "mission_control"
    return result
