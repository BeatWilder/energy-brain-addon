from __future__ import annotations

from energy_brain.ui.layout_preferences import normalize_layout_profile


def resolve_layout_profile(request_args: dict | None = None) -> str:
    request_args = request_args or {}

    requested = request_args.get("layout")

    return normalize_layout_profile(requested)
