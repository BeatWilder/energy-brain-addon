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


def resolve_layout_profile(
    request_args: dict | None = None,
) -> str:
    request_args = request_args or {}

    requested = request_args.get("layout")

    return normalize_layout_profile(requested)


# --------------------------------------------------
# BACKWARD COMPATIBILITY
# renderer.py verwacht deze functie nog steeds
# --------------------------------------------------

def build_layout_view(*args, **kwargs):
    return {
        "layout_profile": "tablet",
        "args": args,
        "kwargs": kwargs,
    }
