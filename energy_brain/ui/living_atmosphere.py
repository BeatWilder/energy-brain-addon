from __future__ import annotations

from typing import Any


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def build_living_atmosphere(snapshot: dict[str, Any]) -> dict[str, Any]:
    pv_kw = float(snapshot.get("pv_kw", 0.0) or 0.0)
    battery_kw = float(snapshot.get("battery_kw", 0.0) or 0.0)
    grid_kw = float(snapshot.get("grid_kw", 0.0) or 0.0)
    load_kw = float(snapshot.get("load_kw", 0.0) or 0.0)

    total_activity = abs(pv_kw) + abs(battery_kw) + abs(grid_kw) + abs(load_kw)

    energy_intensity = clamp(total_activity / 12.0, 0.15, 1.0)

    if pv_kw >= 3.5:
        solar_mood = "solar_peak"
        solar_glow = "#ffd34d"
    elif pv_kw >= 1.5:
        solar_mood = "solar_active"
        solar_glow = "#ffbf3f"
    else:
        solar_mood = "solar_low"
        solar_glow = "#665c2f"

    if battery_kw <= -0.4:
        battery_state = "charging"
        battery_glow = "#4de1ff"
    elif battery_kw >= 0.4:
        battery_state = "discharging"
        battery_glow = "#7effa1"
    else:
        battery_state = "idle"
        battery_glow = "#7a8a99"

    if grid_kw > 0.5:
        grid_state = "import"
        grid_glow = "#ff8a65"
    elif grid_kw < -0.5:
        grid_state = "export"
        grid_glow = "#57d9a3"
    else:
        grid_state = "balanced"
        grid_glow = "#8ea0b5"

    dashboard_brightness = clamp(
        0.35 + (pv_kw / 8.0) + (energy_intensity * 0.3),
        0.25,
        1.0,
    )

    atmosphere = {
        "energy_intensity": round(energy_intensity, 2),
        "dashboard_brightness": round(dashboard_brightness, 2),
        "solar_mood": solar_mood,
        "solar_glow": solar_glow,
        "battery_state": battery_state,
        "battery_glow": battery_glow,
        "grid_state": grid_state,
        "grid_glow": grid_glow,
        "background_opacity": round(
            clamp(0.55 + energy_intensity * 0.25, 0.55, 0.92),
            2,
        ),
        "glass_blur": round(
            clamp(18 + total_activity * 1.5, 18, 42),
            1,
        ),
        "flow_glow_strength": round(
            clamp(total_activity / 10.0, 0.2, 1.0),
            2,
        ),
    }

    return atmosphere
