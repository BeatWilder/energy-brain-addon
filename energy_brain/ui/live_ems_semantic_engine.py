from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SemanticEMSState:
    energy_mode: str
    battery_state: str
    grid_state: str
    solar_state: str
    comfort_state: str
    planner_state: str
    confidence: str
    glow_intensity: str
    timeline_hint: str


def _f(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def build_semantic_state(snapshot: dict[str, Any]) -> SemanticEMSState:

    pv_kw = _f(snapshot.get("sensor.alphaess_current_pv_production")) / 1000
    load_kw = _f(snapshot.get("sensor.alphaess_current_house_load")) / 1000
    battery_w = _f(snapshot.get("sensor.alphaess_power_battery"))
    grid_w = _f(snapshot.get("sensor.alphaess_power_grid"))
    soc = _f(snapshot.get("sensor.alphaess_soc_battery"))

    reserve_soc = _f(
        snapshot.get("sensor.energybrain_required_reserve_soc"),
        25.0,
    )

    dispatch_enabled = (
        str(snapshot.get("input_boolean.alphaess_helper_dispatch", "off")).lower()
        == "on"
    )

    living_presence = (
        str(snapshot.get("binary_sensor.aanwezigheidssensor_woonkamer_occupancy", "off")).lower()
        == "on"
    )

    kitchen_override = (
        str(snapshot.get("input_boolean.ai_ir_override_keuken", "off")).lower()
        == "on"
    )

    cheap_energy = False

    prices = snapshot.get("sensor.energybrain_prices_forecast")

    if isinstance(prices, list) and prices:
        cheap_energy = min(prices) < 0.20

    if pv_kw > load_kw + 0.8:
        energy_mode = "Zonne-overschot benutten"
    elif cheap_energy and soc < 90:
        energy_mode = "Goedkoop energiemoment benutten"
    elif grid_w > 1500:
        energy_mode = "Netafname beperken"
    elif soc <= reserve_soc + 5:
        energy_mode = "Reserve beschermen"
    else:
        energy_mode = "Energie balanceren"

    if battery_w < -500:
        battery_state = "Batterij laadt actief"
    elif battery_w > 500:
        battery_state = "Batterij voedt woning"
    else:
        battery_state = "Batterij stand-by"

    if grid_w > 300:
        grid_state = "Import van net"
    elif grid_w < -300:
        grid_state = "Export naar net"
    else:
        grid_state = "Net vrijwel neutraal"

    if pv_kw > 3:
        solar_state = "Sterke zonneproductie"
    elif pv_kw > 0.5:
        solar_state = "Normale zonneproductie"
    else:
        solar_state = "Weinig zonneproductie"

    if living_presence and kitchen_override:
        comfort_state = "Comfort prioriteit actief"
    elif living_presence:
        comfort_state = "Woning actief gebruikt"
    else:
        comfort_state = "Comfort in eco-balans"

    if dispatch_enabled:
        planner_state = "EMS dispatch actief"
    elif cheap_energy:
        planner_state = "Planner bewaakt goedkoop venster"
    else:
        planner_state = "Planner observeert"

    telemetry_score = 0

    required = [
        "sensor.alphaess_soc_battery",
        "sensor.alphaess_power_battery",
        "sensor.alphaess_power_grid",
        "sensor.alphaess_current_pv_production",
        "sensor.alphaess_current_house_load",
    ]

    for entity in required:
        if snapshot.get(entity) not in [None, "unknown", "unavailable"]:
            telemetry_score += 1

    if telemetry_score >= 5:
        confidence = "Hoog"
    elif telemetry_score >= 3:
        confidence = "Gemiddeld"
    else:
        confidence = "Laag"

    total_flow = abs(pv_kw) + abs(load_kw) + abs(grid_w / 1000)

    if total_flow > 8:
        glow_intensity = "ultra"
    elif total_flow > 4:
        glow_intensity = "high"
    elif total_flow > 1:
        glow_intensity = "medium"
    else:
        glow_intensity = "low"

    if cheap_energy:
        timeline_hint = "Goedkoop laadmoment verwacht"
    elif pv_kw > 2:
        timeline_hint = "PV-overschot beschikbaar"
    elif soc < reserve_soc + 10:
        timeline_hint = "Reserve-opbouw aanbevolen"
    else:
        timeline_hint = "Normale EMS horizon"

    return SemanticEMSState(
        energy_mode=energy_mode,
        battery_state=battery_state,
        grid_state=grid_state,
        solar_state=solar_state,
        comfort_state=comfort_state,
        planner_state=planner_state,
        confidence=confidence,
        glow_intensity=glow_intensity,
        timeline_hint=timeline_hint,
    )
