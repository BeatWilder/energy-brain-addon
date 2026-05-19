from __future__ import annotations

from typing import Any

from energy_brain.ui.state.display_values import power_intensity


MAX_REFERENCE_KW = 8.0


def _num(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _known(section: dict[str, Any], key: str) -> bool:
    return section.get(key) is not False


def _direction(value: float, positive: str, negative: str) -> str:
    if value > 0.05:
        return positive
    if value < -0.05:
        return negative
    return "idle"


def _flow_vars(intensity: float) -> dict[str, str]:
    speed = max(1.15, 5.2 - intensity * 3.25)
    density = 0 if intensity <= 0.01 else 1 + int(intensity >= 0.25) + int(intensity >= 0.58) + int(intensity >= 0.82)
    return {
        "intensity": f"{intensity:.3f}",
        "speed": f"{speed:.2f}s",
        "density": str(density),
        "glow": f"{0.14 + intensity * 0.72:.3f}",
        "thickness": f"{5.0 + intensity * 8.0:.2f}",
    }


def _lane(
    *,
    lane_id: str,
    path_id: str,
    path: str,
    kw: float,
    state: str,
    tone: str,
) -> dict[str, Any]:
    intensity = power_intensity(kw, max_reference_kw=MAX_REFERENCE_KW)
    return {
        "id": lane_id,
        "path_id": path_id,
        "path": path,
        "kw": round(abs(kw), 3),
        "state": state,
        "tone": tone,
        "active": state != "idle" and intensity > 0,
        "vars": _flow_vars(intensity),
    }


def _house_mix(solar_kw: float, battery_kw: float, grid_kw: float, house_kw: float) -> list[dict[str, Any]]:
    if house_kw <= 0.05:
        return [{"source": "idle", "share": 1.0, "color": "rgba(255,255,255,0.16)"}]

    solar = min(max(solar_kw, 0.0), house_kw)
    battery = min(max(-battery_kw, 0.0), max(0.0, house_kw - solar))
    grid = min(max(grid_kw, 0.0), max(0.0, house_kw - solar - battery))
    remaining = max(0.0, house_kw - solar - battery - grid)
    if remaining > 0.01:
        grid += remaining

    colors = {
        "solar": "#ffd166",
        "battery": "#7fc7ff",
        "grid": "#ff8b5f",
    }
    parts = [
        ("solar", solar),
        ("battery", battery),
        ("grid", grid),
    ]
    mix = [
        {"source": source, "share": round(value / house_kw, 3), "color": colors[source]}
        for source, value in parts
        if value > 0.01
    ]
    return mix or [{"source": "unknown", "share": 1.0, "color": "rgba(255,255,255,0.18)"}]


def _mix_gradient(mix: list[dict[str, Any]]) -> str:
    cursor = 0.0
    stops: list[str] = []
    for item in mix:
        start = cursor
        cursor = min(1.0, cursor + float(item["share"]))
        color = item["color"]
        stops.append(f"{color} {start * 100:.1f}% {cursor * 100:.1f}%")
    return ", ".join(stops)


def build_powerflow_scene(section: dict[str, Any]) -> dict[str, Any]:
    solar_kw = _num(section.get("solar_kw"))
    house_kw = _num(section.get("house_kw"))
    battery_kw = _num(section.get("battery_kw"))
    grid_kw = _num(section.get("grid_kw"))
    soc = max(0.0, min(100.0, _num(section.get("soc_percent"))))

    battery_state = _direction(battery_kw, "charging", "discharging")
    grid_state = _direction(grid_kw, "importing", "exporting")
    house_state = "consuming" if house_kw > 0.05 else "idle"
    solar_state = "generating" if solar_kw > 0.05 else "idle"
    scene_intensity = max(
        power_intensity(solar_kw),
        power_intensity(house_kw),
        power_intensity(battery_kw),
        power_intensity(grid_kw),
    )
    mix = _house_mix(solar_kw, battery_kw, grid_kw, house_kw)

    return {
        "schema_version": "energy_brain.ui.powerflow_scene.v2",
        "scene_intensity": round(scene_intensity, 3),
        "battery_state": battery_state,
        "grid_state": grid_state,
        "house_mix": mix,
        "house_mix_gradient": _mix_gradient(mix),
        "lanes": [
            _lane(
                lane_id="solar-home",
                path_id="pf-path-solar",
                path="M 210 58 C 210 108, 210 148, 210 184",
                kw=solar_kw,
                state=solar_state,
                tone="solar",
            ),
            _lane(
                lane_id="battery-home",
                path_id="pf-path-battery",
                path="M 72 210 C 122 210, 148 210, 184 210",
                kw=battery_kw,
                state=battery_state,
                tone="battery",
            ),
            _lane(
                lane_id="home-grid",
                path_id="pf-path-grid",
                path="M 236 210 C 274 210, 304 210, 352 210",
                kw=grid_kw,
                state=grid_state,
                tone="grid",
            ),
            _lane(
                lane_id="home-load",
                path_id="pf-path-load",
                path="M 210 236 C 210 276, 210 310, 210 360",
                kw=house_kw,
                state=house_state,
                tone="home",
            ),
        ],
        "nodes": {
            "solar": {
                "state": solar_state,
                "known": _known(section, "solar_known"),
                "kw": solar_kw,
                "intensity": power_intensity(solar_kw),
                "ring": "var(--solar)",
            },
            "home": {
                "state": house_state,
                "known": _known(section, "house_known"),
                "kw": house_kw,
                "intensity": power_intensity(house_kw),
                "ring": _mix_gradient(mix),
            },
            "battery": {
                "state": battery_state,
                "known": _known(section, "battery_known"),
                "kw": battery_kw,
                "intensity": power_intensity(battery_kw),
                "soc": soc,
                "ring": "var(--battery)" if battery_state == "charging" else "var(--grid)",
            },
            "grid": {
                "state": grid_state,
                "known": _known(section, "grid_known"),
                "kw": grid_kw,
                "intensity": power_intensity(grid_kw),
                "ring": "var(--import)" if grid_state == "importing" else "var(--export)",
            },
        },
    }
