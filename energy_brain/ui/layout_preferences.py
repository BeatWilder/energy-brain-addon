from __future__ import annotations

from typing import Literal

LayoutMode = Literal[
    "auto",
    "desktop",
    "tablet",
    "mobile",
]


DEFAULT_LAYOUT_MODE: LayoutMode = "auto"


def normalize_layout_mode(value: str | None) -> LayoutMode:
    allowed = {
        "auto",
        "desktop",
        "tablet",
        "mobile",
    }

    if value in allowed:
        return value  # type: ignore[return-value]

    return DEFAULT_LAYOUT_MODE


def get_layout_description(mode: LayoutMode) -> str:
    descriptions = {
        "auto": "Automatische apparaatdetectie",
        "desktop": "Desktop command center",
        "tablet": "Tablet bedienpaneel",
        "mobile": "Mobiele cockpit",
    }

    return descriptions[mode]
