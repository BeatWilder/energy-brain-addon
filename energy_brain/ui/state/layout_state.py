from __future__ import annotations

from urllib.parse import parse_qs


VALID_LAYOUT_MODES = frozenset(("auto", "mobile", "tablet", "desktop"))
RENDERED_LAYOUT_MODES = frozenset(("mobile", "tablet", "desktop"))
DEFAULT_LAYOUT_MODE = "auto"
MOBILE_MAX_WIDTH = 767
TABLET_MAX_WIDTH = 1199


def select_layout_mode(query: str | dict[str, list[str] | str] | None) -> str:
    if query is None:
        return DEFAULT_LAYOUT_MODE

    params = parse_qs(query, keep_blank_values=True) if isinstance(query, str) else query
    value = params.get("layout") if isinstance(params, dict) else None
    if isinstance(value, list):
        selected = value[0] if value else ""
    else:
        selected = value or ""

    mode = str(selected).strip().lower()
    if mode in VALID_LAYOUT_MODES:
        return mode
    return DEFAULT_LAYOUT_MODE


def layout_for_viewport(width: int | float | None) -> str:
    try:
        screen_width = int(width or 0)
    except (TypeError, ValueError):
        screen_width = 0

    if screen_width >= TABLET_MAX_WIDTH + 1:
        return "desktop"
    if screen_width >= MOBILE_MAX_WIDTH + 1:
        return "tablet"
    return "mobile"


def effective_layout_mode(
    preference: str | None,
    *,
    viewport_width: int | float | None = None,
) -> str:
    selected = select_layout_mode({"layout": preference or DEFAULT_LAYOUT_MODE})
    if selected in RENDERED_LAYOUT_MODES:
        return selected
    return layout_for_viewport(viewport_width)
