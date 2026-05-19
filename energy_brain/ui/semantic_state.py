from __future__ import annotations

from typing import Any


UNKNOWN = "onbekend"

CANONICAL_ENTITIES: dict[str, str] = {
    "battery_soc_percent": "sensor.alphaess_soc_battery",
    "battery_power_kw": "sensor.alphaess_power_battery",
    "battery_usable_capacity": "sensor.energy_model_battery_usable_capacity",
    "battery_soft_reserve_soc": "sensor.battery_soft_reserve_soc",
    "battery_required_reserve_soc": "sensor.energybrain_required_reserve_soc",
    "battery_hard_floor_soc": "sensor.battery_hard_floor_soc",
    "grid_power_kw": "sensor.alphaess_power_grid",
    "grid_phase_a_kw": "sensor.alphaess_power_phase_a_grid",
    "grid_phase_b_kw": "sensor.alphaess_power_phase_b_grid",
    "grid_phase_c_kw": "sensor.alphaess_power_phase_c_grid",
    "pv_power_kw": "sensor.alphaess_current_pv_production",
    "pv_forecast_now_kw": "sensor.solcast_pv_forecast_power_now",
    "pv_forecast_30m_kw": "sensor.solcast_pv_forecast_power_in_30_minutes",
    "pv_forecast_1h_kw": "sensor.solcast_pv_forecast_power_in_1_hour",
    "pv_forecast_today": "sensor.solcast_pv_forecast_forecast_today",
    "pv_forecast_tomorrow": "sensor.solcast_pv_forecast_forecast_tomorrow",
    "household_load_kw": "sensor.alphaess_current_house_load",
    "nordpool_price": "sensor.nordpool_kwh_nl_eur_3_10_021",
    "grid_price": "sensor.current_electricity_market_price",
    "prices_forecast": "sensor.energybrain_prices_forecast",
    "dispatch_enabled": "input_boolean.alphaess_helper_dispatch",
    "dispatch_power": "input_number.alphaess_helper_dispatch_power",
    "dispatch_duration": "input_number.alphaess_helper_dispatch_duration",
    "dispatch_cutoff_soc": "input_number.alphaess_helper_dispatch_cutoff_soc",
    "dispatch_mode": "input_select.alphaess_helper_dispatch_mode",
    "climate_living": "climate.ir_woonkamer",
    "climate_kitchen": "climate.w100_keuken",
    "ir_override_living": "input_boolean.ai_ir_override_woonkamer",
    "ir_override_kitchen": "input_boolean.ai_ir_override_keuken",
    "ir_gate": "sensor.energybrain_ir_gate",
    "heating_allowed": "binary_sensor.verwarming_mag_nu_op_energie",
    "presence_app": "binary_sensor.iemand_thuis_app",
    "presence_ping": "binary_sensor.iemand_thuis_ping",
    "presence_kitchen": "binary_sensor.keuken_bezet_stabiel",
    "presence_living": "binary_sensor.aanwezigheidssensor_woonkamer_occupancy",
    "battery_foundation_status": "sensor.ai_battery_foundation_status",
    "battery_charge_reason": "sensor.ai_battery_charge_reason",
    "battery_gate": "sensor.energybrain_battery_gate",
    "charge_window_active": "binary_sensor.battery_charge_window_active_clean",
}


def _missing(value: Any) -> bool:
    return value in (None, "", "unknown", "unavailable", "none", "None", "—")


def _num(value: Any) -> float | None:
    if isinstance(value, dict):
        value = value.get("state", value.get("value"))
    if _missing(value):
        return None
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _text(value: Any, default: str = UNKNOWN) -> str:
    if isinstance(value, dict):
        value = value.get("state", value.get("value"))
    if _missing(value):
        return default
    return str(value)


def _state(entity_states: dict[str, Any], entity_id: str) -> Any:
    value = entity_states.get(entity_id)
    if isinstance(value, dict):
        return value.get("state", value.get("value"))
    return value


def _kw_from_entity(value: Any) -> float | None:
    number = _num(value)
    if number is None:
        return None
    if abs(number) > 50:
        return number / 1000.0
    return number


def canonical_values_from_entities(entity_states: dict[str, Any]) -> dict[str, Any]:
    """Map known Home Assistant entities to canonical UI payload fields.

    Unknown or unavailable states are omitted so downstream UI remains degraded
    instead of receiving fabricated defaults.
    """
    mapped: dict[str, Any] = {}
    for key, entity_id in CANONICAL_ENTITIES.items():
        value = _state(entity_states, entity_id)
        if _missing(value):
            continue
        if key.endswith("_kw"):
            mapped[key] = _kw_from_entity(value)
        else:
            mapped[key] = value
    return mapped


def merge_entity_values(payload: dict[str, Any], entity_states: dict[str, Any]) -> dict[str, Any]:
    mapped = canonical_values_from_entities(entity_states)
    object_values = {
        key: entity_states[entity_id]
        for key, entity_id in CANONICAL_ENTITIES.items()
        if key in {"climate_living", "climate_kitchen"} and isinstance(entity_states.get(entity_id), dict)
    }
    merged = dict(payload)
    for key, value in mapped.items():
        merged[key] = value
    if "battery_soc_percent" in mapped:
        merged["soc_percent"] = mapped["battery_soc_percent"]
    if "pv_power_kw" in mapped:
        merged["pv_now_kw"] = mapped["pv_power_kw"]
    if "household_load_kw" in mapped:
        merged["home_load_kw"] = mapped["household_load_kw"]
    if "grid_price" in mapped:
        merged["price_now"] = mapped["grid_price"]
    merged["canonical_entities"] = dict(CANONICAL_ENTITIES)
    merged["canonical_entity_values"] = mapped
    merged["canonical_entity_objects"] = object_values
    return merged


