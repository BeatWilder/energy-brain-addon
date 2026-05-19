from __future__ import annotations

from dataclasses import dataclass


VALID_VIEWPORT_MODES = frozenset(("auto", "mobile", "tablet", "desktop"))
RENDERED_VIEWPORT_MODES = frozenset(("mobile", "tablet", "desktop"))
DEFAULT_VIEWPORT_MODE = "auto"


@dataclass(frozen=True)
class ViewportBreakpoints:
    mobile_max: int = 767
    tablet_max: int = 1199

    @property
    def tablet_min(self) -> int:
        return self.mobile_max + 1

    @property
    def desktop_min(self) -> int:
        return self.tablet_max + 1

    def as_dict(self) -> dict[str, int]:
        return {
            "mobile_max": self.mobile_max,
            "tablet_min": self.tablet_min,
            "tablet_max": self.tablet_max,
            "desktop_min": self.desktop_min,
        }


BREAKPOINTS = ViewportBreakpoints()


def classify_viewport_width(
    width: int | float | None,
    *,
    breakpoints: ViewportBreakpoints = BREAKPOINTS,
) -> str:
    try:
        screen_width = int(width or 0)
    except (TypeError, ValueError):
        screen_width = 0

    if screen_width >= breakpoints.desktop_min:
        return "desktop"
    if screen_width >= breakpoints.tablet_min:
        return "tablet"
    return "mobile"
