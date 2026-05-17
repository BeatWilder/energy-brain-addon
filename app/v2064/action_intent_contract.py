"""Typed offline action-intent contract.

Action intents are candidate instructions for deterministic simulation only.
This layer cannot authorize or perform execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.v2000.predbat_lesson_simulation_contract import SimulationInput


ACTION_TYPES = frozenset(
    {
        "self_consumption",
        "grid_charge_candidate",
        "battery_discharge_candidate",
        "export_candidate",
        "hold_candidate",
    }
)


@dataclass(frozen=True)
class ActionIntent:
    slot_index: int
    action_type: str
    requested_energy_kwh: float
    reason_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class ActionIntentValidation:
    valid: bool
    errors: tuple[str, ...] = ()


def validate_action_intents(
    simulation_input: SimulationInput | None,
    action_intents: Iterable[ActionIntent] | None,
) -> ActionIntentValidation:
    """Validate action intents against an already-loaded simulation input."""

    errors: list[str] = []
    if simulation_input is None:
        errors.append("simulation_input_required")
    if action_intents is None:
        errors.append("action_intents_required")

    if errors:
        return ActionIntentValidation(valid=False, errors=tuple(errors))

    slot_count = len(simulation_input.slots)
    seen: set[int] = set()
    for index, intent in enumerate(action_intents):
        prefix = f"action_intent_{index}"
        if not isinstance(intent, ActionIntent):
            errors.append(f"{prefix}_typed_contract_required")
            continue
        if intent.slot_index < 0 or intent.slot_index >= slot_count:
            errors.append(f"{prefix}_slot_index_out_of_range")
        if intent.slot_index in seen:
            errors.append(f"{prefix}_duplicate_slot_index")
        seen.add(intent.slot_index)
        if intent.action_type not in ACTION_TYPES:
            errors.append(f"{prefix}_unknown_action_type")
        if intent.requested_energy_kwh < 0:
            errors.append(f"{prefix}_requested_energy_must_be_non_negative")

    return ActionIntentValidation(valid=not errors, errors=tuple(errors))


__all__ = [
    "ACTION_TYPES",
    "ActionIntent",
    "ActionIntentValidation",
    "validate_action_intents",
]
