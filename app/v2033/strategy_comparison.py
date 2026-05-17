"""Offline three-strategy comparison harness.

The strategies are advisory only. Candidate strategies identify deterministic
windows but do not execute or alter the canonical self-consumption simulation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.v2000.predbat_lesson_simulation_contract import SimulationInput, SimulationResult
from app.v2001.canonical_self_consumption_simulator import simulate_self_consumption
from app.v2032.fixture_replay_contract import build_simulation_input


@dataclass(frozen=True)
class StrategyScore:
    strategy_name: str
    valid: bool
    execution_allowed: bool
    total_cost: float
    total_grid_import_kwh: float
    total_grid_export_kwh: float
    final_soc_kwh: float
    min_soc_kwh: float
    action_change_count: int
    reason_codes: tuple[str, ...]
    candidate_slot_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class StrategyComparison:
    valid: bool
    scores: tuple[StrategyScore, ...]
    reason_codes: tuple[str, ...]


def compare_strategies(fixture: Mapping[str, Any] | SimulationInput) -> StrategyComparison:
    """Return deterministic scores for the three offline strategies."""

    loaded = build_simulation_input(fixture)
    if not loaded.valid or loaded.simulation_input is None:
        return StrategyComparison(
            valid=False,
            scores=(
                _invalid_score("baseline_self_consumption", loaded.reason_codes + loaded.errors),
                _invalid_score("cheapest_window_charge", loaded.reason_codes + loaded.errors),
                _invalid_score("export_aware_placeholder", loaded.reason_codes + loaded.errors),
            ),
            reason_codes=loaded.reason_codes + loaded.errors,
        )

    simulation_input = loaded.simulation_input
    baseline = baseline_self_consumption(simulation_input)
    cheapest = cheapest_window_charge(simulation_input)
    export_aware = export_aware_placeholder(simulation_input)
    return StrategyComparison(
        valid=all(score.valid for score in (baseline, cheapest, export_aware)),
        scores=(baseline, cheapest, export_aware),
        reason_codes=("offline_fixture_replay", "three_strategy_comparison", "observer_only_no_execution"),
    )


def baseline_self_consumption(simulation_input: SimulationInput) -> StrategyScore:
    """Score the canonical PV-first self-consumption simulation."""

    result = simulate_self_consumption(simulation_input)
    return _score_from_result(
        strategy_name="baseline_self_consumption",
        result=result,
        reason_codes=result.reason_codes,
    )


def cheapest_window_charge(simulation_input: SimulationInput) -> StrategyScore:
    """Identify cheapest import-price slots without performing grid charging."""

    result = simulate_self_consumption(simulation_input)
    if not result.valid:
        return _score_from_result(
            strategy_name="cheapest_window_charge",
            result=result,
            reason_codes=result.reason_codes + ("invalid_input_no_candidate_window",),
        )

    cheapest = min(
        simulation_input.slots,
        key=lambda slot: (slot.import_price_per_kwh, slot.slot_id),
    )
    return _score_from_result(
        strategy_name="cheapest_window_charge",
        result=result,
        reason_codes=(
            "candidate_window_only",
            "grid_charge_not_supported_by_simulator",
            "observer_only_no_execution",
        ),
        candidate_slot_ids=(cheapest.slot_id,),
        action_change_count=0,
    )


def export_aware_placeholder(simulation_input: SimulationInput) -> StrategyScore:
    """Identify highest export-price slots without performing export actions."""

    result = simulate_self_consumption(simulation_input)
    if not result.valid:
        return _score_from_result(
            strategy_name="export_aware_placeholder",
            result=result,
            reason_codes=result.reason_codes + ("invalid_input_no_candidate_window",),
        )

    highest = min(
        simulation_input.slots,
        key=lambda slot: (-slot.export_price_per_kwh, slot.slot_id),
    )
    return _score_from_result(
        strategy_name="export_aware_placeholder",
        result=result,
        reason_codes=(
            "candidate_window_only",
            "controlled_export_not_supported_by_simulator",
            "observer_only_no_execution",
        ),
        candidate_slot_ids=(highest.slot_id,),
        action_change_count=0,
    )


def _score_from_result(
    *,
    strategy_name: str,
    result: SimulationResult,
    reason_codes: tuple[str, ...],
    candidate_slot_ids: tuple[str, ...] = (),
    action_change_count: int | None = None,
) -> StrategyScore:
    soc_values = [trace.soc_end_kwh for trace in result.trace]
    if result.trace:
        soc_values.append(result.trace[0].soc_start_kwh)
    min_soc = min(soc_values) if soc_values else 0.0
    return StrategyScore(
        strategy_name=strategy_name,
        valid=result.valid,
        execution_allowed=False,
        total_cost=result.total_cost,
        total_grid_import_kwh=result.total_import_kwh,
        total_grid_export_kwh=result.total_export_kwh,
        final_soc_kwh=result.final_soc_kwh,
        min_soc_kwh=round(min_soc, 6),
        action_change_count=_action_change_count(result) if action_change_count is None else action_change_count,
        reason_codes=reason_codes,
        candidate_slot_ids=candidate_slot_ids,
    )


def _action_change_count(result: SimulationResult) -> int:
    states = tuple(_action_state(trace.battery_power_kw) for trace in result.trace)
    return sum(1 for previous, current in zip(states, states[1:]) if previous != current)


def _action_state(power_kw: float) -> str:
    if power_kw > 0:
        return "charge"
    if power_kw < 0:
        return "discharge"
    return "idle"


def _invalid_score(strategy_name: str, reason_codes: tuple[str, ...]) -> StrategyScore:
    return StrategyScore(
        strategy_name=strategy_name,
        valid=False,
        execution_allowed=False,
        total_cost=0.0,
        total_grid_import_kwh=0.0,
        total_grid_export_kwh=0.0,
        final_soc_kwh=0.0,
        min_soc_kwh=0.0,
        action_change_count=0,
        reason_codes=reason_codes,
    )


__all__ = [
    "StrategyComparison",
    "StrategyScore",
    "baseline_self_consumption",
    "cheapest_window_charge",
    "compare_strategies",
    "export_aware_placeholder",
]

