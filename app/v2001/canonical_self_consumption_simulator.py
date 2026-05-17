"""Canonical offline self-consumption simulator.

The simulator is advisory only: it cannot authorize runtime execution and it
does not include any integration-facing write surface.
"""

from __future__ import annotations

from app.v2000.predbat_lesson_simulation_contract import (
    EnergySlot,
    SimulationInput,
    SimulationResult,
    SlotTrace,
    no_action_result,
    validate_simulation_input,
)


def simulate_self_consumption(simulation_input: SimulationInput) -> SimulationResult:
    """Simulate PV-first self-consumption with battery buffering."""

    validation = validate_simulation_input(simulation_input)
    if not validation.valid:
        return no_action_result(validation.errors)

    battery = simulation_input.battery
    soc = battery.initial_soc_kwh
    trace: list[SlotTrace] = []
    total_import = 0.0
    total_export = 0.0
    total_cost = 0.0

    for slot in simulation_input.slots:
        soc_start = soc
        reasons: list[str] = []

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

        export_kwh = pv_surplus - pv_to_battery
        if export_kwh > 0:
            reasons.append("remaining_pv_exported")

        discharge_floor = max(battery.min_soc_kwh, battery.reserve_kwh)
        discharge_output_limit = battery.discharge_power_kw * slot.duration_hours
        available_output = max(0.0, soc - discharge_floor) * battery.round_trip_efficiency
        battery_to_load = min(remaining_load, discharge_output_limit, available_output)
        if battery_to_load > 0:
            soc -= battery_to_load / battery.round_trip_efficiency
            remaining_load -= battery_to_load
            reasons.append("battery_discharged_to_load")
        elif remaining_load > 0 and soc <= discharge_floor:
            reasons.append("reserve_floor_blocked_discharge")
        elif remaining_load > 0 and discharge_output_limit <= 0:
            reasons.append("discharge_power_zero_import_load")
        elif remaining_load > 0:
            reasons.append("discharge_power_limited_import_load")

        import_kwh = remaining_load
        if import_kwh > 0:
            reasons.append("remaining_load_imported")

        cost = (import_kwh * slot.import_price_per_kwh) - (export_kwh * slot.export_price_per_kwh)
        battery_power_kw = (pv_to_battery - battery_to_load) / slot.duration_hours

        trace.append(
            SlotTrace(
                slot_id=slot.slot_id,
                soc_start_kwh=round(soc_start, 6),
                soc_end_kwh=round(soc, 6),
                pv_kwh=slot.pv_kwh,
                load_kwh=slot.load_kwh,
                pv_to_load_kwh=round(pv_to_load, 6),
                pv_to_battery_kwh=round(pv_to_battery, 6),
                battery_to_load_kwh=round(battery_to_load, 6),
                import_kwh=round(import_kwh, 6),
                export_kwh=round(export_kwh, 6),
                battery_power_kw=round(battery_power_kw, 6),
                cost=round(cost, 6),
                reason_codes=tuple(reasons or ["balanced_no_battery_action"]),
            )
        )
        total_import += import_kwh
        total_export += export_kwh
        total_cost += cost

    return SimulationResult(
        valid=True,
        observer_only=simulation_input.observer_only,
        execution_allowed=False,
        total_import_kwh=round(total_import, 6),
        total_export_kwh=round(total_export, 6),
        total_cost=round(total_cost, 6),
        final_soc_kwh=round(soc, 6),
        trace=tuple(trace),
        reason_codes=("observer_only_no_execution", "offline_self_consumption_simulation"),
    )


__all__ = [
    "EnergySlot",
    "SimulationInput",
    "SimulationResult",
    "SlotTrace",
    "simulate_self_consumption",
    "validate_simulation_input",
]
