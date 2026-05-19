from __future__ import annotations

VALID_LAYOUTS = {
    "mobile",
    "tablet",
    "workstation",
}


def normalize_layout_profile(value: str | None) -> str:
    if not value:
        return "tablet"

    value = str(value).strip().lower()

    if value not in VALID_LAYOUTS:
        return "tablet"

    return value
