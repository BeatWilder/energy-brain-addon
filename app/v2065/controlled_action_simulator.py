"""Controlled offline action-intent simulator.

The simulator evaluates candidate actions against battery constraints and
returns advisory traces only. It has no integration-facing execution surface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from app.v2000.predbat_lesson_simulation_contract import (
    SimulationInput,
    validate_simulation_input,
)
from app.v2032.fixture_replay_contract import build_simulation_input
from app.v2064.action_intent_contract import ActionIntent, validate_action_intents


@dataclass(frozen=True)
class ControlledSlotTrace:
    slot_index: int
    slot_id: str
    action_type_applied: str
    requested_energy_kwh: float
    clipped_energy_kwh: float
    soc_start_kwh: float
    soc_end_kwh: float
    grid_import_kwh: float
    grid_export_kwh: float
    load_served_by_pv_kwh: float
    load_served_by_battery_kwh: float
    load_served_by_grid_kwh: float
    pv_to_battery_kwh: float
    pv_to_export_kwh: float
    grid_to_battery_kwh: float
    battery_to_grid_kwh: float
    battery_charge_power_kw: float
    battery_discharge_power_kw: float
    slot_cost: float
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class ControlledActionResult:
    valid: bool
    observer_only: bool
    execution_allowed: bool
    total_cost: float = 0.0
    total_grid_import_kwh: float = 0.0
    total_grid_export_kwh: float = 0.0
    final_soc_kwh: float = 0.0
    min_soc_kwh: float = 0.0
    max_soc_kwh: float = 0.0
    trace: tuple[ControlledSlotTrace, ...] = ()
    errors: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = field(default_factory=lambda: ("observer_only_no_execution",))


def simulate_controlled_actions(
    simulation_input: Mapping[str, Any] | SimulationInput | None,
    action_intents: tuple[ActionIntent, ...] | list[ActionIntent] | None,
) -> ControlledActionResult:
    """Simulate candidate actions without execution permission."""

    loaded = build_simulation_input(simulation_input) if simulation_input is not None else None
    if loaded is None or not loaded.valid or loaded.simulation_input is None:
        errors = ("simulation_input_required",) if loaded is None else loaded.reason_codes + loaded.errors
        return _invalid_result(errors)

    offline_input = loaded.simulation_input
    input_validation = validate_simulation_input(offline_input)
    if not input_validation.valid:
        return _invalid_result(input_validation.errors)

    intent_validation = validate_action_intents(offline_input, action_intents)
    if not intent_validation.valid:
        return _invalid_result(intent_validation.errors)

    intents_by_slot = {intent.slot_index: intent for intent in action_intents or ()}
    battery = offline_input.battery
    soc = battery.initial_soc_kwh
    trace: list[ControlledSlotTrace] = []
    total_import = 0.0
    total_export = 0.0
    total_cost = 0.0
    min_soc = soc
    max_soc = soc

    for slot_index, slot in enumerate(offline_input.slots):
        intent = intents_by_slot.get(
            slot_index,
            ActionIntent(
                slot_index=slot_index,
                action_type="self_consumption",
                requested_energy_kwh=0.0,
                reason_codes=("default_self_consumption",),
            ),
        )
        soc_start = soc
        reasons: list[str] = list(intent.reason_codes)

        pv_to_load = min(slot.pv_kwh, slot.load_kwh)
        pv_surplus = slot.pv_kwh - pv_to_load
        remaining_load = slot.load_kwh - pv_to_load
        if pv_to_load > 0:
            reasons.append("pv_served_load_first")

        charge_input_limit = battery.charge_power_kw * slot.duration_hours
        soc_headroom = max(0.0, battery.max_soc_kwh - soc)
        pv_to_battery = min(pv_surplus, charge_input_limit, soc_headroom / battery.round_trip_efficiency)
        if pv_to_battery > 0:
            soc += pv_to_battery * battery.round_trip_efficiency
            reasons.append("pv_surplus_charged_battery")
        elif pv_surplus > 0 and soc_headroom <= 0:
            reasons.append("battery_full_export_surplus")
        elif pv_surplus > 0 and charge_input_limit <= 0:
            reasons.append("charge_power_zero_export_surplus")
        elif pv_surplus > 0:
            reasons.append("charge_power_limited_export_surplus")

        pv_to_export = pv_surplus - pv_to_battery
        if pv_to_export > 0:
            reasons.append("remaining_pv_exported")

        grid_to_battery = 0.0
        battery_to_load = 0.0
        battery_to_grid = 0.0
        clipped_energy = 0.0
        charge_input_used = pv_to_battery
        discharge_output_limit = battery.discharge_power_kw * slot.duration_hours
        discharge_floor = max(battery.min_soc_kwh, battery.reserve_kwh)

        if intent.action_type == "grid_charge_candidate":
            remaining_charge_input = max(0.0, charge_input_limit - charge_input_used)
            soc_headroom = max(0.0, battery.max_soc_kwh - soc)
            grid_to_battery = min(
                intent.requested_energy_kwh,
                remaining_charge_input,
                soc_headroom / battery.round_trip_efficiency,
            )
            if grid_to_battery > 0:
                soc += grid_to_battery * battery.round_trip_efficiency
                clipped_energy = grid_to_battery
                reasons.append("grid_charge_candidate_simulated")
            if intent.requested_energy_kwh > grid_to_battery:
                reasons.append("grid_charge_candidate_clipped")

        if intent.action_type in ("self_consumption", "battery_discharge_candidate"):
            available_output = max(0.0, soc - discharge_floor) * battery.round_trip_efficiency
            requested_output = remaining_load
            if intent.action_type == "battery_discharge_candidate":
                requested_output = min(remaining_load, intent.requested_energy_kwh)
            battery_to_load = min(requested_output, discharge_output_limit, available_output)
            if battery_to_load > 0:
                soc -= battery_to_load / battery.round_trip_efficiency
                remaining_load -= battery_to_load
                clipped_energy = battery_to_load
                reasons.append("battery_discharged_to_load")
            elif remaining_load > 0 and soc <= discharge_floor:
                reasons.append("reserve_floor_blocked_discharge")
            elif remaining_load > 0 and discharge_output_limit <= 0:
                reasons.append("discharge_power_zero_import_load")
            elif remaining_load > 0:
                reasons.append("discharge_power_limited_import_load")
            if intent.action_type == "battery_discharge_candidate" and intent.requested_energy_kwh > battery_to_load:
                reasons.append("battery_discharge_candidate_clipped")
        elif intent.action_type == "hold_candidate":
            if remaining_load > 0:
                reasons.append("hold_candidate_blocked_battery_discharge_to_load")
        elif intent.action_type == "export_candidate":
            available_output = max(0.0, soc - discharge_floor) * battery.round_trip_efficiency
            battery_to_grid = min(intent.requested_energy_kwh, discharge_output_limit, available_output)
            if battery_to_grid > 0:
                soc -= battery_to_grid / battery.round_trip_efficiency
                clipped_energy = battery_to_grid
                reasons.append("export_candidate_simulated")
            if intent.requested_energy_kwh > battery_to_grid:
                reasons.append("export_candidate_clipped")

        load_served_by_grid = remaining_load
        grid_import = load_served_by_grid + grid_to_battery
        grid_export = pv_to_export + battery_to_grid
        cost = (grid_import * slot.import_price_per_kwh) - (grid_export * slot.export_price_per_kwh)
        charge_power = (pv_to_battery + grid_to_battery) / slot.duration_hours
        discharge_power = (battery_to_load + battery_to_grid) / slot.duration_hours

        total_import += grid_import
        total_export += grid_export
        total_cost += cost
        min_soc = min(min_soc, soc)
        max_soc = max(max_soc, soc)
        trace.append(
            ControlledSlotTrace(
                slot_index=slot_index,
                slot_id=slot.slot_id,
                action_type_applied=intent.action_type,
                requested_energy_kwh=round(intent.requested_energy_kwh, 6),
                clipped_energy_kwh=round(clipped_energy, 6),
                soc_start_kwh=round(soc_start, 6),
                soc_end_kwh=round(soc, 6),
                grid_import_kwh=round(grid_import, 6),
                grid_export_kwh=round(grid_export, 6),
                load_served_by_pv_kwh=round(pv_to_load, 6),
                load_served_by_battery_kwh=round(battery_to_load, 6),
                load_served_by_grid_kwh=round(load_served_by_grid, 6),
                pv_to_battery_kwh=round(pv_to_battery, 6),
                pv_to_export_kwh=round(pv_to_export, 6),
                grid_to_battery_kwh=round(grid_to_battery, 6),
                battery_to_grid_kwh=round(battery_to_grid, 6),
                battery_charge_power_kw=round(charge_power, 6),
                battery_discharge_power_kw=round(discharge_power, 6),
                slot_cost=round(cost, 6),
                reason_codes=tuple(reasons or ["balanced_no_battery_action"]),
            )
        )

    return ControlledActionResult(
        valid=True,
        observer_only=True,
        execution_allowed=False,
        total_cost=round(total_cost, 6),
        total_grid_import_kwh=round(total_import, 6),
        total_grid_export_kwh=round(total_export, 6),
        final_soc_kwh=round(soc, 6),
        min_soc_kwh=round(min_soc, 6),
        max_soc_kwh=round(max_soc, 6),
        trace=tuple(trace),
        reason_codes=("controlled_action_intent_simulation", "observer_only_no_execution"),
    )


def _invalid_result(errors: tuple[str, ...]) -> ControlledActionResult:
    return ControlledActionResult(
        valid=False,
        observer_only=True,
        execution_allowed=False,
        errors=errors,
        reason_codes=("invalid_input_no_action", "observer_only_no_execution"),
    )


__all__ = ["ControlledActionResult", "ControlledSlotTrace", "simulate_controlled_actions"]
