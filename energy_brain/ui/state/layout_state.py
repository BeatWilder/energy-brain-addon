from __future__ import annotations

from energy_brain.ui.viewport.viewport_breakpoints import (
    DEFAULT_VIEWPORT_MODE,
    VALID_VIEWPORT_MODES,
    ViewportBreakpoints,
    classify_viewport_width,
)
from energy_brain.ui.viewport.viewport_state import (
    build_viewport_state,
    select_viewport_preference,
)


VALID_LAYOUT_MODES = VALID_VIEWPORT_MODES
RENDERED_LAYOUT_MODES = frozenset(("mobile", "tablet", "desktop"))
DEFAULT_LAYOUT_MODE = DEFAULT_VIEWPORT_MODE
_BREAKPOINTS = ViewportBreakpoints()
MOBILE_MAX_WIDTH = _BREAKPOINTS.mobile_max
TABLET_MAX_WIDTH = _BREAKPOINTS.tablet_max


def select_layout_mode(query: str | dict[str, list[str] | str] | None) -> str:
    return select_viewport_preference(query)


def layout_for_viewport(width: int | float | None) -> str:
    return classify_viewport_width(width)


def effective_layout_mode(
    preference: str | None,
    *,
    viewport_width: int | float | None = None,
) -> str:
    return build_viewport_state(preference, viewport_width=viewport_width).mode
