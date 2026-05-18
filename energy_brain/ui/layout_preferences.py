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
        "auto": "Automatic device detection",
        "desktop": "Desktop mission control layout",
        "tablet": "Tablet control panel layout",
        "mobile": "Mobile operator companion layout",
    }

    return descriptions[mode]
