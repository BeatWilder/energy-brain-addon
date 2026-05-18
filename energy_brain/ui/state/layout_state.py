from __future__ import annotations

from urllib.parse import parse_qs


VALID_LAYOUT_MODES = frozenset(("mobile", "tablet", "desktop"))
DEFAULT_LAYOUT_MODE = "desktop"


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

