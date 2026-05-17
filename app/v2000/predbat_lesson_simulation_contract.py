"""Offline simulation contract inspired by Predbat lessons.

This module defines Energy Brain-owned data structures for deterministic
offline simulations. It has no Home Assistant runtime dependency and never
permits execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EnergySlot:
    """Normalized per-slot energy input in kWh."""

    slot_id: str
    pv_kwh: float
    load_kwh: float
    import_price_per_kwh: float = 0.0
    export_price_per_kwh: float = 0.0
    duration_hours: float = 1.0


@dataclass(frozen=True)
class BatteryPhysics:
    """Battery limits used by the offline simulator."""

    capacity_kwh: float
    min_soc_kwh: float
    max_soc_kwh: float
    initial_soc_kwh: float
    reserve_kwh: float
    charge_power_kw: float
    discharge_power_kw: float
    round_trip_efficiency: float


@dataclass(frozen=True)
class SimulationInput:
    """Pure offline simulator input.

    observer_only must remain true so results are explicitly advisory.
    """

    slots: tuple[EnergySlot, ...]
    battery: BatteryPhysics
    observer_only: bool = True


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class SlotTrace:
    slot_id: str
    soc_start_kwh: float
    soc_end_kwh: float
    pv_kwh: float
    load_kwh: float
    pv_to_load_kwh: float
    pv_to_battery_kwh: float
    battery_to_load_kwh: float
    import_kwh: float
    export_kwh: float
    battery_power_kw: float
    cost: float
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class SimulationResult:
    valid: bool
    observer_only: bool
    execution_allowed: bool
    total_import_kwh: float = 0.0
    total_export_kwh: float = 0.0
    total_cost: float = 0.0
    final_soc_kwh: float = 0.0
    trace: tuple[SlotTrace, ...] = ()
    errors: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = field(default_factory=lambda: ("observer_only_no_execution",))


def validate_simulation_input(simulation_input: SimulationInput) -> ValidationResult:
    """Validate an offline simulation request."""

    errors: list[str] = []
    battery = simulation_input.battery

    if not simulation_input.observer_only:
        errors.append("observer_only_required")
    if not simulation_input.slots:
        errors.append("slots_required")

    if battery.capacity_kwh <= 0:
        errors.append("capacity_must_be_positive")
    if battery.min_soc_kwh < 0:
        errors.append("min_soc_must_be_non_negative")
    if battery.max_soc_kwh > battery.capacity_kwh:
        errors.append("max_soc_above_capacity")
    if battery.min_soc_kwh > battery.max_soc_kwh:
        errors.append("min_soc_above_max_soc")
    if not battery.min_soc_kwh <= battery.initial_soc_kwh <= battery.max_soc_kwh:
        errors.append("initial_soc_outside_bounds")
    if not battery.min_soc_kwh <= battery.reserve_kwh <= battery.max_soc_kwh:
        errors.append("reserve_outside_bounds")
    if battery.charge_power_kw < 0:
        errors.append("charge_power_must_be_non_negative")
    if battery.discharge_power_kw < 0:
        errors.append("discharge_power_must_be_non_negative")
    if not 0 < battery.round_trip_efficiency <= 1:
        errors.append("efficiency_must_be_above_zero_and_at_most_one")

    for index, slot in enumerate(simulation_input.slots):
        prefix = f"slot_{index}"
        if slot.pv_kwh < 0:
            errors.append(f"{prefix}_pv_must_be_non_negative")
        if slot.load_kwh < 0:
            errors.append(f"{prefix}_load_must_be_non_negative")
        if slot.duration_hours <= 0:
            errors.append(f"{prefix}_duration_must_be_positive")

    return ValidationResult(valid=not errors, errors=tuple(errors))


def no_action_result(errors: tuple[str, ...]) -> SimulationResult:
    """Return a deterministic result for rejected offline simulation input."""

    return SimulationResult(
        valid=False,
        observer_only=True,
        execution_allowed=False,
        errors=errors,
        reason_codes=("invalid_input_no_action", "observer_only_no_execution"),
    )
