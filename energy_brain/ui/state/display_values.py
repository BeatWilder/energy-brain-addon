from __future__ import annotations

import math
from typing import Any


UNKNOWN_LABEL = "unavailable"
MAX_DISPLAY_POWER_KW = 30.0


def number_or_none(value: Any) -> float | None:
    if value in (None, "", "unknown", "unavailable", "none", "None", "—"):
        return None
    try:
        number = float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def sanitize_power_kw(
    value: Any,
    *,
    max_abs_kw: float = MAX_DISPLAY_POWER_KW,
    pv_generation: bool = False,
) -> dict[str, Any]:
    number = number_or_none(value)
    if number is None:
        return {"value": 0.0, "label": UNKNOWN_LABEL, "known": False, "clamped": False}

    if pv_generation:
        number = abs(number)

    clamped = abs(number) > max_abs_kw
    if clamped:
        number = max_abs_kw if number > 0 else -max_abs_kw

    return {
        "value": round(number, 3),
        "label": f"{number:.1f} kW",
        "known": True,
        "clamped": clamped,
    }


def sanitize_percent(value: Any) -> dict[str, Any]:
    number = number_or_none(value)
    if number is None:
        return {"value": 0.0, "label": UNKNOWN_LABEL, "known": False, "clamped": False}

    clamped = number < 0 or number > 100
    number = min(100.0, max(0.0, number))
    return {
        "value": round(number, 1),
        "label": f"{number:.0f}%",
        "known": True,
        "clamped": clamped,
    }


def power_intensity(value: Any, *, max_reference_kw: float = 8.0) -> float:
    number = abs(number_or_none(value) or 0.0)
    return round(min(1.0, number / max_reference_kw), 3)
