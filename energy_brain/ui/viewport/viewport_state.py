from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs

from energy_brain.ui.viewport.viewport_breakpoints import (
    BREAKPOINTS,
    DEFAULT_VIEWPORT_MODE,
    RENDERED_VIEWPORT_MODES,
    VALID_VIEWPORT_MODES,
    ViewportBreakpoints,
    classify_viewport_width,
)


@dataclass(frozen=True)
class ViewportState:
    preference: str
    mode: str
    breakpoints: ViewportBreakpoints = BREAKPOINTS

    @property
    def css_class(self) -> str:
        return f"layout-{self.mode}"

    @property
    def density(self) -> str:
        if self.mode == "desktop":
            return "command"
        if self.mode == "tablet":
            return "operational"
        return "native"

    def as_dict(self) -> dict[str, object]:
        return {
            "preference": self.preference,
            "mode": self.mode,
            "density": self.density,
            "mobile_first": True,
            "breakpoints": self.breakpoints.as_dict(),
        }


def select_viewport_preference(query: str | dict[str, list[str] | str] | None) -> str:
    if query is None:
        return DEFAULT_VIEWPORT_MODE

    params = parse_qs(query, keep_blank_values=True) if isinstance(query, str) else query
    value = params.get("layout") if isinstance(params, dict) else None
    if isinstance(value, list):
        selected = value[0] if value else ""
    else:
        selected = value or ""

    mode = str(selected).strip().lower()
    if mode in VALID_VIEWPORT_MODES:
        return mode
    return DEFAULT_VIEWPORT_MODE


def build_viewport_state(
    preference: str | None,
    *,
    viewport_width: int | float | None = None,
    breakpoints: ViewportBreakpoints = BREAKPOINTS,
) -> ViewportState:
    selected = select_viewport_preference({"layout": preference or DEFAULT_VIEWPORT_MODE})
    mode = selected if selected in RENDERED_VIEWPORT_MODES else classify_viewport_width(viewport_width, breakpoints=breakpoints)
    return ViewportState(preference=selected, mode=mode, breakpoints=breakpoints)
