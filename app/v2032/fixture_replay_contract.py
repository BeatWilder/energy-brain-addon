"""Offline fixture replay contract for strategy comparison.

This module converts neutral fixture dictionaries into the Energy Brain-owned
simulation contract. It has no integration runtime dependencies and cannot
authorize execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.v2000.predbat_lesson_simulation_contract import BatteryPhysics, EnergySlot, SimulationInput


@dataclass(frozen=True)
class FixtureReplayLoadResult:
    valid: bool
    simulation_input: SimulationInput | None = None
    errors: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ("offline_fixture_replay", "observer_only_no_execution")


def build_simulation_input(fixture: Mapping[str, Any] | SimulationInput) -> FixtureReplayLoadResult:
    """Build a SimulationInput from a neutral offline fixture.

    The accepted fixture shape is:

    {
        "slots": [{"slot_id": "s0", "pv_kwh": 0.0, "load_kwh": 1.0, ...}],
        "battery": {"capacity_kwh": 10.0, ...},
        "observer_only": True,
    }
    """

    if isinstance(fixture, SimulationInput):
        if not fixture.observer_only:
            return _invalid("observer_only_required")
        return FixtureReplayLoadResult(valid=True, simulation_input=fixture)

    if not isinstance(fixture, Mapping):
        return _invalid("fixture_mapping_required")

    battery_data = fixture.get("battery")
    slots_data = fixture.get("slots")
    if not isinstance(battery_data, Mapping):
        return _invalid("battery_mapping_required")
    if not isinstance(slots_data, (list, tuple)):
        return _invalid("slots_sequence_required")

    try:
        battery = BatteryPhysics(
            capacity_kwh=_float_field(battery_data, "capacity_kwh"),
            min_soc_kwh=_float_field(battery_data, "min_soc_kwh"),
            max_soc_kwh=_float_field(battery_data, "max_soc_kwh"),
            initial_soc_kwh=_float_field(battery_data, "initial_soc_kwh"),
            reserve_kwh=_float_field(battery_data, "reserve_kwh"),
            charge_power_kw=_float_field(battery_data, "charge_power_kw"),
            discharge_power_kw=_float_field(battery_data, "discharge_power_kw"),
            round_trip_efficiency=_float_field(battery_data, "round_trip_efficiency"),
        )
        slots = tuple(_energy_slot(index, slot_data) for index, slot_data in enumerate(slots_data))
    except (TypeError, ValueError, KeyError) as exc:
        return _invalid(_clean_error(exc))

    observer_only = fixture.get("observer_only", True)
    if observer_only is not True:
        return _invalid("observer_only_required")

    return FixtureReplayLoadResult(
        valid=True,
        simulation_input=SimulationInput(slots=slots, battery=battery, observer_only=True),
    )


def _energy_slot(index: int, slot_data: Any) -> EnergySlot:
    if not isinstance(slot_data, Mapping):
        raise TypeError(f"slot_{index}_mapping_required")
    return EnergySlot(
        slot_id=str(slot_data.get("slot_id", f"slot_{index}")),
        pv_kwh=_float_field(slot_data, "pv_kwh"),
        load_kwh=_float_field(slot_data, "load_kwh"),
        import_price_per_kwh=_float_field(slot_data, "import_price_per_kwh", default=0.0),
        export_price_per_kwh=_float_field(slot_data, "export_price_per_kwh", default=0.0),
        duration_hours=_float_field(slot_data, "duration_hours", default=1.0),
    )


def _float_field(data: Mapping[str, Any], key: str, *, default: float | None = None) -> float:
    if key not in data:
        if default is None:
            raise KeyError(f"{key}_required")
        return default
    value = data[key]
    if isinstance(value, bool):
        raise TypeError(f"{key}_must_be_number")
    return float(value)


def _invalid(error: str) -> FixtureReplayLoadResult:
    return FixtureReplayLoadResult(
        valid=False,
        errors=(error,),
        reason_codes=("invalid_fixture_no_action", "observer_only_no_execution"),
    )


def _clean_error(exc: BaseException) -> str:
    text = str(exc).strip("'")
    return text or exc.__class__.__name__


__all__ = ["FixtureReplayLoadResult", "build_simulation_input"]