def build_semantic_state(payload: dict[str, Any]) -> dict[str, Any]:
    soc = _num(payload.get("battery_soc_percent") or payload.get("soc_percent"))
    battery_kw = _num(payload.get("battery_power_kw"))
    pv_kw = _num(payload.get("pv_power_kw") or payload.get("pv_now_kw"))
    load_kw = _num(payload.get("household_load_kw") or payload.get("home_load_kw"))
    grid_kw = _num(payload.get("grid_power_kw"))
    price = _num(payload.get("grid_price") or payload.get("price_now"))
    reserve = (
        _num(payload.get("battery_required_reserve_soc"))
        or _num(payload.get("reserve_percent"))
        or _num(payload.get("battery_soft_reserve_soc"))
    )
    hard_floor = _num(payload.get("battery_hard_floor_soc"))
    charge_window = _text(payload.get("charge_window_active"), "").lower()
    battery_gate = _text(payload.get("battery_gate"), UNKNOWN)
    foundation = _text(payload.get("battery_foundation_status"), UNKNOWN)
    charge_reason = _text(payload.get("battery_charge_reason"), "")

    if soc is None:
        reserve_state = "Reserve onbekend"
    else:
        floor = max(value for value in (reserve, hard_floor, 0.0) if value is not None)
        reserve_state = "Hard floor actief" if soc <= floor else "Reserve beschermd"

    if battery_kw is None:
        battery_strategy = "Batterijstrategie onbekend"
    elif battery_kw > 0.05:
        battery_strategy = "Batterij laadt"
    elif battery_kw < -0.05:
        battery_strategy = "Batterij voedt huis"
    elif "on" in charge_window or "active" in charge_window:
        battery_strategy = "Laadvenster bewaakt"
    else:
        battery_strategy = "Batterij houdt vast"

    if pv_kw is None:
        solar_state = "Zon onbekend"
    elif load_kw is not None and pv_kw > load_kw + 0.15:
        solar_state = "Zonne-overschot"
    elif pv_kw > 0.1:
        solar_state = "Zon dekt mee"
    else:
        solar_state = "Weinig zon"

    if grid_kw is None:
        grid_dependency = "Net onbekend"
    elif grid_kw > 0.05:
        grid_dependency = "Netimport"
    elif grid_kw < -0.05:
        grid_dependency = "Teruglevering"
    else:
        grid_dependency = "Net in balans"

    if price is not None and price >= 0.32:
        energy_mode = "Dure neturen vermijden"
    elif solar_state == "Zonne-overschot":
        energy_mode = "Zonne-overschot benutten"
    elif reserve_state != "Reserve beschermd":
        energy_mode = "Reserve beschermen"
    elif price is not None and price <= 0.08:
        energy_mode = "Goedkope energie bewaken"
    else:
        energy_mode = "Autonoom balanceren"

    overrides = [
        _text(payload.get("ir_override_living"), "").lower(),
        _text(payload.get("ir_override_kitchen"), "").lower(),
    ]
    occupied = any(
        _text(payload.get(key), "").lower() in {"on", "home", "true", "detected", "occupied"}
        for key in ("presence_app", "presence_ping", "presence_kitchen", "presence_living")
    )
    heating_allowed = _text(payload.get("heating_allowed"), "").lower()
    ir_gate = _text(payload.get("ir_gate"), UNKNOWN)
    if any(value == "on" for value in overrides):
        comfort_mode = "AI override actief"
    elif occupied:
        comfort_mode = "Comfort bewaakt"
    else:
        comfort_mode = "Aanwezigheid onbekend" if all(_missing(payload.get(key)) for key in ("presence_app", "presence_ping", "presence_kitchen", "presence_living")) else "Afwezig / laag comfort"
    if heating_allowed == "on":
        thermal_strategy = "Verwarmen mag op energie"
    elif ir_gate != UNKNOWN:
        thermal_strategy = f"IR gate: {ir_gate}"
    else:
        thermal_strategy = UNKNOWN

    dispatch_on = _text(payload.get("dispatch_enabled"), "").lower()
    dispatch_mode = _text(payload.get("dispatch_mode"), UNKNOWN)
    if dispatch_on == "on":
        dispatch_state = f"Helper actief ({dispatch_mode})" if dispatch_mode != UNKNOWN else "Helper actief"
    elif dispatch_on == "off":
        dispatch_state = "Helper uit"
    else:
        dispatch_state = "Dispatch onbekend"

    forecast_confidence = payload.get("forecast_confidence") or ("beperkt" if payload.get("degraded") else "actief")
    planner_confidence = "beperkt" if payload.get("degraded") else "actief"

    return {
        "schema_version": "energy_brain.semantic_state.v1",
        "energy_mode": energy_mode,
        "battery_strategy": battery_strategy,
        "grid_dependency": grid_dependency,
        "solar_state": solar_state,
        "comfort_mode": comfort_mode,
        "thermal_strategy": thermal_strategy,
        "planner_confidence": planner_confidence,
        "forecast_confidence": forecast_confidence,
        "reserve_state": reserve_state,
        "next_expensive_window": UNKNOWN,
        "dispatch_state": dispatch_state,
        "battery_gate": battery_gate,
        "battery_foundation_status": foundation,
        "battery_charge_reason": charge_reason or UNKNOWN,
        "living_state": energy_mode,
    }
