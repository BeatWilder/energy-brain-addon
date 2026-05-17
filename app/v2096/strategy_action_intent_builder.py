"""Build deterministic offline strategy action intents.

These helpers translate candidate strategy choices into V2064 action intents.
They are pure selectors: no runtime access, no execution permission, and no
side effects.
"""

from __future__ import annotations

from app.v2000.predbat_lesson_simulation_contract import SimulationInput
from app.v2064.action_intent_contract import ActionIntent


def build_baseline_action_intents(simulation_input: SimulationInput) -> tuple[ActionIntent, ...]:
    """Return no explicit actions so V2065 applies self-consumption defaults."""

    _ = simulation_input
    return ()


def build_cheapest_window_charge_intents(
    simulation_input: SimulationInput,
    requested_energy_kwh: float,
) -> tuple[ActionIntent, ...]:
    """Select cheapest import-price slots for candidate grid charging."""

    if requested_energy_kwh <= 0:
        return ()

    remaining_energy = float(requested_energy_kwh)
    intents: list[ActionIntent] = []
    battery = simulation_input.battery
    ranked_slots = sorted(
        enumerate(simulation_input.slots),
        key=lambda item: (item[1].import_price_per_kwh, item[0]),
    )

    for slot_index, slot in ranked_slots:
        if remaining_energy <= 0:
            break
        per_slot_request = min(remaining_energy, battery.charge_power_kw * slot.duration_hours)
        if per_slot_request <= 0:
            continue
        intents.append(
            ActionIntent(
                slot_index=slot_index,
                action_type="grid_charge_candidate",
                requested_energy_kwh=round(per_slot_request, 6),
                reason_codes=("cheapest_import_price_slot", "observer_only_no_execution"),
            )
        )
        remaining_energy -= per_slot_request

    return tuple(intents)


def build_export_aware_intents(
    simulation_input: SimulationInput,
    requested_energy_kwh: float,
) -> tuple[ActionIntent, ...]:
    """Select highest export-price slots for candidate battery export."""

    if requested_energy_kwh <= 0:
        return ()

    remaining_energy = float(requested_energy_kwh)
    intents: list[ActionIntent] = []
    battery = simulation_input.battery
    ranked_slots = sorted(
        enumerate(simulation_input.slots),
        key=lambda item: (-item[1].export_price_per_kwh, item[0]),
    )

    for slot_index, slot in ranked_slots:
        if remaining_energy <= 0:
            break
        per_slot_request = min(remaining_energy, battery.discharge_power_kw * slot.duration_hours)
        if per_slot_request <= 0:
            continue
        intents.append(
            ActionIntent(
                slot_index=slot_index,
                action_type="export_candidate",
                requested_energy_kwh=round(per_slot_request, 6),
                reason_codes=("highest_export_price_slot", "observer_only_no_execution"),
            )
        )
        remaining_energy -= per_slot_request

    return tuple(intents)


def build_hold_reserve_intents(
    simulation_input: SimulationInput,
    min_import_price_threshold: float | None = None,
) -> tuple[ActionIntent, ...]:
    """Select deterministic high-risk slots for reserve-hold simulation."""

    if not simulation_input.slots:
        return ()

    if min_import_price_threshold is None:
        selected_indexes = [
            slot_index
            for slot_index, slot in enumerate(simulation_input.slots)
            if slot.load_kwh > slot.pv_kwh
        ]
    else:
        threshold = float(min_import_price_threshold)
        selected_indexes = [
            slot_index
            for slot_index, slot in enumerate(simulation_input.slots)
            if slot.import_price_per_kwh >= threshold
        ]

    return tuple(
        ActionIntent(
            slot_index=slot_index,
            action_type="hold_candidate",
            requested_energy_kwh=0.0,
            reason_codes=("hold_reserve_candidate_slot", "observer_only_no_execution"),
        )
        for slot_index in selected_indexes
    )


__all__ = [
    "build_baseline_action_intents",
    "build_cheapest_window_charge_intents",
    "build_export_aware_intents",
    "build_hold_reserve_intents",
]
